"""Minimal YAML-frontmatter reader for the COS eval harness.

Uses pyyaml when present; otherwise falls back to a tiny parser that covers the
restricted frontmatter we author (scalars + simple inline lists). Memory files
are plain Markdown with a `---` fenced YAML head, per `engine/templates/*`.
"""
from __future__ import annotations

from pathlib import Path

try:  # pyyaml is the documented dev dependency, but the harness must not hard-require it
    import yaml  # type: ignore

    _HAVE_YAML = True
except Exception:  # pragma: no cover
    _HAVE_YAML = False


def split_frontmatter(text: str):
    """Return (meta_text, body). meta_text is '' when there is no frontmatter."""
    if not text.startswith("---"):
        return "", text
    lines = text.splitlines()
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return "", text
    return "\n".join(lines[1:end]), "\n".join(lines[end + 1:])


def parse(path: Path):
    """Return (meta: dict, body: str) for a markdown file."""
    text = path.read_text(encoding="utf-8-sig")  # strip a BOM if the file was saved with one
    meta_text, body = split_frontmatter(text)
    meta = {}
    if meta_text:
        if _HAVE_YAML:
            try:
                meta = yaml.safe_load(meta_text) or {}
            except Exception:
                meta = _fallback_parse(meta_text)
        else:
            meta = _fallback_parse(meta_text)
    if not isinstance(meta, dict):
        meta = {}
    return meta, body


def _scalar(v: str):
    """Coerce a bare scalar to bool/int/float/None like yaml.safe_load would, for parity."""
    v = v.strip().strip('"').strip("'")
    low = v.lower()
    if low == "true":
        return True
    if low == "false":
        return False
    if low in ("null", "~", ""):
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        return v


def _fallback_parse(meta_text: str) -> dict:
    """Tiny `key: value` parser for restricted frontmatter (scalars + inline lists).

    Coerces scalar types so behavior matches pyyaml when it isn't installed.
    """
    out: dict = {}
    for line in meta_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip(), val.strip()
        # drop trailing inline comment
        if "  #" in val:
            val = val.split("  #", 1)[0].strip()
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            out[key] = [_scalar(v) for v in inner.split(",") if v.strip()]
        else:
            out[key] = _scalar(val)
    return out
