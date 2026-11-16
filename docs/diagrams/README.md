# Diagrams

Graphviz sources for the WVV project plans. All files are plain DOT, so they
diff cleanly in git and can be regenerated at any time.

| File | Shows | Derived from |
|---|---|---|
| `pipeline_simple.dot` | Source overview: the four sources side by side with their handling path (s3() SQL, Python GTFS filter, LLM extraction), the RustFS raw zone, the ClickHouse layers, serving views and consumers. No phases or provenance detail. | `docs/data_pipeline_plan.md` §3–§5, condensed |
| `pipeline.dot` | End-to-end data flow: upstream providers → RustFS raw zone → ingest jobs → ClickHouse raw / bronze→silver→gold / clean+dim → consumers. Edge labels carry the execution phase. | `docs/data_pipeline_plan.md` §3–§6 |
| `system_context.dot` | Domain 1 as platform and interface owner: sources, the three Medallion layers, ubiquitous join keys, and the bidirectional contract with Domain 2, Domain 3 and the dashboard. | `docs/paper_plan.md` §1, §5 |

## Rendering

Requires the Graphviz `dot` binary (`sudo apt install graphviz`).

```bash
cd docs/diagrams
dot -Tsvg pipeline_simple.dot  -o pipeline_simple.svg
dot -Tsvg pipeline.dot         -o pipeline.svg
dot -Tsvg system_context.dot   -o system_context.svg

# raster versions for slides / Word
dot -Tpng -Gdpi=200 pipeline_simple.dot  -o pipeline_simple.png
dot -Tpng -Gdpi=200 pipeline.dot         -o pipeline.png
dot -Tpng -Gdpi=200 system_context.dot   -o system_context.png
```

`render.sh` renders every `.dot` file in one go.

## Reading the colours

- grey-blue — upstream sources
- orange — RustFS bucket (raw zone)
- purple — ingest jobs (pure ClickHouse SQL or Python)
- green — ClickHouse layers, darkening towards the serving layer
- yellow — consumers

In `pipeline.dot`, dashed edges are write-backs or derived flags rather than
data products. In `system_context.dot`, double-headed arrows carry both
directions: `→` what Domain 1 delivers, `←` what it needs back.

Both detailed diagrams are laid out top-to-bottom and land at roughly
12 in × 10 in and 13 in × 8 in, so they scale down cleanly to a full-width
figure in the paper.

`pipeline_simple.dot` trades the phase labels and per-table detail of
`pipeline.dot` for four visible source lanes, so each source and its handling
path stays readable at a glance (≈11.3 in × 6.2 in).
