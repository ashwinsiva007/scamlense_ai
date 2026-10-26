"""
Rule Pack Validator Script
--------------------------
Validates all YAML rule packs in backend/rules/ against rule_pack_schema.json.
Ensures structural conformity, valid regexes, and multilingual pattern presence.
"""

import glob
import io
import json
import os
import re
import sys
import yaml

# Reconfigure stdout/stderr for Windows console unicode support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
rules_dir = os.path.join(backend_root, "rules")
schema_path = os.path.join(rules_dir, "rule_pack_schema.json")


def validate_rule_pack(file_path: str, schema: dict) -> list[str]:
    errors = []
    basename = os.path.basename(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return [f"YAML parse error in {basename}: {e}"]

    if not isinstance(data, dict):
        return [f"{basename}: root must be a mapping/dict"]

    category = data.get("category")
    allowed_categories = schema["properties"]["category"]["enum"]
    if category not in allowed_categories:
        errors.append(f"{basename}: invalid or missing category '{category}'")

    rules = data.get("rules", [])
    if not isinstance(rules, list):
        errors.append(f"{basename}: 'rules' must be a list")
        return errors

    rule_ids = set()
    for idx, rule in enumerate(rules):
        rule_prefix = f"{basename} rule #{idx+1}"
        if not isinstance(rule, dict):
            errors.append(f"{rule_prefix}: rule must be a mapping")
            continue

        rid = rule.get("id")
        if not rid or not re.match(r"^[A-Z0-9_]+$", str(rid)):
            errors.append(f"{rule_prefix}: invalid or missing id '{rid}'")
        elif rid in rule_ids:
            errors.append(f"{rule_prefix}: duplicate rule id '{rid}'")
        else:
            rule_ids.add(rid)

        rcat = rule.get("category")
        if rcat != category:
            errors.append(f"{rule_prefix} ({rid}): category '{rcat}' does not match pack category '{category}'")

        weight = rule.get("weight")
        if not isinstance(weight, (int, float)):
            errors.append(f"{rule_prefix} ({rid}): invalid weight '{weight}'")

        patterns = rule.get("patterns")
        if not isinstance(patterns, dict):
            errors.append(f"{rule_prefix} ({rid}): missing 'patterns' dict")
            continue

        for lang in ["en", "ta", "hi"]:
            lang_patterns = patterns.get(lang)
            if not isinstance(lang_patterns, list):
                errors.append(f"{rule_prefix} ({rid}): missing pattern list for '{lang}'")
            else:
                for p in lang_patterns:
                    try:
                        re.compile(p, re.IGNORECASE)
                    except re.error as re_err:
                        errors.append(f"{rule_prefix} ({rid}) invalid regex in '{lang}': {p} ({re_err})")

    return errors


def main():
    if not os.path.exists(schema_path):
        print(f"Error: Schema not found at {schema_path}", file=sys.stderr)
        sys.exit(1)

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    yaml_files = glob.glob(os.path.join(rules_dir, "*.yaml"))
    if not yaml_files:
        print(f"No YAML files found in {rules_dir}", file=sys.stderr)
        sys.exit(1)

    total_rules = 0
    total_errors = []

    print(f"Validating {len(yaml_files)} rule packs against {os.path.basename(schema_path)}...\n")

    for yf in sorted(yaml_files):
        errs = validate_rule_pack(yf, schema)
        with open(yf, "r", encoding="utf-8") as f:
            pack_data = yaml.safe_load(f) or {}
        rcount = len(pack_data.get("rules", []))
        total_rules += rcount

        if errs:
            print(f"❌ {os.path.basename(yf)} ({rcount} rules) - FAIL")
            for e in errs:
                print(f"   • {e}")
            total_errors.extend(errs)
        else:
            print(f"✅ {os.path.basename(yf)} ({rcount} rules) - PASS")

    print(f"\nTotal rules checked: {total_rules}")

    if total_errors:
        print(f"Validation failed with {len(total_errors)} errors.", file=sys.stderr)
        sys.exit(1)
    else:
        print("All rule packs are structurally valid!")


if __name__ == "__main__":
    main()
