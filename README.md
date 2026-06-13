# AI Chief of Staff

Your personal Chief of Staff, running on top of Claude. It prepares you for what's ahead, closes the loops you'd otherwise drop, coaches you on your real work, and **gets sharper the longer it runs**. It sets itself up by interviewing you — no configuration files to hand-edit.

One principle shapes everything: **it proposes, you approve.** Nothing is sent, posted, or scheduled on your behalf without your sign-off. Every draft reply, every follow-up, every calendar change lands in a review queue first.

---

## What it is

Think of it as a staff member who reads your inbox, calendar, meeting notes, and documents, then quietly does the prep work:

- **Briefs you before meetings** — who's attending, the open threads with them, a suggested agenda.
- **Triages your inbox** — turns the last day's email into ready-to-edit draft replies, open questions, and a short FYI digest.
- **Catches calendar problems early** — double-bookings, back-to-back marathons, days with no breaks, meetings missing a key person.
- **Closes loops** — surfaces what's stalled, unassigned, or ownerless, and proposes the next step.
- **Captures outcomes** — after your day's meetings, it records what was decided and drafts the follow-ups.
- **Coaches you** — one or two specific, strengths-based moves each week, grounded in how you actually showed up.
- **Remembers** — it builds a private, plain-text picture of your people, accounts, projects, priorities, and voice, and keeps it current.

It works for **one person** — you. Your private memory is yours alone; it never lives in any shared package.

---

## How it works

**Plain text is the brain.** Everything it knows about you is stored as plain Markdown files in a private folder on your machine — no database, no cloud lock-in. You can read it, edit it, and back it up like any other folder. Because every change is a plain-text diff, you can always see exactly what changed and roll it back.

**It observes instead of interrogating.** Rather than making you fill out forms, it learns how you work from your email, calendar, and meeting transcripts, and only asks when something genuinely matters and it can't tell.

**It proposes, you decide.** Anything that touches the outside world — an email, a Slack message, a calendar invite — is written up as a proposal you review before it goes anywhere. Approving or editing a draft also teaches it your preferences for next time. How much it does on its own is a dial you control; out of the box, it proposes everything and sends nothing.

**It maintains itself.** Memory and habits both go stale, so housekeeping is built in: once a week it consolidates what it learned, promotes the durable facts, and prunes the noise — always as a reviewable change, never a silent overwrite.

**Your decisions live in one place.** A review dashboard paints every pending draft, open question, and proposed memory change as a card you triage by clicking. Approve, edit, or reject — your decisions feed straight back in.

---

## Install

Pick the path that matches how you use Claude. Each is self-contained — full step-by-step instructions are in **[INSTALL.md](INSTALL.md)**.

| You're using… | Quick start |
|---|---|
| **Claude desktop app** (no terminal) | **Customize → Plugins → Browse plugins** → install **chief-of-staff** → open the folder for your brain → run `/cos-onboarding`. |
| **Claude Code** (command line) | `/plugin marketplace add fontesgerards/chief-of-staff` then `/plugin install chief-of-staff@chief-of-staff`, then run `/cos-onboarding`. |
| **A direct clone** (for tinkering) | `git clone https://github.com/fontesgerards/chief-of-staff`, run `./setup.sh`, open the folder, run `/cos-onboarding`. |

**`/cos-onboarding` is always the first thing you run.** It has one conversation with you: confirms where your private brain folder lives, checks what your setup supports, observes a sample of your email and calendar to draft a profile, captures your writing voice, and hands you a short getting-started guide. Re-run it any time to start fresh.

**Connecting your tools.** During onboarding you'll connect the sources it reads — Gmail, Calendar, Drive, and meeting-note tools like Granola, Zoom, Fathom, or Fireflies. Connect them **read-only** wherever you're offered the choice. INSTALL.md covers exactly where each connector lives.

---

## Skills

Each capability is a **skill** you can invoke as a slash command (e.g. `/cos-meeting-prep`). Most also run automatically on a schedule you set during onboarding — and **every scheduled run still only proposes**, never sends.

### Daily

| Skill | What it does | When |
|---|---|---|
| **`/cos-meeting-prep`** | Your morning brief — priorities, calendar, deadlines, and the review queue — plus per-meeting prep with attendee context, open threads, and a suggested agenda. | Each morning; invoke anytime before a call. |
| **`/cos-calendar-audit`** | Scans the next few days for double-bookings, long back-to-back runs, days with no break, and meetings missing a critical participant. Each finding becomes an answerable card. | Early morning. |
| **`/cos-inbox-sweep`** | Turns the last 24 hours of email into draft replies awaiting your approval, a list of open questions, and a short FYI brief. Drafts are written in your voice; nothing is ever sent. | Early evening. |
| **`/cos-meeting-follow-up`** | After the day's meetings, captures outcomes into memory, extracts commitments, and drafts any follow-up messages as proposals. | End of day; invoke anytime after a call. |
| **`/cos-entity-enrichment`** | Keeps your world model current — refreshes people, accounts, projects, and competitors from the day's activity. | Evening. |

### Weekly

| Skill | What it does | When |
|---|---|---|
| **`/cos-loop-closing`** | Surfaces what's unassigned, stalled, or ownerless across your open loops and commitments — including key relationships going quiet — and proposes next steps. | Monday. |
| **`/cos-research`** | A competitor, technology, and market digest on the topics, people, and companies you're watching — sourced, and leading with the so-what. | Monday. |
| **`/cos-coaching`** | Strengths-based coaching grounded in your real meetings: one or two specific, role-relevant moves and an experiment for the week ahead. | Friday. |
| **`/cos-system-maintenance`** | Reviews what worked and what didn't this week and proposes improvements to the system itself — always as proposals, never silent edits. | Friday. |
| **`/cos-consolidate-memory`** | The weekly tidy-up: promotes durable learnings, retires stale facts, prunes noise, and hands you the change as one reviewable diff. The only skill that edits memory. | Sunday. |

### Monthly

| Skill | What it does | When |
|---|---|---|
| **`/cos-goal-setting`** | Reviews progress against your goals, then proposes an updated set of current priorities for your approval. | 1st of the month. |

### On-demand

| Skill | What it does |
|---|---|
| **`/cos-review`** | Opens the decision dashboard — every pending draft, open question, and proposed memory change as a card you triage by clicking. Invoke whenever you have things to approve. |
| **`/cos-onboarding`** | Sets the whole system up (or re-seeds it). Run this first. |

Behind the scenes, a read-only pass gathers the day's email, documents, transcripts, and calendar into staging notes that the daily skills draw on — so the skills above stay fast and consistent. It never writes to memory or sends anything.

---

## At a glance

- **Local-first** — your memory is plain Markdown in a folder you own.
- **Propose-never-act** — drafts wait for your approval; you stay in control.
- **Observes, doesn't interrogate** — it learns from your real work.
- **Self-maintaining** — weekly consolidation keeps it sharp, every change reviewable.
- **Gets better the longer it runs** — your corrections become its instincts.

Run `/cos-onboarding` to begin.
