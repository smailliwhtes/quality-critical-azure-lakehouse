# Security

## Security objective

The project minimizes persistent credentials, constrains authorization to the isolated Part 4 scope, and separates raw private captures from public sanitized evidence.

## Identity design

- Azure Data Factory accesses ADLS with its system-assigned managed identity.
- Azure Databricks accesses ADLS through the Access Connector managed identity and scoped RBAC.
- GitHub Actions uses a federated user-assigned managed identity scoped to `rg-qcal-part4-dev`.
- Azure CLI authentication is used for Databricks automation where supported; no long-lived Databricks token is created.
- The deployment workflow stores only non-secret Azure identifiers as repository secrets required by the OIDC action.

## Storage and transport

The storage account uses ADLS Gen2 hierarchical namespace, `Standard_LRS`, TLS 1.2 or newer, disabled public blob access, and disabled shared-key authorization. Event Hubs uses the Standard tier with one throughput unit and no auto-inflate. Key Vault has soft-delete and purge protection appropriate to the short-lived environment.

## Secret handling

No secret value is committed, printed, copied into a notebook, placed in a receipt, or captured in a public screenshot. If Event Hubs connection material is required, the deployment retrieves it into process memory, writes it to Key Vault, and exposes only the secret name. Raw evidence stays outside Git at `C:\Users\micha\Part4_Private_Evidence`.

## Public release gate

Release scanning covers repository history, tokens, connection strings, SAS signatures, client secrets, storage keys, subscription and tenant identifiers, personal email addresses, public JSON, screenshot pixels and metadata, PDF metadata, HTML output, Git diffs, and disallowed authoring attribution strings.

## Threat considerations

The main risks are over-scoped identities, leaked Event Hubs credentials, identifiers embedded in receipts, public screenshots that expose account UI, and teardown scripts that target unrelated resources. Exact resource-group names, authoritative inventory checks, value redaction, and fixed deletion scope reduce those risks.

## Executed controls

ADF used its managed identity for the six-file ADLS copy. The Access Connector backed Unity Catalog storage, external locations, and governed volumes. GitHub's federated identity completed a resource-group-scoped OIDC validation. No long-lived Databricks token or cloud password was created. The public producer, streaming, platform, and governance receipts exclude connection material and account identifiers.

## Current evidence boundary

Identity definitions and local scanning are `DEMONSTRATED` as code. Managed-identity data access, Access Connector storage, scoped OIDC deployment, secret-value exclusion, tags/comments, and column masking are `VERIFIED`. Databricks ARM diagnostics remain `PRODUCTION_BLUEPRINT` because the Trial workspace exposed no supported category. Exact-scope resource absence is promoted only after teardown readback.

## Known limitations

The Trial exposed no Databricks ARM diagnostic categories and executed Python tasks through Spark Connect without the classic status store. Cost telemetry also remained unavailable during the evidence window. Each limitation is retained at feature level and never generalized into a false security or operations claim.
