# LinkedIn Featured content

## Featured title

Azure Data Engineering Evidence Portfolio: Quality Critical Lakehouse

## Featured description

I built and executed a reproducible Azure lakehouse spanning Bicep, ADLS Gen2, Data Factory, Event Hubs, Azure Databricks, Unity Catalog, PySpark, Delta Lake, Lakeflow, Azure Monitor, CI/CD, failure recovery, performance measurement, governance, and cost control, with authoritative teardown verification. The case study links every major claim to implementation, validation, execution status, and sanitized evidence.

## Featured link

https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

## Post draft

I built Part 4 of my Azure Data Engineering portfolio around a question that matters in any quality critical operation: can a published KPI be traced all the way back to the batch record or sensor event that created it?

Azure Data Factory copied six commit pinned files and reconciled 30,000 batch quality rows. Event Hubs carried exactly 20,000 deterministic telemetry messages into checkpointed Structured Streaming. PySpark and Delta Lake then moved both paths through Bronze provenance, Silver validation and quarantine, Lakeflow AUTO CDC for SCD Type 2 history, and six documented Gold data products.

The ten task Lakeflow Jobs graph completed on Azure Databricks Trial. Unity Catalog recorded table and column lineage, applied managed storage and scoped grants, and demonstrated column masking. I then injected a reserved quality failure, captured the real failed task and diagnostic, repaired only the affected path, and proved the recovered content matched the clean baseline.

I also ran a separate five million row Spark experiment three times per implementation on the same compute. The broadcast plan produced the same result hash but was 39.009 percent slower by median wall time. I published that result because honest measurement is more useful than a predetermined optimization story.

Architecture, code, tests, platform captures, machine receipts, validation results, UTC timestamps, commit references, and SHA256 hashes are connected at the claim level. Cost telemetry remained pending settlement, so no zero or estimate is invented. Azure also confirmed the isolated resource groups and Part 4 budget were absent after exact scope teardown.

The full case study includes a 90 second recruiter path, a technical deep dive, a searchable evidence explorer, and a 32 page document.

Portfolio: https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

Repository: https://github.com/smailliwhtes/quality-critical-azure-lakehouse

#Azure #AzureDatabricks #DataEngineering #PySpark #DeltaLake #DataFactory #EventHubs #Lakeflow #UnityCatalog

## Publication boundary

This file is a draft only. It is not uploaded or posted by project automation. Before publication, update any statement whose evidence status changed and verify that every cloud execution claim is marked consistently with the public evidence manifest.
