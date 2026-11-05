# Literature 01 — Tool surfaces for building energy models

Navid Shirzadi, Phylroy Lopez and Meli Stylianou (2026).
**Tool-augmented vs. autonomous LLM agents for building energy model modifications:
A comparative study using NECB compliance models.** Energy and AI 26, 100896.
https://doi.org/10.1016/j.egyai.2026.100896

[Original, unmodified paper](shirzadi_2026_building_energy_agents.pdf).
© 2026 His Majesty the King in Right of Canada, as represented by Natural Resources
Canada. Published by Elsevier Ltd. Distributed under the paper's
[CC BY license](http://creativecommons.org/licenses/by/4.0/).
Code is independently implemented from the described tasks; no author code is claimed.

## What the study reports

The study contrasts high-level domain tools and primitive object editing with
matched foundation-model settings across seven building archetypes/locations.
Window and lighting tasks succeed in both conditions; complex PTAC/packaged-DX to
VRF conversion succeeds only in the tool-augmented condition in this pilot study.
The tool condition combines coarser action abstraction with embedded engineering
knowledge, so these two effects are not isolated. A small, temperature-zero study
cannot establish general performance across models, climates or repeated trials.

## Evidence-to-implementation map

| Paper element | Repository treatment | Validation boundary |
| --- | --- | --- |
| Section 2.5: window U-factor = 1.5 | `edit_windows` on simple-glazing epJSON fields | Exact field effect and preservation |
| Section 2.5: 30% lighting reduction | `edit_lighting` for LightingLevel, Watts/Area, Watts/Person | Active field only, schedules preserved |
| Tool-augmented vs primitive actions | Domain functions vs allowlisted `set_field` | Scripted policies plus optional HTTP LLM adapter |
| Three-attempt cap | Isolated retries with rollback and call budgets | Local deterministic tests |
| Table 8A | 14 transcribed calls/token observations in packaged JSON | Imported published evidence, not rerun |
| IDF + EnergyPlus + NECB RAG + MCP | Future work | Not implemented or implied |
| Complex HVAC conversion | Future work | No placeholder conversion advertised as valid |

The repository uses epJSON field names instead of a custom IDF parser. The fragment
contains no geometry or complete HVAC model; it is unsuitable for annual simulation.
Reference for lighting field semantics: EnergyPlus Input Output Reference,
[internal gains](https://energyplus.readthedocs.io/en/v26.2.0/guides/input-output-reference/1.14-group-internal-gains-people-lights-other-internal-zone-equipment.html).
Only traditional `Lights` objects are supported, not new `Lights:Definition`/`Lights:Instance` forms.

## Source discrepancies retained, not silently corrected

Section 3.2 describes three tool-augmented calls across all window buildings and
five autonomous calls for apartments. Table 8A instead lists apartment TA counts
1/1/1 and AU counts 10/7/11. Our imported dataset follows **Table 8A**, with the
conflict explicitly recorded here. The paper also says 22 lighting trials while
the seven-building/two-condition design gives 14 base condition combinations;
we do not infer an unreported allocation or pool trial counts.

The data-availability statement says no data was used, despite descriptions of
reference models and simulations. The supplied paper alone does not provide a
complete, version-pinned replication bundle. We do not claim to possess the
original models, traces, code, retrieval database, or weather inputs.

## Local evidence

Offline policy counts are edit invocations only; they exclude the final completion
request. They are **not comparable in scope to the paper's reported calls** and do
not measure tokens, latency, energy or cost. Both scripted policies intentionally
succeed; no autonomous failures are manufactured to reproduce the paper's conclusion.
