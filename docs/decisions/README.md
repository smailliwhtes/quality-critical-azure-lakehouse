# Architecture Decision Dossier

Decision state: accepted-record index  
Evidence state: mixed public evidence states  
Reconsider when: a source, runtime, governance, cost, or production requirement changes enough to invalidate a record.

## Purpose

This dossier is the recruiter-accessible index for the six architecture decisions behind the Quality-Critical Azure Lakehouse. It explains why the system was shaped this way without turning the repository into an Azure service catalog.

## Records

| Record | Decision state | Evidence state |
| --- | --- | --- |
| [Batch and streaming ingestion](batch-and-streaming-ingestion.md) | `ACCEPTED` | `VERIFIED` |
| [Bronze provenance](bronze-provenance.md) | `ACCEPTED` | `VERIFIED` |
| [Quality policy routing](quality-policy-routing.md) | `ACCEPTED` | `VERIFIED` |
| [Temporal history CDC](temporal-history-cdc.md) | `ACCEPTED` | `VERIFIED` |
| [Governed table operations](governed-table-operations.md) | `ACCEPTED` | `VERIFIED` |
| [Evidence-led performance](evidence-led-performance.md) | `ACCEPTED` | `VERIFIED` |

## Current evidence boundary

Every record points back to existing public evidence. No record creates a new Azure run, a new screenshot slot, or a new evidence status.
