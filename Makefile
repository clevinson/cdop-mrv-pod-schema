SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help
.DELETE_ON_ERROR:

RUN := uv run --locked
SCHEMA := schema/mrv-pod.yaml
JSON_SCHEMA := build/mrv-pod.schema.json
EXAMPLES ?= $(wildcard examples/*.yaml)

.PHONY: help schema validate docs serve

help:
	@printf '%s\n' 'make schema    Compile build/mrv-pod.schema.json' \
	  'make validate  Validate the schema and examples using LinkML CLI' \
	  'make docs      Build the documentation in build/site/' \
	  'make serve     Build and preview docs at http://127.0.0.1:8000'

schema: $(JSON_SCHEMA)

$(JSON_SCHEMA): $(SCHEMA) pyproject.toml uv.lock Makefile build.py
	mkdir -p build
	$(RUN) gen-json-schema --closed --top-class Project $(SCHEMA) | \
	  $(RUN) python build.py json-schema $(SCHEMA) > $@

validate: schema
	$(RUN) linkml validate $(SCHEMA)
	$(RUN) python build.py validation-config $(SCHEMA) $(JSON_SCHEMA) $(EXAMPLES) > build/validation.yaml
	# Pass filenames too: LinkML 1.11.1 exhausts config-only source iterators early.
	$(RUN) linkml validate --config build/validation.yaml $(EXAMPLES)

docs: schema
	$(RUN) python build.py clean-docs
	$(RUN) gen-doc --directory build/docs/schema --render-imports \
	  --example-directory examples \
	  --diagram-type mermaid_class_diagram --subfolder-type-separation $(SCHEMA)
	$(RUN) python build.py customize-docs
	mkdir -p build/docs/examples build/docs/schema
	cp examples/*.yaml build/docs/examples/
	cp $(SCHEMA) build/docs/schema/mrv-pod.yaml
	cp $(JSON_SCHEMA) build/docs/schema/mrv-pod.schema.json
	$(RUN) mkdocs build --strict

serve: docs
	$(RUN) mkdocs serve
