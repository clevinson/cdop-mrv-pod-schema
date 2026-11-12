# CDOP MRV pod schemas

A draft set of shared data definitions for the CDOP pod's monitoring, reporting
and verification (MRV) work. It describes project information, monitoring plans
and results, and supporting evidence for discussion and review with the pod.

[Browse the documentation](https://clevinson.github.io/cdop-mrv-pod-schema/)
for field descriptions, required information, and examples.

The definitions use [LinkML](https://linkml.io/), a language for describing
structured data, and are kept in one [schema file](schema/mrv-pod.yaml).

## Current revision and build

The current LinkML source is Chad's 0.2.7 revision, supplied September 29 and
reattached November 5, 2026. The [September 24 workbook](MRV-schema-2026-09-24.xlsx)
is its original review companion. See the [import audit](docs/chad-update-audit.md)
for JSON-generation differences, workbook inconsistencies, and pending proposals.

```sh
uv sync --locked
make validate docs
```

JSON Schema is regenerated into `build/mrv-pod.schema.json` from LinkML; generated
schema and documentation are not committed. The September 22 workbook is retained
for history only. Existing 0.1.0 data must be migrated: typed quantities,
methodology objects, keyed reporting periods, and separate static/measurement/result
collections replace the earlier free-text and JSON-blob structures.
