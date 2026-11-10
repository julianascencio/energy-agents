"""Portable HTML decision report with local filtering and expandable evidence."""

from html import escape


def render_report(result):
    """Escape every data value; no external scripts, fonts, CDNs or data requests."""

    def e(value):
        return escape(str(value), quote=True)

    summaries = []
    for group in result["summaries"]:
        summaries.append(
            f'<section class="summary"><div><p class="eyebrow">COMPARABLE REVIEW WINDOW</p>'
            f"<h2>{e(group['currency'])} · {e(group['period_start'])} → {e(group['period_end'])}</h2>"
            f"<p>{e(group['timezone'])} · {group['assets']} assets · "
            f"{group['held_assets']} held for missing data</p></div>"
            f'<div><span class="big">{group["ranked_conditional_net_value"]:,.0f}</span>'
            f"<p>{e(group['currency'])} conditional net value in ranked opportunities</p></div>"
            f'<p class="subtle">Observed deficit: {group["observed_deficit_mwh"]:,.1f} MWh. '
            "Recovery assumes an equivalent repeat period; it is not a forecast.</p></section>"
        )
    rankings = []
    for group in result["summaries"]:
        for action in group["ranked_actions"]:
            rankings.append(
                f'<div class="rank"><strong>#{action["rank"]} · {e(action["asset_id"])}</strong>'
                f"<span>{e(group['period_start'])} → {e(group['period_end'])}</span>"
                f"<b>{action['conditional_net_value']:,.0f} {e(action['currency'])}</b>"
                "<span>Inspect evidence and confirm repair scope</span></div>"
            )
    cards = []
    for asset in result["assets"]:
        ledger = asset["ledger"]
        kinds = ", ".join(sorted({v["kind"] for v in asset["evidence"].values()}))
        bars = []
        for label, amount in ledger["deficit_by_event_mwh"].items():
            width = 100 * amount / ledger["deficit_mwh"] if ledger["deficit_mwh"] else 0
            bars.append(
                f'<div class="barrow"><span>{e(label.replace("_", " "))}</span>'
                f'<div class="track"><div class="bar {e(label)}" style="width:{width:.3f}%"></div></div>'
                f"<b>{amount:,.1f} MWh</b></div>"
            )
        evidence = "".join(
            f"<li><b>{e(key)}</b> · {e(source['kind'])} · {e(source['verification'])}"
            f"<br>{e(source['source'])}</li>"
            for key, source in asset["evidence"].items()
        )
        actions = "".join(
            f"<li>{e(a['title'])}<br><small>{e(a['owner'].replace('_', ' '))} · Draft</small></li>"
            for a in asset["actions"]
        )
        missing = list(ledger["excluded_dates"]) + list(ledger["missing_calendar_dates"])
        cards.append(
            f'<article class="asset" data-state="{e(asset["state"])}" '
            f'data-name="{e(asset["asset_id"].lower())}"><div class="cardhead">'
            f'<div><p class="eyebrow">SOLAR PV · {e(kinds)}</p><h3>{e(asset["asset_id"])}</h3></div>'
            f'<span class="badge {e(asset["state"])}">{e(asset["state"].replace("_", " "))}</span></div>'
            f'<div class="metrics"><div><b>{ledger["deficit_mwh"]:,.1f}</b><span>MWh deficit</span></div>'
            f"<div><b>{ledger['coverage_fraction']:.0%}</b><span>Daily coverage</span></div>"
            f"<div><b>{ledger['conditional_net_value']:,.0f}</b>"
            f"<span>{e(asset['currency'])} conditional net</span></div></div>"
            + "".join(bars)
            + f'<p class="subtle">{e(asset["scenario"]["scenario_description"])}</p>'
            + (
                f'<p class="gap">Missing dates: {e(", ".join(missing))}. Economic ranking held.</p>'
                if missing
                else ""
            )
            + f"<details><summary>Proposed actions · {len(asset['actions'])}</summary><ul>{actions}</ul></details>"
            + f"<details><summary>Source evidence & assumptions</summary><ul>{evidence}</ul>"
            + f'<p class="hash">Case SHA-256: {e(asset["case_sha256"])}</p></details></article>'
        )
    return (
        """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Energy Operations · Asset management review</title><style>
:root{color-scheme:light;--ink:#102936;--muted:#526a76;--line:#dbe4e7;--teal:#087e80}
*{box-sizing:border-box}body{margin:0;background:#f2f6f7;color:var(--ink);font:15px/1.6 system-ui,sans-serif}
header{background:#102936;color:white;padding:42px max(24px,calc((100vw - 1160px)/2)) 36px}
nav{display:flex;justify-content:space-between;gap:20px;color:#b7d4dd;font-size:13px}
h1{font-size:clamp(30px,5vw,48px);line-height:1.15;margin:26px 0 12px;letter-spacing:-1.5px}
header p{color:#c3d8df;max-width:760px}main{max-width:1208px;margin:auto;padding:30px 24px}
a{color:var(--teal)}header a{color:#a5ebe0}.eyebrow{font-size:11px;font-weight:700;letter-spacing:1.7px;margin:0 0 8px}
.summary{background:white;border:1px solid var(--line);border-radius:14px;padding:24px;display:grid;
grid-template-columns:1.4fr 1fr;gap:12px 28px;margin-bottom:18px}.summary h2{font-size:19px;margin:0}
.summary p{margin:4px 0}.big{font-size:38px;font-weight:750;line-height:1.1;color:var(--teal)}
.subtle{font-size:13px;color:var(--muted)}.summary>.subtle{grid-column:1/-1}.sectiontitle{font-size:22px;margin:30px 0 14px}
.rank{border-left:4px solid var(--teal);background:#e0f2ed;padding:18px 20px;display:flex;
flex-wrap:wrap;gap:10px 25px;align-items:center;margin-bottom:10px}.rank b{margin-left:auto}
.controls{display:flex;gap:12px;flex-wrap:wrap;margin:18px 0}label{font-size:13px;display:grid;gap:5px}
input,select{padding:11px 14px;border:1px solid #a7bbc3;border-radius:7px;background:white;font:inherit;color:var(--ink)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.asset{background:white;border:1px solid var(--line);
border-radius:14px;padding:24px;min-width:0}.cardhead{display:flex;gap:12px;align-items:start;justify-content:space-between}
h3{font-size:23px;margin:0}.badge{border-radius:20px;padding:5px 10px;font-size:11px;white-space:nowrap;background:#e9eef1}
.investigate{background:#d7f2e6;color:#145e47}.held_data_quality{background:#fff0cd;color:#795712}
.review_economics{background:#f4e4e9;color:#86445b}.metrics{display:flex;gap:24px;margin:24px 0}
.metrics b{display:block;font-size:24px;line-height:1.3}.metrics span{font-size:12px;color:var(--muted)}
.barrow{display:grid;grid-template-columns:125px 1fr 75px;gap:10px;font-size:12px;align-items:center;margin:9px 0}
.barrow b{text-align:right}.track{height:8px;background:#edf2f4;border-radius:4px;overflow:hidden}.bar{height:100%;background:#087e80}
.bar.curtailment{background:#d19a32}.bar.unresolved{background:#9c7183}.gap{font-size:13px;color:#795712;background:#fff6dc;padding:12px}
details{border-top:1px solid var(--line);padding-top:12px;margin-top:12px}summary{cursor:pointer;font-weight:600;font-size:13px}
ul{padding-left:20px}li{margin:10px 0;font-size:13px}small{color:var(--muted)}.hash{font:11px monospace;overflow-wrap:anywhere}
footer{color:var(--muted);font-size:12px;margin:32px 0}.asset[hidden]{display:none}
@media(max-width:760px){.grid,.summary{grid-template-columns:1fr}.cardhead{flex-wrap:wrap}.rank b{margin-left:0}
.metrics{gap:18px}.barrow{grid-template-columns:115px 1fr 65px}main{padding:22px 14px}.asset{padding:18px}nav{flex-wrap:wrap}}
</style></head><body><header><nav><strong>ASVA / ENERGY OPERATIONS</strong>
<span>Energy Agents → Energy Data Insights</span></nav><h1>From lost energy<br>to a reviewable action.</h1>
<p>Portfolio operations and asset management. Inspect evidence, compare conditional recovery value,
and prepare maintenance decisions with an explicit audit trail.</p>
<a href="portfolio.json" download>Download review JSON</a> ·
<a href="work_orders.json" download>Download work-order drafts</a>
</header><main>"""
        + "".join(summaries)
        + """
<h2 class="sectiontitle">Economic investigation queue</h2>
<p class="subtle">Ranks restart for each currency, review period and timezone. Incomplete data and
nonpositive repair scenarios are excluded. This is not a safety or dispatch priority.</p>"""
        + ("".join(rankings) or "<p>No eligible economic investigation opportunities.</p>")
        + """<h2 class="sectiontitle">Portfolio evidence</h2><div class="controls">
<label>Search assets<input id="search" type="search" placeholder="Asset name"></label>
<label>Review status<select id="state"><option value="">All statuses</option>
<option value="investigate">Investigate</option><option value="held_data_quality">Held: data quality</option>
<option value="review_economics">Review economics</option><option value="monitor">Monitor</option></select></label>
</div><div class="grid">"""
        + "".join(cards)
        + """</div><p id="empty" hidden>No matching assets.</p>
<footer>Advisory review · Drafts require human approval. Evidence labels describe supplied provenance;
they do not independently verify measurements. Event association is not causal diagnosis.
<br>Backend: """
        + e(result["backend"]["callable"])
        + " · executed locally<br>Input SHA-256: "
        + e(result["input_sha256"])
        + """</footer></main><script>
const search=document.getElementById('search'),state=document.getElementById('state');
function filter(){let visible=0;document.querySelectorAll('.asset').forEach(card=>{
card.hidden=!(card.dataset.name.includes(search.value.toLowerCase())&&(!state.value||card.dataset.state===state.value));
if(!card.hidden)visible++});document.getElementById('empty').hidden=visible>0}
search.addEventListener('input',filter);state.addEventListener('change',filter);
</script></body></html>"""
    )
