# Threadline — User Flow

**Version:** 1.0  
**Status:** Approved for build  
**Last updated:** July 1, 2026  

---

## Overview

This document describes the full experience a user has from the moment they open Threadline to the moment they leave with a product idea they are confident in.

The flow has four stages:

```
1. Landing       → user understands what Threadline does
2. Selection     → user picks one or more conditions
3. Discovery     → user sees ranked product opportunities
4. Brief         → user clicks into a full product brief
```

---

## Stage 1 — Landing

**What the user sees:**

A clean page with two elements:

1. A short explanation of what Threadline does — one or two sentences maximum. No marketing fluff. Something honest and direct, for example:
   > *"Threadline surfaces what adaptive fashion consumers are asking for — so you know what to build before you run a focus group."*

2. The condition selector immediately below — visible without scrolling

**What the user does:**

Reads the explanation, then moves directly to selecting a condition. There is no login, no sign-up, no barrier.

**Design principle:** The landing page should be simple enough that the user can move to results without friction.

---

## Stage 2 — Condition Selection

**What the user sees:**

Four condition options displayed as selectable cards or buttons:

- Post-mastectomy / breast cancer recovery
- Ostomy
- Rheumatoid arthritis / mobility limitations
- Post-surgical recovery (general)

**What the user does:**

Selects one or more conditions. Multiple selections are allowed. There is no limit.

**Behaviour:**

- Selected conditions are visually highlighted
- A "Show opportunities" button appears once at least one condition is selected
- If multiple conditions are selected, results will include opportunities across all selected conditions, with cross-condition overlap flagged where it exists

**Open question (decide during build):** Whether results load immediately on selection or after the user clicks "Show opportunities." To be decided based on how fast the backend responds in practice.

---

## Stage 3 — Discovery (Ranked Opportunities)

**What the user sees:**

A ranked list of product opportunities based on the selected condition(s). Each item in the list is an opportunity card showing:

- **Product idea title** — a specific, actionable product name (e.g. "Front-closure adaptive bra")
- **Signal strength score** — a number from 0–100 indicating how strongly real consumer signals support this opportunity
- **Top pain point summary** — one line describing the primary consumer frustration this product addresses
- **Conditions** — which condition(s) this opportunity applies to

Cards are ranked by signal strength, highest first.

**Cross-condition overlap:**

If an opportunity appears across multiple conditions, it is flagged visually (e.g. a badge or tag). This tells the user that the need is broader than one condition — a larger market opportunity.

**What the user does:**

Browses the ranked list. Clicks any card to open the full product brief for that opportunity.

**Edge cases:**

- If there is not enough data to generate reliable opportunities for a selected condition, Threadline displays an honest message rather than showing low-quality results
- If no cross-condition overlap exists, nothing is flagged — overlap is surfaced only when it genuinely exists in the data

---

## Stage 4 — Product Brief

**What the user sees:**

A full product brief for the selected opportunity, containing:

**Header**
- Product idea title
- Signal strength score + confidence level (e.g. High / Medium / Low)
- Conditions this applies to

**Confirmed pain points**
- A list of the specific consumer frustrations this product addresses

**Recommended product features**
- Specific product features consumers mention consistently in the data — categories will be determined by what the data actually surfaces

**Priority features**
- What to build first, ranked by signal frequency

**Gaps**
- What the data does not yet tell us — honest about the limits of current signal volume

**Source evidence**
- A sample of the actual Reddit posts and Amazon reviews that drove this brief
- Each source shows: platform (Reddit or Amazon), a short excerpt, and a link to the original

**What the user does:**

Reads the brief. Uses it to make a product decision. Can navigate back to the ranked list to explore other opportunities.

---

## Full Flow Diagram

```
User opens Threadline
        ↓
Landing — brief explanation + condition selector
        ↓
User selects one or more conditions
        ↓
[TBD: results load immediately OR user clicks "Show opportunities"]
        ↓
Ranked opportunity cards load
  [title + score + pain point + conditions]
        ↓
        ├── Cross-condition overlap flagged if it exists
        │
        └── User clicks a card
                ↓
        Full product brief loads
          [pain points + features + priority + gaps + evidence]
                ↓
        User navigates back to list
        or leaves with their product idea
```

---

## What Threadline Does Not Ask the User to Do

- It does not ask the user to type in a product idea
- It does not ask the user to create an account (at launch)
- It does not ask the user to fill in a form
- It does not make the user wait for a long loading state without feedback

---

## Open Questions (decide during build)

| # | Question | Decision needed by |
|---|---|---|
| 1 | Do results load immediately on condition selection, or after clicking "Show opportunities"? | Frontend build — depends on backend response time |
| 2 | How many opportunity cards are shown by default? All of them, or a top N with a "show more"? | Frontend build |
| 3 | Can the user change their condition selection without going back to the landing page? | Frontend build |
| 4 | Does the brief open as a new page or as an expanded panel on the same page? | Frontend build |
