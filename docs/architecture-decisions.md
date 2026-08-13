# Architecture Decisions

## Decision

The Part 4 portfolio now leads with architecture judgment: why the Azure data platform was shaped this way, what credible alternatives were rejected, which trade-offs were accepted, and what executed evidence supports the choices.

## Decision summary

| Decision | Why it matters | Evidence state |
| --- | --- | --- |
| Split ingestion by workload shape | Files and events expose different monitoring and recovery signals. | `VERIFIED` |
| Preserve source fidelity before conformance | Replay, audit, and incident diagnosis need source-state records. | `VERIFIED` |
| Apply risk-based quality policies | Different defects need observe, quarantine, or hard-fail outcomes. | `VERIFIED` |
| Use declarative temporal history | Executed SCD Type 2 history should not be rebuilt by every consumer. | `VERIFIED` |
| Build governance into named table operations | Access, metadata, and lineage belong inside the data path. | `VERIFIED` |
| Measure performance instead of assuming optimization | The broadcast change was slower, and that result is published. | `VERIFIED` |

## Current evidence boundary

These records interpret the executed portfolio; they do not introduce new Azure execution. The existing platform screenshots, receipts, code paths, validations, timestamps, commits, and hashes remain the source of proof.

## Production boundary

Production hardening remains separate from bounded evidence. Private networking, production scale, routed operations, formal disaster recovery, enterprise access processes, and operating chargeback are documented as `PRODUCTION_BLUEPRINT` extensions.

## Full records

The full decision dossier lives in [docs/decisions](decisions/README.md). Each record separates decision state from evidence state so architecture lifecycle language does not collide with the public evidence vocabulary.
