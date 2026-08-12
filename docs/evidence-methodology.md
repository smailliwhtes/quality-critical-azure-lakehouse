# Evidence methodology

## Principle

A claim is only as strong as the artifact that proves the claimed behavior. A resource screenshot proves existence; it does not prove ingestion, transformation, recovery, lineage, performance, alert firing, cost, CI, or teardown.

## Public status vocabulary

- `VERIFIED`: the stated Azure or Databricks behavior executed and has sanitized platform evidence.
- `DEMONSTRATED`: deterministic behavior ran outside the stated cloud environment or an implementation artifact was validated.
- `PRODUCTION_BLUEPRINT`: the extension is designed and documented but was not executed in this bounded environment.

No synonym is accepted in the evidence manifest.

## Major claim bundle

A major `VERIFIED` claim binds a platform screenshot, implementation path, machine-readable receipt, validation result, UTC capture time, execution run, commit SHA, and SHA-256 hash. The manifest schema is `part4-evidence-manifest/v1`.

## Capture pipeline

Raw captures are stored outside Git at `C:\Users\micha\Part4_Private_Evidence`. Platform content uses a consistent 1600-pixel-wide viewport and excludes account menus or sensitive headers where practical. Sanitized derivatives are visually inspected before moving to `evidence/public`.

## Required sanitization

Public files exclude credentials, tokens, connection strings, SAS parameters, keys, tenant and subscription identifiers, personal email, unnecessary resource identifiers, private URLs, and image or document metadata that reveals private capture context.

## Screenshot curation

`evidence/public/screenshot_manifest.json` declares exactly 34 meaningful public slots, including architecture, PySpark, Jobs DAG, lineage, failure and repair, and performance as the six recruiter heroes. Platform captures remain platform captures. Generated panels are labeled as generated artifacts and derive only from public code or machine receipts; they do not imitate Azure or Databricks interfaces.

## Integrity and reconciliation

Receipts are sanitized before hashing. Counts are reconciled across producer, Event Hubs, stream progress, Delta output, ADF activities, tables, and validations. Benchmark medians use all three runs per path. Teardown is verified through authoritative Azure absence readback.

## Current evidence boundary

The manifest schema, validator, deterministic hashing, capture pipeline, sanitization policy, and 34-slot curation are `DEMONSTRATED`. Executed Azure and Databricks claims are individually `VERIFIED` only when their required bundle exists. Cost remains pending settlement; the activity-log alert is configured but not fired; the Trial workspace's unsupported ARM diagnostics category is `PRODUCTION_BLUEPRINT`; teardown remains pending until authoritative readback.

## Release rule

The release fails if a required file is missing, a hash is invalid, a verified claim lacks its paired evidence, a public secret or forbidden attribution is found, a screenshot remains unsanitized, PDF metadata is incorrect, site checks fail, or the final teardown receipt is absent.
