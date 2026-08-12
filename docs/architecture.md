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

## Operating boundaries

The implementation targets East US 2, Databricks Trial only, one `Standard_DS3_v2` driver plus one worker, ephemeral job compute, and aggressive termination. New compute and retries stop at $15; teardown begins immediately at $20.

## Current evidence boundary

The architecture composition, modular Bicep, deterministic transforms, and orchestration definition are `DEMONSTRATED`. Azure resource, workload, lineage, alert, cost, and teardown behavior remains `PRODUCTION_BLUEPRINT` until the bounded execution receipts and sanitized platform captures are present.

## Production blueprint extensions

Production would add private networking, customer-managed keys where required, separate environments and identities, policy enforcement, longer retention, formal data ownership, workload-specific sizing, and service-level objectives. Those extensions are documented rather than executed here because they do not strengthen the bounded portfolio proof enough to justify cost or complexity.
