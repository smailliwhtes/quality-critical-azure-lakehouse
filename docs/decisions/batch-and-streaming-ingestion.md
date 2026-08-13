# Batch and Streaming Ingestion

## Title

Split ingestion by workload shape.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

Batch files and telemetry events have different operating semantics. File movement needs copy activity evidence. Event ingress needs partition, offset, timestamp, checkpoint, and lag evidence.

## Decision drivers / constraints

The build needed bounded cost, clear recovery state, deterministic inputs, and real Azure evidence for both batch and streaming patterns.

## Options considered

Use ADF for everything, use Event Hubs for everything, implement all ingestion directly inside Databricks, or split the work by workload shape.

## Decision

ADF owns bounded file movement. Event Hubs and Structured Streaming own event ingress. Both converge in Bronze.

## Why this option won

It lets each platform surface the evidence that matches its workload: files, rows, bytes, and activity runs for ADF; topic, partition, offset, timestamp, checkpoint, and append semantics for streaming.

## Trade-offs accepted

Two ingress control planes are more complex than one.

## Consequences

The public case study can prove both six-file batch ingestion and exactly 20,000 streamed messages without pretending one tool is ideal for both shapes.

## Executed evidence

ADF, Event Hubs, and Lakeflow orchestration receipts support this decision.

## Production extension

Add source onboarding standards, SLAs, and operational ownership for each ingress mode.

## Reconsider when

Reconsider when source volume, latency, enterprise ingestion standards, or the cost of two ingress planes changes materially.

## Current evidence boundary

This record interprets executed evidence; it does not add new workload execution.
