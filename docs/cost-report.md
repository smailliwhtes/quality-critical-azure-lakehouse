# Cost report

## Cost objective

The target is less than $10 incremental cost for the isolated evidence window. New compute and retries stop at $15. Teardown begins immediately at $20.

## Controls

- A $20 Azure Cost Management budget is created before the workload resources.
- Actual notifications are configured at 50, 75, and 100 percent.
- A forecast notification is configured at 100 percent.
- Databricks is Trial only; paid Premium is never selected as a fallback.
- One driver plus one worker uses `Standard_DS3_v2`, totaling eight vCPUs within the verified ten-vCPU quota.
- Compute is job-scoped, ephemeral, and aggressively auto-terminated.
- Event Hubs is Standard with one throughput unit and no auto-inflate.
- ADLS uses `Standard_LRS` and the business stream is bounded to 20,000 messages.

## Evidence labels

Cost data is reported only as `ACTUAL AVAILABLE COST`, `CURRENT COST SNAPSHOT`, `ESTIMATE`, or `PENDING BILLING SETTLEMENT`. Budgets are notification tools, not shutdown controls, and delayed billing is never converted into a precise actual value.

## Checkpoints

Snapshots are attempted before provisioning, after infrastructure deployment, after batch and streaming execution, after incident and performance work, and immediately before teardown. Each receipt records capture time, scope, available period, source, and label.

## Decision rule

At $15, the project stops exploration and retries and moves directly to evidence preservation. At $20, teardown starts immediately even if optional captures remain. No cloud feature is worth exceeding the approved boundary.

## Current evidence boundary

Budget IaC, thresholds, compute sizing, bounded stream, and fail-closed local budget parsing are `DEMONSTRATED`. Azure cost values remain `PRODUCTION_BLUEPRINT` until a timestamped Cost Management response is captured.

## Cost result

`PENDING BILLING SETTLEMENT`: no actual or estimated project value is published before the bounded deployment produces a source-backed snapshot.
