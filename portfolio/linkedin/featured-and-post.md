# LinkedIn Featured content

## Featured title

Azure Data Engineering Evidence Portfolio: Quality Critical Lakehouse

## Featured description

I built and executed a reproducible Azure lakehouse, but the strongest part of the case study is the architecture judgment behind it: why batch files and telemetry events use different ingress paths, why Bronze preserves source fidelity before conformance, why bad records do not all receive the same consequence, why AUTO CDC was chosen for executed SCD Type 2 history, why governed table operations matter, and why a proposed Spark optimization was rejected after measurement.

## Featured link

https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

## Post draft

I built Part 4 of my Azure Data Engineering portfolio around a question that matters in any quality critical operation: can a published KPI be traced all the way back to the batch record or sensor event that created it, and can I defend why the platform was designed this way?

Azure Data Factory copied six commit pinned files and reconciled 30,000 batch quality rows. Event Hubs carried exactly 20,000 deterministic telemetry messages into checkpointed Structured Streaming. The split ingress was deliberate: files and events expose different monitoring, recovery, and evidence signals.

PySpark and Delta Lake then moved both paths through an append-only, source-fidelity Bronze preservation contract, Silver validation, reason-coded quarantine, Lakeflow AUTO CDC for SCD Type 2 history, and six documented Gold data products. Unity Catalog recorded table and column lineage, applied managed storage and scoped grants, and demonstrated column masking.

I injected a reserved quality failure, captured the real failed task and diagnostic, repaired the affected and dependent recovery path while preserving unaffected successful upstream work, and proved the recovered content matched the clean baseline.

I also ran a separate five million row Spark experiment three times per implementation on the same compute. The broadcast plan produced the same result hash but was 39.009 percent slower by median wall time. I published that result because honest measurement is more useful than a predetermined optimization story.

Architecture, code, tests, platform captures, machine receipts, validation results, UTC timestamps, commit references, and SHA256 hashes are connected at the claim level. Cost telemetry remained pending settlement, so no zero or estimate is invented. Azure also confirmed the isolated resource groups and Part 4 budget were absent after exact scope teardown.

The full case study includes a 90 second recruiter path, an architecture decision dossier, a technical deep dive, a searchable evidence explorer, a governed Gold boundary for a future AI Engineering portfolio, and a 32 page document.

Portfolio: https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

Repository: https://github.com/smailliwhtes/quality-critical-azure-lakehouse

#Azure #AzureDatabricks #DataEngineering #PySpark #DeltaLake #DataFactory #EventHubs #Lakeflow #UnityCatalog

## Publication boundary

This file is a draft only. It is not uploaded or posted by project automation. Before publication, update any statement whose evidence status changed and verify that every cloud execution claim is marked consistently with the public evidence manifest.
