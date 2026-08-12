# LinkedIn Featured content

## Featured title

Azure Data Engineering Evidence Portfolio: Quality-Critical Lakehouse

## Featured description

I built a reproducible Azure lakehouse implementation spanning Bicep, ADLS Gen2, Data Factory, Event Hubs, Azure Databricks, Unity Catalog, PySpark, Delta Lake, Lakeflow, Azure Monitor, CI/CD, failure recovery, Spark performance measurement, governance, cost control, and verified teardown. The case study links every major claim to its implementation, validation, execution status, and sanitized evidence.

## Featured link

https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

## Post draft

I built Part 4 of my Azure Data Engineering portfolio around a question that matters in any quality-critical operation: can a published KPI be traced all the way back to the batch record or sensor event that created it?

The project combines scheduled batch ingestion through Azure Data Factory with bounded streaming telemetry through Event Hubs. PySpark and Delta Lake carry both paths through Bronze provenance, Silver validation and quarantine, CDC and SCD Type 2 history, and six documented Gold data products.

The strongest part is the evidence model. Architecture, code, tests, platform receipts, validation results, timestamps, commit references, and SHA-256 hashes are connected at the claim level. A resource existing is not treated as proof that a workload ran.

I also designed the operational story into the build: a controlled quality failure, focused Lakeflow repair, idempotency checks, a three by three Spark benchmark, monitoring, explicit cost gates, and authoritative teardown verification.

The full case study includes a 90-second recruiter path, a technical deep dive, a searchable evidence explorer, and a 32-page document.

Portfolio: https://smailliwhtes.github.io/quality-critical-azure-lakehouse/

Repository: https://github.com/smailliwhtes/quality-critical-azure-lakehouse

#Azure #AzureDatabricks #DataEngineering #PySpark #DeltaLake #DataFactory #EventHubs #Lakeflow #UnityCatalog

## Publication boundary

This file is a draft only. It is not uploaded or posted by project automation. Before publication, update any statement whose evidence status changed and verify that every cloud-execution claim is marked consistently with the public evidence manifest.
