"""Structural assertions for the COS eval harness.

Deterministic, no model calls. This is the layer that catches schema drift,
broken provenance, lost history, and dangling links — the things an LLM judge
should NOT be spending tokens on. Each check returns (ok: bool, detail: str).

Mirrors the discipline in pm-brain's harness: "the biggest mistake is using
LLM-as-judge for what a structural assertion can answer."
"""
from __future__ import annotations

import re
from pathlib import Path

from . import frontmatter

# The closed origin set from engine/INSTRUCTIONS.md §6.
VALID_ORIGINS = {"observed", "confirmed", "inferred", "imported"}
WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")

JUDGE = "judge"  # reserved key: content assertions handled by the (optional) LLM phase


def _p(instance: Path, rel: str) -> Path:
    return instance / rel


def _read(instance: Path, rel: str):
    path = _p(instance, rel)
    return path.read_text(encoding="utf-8") if path.exists() else None


def file_exists(instance, spec):
    ok = _p(instance, spec).is_file()
    return ok, f"{spec} {'exists' if ok else 'MISSING'}"


def file_absent(instance, spec):
    ok = not _p(instance, spec).exists()
    return ok, f"{spec} {'absent' if ok else 'UNEXPECTEDLY PRESENT'}"


def contains(instance, spec):
    text = _read(instance, spec["path"])
    if text is None:
        return False, f"{spec['path']} MISSING"
    ci = spec.get("ci", True)
    found = (spec["text"].lower() in text.lower()) if ci else (spec["text"] in text)
    return found, f"{spec['path']} {'contains' if found else 'MISSING text'}: {spec['text']!r}"


def not_contains(instance, spec):
    text = _read(instance, spec["path"])
    if text is None:
        return False, f"{spec['path']} MISSING"
    ci = spec.get("ci", True)
    found = (spec["text"].lower() in text.lower()) if ci else (spec["text"] in text)
    verb = "correctly omits" if not found else "UNEXPECTEDLY contains"
    return (not found), f"{spec['path']} {verb}: {spec['text']!r}"


def regex(instance, spec):
    text = _read(instance, spec["path"])
    if text is None:
        return False, f"{spec['path']} MISSING"
    flags = re.DOTALL | (re.IGNORECASE if spec.get("ci", True) else 0)
    ok = re.search(spec["pattern"], text, flags) is not None
    return ok, f"{spec['path']} pattern {'matched' if ok else 'NO MATCH'}: {spec['pattern']!r}"


def frontmatter_eq(instance, spec):
    path = _p(instance, spec["path"])
    if not path.is_file():
        return False, f"{spec['path']} MISSING"
    meta, _ = frontmatter.parse(path)
    val = meta.get(spec["key"])
    ok = str(val).strip() == str(spec["value"]).strip()
    return ok, f"{spec['path']}:{spec['key']} = {val!r} (want {spec['value']!r})"


def has_origin(instance, spec):
    """Provenance gate: an entity file must declare a valid `origin` (§6)."""
    path = _p(instance, spec)
    if not path.is_file():
        return False, f"{spec} MISSING"
    meta, _ = frontmatter.parse(path)
    origin = str(meta.get("origin", "")).strip()
    ok = origin in VALID_ORIGINS
    return ok, f"{spec} origin={origin!r} ({'valid' if ok else 'NOT in closed set ' + str(sorted(VALID_ORIGINS))})"


def superseded(instance, spec):
    """The supersede-don't-overwrite invariant (write-back.md §5 op 3):
    after a #fact correction, BOTH the new and old values remain readable and the
    old one carries a `valid_until` stamp. History is preserved, not destroyed."""
    text = _read(instance, spec["path"])
    if text is None:
        return False, f"{spec['path']} MISSING"
    low = text.lower()
    missing = []
    if spec["new"].lower() not in low:
        missing.append("new value")
    if spec["old"].lower() not in low:
        missing.append("old value")
    if "valid_until" not in low:
        missing.append("valid_until stamp")
    ok = not missing
    return ok, f"{spec['path']} supersede " + ("ok (history preserved)" if ok else "MISSING " + ", ".join(missing))


def valid_links(instance, spec):
    """Every [[wikilink]] resolves to a real `*.md` somewhere under the instance."""
    text = _read(instance, spec)
    if text is None:
        return False, f"{spec} MISSING"
    stems = {p.stem.lower() for p in instance.rglob("*.md")}
    unresolved = []
    for m in WIKILINK.findall(text):
        target = m.split("|")[0].strip().split("/")[-1].lower()
        if target and target not in stems:
            unresolved.append(m)
    ok = not unresolved
    return ok, f"{spec} links " + ("all resolve" if ok else "UNRESOLVED: " + ", ".join(sorted(set(unresolved))))


CHECKS = {
    "file_exists": file_exists,
    "file_absent": file_absent,
    "contains": contains,
    "not_contains": not_contains,
    "regex": regex,
    "frontmatter_eq": frontmatter_eq,
    "has_origin": has_origin,
    "superseded": superseded,
    "valid_links": valid_links,
}
