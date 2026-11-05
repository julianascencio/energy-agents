Literature and implementation scope
===================================

Shirzadi, N., Lopez, P., and Stylianou, M. (2026). Tool-augmented vs. autonomous
LLM agents for building energy model modifications: A comparative study using
NECB compliance models. *Energy and AI*, 26, 100896.
`DOI <https://doi.org/10.1016/j.egyai.2026.100896>`_.

:download:`Read the original paper <../../literature/shirzadi_2026_building_energy_agents.pdf>`.

© 2026 His Majesty the King in Right of Canada, as represented by Natural
Resources Canada. Published by Elsevier Ltd., under
`CC BY <http://creativecommons.org/licenses/by/4.0/>`_. The PDF is unmodified.

Implemented tasks
-----------------

Section 2.5 defines window U-factor 1.5 W/(m² K) and a 30% reduction to the active
Lights design-power input. Our transactional epJSON editors implement these
transformations. The offline agent policies are scripted and use synthetic data.
A real-provider adapter is available but has not been benchmarked live.

The original experiment's NECB RAG, MCP servers, complete EnergyPlus reference
models and complex PTAC/DX-to-VRF conversion are not reproduced here. A passing
local postcondition is not a simulation or regulatory-compliance result.

Published evidence and discrepancies
------------------------------------

The gallery separately plots 14 reported window-task call counts from Table 8A.
That table lists apartment TA calls 1/1/1 and AU calls 10/7/11, conflicting with
Section 3.2's narrative counts. We retain the table values and do not reconcile
them by guesswork. The text also refers to 22 lighting trials although seven
buildings × two conditions gives 14 base combinations. We do not pool these counts.

The data-availability statement supplies no replication bundle. The original
models, weather, full traces and code are not assumed available from the PDF.

See the repository's `detailed evidence matrix
<https://github.com/julianascencio/energy-agents/blob/main/docs/literature/01_building_energy_agents.md>`_
for attribution, limits and further source notes.
