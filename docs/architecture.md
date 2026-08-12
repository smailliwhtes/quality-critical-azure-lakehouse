# Architecture

## Decision

The lakehouse uses two bounded ingestion paths that converge on one governed medallion model. Azure Data Factory moves deterministic quality and CDC files into ADLS Gen2. Event Hubs receives deterministic telemetry that Spark Structured Streaming writes to checkpointed Bronze Delta output. Azure Databricks and Lakeflow apply PySpark quality, conformance, temporal-history, and Gold publication logic.

## Service responsibilities

| Service | Single responsibility |
| --- | --- |
| Azure Data Factory | Parameterized batch movement with file, row, byte, duration, and run evidence |
| Event Hubs Standard | Bounded telemetry ingress through the Kafka-compatible interface |
| ADLS Gen2 | Landing, checkpoint, quarantine, and durable operational evidence paths |
| Azure Databricks | PySpark, Delta, Structured Streaming, and measured performance execution |
| Lakeflow | Quality expectations, dependency-aware jobs, controlled failure, and focused repair |
| Unity Catalog | Object governance, scoped access, metadata, and actual table and column lineage |
| Azure Monitor and Log Analytics | Cross-service diagnostics, KQL evidence, and alert state |
| GitHub Actions | Validated CI, federated deployment, evidence collection, and Pages publication |

## Data flow

Bronze preserves source fidelity and provenance. Silver enforces types, business keys, units, domains, deduplication, quarantine, and CDC/SCD2 history. Gold publishes two facts, three dimensions, and one KPI table with explicit grain and validation SQL.

The cross-cutting trust path is Microsoft Entra managed identity to scoped Azure RBAC, then Access Connector to ADLS and Unity Catalog storage objects. Key Vault is reserved for the Event Hubs credential only if the runtime requires it.

## Executed compute boundary

The workspace ran in East US 2 on the Portal-confirmed `trial` SKU and Hybrid mode. East US 2 capacity and live node metadata did not support the planned `Standard_DS3_v2` shape. The bounded fallback used one single-node `Standard_D4ads_v6` job cluster (4 vCPUs) and one single-node `Standard_D2ads_v6` Lakeflow cluster (2 vCPUs), for a peak verified plan of 6 vCPUs inside the 10-vCPU quota. Databricks Runtime was `17.3.x-scala2.13` (17.3 LTS, Spark 4.0.0, Scala 2.13).

## Current evidence boundary

Provisioning, managed-identity access, ADF batch ingestion, Event Hubs streaming, Bronze/Silver/Gold processing, Lakeflow orchestration, AUTO CDC, Unity Catalog governance and lineage, controlled failure, focused repair, performance execution, and exact-scope teardown are `VERIFIED`. The architecture rendering and production extensions are `DEMONSTRATED`. Databricks ARM diagnostics are `PRODUCTION_BLUEPRINT` because the live Trial workspace exposed no diagnostic category through ARM. Cost remains `PENDING BILLING SETTLEMENT`. Azure confirmed both isolated resource groups and the Part 4 budget absent after 20 polls.

## Production blueprint extensions

Production would add private networking, customer-managed keys where required, separate environments and identities, policy enforcement, longer retention, formal data ownership, workload-specific sizing, and service-level objectives. Those extensions are documented rather than executed here because they do not strengthen the bounded portfolio proof enough to justify cost or complexity.
