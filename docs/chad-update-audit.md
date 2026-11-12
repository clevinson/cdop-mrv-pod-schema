# Audit of Chad's 0.2.7 update

Audited 2026-11-12 against the four files Chad Kapatch attached on September 29,
2026 and reattached on November 5. All four November attachments are byte-for-byte
identical to September's. This imports the supplied revision, not the additional
changes proposed in the November email.

## Imported sources

- `schema/mrv-pod.yaml`: original LinkML, unchanged (version 0.2.7).
- `examples/Project-with-monitoring.yaml`: original worked example, unchanged.
- `MRV-schema-2026-09-24.xlsx`: original review workbook, unchanged. The September
  22 workbook remains as historical input, not the current definition.
- `tests/fixtures/chad-2026-11-05/mrv-pod.schema.json`: original supplied JSON for
  comparison only. The actual generated artifact remains `build/mrv-pod.schema.json`.

LinkML remains the source of truth. The workbook is a review companion, not an
input to generation; it has the discrepancies below.

## Findings

### JSON Schema: one semantic discrepancy

With the repository's locked LinkML 1.11.1 environment and existing command
`gen-json-schema --closed --top-class Project schema/mrv-pod.yaml`, parsed JSON
is identical to Chad's except for root `additionalProperties`:

- Chad's JSON: `true` (unknown project-level properties accepted).
- Repository generation: `false` (unknown project-level properties rejected).

All definitions, property types, required lists, enums, and other constraints
match. The PR retains the repository's established closed-root behavior rather
than weakening validation to obtain a superficial match. A regression test checks
both the precise difference and its observable validation effect. Whitespace and
JSON key ordering are not considered semantic differences.

The old build postprocessor referenced `JsonObject`, which is no longer in the
schema. It has been removed; the generated JSON now comes directly from LinkML.

### Workbook: six identifiers are incorrectly labeled optional

These rows say `0..1` / `Optional`, but the LinkML attributes have
`identifier: true`, which makes them effectively required. Generated and supplied
JSON both require them:

| Class and field | Workbook sheet | Excel row |
|---|---|---|
| Project.id | General | 3 |
| ReportingPeriod.id | General | 17 |
| MonitoringPlan.id | Monitoring Plan | 3 |
| StaticValue.id | Static Value | 3 |
| Measurement.id | Measurement | 3 |
| Result.id | Result | 3 |

All workbook class/field pairs occur in the LinkML model. Other required/cardinality
and datatype mappings, and picklist values, agree. The original workbook is retained
unaltered so these corrections remain explicit review items, not silently changed
incoming material. Workbook descriptions append removal flags for the four
methodology-specific fields; these correspond to LinkML notes/annotations.

### November proposals are not in the attached revision

The files still use `Result` / `ResultInput` and retain:

- `Project.assessment_area`
- `MonitoringScope.calculation_worksheet`
- `MonitoringScope.hwp_worksheet`
- `MonitoringScope.chain_of_custody_and_application_evidence`

The email's proposed `CalculatedValue` rename and removal of those fields are not
applied in this import. Qualitative applicability/additionality assessment remains
outside this revision. These are separate design changes for pod review.

### Worked example

The unmodified worked example validates against both JSON schemas, including
format checking. Its reporting-period, plan, and result-input references resolve;
IDs within each collection are unique, and the result dependency chain is acyclic.

Arithmetic is consistent at the illustrated four-decimal precision:

- Mean fuel: `(1200 + 1300) / 2 = 1250 kg`.
- Baseline: `2000 * 0.001747 * 0.30 = 1.0482 tCO2e`.
- Project: `1250 * 0.001747 * 0.30 = 0.655125`, shown as `0.6551`.
- Net: `1.0482 - 0.655125 = 0.393075`, shown as `0.3931`.

This is a structural/arithmetic audit, not verification of VM0050 compliance,
scientific assumptions, evidence authenticity, or unit-vocabulary conformance.

### Validation boundaries

JSON Schema checks shapes and values, not referential integrity, identifier
uniqueness across object lists, result dependency cycles, date ordering, or whether
measurements fall inside reporting windows. The example tests inspect references
and cycles for this fixture; they are not a new general-purpose semantic validator.
Units are free strings, with UCUM recommended but not enforced. A Result has no
direct plan property; it can connect to plans indirectly through Measurement inputs (including upstream results).

## Reproduce

Run `uv sync --locked` then `make validate docs`. `make validate` validates the
LinkML model, both updated examples, and the six revision regression tests.
The JSON and documentation remain generated build outputs rather than a second
editable source of truth. The original JSON fixture is deliberately immutable
comparison evidence.

## Attachment checksums (SHA-256)

```
mrv-pod.yaml                    6832a9add88013cce576381e68adc2cad707d7266d6e6a6fc595e18d624d5295
mrv-pod-example.yaml            3518e60e3d8b8b0f7514f4968fe576f952e2c196ac75c6128f9a8b6a728bfaa7
mrv-pod.schema.json             76f460ebdfc02d7a32df2c7c47201f574b6bf71f5502c7f813163e8a472837c5
MRV-schema-2026-09-24.xlsx       f761f2c0adf06962e5a9eef945fa7dee7fb0b190a7660e37b57f51ad576adc13
```
