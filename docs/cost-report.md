# Cost report

## Cost objective

The target is less than $10 incremental cost for the isolated evidence window. New compute and retries stop at $15. Teardown begins immediately at $20.

## Controls

- A $20 Azure Cost Management budget is created before the workload resources.
- Actual notifications are configured at 50, 75, and 100 percent.
- A forecast notification is configured at 100 percent.
- Databricks is Trial only; paid Premium is never selected as a fallback.
- Capacity fallback uses one single-node `Standard_D4ads_v6` job cluster and one single-node `Standard_D2ads_v6` Lakeflow cluster, peaking at six vCPUs inside the verified ten-vCPU quota.
- Compute is job-scoped, ephemeral, and aggressively auto-terminated.
- Event Hubs is Standard with one throughput unit and no auto-inflate.
- ADLS uses `Standard_LRS` and the business stream is bounded to 20,000 messages.

## Evidence labels

Cost data is reported only as `ACTUAL AVAILABLE COST`, `CURRENT COST SNAPSHOT`, `ESTIMATE`, or `PENDING BILLING SETTLEMENT`. Budgets are notification tools, not shutdown controls, and delayed billing is never converted into a precise actual value.

## Checkpoints

Snapshots are attempted before provisioning, after infrastructure deployment, after batch and streaming execution, after incident and performance work, immediately before teardown, and after authoritative teardown readback. Each receipt records capture time, scope, available period, source, and label.

## Decision rule

At $15, the project stops exploration and retries and moves directly to evidence preservation. At $20, teardown starts immediately even if optional captures remain. No cloud feature is worth exceeding the approved boundary.

## Executed checkpoints

Timestamped snapshots were attempted at every planned checkpoint, including immediately before and after teardown. Azure Cost Management returned no usable amount during the bounded window, so every affected receipt records `API_UNAVAILABLE`, an amount of `null`, and `PENDING BILLING SETTLEMENT`. This is not converted to a zero-dollar claim.

## Current evidence boundary

The $20 budget, 50/75/100 percent actual notifications, 100 percent forecast notification, Trial SKU, compute sizing, bounded stream, and fail-closed parsing are `VERIFIED` or `DEMONSTRATED` as stated in the evidence manifest. An actual incremental dollar result is not available and is not claimed.

## Cost result

`PENDING BILLING SETTLEMENT`: the Cost Management query API did not return an amount before or immediately after teardown. The portfolio publishes that limitation rather than inventing an estimate or treating missing telemetry as zero.
