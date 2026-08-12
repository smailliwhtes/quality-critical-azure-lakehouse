# Runbook

## Purpose

This runbook executes one short, bounded Azure window after all local artifacts pass. It stops on unexpected resources, a missing Trial tier, invalid budget state, a $15 retry threshold, or a $20 teardown threshold.

## 1. Preflight

Confirm clean Git state, public baseline commit, Azure and GitHub authentication, East US 2 quota, Trial availability, tool versions, local tests, Bicep build, bundle schema, content validation, secret scan, and a sanitized starting cost snapshot. Keep raw receipts outside Git.

## 2. Provision

Create the Part 4 budget first. Register required providers, run Bicep validation and what-if, sanitize the result, compare resource types to `infra/expected_resource_types.json`, then deploy `rg-qcal-part4-dev`. If ARM cannot activate the Portal-verified Trial SKU, create only that workspace through the retained Portal form and reconcile it immediately.

## 3. Configure

Upload deterministic source and reference files, publish ADF assets, configure the Access Connector storage credential and external locations, create `part4_ops` with Bronze, Silver, Gold, and governance schemas, discover the newest supported stable LTS runtime, and deploy the Declarative Automation Bundle.

## 4. Execute

Run ADF and reconcile landed files. Emit exactly 20,000 messages and run checkpointed streaming. Execute the clean Jobs DAG, validate table counts and invariants, then capture lineage. Do not advance a claim to `VERIFIED` without a platform artifact and matching receipt.

## 5. Incident and performance

Inject only the reserved hard-failure file. Capture the failed task and diagnostic, remove or repair the affected input, invoke Lakeflow repair where supported, and validate clean-versus-recovered content. Run three baseline and three optimized benchmark executions on the same compute and compare medians.

## 6. Monitor and collect

Query the Log Analytics tables that actually arrived, preserve alert state, capture cost using the exact available label, curate platform screenshots at a 1600-pixel viewport, sanitize identifiers, hash public artifacts, and rebuild the site and document before deletion.

## 7. Teardown

Save final inventory, delete only `rg-qcal-part4-dev`, its Databricks-managed resource group, and the Part 4 budget. Poll authoritative Azure readback to confirmed absence. Rebuild public artifacts with the teardown receipt and run the complete release gate.

## Failure handling

At $15, start no new compute and make no exploratory retry. At $20, immediately invoke teardown. If Trial is unavailable, do not select paid Premium. A blocked capability remains `PRODUCTION_BLUEPRINT` with its limitation recorded.

## Current evidence boundary

The commands, gates, exact target names, and local preflight are `DEMONSTRATED`. The cloud execution sections remain `PRODUCTION_BLUEPRINT` until their sanitized receipts are collected.
