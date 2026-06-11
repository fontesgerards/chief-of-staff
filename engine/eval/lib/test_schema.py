"""Lockstep tests for the output-contract schema (plan U2, R11).

Keeps the three expressions of the contract from drifting:
  schema.py (machine-readable) ↔ templates (the truth) ↔ SKILL.md tables (human mirror)
and the origin enum synced into the self-contained provenance hook.
"""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

from lib import assertions, frontmatter, schema

REPO = Path(__file__).resolve().parents[3]
SKILLS_DIR = REPO / "engine" / "skills"
TEMPLATE_REF = re.compile(r"engine/templates/[A-Za-z0-9._-]+\.md")

# Templates legitimately referenced by SKILL.md tables that carry no frontmatter
# schema (append-only block / entry files / human doc).
NON_FRONTMATTER_TEMPLATES = {
    "engine/templates/capture-footer.md",
    "engine/templates/entry-CLAUDE.md",
    "engine/templates/getting-started.md",
    "engine/templates/decision-record.md",   # JSONL schema doc for the decision dashboard
}


def _schema_templates() -> set[str]:
    out: set[str] = set()
    for spec in schema.ARTIFACT_TYPES.values():
        t = spec["template"]
        out.update(t if isinstance(t, list) else [t])
    return out


# --- (a) origin enum is one value everywhere ---------------------------------

def test_origin_enum_synced_into_provenance_hook():
    hook = REPO / "engine" / "eval" / "hooks" / "provenance_check.py"
    spec = importlib.util.spec_from_file_location("provenance_check", hook)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.VALID_ORIGINS == assertions.VALID_ORIGINS, (
        "provenance_check.py's self-contained origin set drifted from "
        "assertions.VALID_ORIGINS — sync the copy."
    )


def test_origin_enum_reexported_and_includes_derived():
    assert schema.VALID_ORIGINS is assertions.VALID_ORIGINS
    assert "derived" in schema.VALID_ORIGINS  # KTD4
    assert schema.VALID_ORIGINS == {"observed", "confirmed", "inferred", "imported", "derived"}


# --- (b) every artifact type points at a real template -----------------------

def test_every_artifact_template_exists():
    missing = sorted(t for t in _schema_templates() if not (REPO / t).is_file())
    assert not missing, f"schema.py references missing templates: {missing}"


# --- (c) required keys actually exist in the template's frontmatter ----------

def test_required_keys_present_in_templates():
    problems = []
    for typ, spec in schema.ARTIFACT_TYPES.items():
        templates = spec["template"]
        for t in templates if isinstance(templates, list) else [templates]:
            meta, _ = frontmatter.parse(REPO / t)
            missing = [k for k in spec["required_keys"] if k not in meta]
            if missing:
                problems.append(f"{typ} ({t}): missing {missing}")
            if meta.get("type") != typ:
                problems.append(f"{typ} ({t}): template declares type={meta.get('type')!r}")
    assert not problems, "\n".join(problems)


# --- (d) SKILL.md output-contract tables match reality ------------------------

def _contract_section(text: str) -> str | None:
    m = re.search(r"^## Output contract\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return m.group(1) if m else None


def test_every_skill_has_an_output_contract():
    missing = sorted(
        p.parent.name
        for p in SKILLS_DIR.glob("*/SKILL.md")
        if _contract_section(p.read_text(encoding="utf-8")) is None
    )
    assert not missing, f"SKILL.md missing '## Output contract': {missing}"


def test_skill_contract_templates_exist_and_are_known():
    known = _schema_templates() | NON_FRONTMATTER_TEMPLATES
    problems = []
    for p in sorted(SKILLS_DIR.glob("*/SKILL.md")):
        section = _contract_section(p.read_text(encoding="utf-8"))
        if section is None:
            continue  # covered by test_every_skill_has_an_output_contract
        refs = set(TEMPLATE_REF.findall(section))
        if not refs:
            problems.append(f"{p.parent.name}: contract table references no template")
        for ref in sorted(refs):
            if not (REPO / ref).is_file():
                problems.append(f"{p.parent.name}: references missing template {ref}")
            elif ref not in known:
                problems.append(f"{p.parent.name}: references template not in schema.py: {ref}")
    assert not problems, "\n".join(problems)
