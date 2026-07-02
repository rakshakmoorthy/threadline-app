# How Threadline Was Built

*A founder's account of what we set out to build, what changed along the way, and why.*

---

## Where It Started

The first version of Threadline was not a web app. It was not even a product. It was a report.

The idea was straightforward: a brand PM types in a product idea — say, a magnetic closure bra for post-mastectomy patients — and Threadline would go look at what real consumers were saying online, score the idea, and hand back a PDF. A document. Something you could print and bring to a meeting.

That idea lasted about a week before we killed it.

A PDF is a dead thing. You generate it once, it captures a moment in time, and then it sits in a folder getting stale while consumer conversations keep moving. The whole point of Threadline is that it knows what consumers are saying right now — not what they were saying when someone last ran a report. A PDF defeats the purpose entirely.

So we scrapped it and decided to build something live.

---

## Rethinking Who the User Is

Once we committed to a web app, we had to rethink the experience from scratch. And the more we thought about it, the more we realized the original concept had a deeper problem than just the output format.

The original idea assumed the PM already had a product idea. They come in, they type something, Threadline validates it. But what about the PM who doesn't know what to build yet? What about the founder entering adaptive fashion for the first time, who knows the market is underserved but has no idea where to start?

That's actually the person who needs Threadline most. And the original design left them with nothing — a blank text box and no idea what to type.

So we made the bigger pivot: we removed the input entirely.

Instead of asking the user for an idea, Threadline surfaces the ideas itself. You pick a condition. Threadline shows you what consumers are actually asking for — ranked, scored, with evidence — and you leave knowing what to build because real consumers told us, not because you guessed.

This changed the entire product. The homepage is not a search bar. It is a ranked list of product opportunities waiting for you when you arrive.

---

## The Intelligence Layers We Added

Once the core flow was locked in, the product kept getting smarter.

The first thing we added was **cross-condition overlap**. We noticed early on that some consumer needs kept appearing across multiple conditions. The need for a front-closure garment is not just a post-mastectomy problem — it shows up in post-surgical recovery, in rheumatoid arthritis communities, in ostomy care. A brand building that product is not serving a niche of forty thousand people. They are serving a market of millions across overlapping conditions. Threadline now detects this automatically and flags it. When you see a lightning bolt next to an opportunity, that is Threadline telling you: this need is bigger than one condition.

The second thing we added was honest **confidence levels**. A score of 87 with high confidence means hundreds of consumers are consistently asking for this. A score of 87 with low confidence means a strong pattern in a small sample. Both are useful, but they mean different things. We did not want to hide that distinction behind a single number.

The third thing — still coming in Phase 2 — is **Talk with Reports**. The idea is that after a PM reads a brief, they can ask questions. Not generic questions — questions grounded in the actual data. "What do ostomy and post-mastectomy patients have in common?" "Which closure type comes up most often?" "What are the gaps nobody is building for?" Claude Sonnet answers using the vector store as context. This turns Threadline from a read-only tool into something you can actually have a conversation with.

---

## Getting the Data

This was the hardest part. And it did not go the way we planned.

**What we wanted:** Live posts from Reddit communities where adaptive fashion consumers speak honestly, and real Amazon reviews from adaptive clothing products.

**What actually happened with Reddit:** To access the Reddit API officially, you need to register a developer app at reddit.com/prefs/apps. Every time we tried, the registration page failed. The CAPTCHA would not process. The form would not submit. We spent a significant amount of time on this before accepting it was a bug on Reddit's end and moving on.

**What actually happened with Amazon:** We built a scraper to pull reviews directly from Amazon product pages. Amazon blocked every single request. Zero reviews returned. Amazon's anti-scraping infrastructure is aggressive and effective.

So we had to get creative.

For Amazon, we found the McAuley Lab Amazon Reviews 2023 dataset — a publicly available academic research dataset containing millions of real Amazon reviews. We streamed through 500,000 records from the Clothing and Health categories and filtered for adaptive fashion keywords. The result: 2,192 real Amazon reviews loaded into our database in a matter of hours. No cost, no blocking, no scraping.

For Reddit, we discovered that every public subreddit exposes a public RSS feed that requires no API key and no app registration. We built a scraper around this and pulled posts from ten adaptive fashion communities — r/breastcancer, r/ostomy, r/arthritis, r/ChronicPain, r/mastectomy, and others. We sorted by hot posts only — the most upvoted, most validated conversations — which gave us 129 Reddit posts.

Is this the permanent solution? No. The permanent solution is Bright Data for Amazon (a professional scraping API that handles Amazon's defenses) and the official Reddit API once the registration bug is resolved. But what we have right now is real data from real consumers, and it is good enough to build on and demo with.

The more interesting lesson from this process: the Hugging Face dataset turned out to be cleaner than what a direct scraper would have returned anyway. Amazon's dataset contains verified purchases and helpful-voted reviews — the community has already done quality filtering for us. The RSS approach for Reddit targets community-validated posts by design. We ended up with better signal quality than we would have gotten from raw scraping.

---

## How We Built the Backend

The backend is a FastAPI application in Python. It sits between the frontend and everything else — Supabase, Claude, OpenAI. Nothing touches those services directly from the browser.

This was a deliberate security decision from the start. API keys in a React frontend are not secrets — anyone who opens browser developer tools can read them. FastAPI keeps every key server-side. The frontend makes requests to our backend. Our backend makes requests to Claude, Supabase, and OpenAI. The keys never leave the server.

The backend has four endpoints. They all read from the database — no LLM calls happen when a user is on the app. Everything is pre-generated.

We deployed it on Render. The free tier works for development. Before any serious demo, we will upgrade to the paid tier to eliminate the cold start delay that happens when the service has been idle.

---

## How We Built the Frontend

The frontend is React, built with Vite. The design direction was deliberately professional — dark background, data-dense, built for someone who makes product decisions for a living rather than someone browsing consumer content.

The experience has three views and nothing else:

**The landing view** is a brief explanation of what Threadline does and four condition buttons. Each button shows the number of consumer signals behind it. You pick one or more conditions and click Show Opportunities.

**The ranked list** shows pre-generated opportunity cards sorted by signal strength. Each card shows the product idea, the score, the one-line pain point summary, which conditions it applies to, the confidence level, and the overlap flag if relevant. You click a card to go deeper.

**The product brief** shows everything: confirmed pain points from real consumer posts, recommended features, what to build first, gaps in the data, and actual excerpts from Reddit and Amazon that drove the brief. Cards you have already read are dimmed so you know where you have been.

That is the whole app. No unnecessary screens, no navigation, no friction.

---

## The Pipeline That Runs Everything

The intelligence behind Threadline runs on five steps, executed weekly:

**Scrape.** Pull hot posts from Reddit communities and reviews from Amazon. Hot posts specifically — not new, not top. Hot means the community has already validated them with upvotes. That is signal quality filtering built into the sort order.

**Clean.** Before any LLM touches the data, strip out the noise. HTML tags, markdown formatting, salutations, anything under fifteen words. This step was added after we saw how much irrelevant content was making it into extraction. Clean input produces dramatically better output.

**Extract (Claude Haiku).** Haiku reads each cleaned record and pulls out structured pain points and product features. Haiku was chosen here because it runs on thousands of records per week and is optimised for exactly this kind of structured extraction task. It is fast and cheap at scale.

**Embed (OpenAI text-embedding-3-small).** Each record is converted into a vector — a numerical representation of its meaning. This is what makes semantic search work. Two records that talk about the same problem in completely different words will have similar vectors. The whole database costs less than five cents to embed.

**Synthesise (Claude Opus 4.8).** Once a week, Opus reads the top signals per condition and turns them into ranked product opportunities with full briefs. Opus was chosen here because synthesis is genuinely hard — it requires reasoning across hundreds of consumer posts, identifying patterns, ranking opportunities, and writing briefs specific enough to act on. Opus does this well. It runs once a week, not on every user request, so cost is not a concern.

After synthesis, every user query is a database read. Instant. No waiting.

---

## What Is Still Ahead

The core product works. The pipeline runs. The data is real. The opportunities are grounded in consumer signals.

What comes next:

Getting the Reddit API working properly will multiply the data volume significantly. Switching to Bright Data for Amazon will give us live reviews updated weekly rather than a 2023 snapshot. Setting up GitHub Actions will automate the entire pipeline so it runs without anyone touching it.

And then Phase 2: Talk with Reports. The ability to ask Threadline a question and get an answer rooted in real consumer data. That is where this goes from a market intelligence tool to something closer to a research partner.

---

*Threadline was built by Raksha Krishna Moorthy, MS Information Systems, Northeastern University.*
*GitHub: github.com/rakshakmoorthy/threadline-app*

---

*Visual version of this document: [threadline_evolution.html](threadline_evolution.html)*
