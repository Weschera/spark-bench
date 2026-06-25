import html
import json
import os
import re
import shutil


def infer_run_kind(label):
    lo = (label or '').lower()
    if any(x in lo for x in ('smoke', 'fixcheck', 'verify', 'debug', 'probe', 'diagnostic')):
        return 'diagnostic'
    return 'benchmark'


def esc(value):
    return html.escape('' if value is None else str(value), quote=True)


def fnum(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt(value):
    n = fnum(value)
    if n is None:
        return esc(value)
    if abs(n) >= 100:
        return f'{n:.0f}'
    if abs(n) >= 10:
        return f'{n:.1f}'
    return f'{n:.2f}'


def inline_md(value):
    value = esc(value)
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)
    value = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', value)
    return value


def markdown_to_html(lines):
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith('#'):
            level = min(3, len(line) - len(line.lstrip('#')))
            out.append(f'<h{level}>{inline_md(line[level:].strip())}</h{level}>')
            i += 1
            continue
        if line.startswith('|') and i + 1 < len(lines) and re.match(r'^\|[-:| ]+\|?$', lines[i + 1]):
            table = []
            while i < len(lines) and lines[i].startswith('|'):
                table.append(lines[i])
                i += 1
            headers = [c.strip() for c in table[0].strip('|').split('|')]
            out.append('<table><thead><tr>' + ''.join(f'<th>{inline_md(h)}</th>' for h in headers) + '</tr></thead><tbody>')
            for row in table[2:]:
                cells = [c.strip() for c in row.strip('|').split('|')]
                cells += [''] * max(0, len(headers) - len(cells))
                out.append('<tr>' + ''.join(f'<td>{inline_md(c)}</td>' for c in cells[:len(headers)]) + '</tr>')
            out.append('</tbody></table>')
            continue
        if line.startswith('- '):
            out.append('<ul>')
            while i < len(lines) and lines[i].startswith('- '):
                out.append(f'<li>{inline_md(lines[i][2:].strip())}</li>')
                i += 1
            out.append('</ul>')
            continue
        out.append(f'<p>{inline_md(line)}</p>')
        i += 1
    return '\n'.join(out)


def row_table(rows):
    if not rows:
        return '<p class="muted">No CSV rows recorded.</p>'
    fields = ['tier', 'workload', 'metric', 'value', 'unit', 'context', 'batch', 'notes']
    body = []
    for row in rows:
        body.append('<tr>' + ''.join(f'<td>{esc(row.get(field, ""))}</td>' for field in fields) + '</tr>')
    return '<table><thead><tr>' + ''.join(f'<th>{field}</th>' for field in fields) + '</tr></thead><tbody>' + ''.join(body) + '</tbody></table>'


def bar(label, value, detail='', warn=False):
    numeric = fnum(value)
    width = max(0.0, min(100.0, numeric or 0.0))
    cls = ' warn' if warn else ''
    return (
        f'<div class="barrow"><div><strong>{esc(label)}</strong><span>{esc(detail)}</span></div>'
        f'<b>{fmt(value)}</b><div class="bar{cls}"><i style="width:{width:.1f}%"></i></div></div>'
    )


def sections(ctx):
    rows = ctx.rows
    overall = {r['metric']: r['value'] for r in rows if r.get('tier') == 'eval' and r.get('workload') == 'overall'}
    domains = [r for r in rows if r.get('tier') == 'eval' and r.get('metric') == 'domain_quality']
    scenarios = [r for r in rows if r.get('tier') == 'eval' and r.get('metric') == 'score']

    def metric(name):
        if overall.get(name) is not None:
            return overall[name]
        if name == 'capability_score':
            return overall.get('quality')
        if name == 'operational_score':
            eff = fnum(overall.get('efficiency'))
            resp = fnum(overall.get('responsiveness'))
            vals = [(eff, 0.10), (resp, 0.15)]
            vals = [(v, w) for v, w in vals if v is not None]
            if vals:
                return sum(v * w for v, w in vals) / sum(w for _, w in vals)
        return None

    cards = [('Run kind', ctx.run_kind), ('Rows', len(rows)), ('Topology', ctx.topology),
             ('Parallelism', ctx.parallelism), ('Spec decode', ctx.spec_decode)]
    if overall.get('truescore') is not None:
        cards.insert(0, ('TrueScore', fmt(overall['truescore'])))
    if metric('capability_score') is not None:
        cards.insert(1, ('Capability', fmt(metric('capability_score'))))
    if metric('operational_score') is not None:
        cards.insert(2, ('Operational', fmt(metric('operational_score'))))
    if overall.get('median_latency') is not None:
        cards.insert(3, ('Median latency', f"{fmt(overall['median_latency'])}s"))

    card_html = ''.join(f'<div class="card"><span>{esc(k)}</span><strong>{esc(v)}</strong></div>' for k, v in cards)

    component_html = ''.join(
        bar(label, value)
        for label, value in (
            ('Capability Score', metric('capability_score')),
            ('Operational Score', metric('operational_score')),
            ('quality', overall.get('quality')),
            ('calibration', overall.get('calibration')),
            ('reliability', overall.get('reliability')),
            ('efficiency', overall.get('efficiency')),
            ('responsiveness', overall.get('responsiveness')),
        )
        if value is not None
    )
    if not component_html:
        numeric = [r for r in rows if fnum(r.get('value')) is not None][:24]
        component_html = ''.join(bar(f"{r['workload']} / {r['metric']}", r['value'], f"{r.get('unit', '')} {r.get('notes', '')}") for r in numeric)
    if not component_html:
        component_html = '<p class="muted">No numeric metrics recorded.</p>'

    domain_html = ''.join(bar(r['workload'], r['value'], r.get('notes', '')) for r in domains)
    if not domain_html:
        domain_html = '<p class="muted">No eval domain rows for this run.</p>'

    scenario_html = ''.join(bar(r['workload'], 100 * (fnum(r['value']) or 0), r.get('notes', ''), (fnum(r['value']) or 0) < 0.75) for r in scenarios)
    if not scenario_html:
        scenario_html = '<p class="muted">No per-scenario eval rows for this run.</p>'
    return card_html, component_html, domain_html, scenario_html


CSS = '''
:root { color-scheme: dark; --bg:#101113; --panel:#191b1f; --panel2:#20242b; --text:#f4f1e8; --muted:#aeb4bc; --line:rgba(255,255,255,.11); --green:#35d07f; --cyan:#5dc8ff; --amber:#f5b84b; --red:#ff6b6b; }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--text); font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; }
.wrap { max-width:1180px; margin:0 auto; padding:26px 20px 44px; }
header { display:grid; grid-template-columns:1.1fr .9fr; gap:16px; align-items:stretch; margin-bottom:16px; }
.hero,.panel,.card { background:var(--panel); border:1px solid var(--line); border-radius:8px; box-shadow:0 18px 60px rgba(0,0,0,.25); }
.hero { padding:22px; }
h1 { margin:6px 0 10px; font-size:clamp(26px,5vw,46px); line-height:1; letter-spacing:0; overflow-wrap:anywhere; }
h2 { margin:0 0 14px; font-size:18px; letter-spacing:0; }
h3 { margin:18px 0 8px; font-size:15px; }
.muted,.meta,.card span,.barrow span { color:var(--muted); }
.meta { display:grid; gap:5px; font-size:13px; }
.cards { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; }
.card { padding:14px; min-height:74px; }
.card span { display:block; font-size:12px; text-transform:uppercase; letter-spacing:.08em; }
.card strong { display:block; margin-top:7px; font-size:25px; line-height:1.1; overflow-wrap:anywhere; }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.panel { padding:18px; margin-bottom:16px; overflow:hidden; }
.barrow { display:grid; grid-template-columns:minmax(190px,1fr) 64px; gap:10px; align-items:center; padding:9px 0; border-bottom:1px solid rgba(255,255,255,.07); }
.barrow:last-child { border-bottom:0; }
.barrow strong { display:block; overflow-wrap:anywhere; }
.barrow span { display:block; font-size:12px; overflow-wrap:anywhere; }
.barrow b { text-align:right; font-variant-numeric:tabular-nums; }
.bar { grid-column:1 / -1; height:10px; background:rgba(255,255,255,.09); border-radius:999px; overflow:hidden; }
.bar i { display:block; height:100%; width:0; background:linear-gradient(90deg,var(--cyan),var(--green)); border-radius:999px; animation:grow .9s cubic-bezier(.2,.8,.2,1) forwards; }
.bar.warn i { background:linear-gradient(90deg,var(--red),var(--amber)); }
@keyframes grow { from { width:0; } }
table { width:100%; border-collapse:collapse; background:var(--panel2); border:1px solid var(--line); border-radius:8px; overflow:hidden; margin:10px 0 18px; }
th,td { padding:8px 9px; border-bottom:1px solid rgba(255,255,255,.08); text-align:left; font-size:13px; vertical-align:top; }
th { color:var(--muted); text-transform:uppercase; letter-spacing:.05em; font-size:11px; }
tr:last-child td { border-bottom:0; }
code { background:#262a31; padding:1px 4px; border-radius:4px; }
pre { white-space:pre-wrap; background:#0c0d10; border:1px solid var(--line); border-radius:8px; padding:14px; overflow:auto; }
a { color:#8bd9ff; }
details summary { cursor:pointer; color:#8bd9ff; margin:8px 0; }
@media (max-width:900px) { header,.grid { grid-template-columns:1fr; } .cards { grid-template-columns:repeat(2,minmax(0,1fr)); } }
@media (max-width:560px) { .cards { grid-template-columns:1fr; } .wrap { padding:16px 12px 32px; } }
'''


def render_report(ctx):
    card_html, component_html, domain_html, scenario_html = sections(ctx)
    raw_md = esc('\n'.join(ctx.md))
    data_json = esc(json.dumps({'run_id': ctx.run_id, 'rows': ctx.rows}, indent=2))
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc('spark-bench report: ' + ctx.run_id)}</title>
<style>{CSS}</style>
</head>
<body>
<main class="wrap">
  <header>
    <section class="hero">
      <div class="muted">spark-bench HTML report</div>
      <h1>{esc(ctx.run_id)}</h1>
      <div class="meta">
        <div><strong>label:</strong> {esc(ctx.label)}</div>
        <div><strong>model:</strong> {esc(ctx.model or 'n/a')}</div>
        <div><strong>endpoint:</strong> {esc(ctx.endpoint or 'n/a')}</div>
        <div><strong>notes:</strong> {esc(ctx.notes or 'n/a')}</div>
      </div>
    </section>
    <section class="cards">{card_html}</section>
  </header>
  <section class="grid">
    <section class="panel"><h2>Score Components / Key Metrics</h2>{component_html}</section>
    <section class="panel"><h2>Domain Breakdown</h2>{domain_html}</section>
  </section>
  <section class="panel"><h2>Per-Scenario Results</h2>{scenario_html}</section>
  <section class="panel"><h2>Rendered Summary</h2>{markdown_to_html(ctx.md)}</section>
  <section class="panel"><h2>All Recorded Rows</h2>{row_table(ctx.rows)}</section>
  <section class="panel">
    <h2>Raw Artifacts</h2>
    <details><summary>Raw markdown summary</summary><pre>{raw_md}</pre></details>
    <details><summary>Raw JSON rows</summary><pre>{data_json}</pre></details>
  </section>
</main>
</body>
</html>
'''


def write_run_report(ctx, html_path):
    os.makedirs(os.path.dirname(html_path), exist_ok=True)
    with open(html_path, 'w') as f:
        f.write(render_report(ctx))
    latest_path = os.path.join(ctx.out_dir, 'latest.html')
    shutil.copyfile(html_path, latest_path)
    return html_path, latest_path
