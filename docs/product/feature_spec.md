# Threadline — Feature Specification

**Version:** 1.0  
**Status:** Approved for build  
**Last updated:** July 1, 2026  

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
The first thing a user sees when they open Threadline. Contains a brief explanation of what Threadline does and the condition selector immediately below it. No login, no sign-up, no barrier between the user and the product.

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
- If a condition has no data in the database, it is still shown as a selectable option but returns an honest empty state rather than hiding itself

---

### Feature 3 — Ranked Opportunity Cards

**Description:**
After condition selection, Threadline displays a ranked list of product opportunities. Each opportunity is shown as a card. Cards are ranked by signal strength, highest first. The user clicks any card to open the full product brief.

**Each card displays:**
- Product idea title
- Signal strength score (0–100)
- Top pain point summary (one line)
- Which condition(s) this opportunity applies to

**Acceptance criteria:**
- [ ] Opportunities are displayed as a ranked list, highest signal strength first
- [ ] Each card shows: title, score, pain point summary, and conditions
- [ ] Cards are clickable and open the full product brief for that opportunity
- [ ] If multiple conditions are selected, opportunities from all selected conditions appear in one ranked list
- [ ] Results reflect the most recent data in the database

**Edge cases:**
- If there is not enough data to generate reliable opportunities for a selected condition, an honest message is shown (e.g. "Not enough data yet for this condition — check back after the next data refresh") rather than showing low-quality results
- If the backend takes longer than expected to respond, a loading indicator is shown
- If the backend fails, an error message is shown with an option to try again

---

### Feature 4 — Cross-Condition Overlap Flagging

**Description:**
When a product opportunity appears across multiple conditions, it is flagged visually on the opportunity card. This tells the user that the need is broader than one condition. Overlap is surfaced only when it genuinely exists in the data — it is never fabricated or forced.

**Acceptance criteria:**
- [ ] Opportunities that appear across multiple conditions are flagged with a visible indicator (e.g. a badge or tag)
- [ ] The flag shows which conditions share the overlap
- [ ] If no overlap exists for a given set of selected conditions, nothing is flagged — no placeholder or empty overlap section is shown
- [ ] Overlap is determined by the backend based on actual data, not assumed

**Edge cases:**
- If a user selects only one condition, no overlap can exist — the overlap flag is not shown at all
- If overlap exists between two conditions but the user has only selected one of them, the overlap is not flagged — only overlap within the user's selected conditions is surfaced

---

### Feature 5 — Full Product Brief

**Description:**
When a user clicks an opportunity card, a full product brief loads for that opportunity. The brief is as specific as the data allows — it does not pad with generic advice when the data is thin.

**The brief contains:**

**Header**
- Product idea title
- Signal strength score
- Confidence level (High / Medium / Low — derived from signal volume and consistency)
- Conditions this opportunity applies to

**Confirmed pain points**
- A list of the specific consumer frustrations this product addresses
- Derived entirely from real consumer posts and reviews

**Recommended product features**
- Specific product features consumers mention consistently in the data
- Categories are determined by what the data actually surfaces — not predefined

**Priority features**
- What to build first, ranked by how frequently it appears in consumer signals

**Gaps**
- What the data does not yet tell us
- Honest about the limits of current signal volume

**Source evidence**
- A sample of the actual Reddit posts and Amazon reviews that drove this brief
- Each source shows: platform (Reddit or Amazon), a short excerpt, and a link to the original source

**Acceptance criteria:**
- [ ] Brief loads for any opportunity card the user clicks
- [ ] All six sections are present: header, pain points, features, priority, gaps, evidence
- [ ] Source evidence links open the original Reddit post or Amazon review in a new tab
- [ ] Brief does not show empty sections — if a section has no data, it is either omitted or shows an honest message
- [ ] Brief reflects the most recent data in the database
- [ ] Confidence level is derived from actual signal volume — not hardcoded

**Edge cases:**
- If a source URL is no longer available (deleted Reddit post, removed Amazon review), the excerpt is still shown but the link is omitted
- If signal volume is very low, the confidence level reflects this honestly (Low) rather than inflating it
- If the brief is longer than the screen, it scrolls cleanly without breaking layout

---

### Feature 6 — Navigation Between Brief and Ranked List

**Description:**
The user can navigate back from a full product brief to the ranked opportunity list without losing their condition selection or their place in the list.

**Acceptance criteria:**
- [ ] A clear back navigation option is present on the brief page
- [ ] Navigating back returns the user to the ranked list with their condition selection intact
- [ ] The ranked list does not reload from scratch when the user navigates back — their position in the list is preserved where technically feasible
- [ ] A card that the user has already clicked and read is visually distinct from unvisited cards so the user knows which ones they have already seen

**Edge cases:**
- If the user uses the browser back button instead of the in-app navigation, behaviour should be consistent — condition selection should still be intact
- On mobile, back navigation is accessible without zooming or horizontal scrolling

---

## Future Features

The following features are planned for after launch. They are not in scope for the initial build. They are documented here so architectural decisions made during the initial build do not block them later.

---

### Future Feature 1 — User Accounts and Saved Briefs

Users can create an account, save product briefs, and return to them in a later session.

**Why deferred:** Adds significant build complexity (auth, session management, saved state). Not needed for the core value proposition at launch.

**Architectural note:** The database schema includes a `validations` table designed to support this when auth is added.

---

### Future Feature 2 — Export Brief as PDF or Report

Users can export any product brief as a PDF to share with their team or include in a presentation.

**Why deferred:** Requires PDF generation on the backend. Not critical for initial demo or pilot use.

---

### Future Feature 3 — Email Delivery of Briefs

Users can enter an email address and receive a product brief by email without needing to stay on the page.

**Why deferred:** Requires email infrastructure. Not needed at launch.

---

### Future Feature 4 — Additional Conditions

Threadline expands beyond the four launch conditions to cover more adaptive fashion needs.

**Why deferred:** Data pipeline needs to be proven reliable for the four launch conditions before expanding scope.

---

### Future Feature 5 — Additional Data Sources

Threadline adds more data sources beyond Reddit and Amazon — for example, Facebook groups, condition-specific forums, or clinical community platforms.

**Why deferred:** Additional sources require additional scraper development and quality validation. Reddit and Amazon are sufficient for launch.

---

## Open Questions

| # | Question | Decision needed by |
|---|---|---|
| 1 | Does the brief open as a new page or as an expanded panel on the same page? | Frontend build |
| 2 | How many opportunity cards are shown by default — all of them or a top N with "show more"? | Frontend build |
| 3 | Do results load immediately on condition selection or after clicking a button? | Frontend build — depends on backend response time |
| 4 | What is the minimum signal volume required before a confidence level is shown as High vs Medium vs Low? | Backend build |
