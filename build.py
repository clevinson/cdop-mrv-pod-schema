"""Small build helpers; run from the repository root. See --help for commands."""

import argparse
import json
from pathlib import Path
import re
import shutil
import sys
from textwrap import indent

import yaml

DOCS = Path("build/docs")


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


def example_tabs(match):
    """Render a generated YAML example as JSON-first Material content tabs."""
    yaml_text = match[2].rstrip()
    json_text = json.dumps(yaml.safe_load(yaml_text), indent=2, ensure_ascii=False, allow_nan=False)
    return match[1] + "\n\n".join(
        f'=== "{language.upper()}"\n\n' + indent(f"```{language}\n{content}\n```", "    ")
        for language, content in (("json", json_text), ("yaml", yaml_text))
    ) + "\n"


def customize_docs():
    """Use workbook terminology and make the schema reference the landing page."""
    prefix = yaml.safe_load(Path("schema/mrv-pod.yaml").read_text())["default_prefix"]
    for path in DOCS.rglob("*.md"):
        # Keep source snippets and external links intact.
        parts = re.split(r"(?ms)(^[ \t]*```.*?^[ \t]*```[^\n]*|`[^`\n]*`)", path.read_text())
        for index in range(0, len(parts), 2):
            # An element's identifier and its documentation URL are distinct.
            # Link the displayed identifier to this page without altering the URI.
            parts[index] = re.sub(
                rf"(?m)^(URI: \[{re.escape(prefix)}:[^\]]+\])\([^)]+\)$",
                lambda match: f"{match[1]}({path.name})",
                parts[index],
            )
            parts[index] = re.sub(
                r"(?<![\w/:])[Ss]lots?(?![\w/])",
                lambda match: match[0].replace("Slot", "Field").replace("slot", "field"),
                parts[index],
            )
        text = re.sub(
            r"(?ms)(^### Example: [^\n]+\n\n)```yaml\n(.*?)^```[ \t]*$",
            example_tabs,
            "".join(parts),
        )
        path.write_text(text)

    index = DOCS / "schema/index.md"
    if index.exists():
        text = re.sub(r"(?m)^(?:URI|Name): .*\n", "", index.read_text())
        text = re.sub(
            r"\]\((classes|slots|enums|types|schemas|subsets)/",
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
