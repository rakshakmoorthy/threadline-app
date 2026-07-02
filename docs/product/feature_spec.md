# Threadline — Feature Specification

**Version:** 2.0  
**Last updated:** July 2, 2026  

---

## Overview

This document defines every feature in Threadline — what it does, how we know it is built correctly, and what edge cases it must handle.

Features are split into two sections:
- **Launch features** — must be built before Threadline is usable
- **Future features** — planned for after launch, not in scope for initial build

---

## Launch Features

---

### Feature 1 — Landing Page

**Description:**
The first thing a user sees when they open Threadline. Contains a brief explanation of what Threadline does and the condition selector immediately below. No login, no sign-up, no barrier.

**Acceptance criteria:**
- [ ] Page loads with a short explanation of Threadline (2 sentences maximum)
- [ ] Condition selector is visible without scrolling on desktop and mobile
- [ ] No login or sign-up is required to use the product

**Edge cases:**
- If the backend is down, the landing page still loads — it shows an error message rather than a blank page
- On mobile, the explanation and condition selector stack cleanly without horizontal scrolling

---

### Feature 2 — Multi-Condition Selection

**Description:**
The user can select one or more of the four conditions. Selected conditions are visually highlighted. At least one condition must be selected before results can be shown.

**The four conditions at launch:**
- Post-mastectomy / breast cancer recovery
- Ostomy
- Rheumatoid arthritis / mobility limitations
- Post-surgical recovery (general)

**Acceptance criteria:**
- [ ] All four conditions are displayed as selectable options
- [ ] User can select one or more conditions simultaneously
- [ ] Selected conditions are visually distinct from unselected ones
- [ ] User can deselect a condition by clicking it again
- [ ] Results cannot be triggered unless at least one condition is selected
- [ ] Condition selection persists if the user navigates back from the brief to the ranked list

**Edge cases:**
- If the user deselects all conditions after results have loaded, results are cleared and the selector returns to its default state
- If a condition has no pre-generated opportunities, it is still shown as a selectable option but returns an honest empty state

---

### Feature 3 — Ranked Opportunity Cards (Instant Load)

**Description:**
After condition selection, Threadline displays a ranked list of pre-generated product opportunities. Results load instantly from the database — no LLM call is made at this point. Cards are ranked by signal strength, highest first.

**Each card displays:**
- Product idea title
- Signal strength score (0–100)
- Top pain point summary (one line)
- Which condition(s) this opportunity applies to

**Acceptance criteria:**
- [ ] Opportunities load instantly from the database — no on-demand generation
- [ ] Cards are ranked by signal strength, highest first
- [ ] Each card shows: title, score, pain point summary, and conditions
- [ ] Cards are clickable and open the full product brief
- [ ] If multiple conditions are selected, opportunities from all selected conditions appear in one ranked list
- [ ] Results reflect the most recently generated opportunities (updated weekly)

**Edge cases:**
- If no opportunities exist for a selected condition, an honest message is shown (e.g. "Opportunities for this condition are being generated — check back after the next weekly update")
- If the backend fails, an error message is shown with an option to try again
- A loading indicator is shown while the database query runs

---

### Feature 4 — Cross-Condition Overlap Flagging

**Description:**
When a product opportunity applies across multiple conditions, it is flagged visually on the opportunity card. Overlap is surfaced only when it genuinely exists in the pre-generated data — it is never fabricated or forced.

**Acceptance criteria:**
- [ ] Opportunities that apply across multiple conditions are flagged with a visible indicator
- [ ] The flag shows which conditions share the overlap
- [ ] If no overlap exists, nothing is flagged — no placeholder or empty section is shown
- [ ] Overlap is determined during the weekly synthesis job, not inferred by the frontend

**Edge cases:**
- If a user selects only one condition, no overlap can exist — the overlap flag is not shown
- If overlap exists between two conditions but the user has only selected one of them, the overlap is not flagged

---

### Feature 5 — Full Product Brief (Instant Load)

**Description:**
When a user clicks an opportunity card, the full pre-generated product brief loads instantly from the database. No LLM call is made at this point.

**The brief contains:**

**Header**
- Product idea title
- Signal strength score + confidence level (High / Medium / Low)
- Conditions this opportunity applies to

**Confirmed pain points**
- Specific consumer frustrations this product addresses
- Derived from real Reddit posts and Amazon reviews

**Recommended product features**
- Specific features consumers mention consistently
- Categories determined by what the data actually surfaces — not predefined

**Priority features**
- What to build first, ranked by signal frequency

**Gaps**
- What the data does not yet tell us — honest about limits

**Source evidence**
- Sample Reddit posts and Amazon reviews that drove this brief
- Each source: platform, short excerpt, link to original

**Acceptance criteria:**
- [ ] Brief loads instantly from the database — no on-demand generation
- [ ] All six sections present: header, pain points, features, priority, gaps, evidence
- [ ] Source evidence links open the original Reddit post or Amazon review in a new tab
- [ ] Brief does not show empty sections — if a section has no data, it is omitted or shows an honest message
- [ ] Brief reflects the most recently generated data (updated weekly)
- [ ] Confidence level reflects actual signal volume — not hardcoded

**Edge cases:**
- If a source URL is no longer available, the excerpt is shown but the link is omitted
- If signal volume is low, confidence level shows as Low rather than inflating it
- If the brief is longer than the screen, it scrolls cleanly

---

### Feature 6 — Navigation Between Brief and Ranked List

**Description:**
The user can navigate back from a full product brief to the ranked opportunity list without losing their condition selection or their place in the list.

**Acceptance criteria:**
- [ ] A clear back navigation option is present on the brief page
- [ ] Navigating back returns the user to the ranked list with condition selection intact
- [ ] The ranked list does not reload from scratch when the user navigates back
- [ ] A card the user has already read is visually distinct from unvisited cards

**Edge cases:**
- If the user uses the browser back button, condition selection should still be intact
- On mobile, back navigation is accessible without zooming or horizontal scrolling

---

## Future Features

The following features are planned for after launch. They are documented here so architectural decisions during the initial build do not block them later.

---

### Future Feature 1 — Talk with Reports (Chatbot + Visualisations)

Users can ask questions about the pre-generated reports and see visualisations of the data.

**Examples:**
- *"What's the most urgent product to build for ostomy patients?"*
- *"Do post-mastectomy and post-surgical patients share the same closure needs?"*

Claude Sonnet answers using the vector store as context. Threadline also proactively surfaces actionable insights without the user asking.

**Why deferred:** Build the core product first. A chatbot on top of bad data is useless — a chatbot on top of well-structured, well-extracted, well-indexed data is powerful.

---

### Future Feature 2 — User Accounts and Saved Briefs

Users can create an account, save product briefs, and return to them in a later session.

**Why deferred:** Adds significant build complexity. Not needed for the core value at launch.

**Architectural note:** The database schema includes a `validations` table designed to support this when auth is added.

---

### Future Feature 3 — Export Brief as PDF

Users can export any product brief as a PDF to share with their team.

**Why deferred:** Requires PDF generation on the backend. Not critical for initial demo or pilot.

---

### Future Feature 4 — Additional Conditions

Threadline expands beyond the four launch conditions.

**Why deferred:** Prove the pipeline works for four conditions before expanding scope.

---

### Future Feature 5 — Additional Data Sources

Threadline adds more sources beyond Reddit and Amazon — Facebook groups, condition-specific forums, clinical community platforms.

**Why deferred:** Reddit and Amazon are sufficient for launch. Additional sources require additional scraper development and quality validation.

---

## Open Questions

| # | Question | Decision needed by |
|---|---|---|
| 1 | How many opportunity cards shown by default — all or top N with show more? | Frontend build |
| 2 | Does the brief open as a new page or expanded panel? | Frontend build |
| 3 | Can the user change condition selection without going back to landing? | Frontend build |
| 4 | What signal volume thresholds define High / Medium / Low confidence? | Backend build |
