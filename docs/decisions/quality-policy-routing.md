# Quality Policy Routing

## Title

Apply risk-based quality policies.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

Some defects are observable warnings, some are recoverable data defects, and some break trust enough to stop publication.

## Decision drivers / constraints

The portfolio needed to prove warning behavior, reason-coded quarantine, and one real hard failure without treating quarantine as a native Lakeflow expectation action.

## Options considered

Drop every invalid row, fail on every defect, allow everything and report later, or use risk-based policies.

## Decision

Implement observe/allow, reason-coded quarantine, and hard fail as business quality policies.

## Why this option won

It avoids both silent corruption and unnecessarily brittle pipelines.

## Trade-offs accepted

The system needs more explicit contracts and routing logic.

## Consequences

Rejected records stay explainable, and trust-breaking records stop publication.

## Executed evidence

Lakeflow expectation metrics, quarantine counts, and the controlled hard failure support this decision.

## Production extension

Add stewardship, remediation queues, schema-change governance, and producer contract ownership.

## Reconsider when

Reconsider when upstream producers formally guarantee schemas or quarantine remediation costs exceed its value.

## Current evidence boundary

The record separates native Lakeflow expectation behaviors from the portfolio's explicit quarantine routing.
