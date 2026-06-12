"""Output-contract schema for COS artifacts — pure data, no logic (plan U2, R11).

The single machine-readable source the validator (U8 sweep) and the eval
harness consume. Each skill's SKILL.md carries the human-readable mirror
("## Output contract" table); test_schema.py keeps the two in lockstep.

Derived from the actual frontmatter of `engine/templates/*.md` — when a
template changes, this file changes with it (test_schema.py asserts the
required keys still exist in each template).
"""
from __future__ import annotations

# Single Python source of the closed origin enum (INSTRUCTIONS.md §6).
# engine/eval/hooks/provenance_check.py keeps a deliberate self-contained copy;
# test_schema.py asserts equality.
from .assertions import VALID_ORIGINS  # noqa: F401  (re-export)

# Keyed by the frontmatter `type` value. Values:
#   template      — repo-relative template file(s); a list when several
#                   templates share one `type` (the five core-* files).
#   path_pattern  — instance-relative location the artifact is written to.
#   required_keys — frontmatter keys every instance of the type must carry.
ARTIFACT_TYPES = {
    # --- semantic entities --------------------------------------------------
    "person": {
        "template": "engine/templates/person.md",
        "path_pattern": "memory/semantic/people/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    "account": {
        "template": "engine/templates/account.md",
        "path_pattern": "memory/semantic/accounts/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    "competitor": {
        "template": "engine/templates/competitor.md",
        "path_pattern": "memory/semantic/competitors/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    "project": {
        "template": "engine/templates/project.md",
        "path_pattern": "memory/semantic/projects/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    "concept": {
        "template": "engine/templates/concept.md",
        "path_pattern": "memory/semantic/concepts/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    "relationship": {
        "template": "engine/templates/relationship.md",
        "path_pattern": "memory/semantic/relationships/<slug>.md",
        "required_keys": ["type", "status", "last_touched", "relationships", "confidence", "origin", "sources"],
    },
    # The glossary: `type: semantic` + `subtype: glossary` (one file, not a dir).
    "semantic": {
        "template": "engine/templates/glossary.md",
        "path_pattern": "memory/semantic/glossary.md",
        "required_keys": ["type", "subtype", "last_touched", "origin"],
    },
    # --- episodic -----------------------------------------------------------
    "episode": {
        "template": "engine/templates/episodic.md",
        "path_pattern": "memory/episodic/<kind>/YYYY-MM-DD-<slug>.md",  # kind: meetings|decisions|interactions|milestones
        "required_keys": ["type", "date", "entities", "origin", "sources"],
    },
    "coaching-note": {
        "template": "engine/templates/coaching-note.md",
        "path_pattern": "memory/episodic/coaching/YYYY-MM-DD.md",
        "required_keys": ["type", "date", "covers", "origin"],
    },
    "goals-snapshot": {
        "template": "engine/templates/goals-snapshot.md",
        "path_pattern": "memory/episodic/goals/YYYY-MM.md",  # month granularity is intentional (U1)
        "required_keys": ["type", "month", "date", "origin"],
    },
    # --- procedural ----------------------------------------------------------
    "procedural": {
        "template": "engine/templates/procedural-skill.md",
        "path_pattern": "memory/procedural/<skill>.md",
        "required_keys": ["type", "skill", "last_touched", "origin"],
    },
    # --- core (the five core-* templates share `type: core`) -----------------
    "core": {
        "template": [
            "engine/templates/core-identity.md",
            "engine/templates/core-operating-context.md",
            "engine/templates/core-autonomy.md",
            "engine/templates/core-voice.md",
            "engine/templates/core-current-priorities.md",
        ],
        "path_pattern": "memory/core/<name>.md",
        "required_keys": ["type", "origin", "budget_chars"],
    },
    # --- sources (write-time schema; the sweep NEVER reads this dir) ----------
    "source": {
        "template": "engine/templates/source-summary.md",
        "path_pattern": "memory/sources/<kind>/<slug>.md",  # kind: email|calendar|transcript|doc|web
        "required_keys": ["type", "source_kind", "date", "origin", "captured_by", "retention_until"],
    },
    # --- briefs / run artifacts -----------------------------------------------
    "daily-brief": {
        "template": "engine/templates/daily-brief.md",
        "path_pattern": "state/briefs/daily-brief-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "covers", "origin"],
    },
    "inbox-sweep-brief": {
        "template": "engine/templates/inbox-sweep-brief.md",
        "path_pattern": "state/briefs/inbox-sweep-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "covers", "origin"],
    },
    "loop-closing-brief": {
        "template": "engine/templates/loop-closing-brief.md",
        "path_pattern": "state/briefs/loop-closing-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "origin"],
    },
    "meeting-prep-brief": {
        "template": "engine/templates/meeting-prep-brief.md",
        "path_pattern": "state/briefs/meeting-prep-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "meeting", "when", "entities", "origin"],
    },
    "research-digest": {
        "template": "engine/templates/research-digest.md",
        "path_pattern": "state/briefs/research-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "covers", "origin"],
    },
    "system-maintenance-note": {
        "template": "engine/templates/system-maintenance-note.md",
        "path_pattern": "state/briefs/system-maintenance-YYYY-MM-DD.md",
        "required_keys": ["type", "date", "covers", "origin"],
    },
    "consolidation-changelog": {
        "template": "engine/templates/consolidation-changelog.md",
        "path_pattern": "log/maintenance/YYYY-MM-DD.md",
        "required_keys": ["type", "date", "origin"],
    },
    # --- queue ----------------------------------------------------------------
    "proposal": {
        "template": "engine/templates/proposal.md",
        "path_pattern": "queue/outbound/YYYY-MM-DD-<slug>.md",
        "required_keys": ["type", "date", "skill", "status", "reversibility", "tool", "args_digest"],
    },
    # --- instance root ----------------------------------------------------------
    "config": {
        "template": "engine/templates/config.md",
        "path_pattern": "config.md",
        "required_keys": ["type", "date"],
    },
}

# Instance-relative globs the validator sweep must SKIP.
SWEEP_EXCLUSIONS = [
    "queue/**",            # proposals/review surface — lifecycle, not standing memory
    "log/**",              # run logs + maintenance changelogs — append-only observability
    "state/*.md",          # the append-only tables (current/commitments/open-loops/
                           #   corrections/pending-questions) carry no frontmatter;
                           #   state/briefs/** IS swept
    "state/validation/**", # the validator's own findings manifests — machine-written
    "memory/sources/**",   # NEVER read by the sweep — injection boundary; schema is
                           #   enforced at write time by the isolated extractor
    ".claude/**",          # runtime settings, not memory
    "*-snapshots/**",      # backup/test snapshots
]

# Checks that warn rather than fail (a wikilink may resolve on a later write).
WARN_ONLY_CHECKS = {"valid_links"}
