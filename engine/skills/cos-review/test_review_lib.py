import json

import frontmatter
import outbound
import review_lib


def _instance(tmp_path):
    inst = tmp_path / "instance"
    (inst / "queue" / "outbound").mkdir(parents=True)
    (inst / "queue" / "review" / "memory").mkdir(parents=True)
    (inst / "state").mkdir(parents=True)
    return inst


def _proposal(inst, slug, args, *, status="pending", tool="mcp__claude_ai_Gmail__create_draft",
              topic=None, source=None, body_extra="", reversibility="reversible"):
    dig = outbound.digest(args)
    fm = [f"type: proposal", f"status: {status}", f"reversibility: {reversibility}",
          f"tool: {tool}", f"args_digest: {dig}", "date: 2026-06-03"]
    if topic:
        fm.append(f"topic: {topic}")
    if source:
        fm.append(f"source: {source}")
    body = (
        "---\n" + "\n".join(fm) + "\n---\n\n"
        f"# Proposal: {slug}\n\n{body_extra}\n"
        f"```json\n{json.dumps(args, indent=2)}\n```\n"
    )
    p = inst / "queue" / "outbound" / f"{slug}.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_collect_buckets_by_tab(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "p-pending", {"to": "a@x.com"}, status="pending")
    _proposal(inst, "p-approved", {"to": "b@x.com"}, status="approved")
    _proposal(inst, "p-sent", {"to": "c@x.com"}, status="sent")
    _proposal(inst, "p-rejected", {"to": "d@x.com"}, status="rejected")
    tabs = {c.card_id: c.tab for c in review_lib.collect_cards(inst)}
    assert tabs["outbound:p-pending"] == "review"
    assert tabs["outbound:p-approved"] == "queued"
    assert tabs["outbound:p-sent"] == "done"
    assert tabs["outbound:p-rejected"] == "done"


def test_only_review_tab_has_action_buttons(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "p-pending", {"to": "a@x.com"}, status="pending")
    _proposal(inst, "p-approved", {"to": "b@x.com"}, status="approved")
    cards = {c.card_id: c for c in review_lib.collect_cards(inst)}
    assert cards["outbound:p-pending"].decisions == ["send", "edit", "reject"]
    assert cards["outbound:p-approved"].decisions == ["reject"]   # queued: pull-back only


def test_topic_and_source_eyebrow(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "p1", {"to": "a@x.com"}, topic="Sponsorships", source="inbox")
    _proposal(inst, "p2", {"to": "b@x.com"})  # defaults
    cards = {c.card_id: c for c in review_lib.collect_cards(inst)}
    assert cards["outbound:p1"].topic == "Sponsorships"
    assert cards["outbound:p1"].source_label == "INBOX"
    assert cards["outbound:p2"].topic == "General"
    assert cards["outbound:p2"].source_label == "INBOX"  # derived from gmail tool


def test_rich_card_sections_parsed(tmp_path):
    inst = _instance(tmp_path)
    body_extra = (
        "The note is a concrete sponsorship inquiry.\n\n"
        "## What happened\nPolicy says unknown sponsorship requests route to Sydney.\n\n"
        "## Why this is in the sweep\n- Request hit sponsorships@every.to\n- Brand not a known sponsor\n\n"
        "## Read full source\nFull email body here.\n\n"
    )
    _proposal(inst, "miquido", {"to": "s@x.com", "body": "sydney - this came through sponsorships."},
              topic="Sponsorships", source="inbox", body_extra=body_extra)
    c = review_lib.collect_cards(inst)[0]
    f = c.fields
    assert f["what_happened"].startswith("Policy says unknown sponsorship")
    assert f["why"] == ["Request hit sponsorships@every.to", "Brand not a known sponsor"]
    assert f["full_source"] == "Full email body here."
    assert f["draft"] == "sydney - this came through sponsorships."  # from Action body
    assert f["context"].startswith("The note is a concrete")


def test_questions_and_memory_tabs(tmp_path):
    inst = _instance(tmp_path)
    (inst / "state" / "pending-questions.md").write_text(
        "| Question | Why | Raised | Status |\n|---|---|---|---|\n"
        "| Open one? | x | 2026-06-11 | open |\n"
        "| Done one? | y | 2026-06-10 | resolved |\n", encoding="utf-8")
    (inst / "queue" / "review" / "memory" / "promote-willie.diff").write_text(
        "- Role: contractor\n+ Role: Head of Ops\n", encoding="utf-8")
    cards = {c.card_id: c for c in review_lib.collect_cards(inst)}
    q_open = next(c for c in cards.values() if c.kind == "question" and c.tab == "review")
    q_done = next(c for c in cards.values() if c.kind == "question" and c.tab == "done")
    assert q_open.title == "Open one?" and q_open.decisions == ["answer", "dismiss"]
    assert q_done.title == "Done one?" and q_done.decisions == []
    mem = cards["memory:promote-willie"]
    assert mem.tab == "review" and mem.topic == "Memory"
    assert mem.fields["diff"] == "- Role: contractor\n+ Role: Head of Ops\n"  # raw


def test_resolve_memory_approve_and_reject(tmp_path):
    inst = _instance(tmp_path)
    mem = inst / "queue" / "review" / "memory"
    (mem / "promote-willie.diff").write_text("- a\n+ b\n", encoding="utf-8")
    (mem / "merge-acme.diff").write_text("- c\n+ d\n", encoding="utf-8")
    ap = review_lib.resolve_memory(inst, "memory:promote-willie", "approve")
    rj = review_lib.resolve_memory(inst, "memory:merge-acme", "reject")
    assert ap == mem / "approved" / "promote-willie.diff" and ap.is_file()
    assert rj == mem / "rejected" / "merge-acme.diff" and rj.is_file()
    # resolved diffs no longer surface as Memory cards (non-recursive glob)
    assert not [c for c in review_lib.collect_cards(inst) if c.kind == "memory"]
    # idempotent: re-resolving a gone file returns None
    assert review_lib.resolve_memory(inst, "memory:promote-willie", "approve") is None


def test_add_question_creates_table_and_surfaces_card(tmp_path):
    inst = _instance(tmp_path)
    qfile = inst / "state" / "pending-questions.md"
    cid = review_lib.add_question(qfile, "Route unknown sponsors to Sydney?",
                                  why="policy is ambiguous", ts="2026-06-11T09:00:00Z")
    assert cid.startswith("question:")
    # surfaces as an answerable To-review card
    card = next(c for c in review_lib.collect_cards(inst) if c.kind == "question")
    assert card.card_id == cid and card.tab == "review"
    assert card.title == "Route unknown sponsors to Sydney?"
    assert card.fields["context"] == "policy is ambiguous" and card.date == "2026-06-11"
    # idempotent on the question text
    review_lib.add_question(qfile, "Route unknown sponsors to Sydney?")
    assert len([c for c in review_lib.collect_cards(inst) if c.kind == "question"]) == 1


def test_add_question_appends_to_existing_table(tmp_path):
    inst = _instance(tmp_path)
    qfile = inst / "state" / "pending-questions.md"
    qfile.write_text(
        "# Pending questions\n\n| Question | Why it matters | Raised | Status |\n"
        "|---|---|---|---|\n| First? | a | 2026-06-10 | open |\n\n## Answers\n", encoding="utf-8")
    review_lib.add_question(qfile, "Second?", why="b", raised="2026-06-11")
    qs = [c.title for c in review_lib.collect_cards(inst) if c.kind == "question"]
    assert qs == ["First?", "Second?"]                       # inserted into the table, not after Answers
    assert qfile.read_text(encoding="utf-8").rstrip().endswith("## Answers")


def test_resolve_question_answer_logs_and_moves_to_done(tmp_path):
    inst = _instance(tmp_path)
    qfile = inst / "state" / "pending-questions.md"
    cid = review_lib.add_question(qfile, "Reply on weekends?", why="unclear")
    status = review_lib.resolve_question(qfile, cid, "answer",
                                         answer="never on weekends", ts="2026-06-11T15:00:00Z")
    assert status == "answered"
    card = next(c for c in review_lib.collect_cards(inst) if c.kind == "question")
    assert card.tab == "done" and card.decisions == []
    body = qfile.read_text(encoding="utf-8")
    assert "## Answers" in body and "Reply on weekends? → never on weekends" in body
    # idempotent: unknown card_id is a no-op
    assert review_lib.resolve_question(qfile, "question:nope", "answer") is None


def test_question_with_pipe_round_trips(tmp_path):
    inst = _instance(tmp_path)
    qfile = inst / "state" / "pending-questions.md"
    q = "Route to Sydney | Tony, or pick by region?"   # literal pipe in the question
    cid = review_lib.add_question(qfile, q, why="ambiguous owner")
    # idempotency holds despite the escaped pipe (no duplicate row)
    review_lib.add_question(qfile, q)
    qcards = [c for c in review_lib.collect_cards(inst) if c.kind == "question"]
    assert len(qcards) == 1
    assert qcards[0].title == q                          # displayed unescaped, pipe intact
    # the row still parses to exactly 4 cells (Status not shifted by the inner pipe)
    rows = [r for r in review_lib._markdown_rows(qfile.read_text(encoding="utf-8"))
            if r[0].lower() != "question"]
    assert len(rows[0]) == 4 and rows[0][3] == "open"
    # and it resolves by card_id, flipping the right cell
    assert review_lib.resolve_question(qfile, cid, "answer", answer="by region") == "answered"
    assert review_lib.collect_cards(inst)[0].tab == "done"
    assert q + " → by region" in qfile.read_text(encoding="utf-8")


def test_resolve_question_dismiss(tmp_path):
    inst = _instance(tmp_path)
    qfile = inst / "state" / "pending-questions.md"
    cid = review_lib.add_question(qfile, "Archive old threads?")
    assert review_lib.resolve_question(qfile, cid, "dismiss") == "dismissed"
    card = next(c for c in review_lib.collect_cards(inst) if c.kind == "question")
    assert card.tab == "done"
    assert "## Answers" not in qfile.read_text(encoding="utf-8")   # dismiss logs no answer


def test_parse_decisions_includes_notes_skips_malformed(tmp_path):
    p = tmp_path / "decisions.jsonl"
    p.write_text(
        json.dumps({"card_id": "outbound:a", "decision": "send"}) + "\n"
        + "{bad}\n"
        + json.dumps({"card_id": "topic:Sponsorships", "decision": "note",
                      "scope": "topic", "text": "route to Sydney"}) + "\n",
        encoding="utf-8")
    out = review_lib.parse_decisions(p)
    assert [d["decision"] for d in out] == ["send", "note"]


def test_add_note_appends_and_flips_to_feedback(tmp_path):
    inst = _instance(tmp_path)
    p = _proposal(inst, "miquido", {"to": "s@x.com", "body": "hi"}, topic="Sponsorships")
    review_lib.add_note(p, "route this to Sydney unless already picked up", ts="2026-06-11T14:40:00Z")
    meta, body = frontmatter.parse(p)
    assert meta["status"] == "feedback"
    assert "## Notes" in body
    assert "route this to Sydney" in body
    # collect now buckets it in the Feedback tab with the note visible
    card = review_lib.collect_cards(inst)[0]
    assert card.tab == "feedback"
    assert any("route this to Sydney" in n for n in card.fields["notes"])


def test_add_note_second_note_newest_first(tmp_path):
    inst = _instance(tmp_path)
    p = _proposal(inst, "m", {"to": "s@x.com", "body": "hi"})
    review_lib.add_note(p, "first note", ts="2026-06-11T10:00:00Z")
    review_lib.add_note(p, "second note", ts="2026-06-11T11:00:00Z")
    notes = review_lib.collect_cards(inst)[0].fields["notes"]
    assert notes[0].endswith("second note") and notes[1].endswith("first note")


def test_set_status_and_regen_digest(tmp_path):
    inst = _instance(tmp_path)
    p = _proposal(inst, "e1", {"to": "a@x.com", "body": "hi"})
    review_lib.set_status(p, "approved")
    assert frontmatter.parse(p)[0]["status"] == "approved"

    text = p.read_text(encoding="utf-8").replace('"body": "hi"', '"body": "revised"')
    text = text.replace(outbound.digest({"to": "a@x.com", "body": "hi"}), "STALE")
    p.write_text(text, encoding="utf-8")
    new = review_lib.regenerate_digest(p)
    assert new == outbound.digest({"to": "a@x.com", "body": "revised"})
    assert frontmatter.parse(p)[0]["args_digest"] == new
