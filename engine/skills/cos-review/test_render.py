import json

import outbound
import render as render_mod


def _instance(tmp_path):
    inst = tmp_path / "instance"
    (inst / "queue" / "outbound").mkdir(parents=True)
    (inst / "queue" / "review" / "memory").mkdir(parents=True)
    (inst / "state").mkdir(parents=True)
    return inst


def _proposal(inst, slug, args, *, status="pending", topic="General"):
    dig = outbound.digest(args)
    (inst / "queue" / "outbound" / f"{slug}.md").write_text(
        f"---\ntype: proposal\nstatus: {status}\nreversibility: reversible\n"
        f"tool: mcp__claude_ai_Gmail__create_draft\nargs_digest: {dig}\n"
        f"date: 2026-06-03\ntopic: {topic}\n---\n\n# Proposal: {slug}\n\n"
        f"Context line.\n\n## Why this is in the sweep\n- reason one\n\n"
        f"```json\n{json.dumps(args, indent=2)}\n```\n", encoding="utf-8")


def test_self_contained_and_has_tabs(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "p1", {"to": "a@x.com", "body": "hello"}, topic="Sponsorships")
    _proposal(inst, "p2", {"to": "b@x.com", "body": "hi"}, status="approved")
    html = render_mod.render(inst, "2026-06-11")
    assert "http://" not in html and "https://" not in html   # fully self-contained
    for label in ("To review", "Feedback", "Queued", "Working", "Done", "Prompts & sources"):
        assert label in html
    assert "Talking to" in html and "Broader" in html         # feedback bar present
    assert "Sponsorships" in html                              # topic surfaces in island


def test_card_content_cannot_break_out_of_script(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "evil", {"to": "a@x.com", "body": "</script><b>pwned</b>"})
    html = render_mod.render(inst, "2026-06-11")
    assert html.count("</script>") == 1   # only the page's own closing tag
    assert "<\\/script>" in html           # payload escaped inside the JSON island


def test_empty_queue_renders_valid_page(tmp_path):
    inst = _instance(tmp_path)
    html = render_mod.render(inst, "2026-06-11")
    assert "<!doctype html>" in html
    assert "__CARDS__ = []" in html


def test_live_mode_injects_post_endpoint(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "p1", {"to": "a@x.com", "body": "hi"})
    html = render_mod.render(inst, "2026-06-11", server_post="/decision", server_done="/done")
    assert "__REVIEW_POST__" in html and "/decision" in html
    assert "banner live" in html


def test_feedback_card_renders_notes(tmp_path):
    inst = _instance(tmp_path)
    _proposal(inst, "m", {"to": "a@x.com", "body": "hi"})
    import review_lib
    review_lib.add_note(inst / "queue" / "outbound" / "m.md",
                        "route to Sydney", ts="2026-06-11T14:40:00Z")
    html = render_mod.render(inst, "2026-06-11")
    assert "Your feedback" in html
    assert "route to Sydney" in html
    assert '"tab": "feedback"' in html or '"tab":"feedback"' in html


def test_write_emits_file(tmp_path):
    inst = _instance(tmp_path)
    out = render_mod.write(inst, "2026-06-11")
    assert out.name == "dashboard-2026-06-11.html"
    assert out.read_text(encoding="utf-8").startswith("<!doctype html>")


def test_open_in_browser_uses_file_uri(tmp_path, monkeypatch):
    import webbrowser
    f = tmp_path / "d.html"; f.write_text("<html></html>", encoding="utf-8")
    calls = []
    monkeypatch.setattr(webbrowser, "open", lambda u: calls.append(u) or True)
    assert render_mod.open_in_browser(f) is True
    assert calls and calls[0].startswith("file://") and calls[0].endswith("d.html")


def test_open_in_browser_swallows_errors(tmp_path, monkeypatch):
    import webbrowser
    def boom(u): raise RuntimeError("no display")
    monkeypatch.setattr(webbrowser, "open", boom)
    assert render_mod.open_in_browser(tmp_path / "x.html") is False   # best-effort, never raises
