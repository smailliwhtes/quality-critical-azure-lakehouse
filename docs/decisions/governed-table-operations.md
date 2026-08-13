# Governed Table Operations

## Title

Build governance into named table operations.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

Access control, discoverability, metadata, masking, and lineage need to be part of the data path, not only a downstream reporting concern.

## Decision drivers / constraints

The project needed a governed interface that could be inspected through Unity Catalog without using arbitrary path access as the default.

## Options considered

Catalog-qualified table operations, path-based Delta access, downstream-only governance, or manual lineage documentation.

## Decision

Use named tables, ownership, grants, comments, tags, masking, and Unity Catalog lineage for governed objects.

## Why this option won

It makes access, metadata, and lineage inspectable at runtime.

## Trade-offs accepted

The system requires stronger namespace, ownership, and permission discipline.

## Consequences

Gold outputs can be traced through governed table relationships instead of relying only on a diagram.

## Executed evidence

Unity Catalog hierarchy, governance controls, table lineage, column lineage, and managed-identity receipts support this decision.

## Production extension

Add enterprise ownership workflow, access reviews, environment separation, and policy assignment.

## Reconsider when

Reconsider only for explicit interoperability exceptions that cannot consume governed tables.

## Current evidence boundary

This record does not imply every possible lineage scenario is captured.
