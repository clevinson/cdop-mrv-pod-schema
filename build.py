"""Small build helpers; run from the repository root. See --help for commands."""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import yaml

DOCS = Path("build/docs")
DOC_FOLDERS = {"classes": "class", "slots": "slot", "enums": "enum"}


def json_schema(schema):
    """Apply the extra_slots setting omitted by LinkML 1.11.1's generator."""
    artifact = json.load(sys.stdin)
    model = yaml.safe_load(Path(schema).read_text())
    artifact["$defs"]["JsonObject"]["additionalProperties"] = model["classes"][
        "JsonObject"
    ]["extra_slots"]["allowed"]
    print(json.dumps(artifact, indent=2, ensure_ascii=False))


def validation_config(schema, artifact, examples):
    """Select the built-in reader that preserves nulls in both YAML and JSON."""
    config = {
        "schema": schema,
        "target_class": "Project",
        "plugins": {"JsonschemaValidationPlugin": {"json_schema_path": artifact}},
        "data_sources": [{"YamlLoader": {"source": path}} for path in examples],
    }
    print(json.dumps(config, indent=2))


def clean_docs():
    """Remove stale generated pages before running gen-doc."""
    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir(parents=True)


def customize_docs():
    """Use workbook terminology and make the schema reference the landing page."""
    # LinkML emits singular URI paths but plural documentation folders.
    for plural, singular in DOC_FOLDERS.items():
        folder = DOCS / "schema" / plural
        if folder.exists():
            folder.rename(folder.with_name(singular))

    for path in DOCS.rglob("*.md"):
        # Keep source snippets intact; rewrite only local links and prose labels.
        parts = re.split(r"(?ms)(^```.*?^```[^\n]*|`[^`\n]*`)", path.read_text())
        for index in range(0, len(parts), 2):
            parts[index] = re.sub(
                r"(\]\((?:\.\./)*(?:schema/)?)(classes|slots|enums)/",
                lambda match: match[1] + DOC_FOLDERS[match[2]] + "/",
                parts[index],
            )
            parts[index] = re.sub(
                r"(?<![\w/:])[Ss]lots?(?![\w/])",
                lambda match: match[0].replace("Slot", "Field").replace("slot", "field"),
                parts[index],
            )
        for index in range(1, len(parts), 2):
            if parts[index].startswith("```mermaid"):
                parts[index] = re.sub(
                    r'(\bclick [^\n]*? href "(?:\.\./)*)(classes|slots|enums)/',
                    lambda match: match[1] + DOC_FOLDERS[match[2]] + "/",
                    parts[index],
                )
        path.write_text("".join(parts))

    index = DOCS / "schema/index.md"
    if index.exists():
        text = re.sub(r"(?m)^(?:URI|Name): .*\n", "", index.read_text())
        text = re.sub(
            r"\]\((class|slot|enum|types|schemas|subsets)/",
            r"](schema/\1/",
            text,
        )
        (DOCS / "index.md").write_text(text)
        # Keep schema/index.md too: the schema's own identifier resolves here.


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser("json-schema", help="Patch generated JSON Schema from stdin")
    schema.add_argument("schema", help="Source LinkML schema")
    config = commands.add_parser("validation-config", help="Print LinkML CLI configuration")
    config.add_argument("schema")
    config.add_argument("artifact", help="Generated JSON Schema")
    config.add_argument("examples", nargs="+")
    commands.add_parser("clean-docs", help="Clear the generated documentation directory")
    commands.add_parser("customize-docs", help="Customize generated Markdown for the pod")
    args = parser.parse_args()

    if args.command == "json-schema":
        json_schema(args.schema)
    elif args.command == "validation-config":
        validation_config(args.schema, args.artifact, args.examples)
    elif args.command == "clean-docs":
        clean_docs()
    else:
        customize_docs()


if __name__ == "__main__":
    main()
