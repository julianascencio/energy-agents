"""HTML review for real CEN observations, without synthetic monetary values."""

from html import escape


def render_cen_report(result):
    def e(value):
        return escape(str(value), quote=True)

    summary = result["summary"]
    queue = "".join(
        f"<tr><td>{a['rank']}</td><td>{e(a['asset_id'])}</td><td>{a['shortfall_mwh']:,.2f}</td></tr>"
        for a in result["investigation_queue"][:10]
    )
    notices = "".join(
        f"<li><strong>{e(a['asset_id'])}</strong> · {e(a['state'].replace('_', ' '))}<br>"
        + "<br>".join(
            f"{n['reported_availability_percent']:g}% reported · {e(n['category'])} · "
            f"{e(', '.join(n['notice_ids']))} "
            f'<a href="{e(n["source_url"])}#page={n["source_page"]}">Source page {n["source_page"]}</a>'
            for n in a["latest_notices"]
        )
        + "</li>"
        for a in result["availability_queue"]
    )
    rows = []
    for a in result["assets"]:
        k = a["ledger"]
        sources = "".join(
            f'<li><a href="{e(s["source_url"])}#page={s["generation_row"]["source_page"]}">'
            f"{e(s['report_date'])} · page {s['generation_row']['source_page']}</a>: "
            f"{s['generation_row']['scheduled_mwh']:,.2f} scheduled / "
            f"{s['generation_row']['actual_mwh']:,.2f} actual MWh</li>"
            for s in a["evidence"]
            if s["generation_row"] is not None
        )
        actions = "".join(f"<li>{e(action['title'])} · draft</li>" for action in a["actions"])
        rows.append(
            f'<tr class="asset" data-name="{e(a["asset_id"].lower())}"><td><b>{e(a["asset_id"])}</b>'
            f"<br><small>{e(a['state'].replace('_', ' '))}</small>"
            f"<details><summary>Evidence and proposed actions</summary><ul>{sources}{actions}</ul>"
            f"<p>Missing dates: {e(', '.join(k['missing_dates']) or 'none')}</p></details></td>"
            f"<td>{k['scheduled_mwh']:,.2f}</td><td>{k['actual_mwh']:,.2f}</td>"
            f"<td>{k['shortfall_mwh']:,.2f}</td><td>{k['above_schedule_mwh']:,.2f}</td>"
            f"<td>{k['coverage_fraction']:.0%}</td></tr>"
        )
    return (
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CEN Chile | Operations review</title>
<style>*{box-sizing:border-box}body{margin:0;background:#f0f5f6;color:#173440;font:15px/1.55 system-ui,sans-serif}
header{background:#12313d;color:white;padding:36px max(24px,calc((100vw - 1200px)/2));}header p{color:#bbd7de}
h1{font-size:clamp(30px,5vw,46px);margin:20px 0 10px;line-height:1.15}header small{letter-spacing:2px}
main{max-width:1250px;margin:auto;padding:26px}a{color:#087c83}header a{color:#9be7db}h2{font-size:21px}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,.panel{background:white;padding:22px;
border:1px solid #d7e3e6;border-radius:12px}.card b{display:block;font-size:27px;color:#087c83}.card span{font-size:12px}
.columns{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin:24px 0}.panel{min-width:0}
.note{background:#fff2d5;color:#695326;padding:16px;border-radius:8px;margin:20px 0}table{width:100%;border-collapse:collapse}
th,td{padding:12px;border-bottom:1px solid #e3eaed;text-align:right;vertical-align:top;font-size:13px}
th:first-child,td:first-child{text-align:left}th{background:#e9f1f3;font-size:11px;text-transform:uppercase}
td:first-child{min-width:200px}li{margin:12px 0}small{color:#667d88}header small{color:#add4da}
details{font-size:12px;text-align:left;max-width:480px}summary{cursor:pointer;color:#087c83;margin-top:8px}
.scroll{overflow-x:auto}input{padding:12px;border:1px solid #abc0c7;border-radius:7px;font:inherit;max-width:100%}
footer{font-size:12px;color:#546d78;margin:26px 0}.asset[hidden]{display:none}
@media(max-width:800px){.columns{grid-template-columns:1fr}.cards{grid-template-columns:1fr 1fr}main{padding:16px}}
</style></head><body><header><small>ASVA · ENERGY OPERATIONS / CHILE</small>
<h1>Real observations.<br>Evidence before intervention.</h1><p>Coordinador Eléctrico Nacional · """
        + e(result["period_start"])
        + " to "
        + e(result["period_end"])
        + """ · America/Santiago</p>
<a href="portfolio.json" download>Review JSON</a> · <a href="input.json" download>Source snapshot</a> ·
<a href="work_orders.json" download>Investigation drafts</a></header><main><div class="cards">"""
        + (
            f'<div class="card"><b>{summary["assets"]}</b><span>PFV source identities · {summary["reports"]} reports</span></div>'
            f'<div class="card"><b>{summary["actual_mwh"]:,.0f}</b><span>Reported actual generation · MWh</span></div>'
            f'<div class="card"><b>{summary["shortfall_mwh"]:,.0f}</b><span>Sum of daily schedule shortfalls · MWh</span></div>'
            '<div class="card"><b>Not valued</b><span>Financial recovery requires additional evidence</span></div>'
        )
        + """</div><div class="note"><strong>A schedule is not technical production potential.</strong>
Shortfalls do not establish equipment losses, curtailment or recoverable revenue. Zero scheduled and
actual generation can coexist with a reported outage. These are report snapshots, subject to revision.</div>
<div class="columns"><section class="panel"><h2>Largest schedule shortfalls</h2>
<p>Investigation order by summed daily MWh, not a repair, safety or financial priority.</p>
<table><thead><tr><th>Rank</th><th>Plant</th><th>MWh</th></tr></thead><tbody>"""
        + queue
        + """</tbody></table>
</section><section class="panel"><h2>Reported availability requires follow-up</h2>
<p>Notices in the final report date. Percentages are source declarations, not calculated time availability.</p>
<ul>"""
        + (notices or "<li>No matching notices in the selected final report.</li>")
        + """</ul></section></div>
<section class="panel"><h2>Plant-by-plant evidence</h2><label>Find a plant <input id="search" type="search"
placeholder="e.g. Huatacondo"></label><p>All energy columns are MWh. Coverage measures comparable report days.</p>
<div class="scroll"><table><thead><tr><th>Source plant identity</th><th>Scheduled</th><th>Actual</th>
<th>Shortfall</th><th>Above schedule</th><th>Coverage</th></tr></thead><tbody>"""
        + "".join(rows)
        + """</tbody>
</table></div></section><footer>Five deterministic professional-role reviews · EDI calculations executed locally.
MCP hosts can use the same review tools conversationally. All actions are drafts; nothing is dispatched.<br>
Scope: PFV-prefixed section 1.1 rows, not the entire Chilean solar fleet. No nodal/PPA prices or technical
production baselines are supplied. Full source hashes and page references are in the JSON exports.<br>
Input SHA-256: """
        + e(result["input_sha256"])
        + """</footer></main><script>
document.getElementById('search').addEventListener('input',event=>{const q=event.target.value.toLowerCase();
document.querySelectorAll('.asset').forEach(row=>row.hidden=!row.dataset.name.includes(q))});
</script></body></html>"""
    )
