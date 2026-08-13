# Bronze Provenance

## Title

Preserve source fidelity before conformance.

## Decision state

`ACCEPTED`

## Evidence state

`VERIFIED`

## Context

Quality-critical investigation needs the ability to reconstruct what arrived before conformance changed units, types, keys, or domains.

## Decision drivers / constraints

The project needed replay, auditability, deterministic validation, and incident diagnosis without claiming unproven physical storage immutability.

## Options considered

Transform in landing, write directly to Silver, retain files without Bronze Delta, or preserve source-fidelity Bronze records.

## Decision

Use an append-only, source-fidelity Bronze preservation contract with source identity, timestamps, run ID, record hash, and schema version.

## Why this option won

It makes downstream conformance reviewable and gives failure investigation a durable source representation.

## Trade-offs accepted

More metadata and storage are retained.

## Consequences

Silver, quarantine, SCD2, and Gold claims can be traced back to raw source representations.

## Executed evidence

Bronze provenance, ADLS layout, and evidence-manifest records support this decision.

## Production extension

Add retention, deletion, privacy, and data-classification policy.

## Reconsider when

Reconsider when legal deletion, privacy, retention, or storage policy makes full source-fidelity retention inappropriate.

## Current evidence boundary

This record does not claim Azure Storage WORM or immutability controls.
