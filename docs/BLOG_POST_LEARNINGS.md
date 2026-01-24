# What We Learned Deprecating local-brain for LiteLLM

**Status:** Draft for publication
**Target audience:** Developers building LLM tools, cost-conscious AI users, open-source contributors
**Tone:** Honest, reflective, educational

---

## From Custom CLI to LiteLLM: Why We Deprecated local-brain

*What building, pausing, and revisiting an LLM side project taught us*

---

## Opening Hook

"Don't build what already exists."

Easy advice to give. Much harder to follow when you're deep in the problem, convinced your case is different, and the ecosystem is moving faster than your mental model.

This is the story of local-brain: a Claude Code optimisation experiment we started in September 2025, worked on in short bursts, repeatedly paused and rethought — and eventually archived once it became clear that better solutions already existed.

This isn't a story about reckless spending or panic-driven optimisation.

It's a story about context, capability boundaries, and knowing when to move on.

---

## 1. The Real Problem: Context Before Cost

The project didn't start with a dramatic bill spike.

It started with context management.

Claude Code was powerful, but it became clear early on that we were routinely sending far more context than necessary:

- Large diffs when only small changes mattered
- Whole files when only specific symbols were relevant
- Historical context that didn't meaningfully affect the answer

This had predictable side effects:

- Costs crept up
- Latency increased
- Output quality became inconsistent

The initial question wasn't "How do we replace Claude?" or even "How do we slash costs?"

It was much simpler:

**Can we reduce context size and only send what the model actually needs?**

Cost was the forcing function — but context efficiency was the real technical problem.

Only later did the numbers become uncomfortable:

- Monthly spend rising into the hundreds
- January 2026 hovering around $50/day ($1,500/month)
- Legitimate ROI questions at team scale

At that point, optimisation wasn't optional — but it also wasn't obvious how to do it safely or predictably.

---

## 2. What We Built (and Why)

### The Original Idea

If most requests don't need top-tier reasoning, route them elsewhere.

```
Claude Code (cloud, expensive)
     ↓
local-brain (custom CLI)
     ↓
Ollama (local, free models)
```

The plan was simple:

- Reduce context aggressively
- Delegate clearly bounded tasks to cheaper or local models
- Keep expensive models for genuinely hard problems

### What We Actually Built

Between September 2025 and January 2026 — worked on intermittently rather than continuously — local-brain grew into:

- A custom Python CLI built on Smolagents
- Delegation logic to local Ollama models
- AST-aware code search
- Read-only Git operations
- A defensive security layer:
  - Path jailing
  - Sensitive file blocking (.env, SSH keys, etc.)
  - Output truncation
  - Timeouts
- Observability via OpenTelemetry + Jaeger

From a software engineering perspective, it was clean, well-structured, and something to be proud of.

But good architecture isn't the same as a good outcome.

---

## 3. The Pivots That Mattered

### Pivot 1: Context → Security (Reluctantly)

Once we started delegating work to local models, we ran into a hard constraint: execution model.

Smolagents executes tools invisibly, without explicit user approval. Sandboxing wasn't an option in our environment, so we compensated in code.

Security wasn't a design goal — it was a tax:

- Path jailing
- File access restrictions
- Output limits
- Timeouts

This security was necessary.

But it also changed the project's centre of gravity. Instead of refining context selection and task boundaries, we were spending increasing effort defending against invisible execution.

**Lesson:** once you introduce invisible execution, security stops being optional — and starts dominating the architecture.

---

### Pivot 2: The Quality Wall

At this point, the project almost worked.

Some flows were genuinely good:

- Summarising Git diffs
- Highlighting structural changes
- Mechanical or descriptive transformations

Encouraged by that, we pushed further:

- Pair-review style feedback
- Suggesting best practices
- Judging whether a change was "good" or "problematic"

This is where things broke down.

The issue wasn't constant failure. It was unpredictability.

Some of these flows worked surprisingly well. Others — which looked similar on the surface — produced subtle but serious problems:

- Missed issues
- Overconfident but shallow advice
- Feedback that sounded plausible but wasn't actionable

We couldn't draw a clean line and say:

*These tasks are safe to delegate; these are not.*

That uncertainty had a real cost:

- Every output needed review
- Trust never fully formed
- Any theoretical savings were eaten by cognitive overhead

**An optimisation that requires constant verification isn't an optimisation.**

It's just moving work around.

---

### Pivot 3: The Ollama Announcement (January 2026)

Ollama v0.14.0 added native Anthropic Messages API compatibility.

```bash
export ANTHROPIC_BASE_URL=http://localhost:11434
export ANTHROPIC_API_KEY=ollama
```

Claude Code could now talk to Ollama directly.

This didn't trigger panic.

It triggered relief.

The question shifted from "How do we salvage this?" to:

**Is this the moment to move on?**

---

### Pivot 4: Stepping Back and Research

With quality concerns unresolved and costs still under scrutiny, we finally stepped back and surveyed the ecosystem properly.

We looked at:

- Prompt caching (Anthropic feature)
- Batch APIs
- RAG-based context selection
- Existing routing and proxy layers

Two things became immediately clear:

1. Prompt caching alone solved most of the cost problem, with almost no engineering effort.
2. LiteLLM already existed — mature, production-ready, and doing exactly what we were attempting to reinvent.

We didn't build the wrong thing. We built something that the ecosystem had already solved.

---

## 4. Why LiteLLM Won

| Feature | local-brain | LiteLLM |
|---------|-------------|---------|
| Model routing | Manual, ad-hoc | Policy-based |
| Providers | Ollama only | 100+ |
| Caching | None | Prompt, semantic, Redis |
| Cost tracking | None | Built-in |
| Team support | None | SSO, budgets |
| Security model | Filesystem-level | IAM, rate limits |
| Observability | Custom OTEL | Prometheus, Langfuse |
| Maintenance | DIY | Actively maintained |

LiteLLM isn't perfect — the configuration surface is large, and you need to understand routing semantics — but that complexity is unavoidable at this layer.

**Setup time:** a few hours
**Savings achieved:** ~78% at team scale

---

## 5. What We Actually Learned

### Lesson 1: Context Selection Beats Model Selection

Most cost and quality problems were upstream of model choice.

Sending less, better-chosen context mattered far more than switching models.

---

### Lesson 2: Capability Boundaries Matter More Than Raw Quality

The hardest problem wasn't failure.

It was knowing when something would succeed.

If you can't clearly define and enforce capability boundaries, you can't automate safely — no matter how good the average output looks.

---

### Lesson 3: Execution Models Shape Everything

Invisible execution forces defensive security.

User-approved execution shifts the trust model entirely.

Architecture choices propagate further than you expect.

---

### Lesson 4: Build vs Buy Applies to Open Source Too

Time spent:

- local-brain: sporadic bursts over several months
- LiteLLM evaluation + setup: hours

The lesson wasn't "don't build".

It was **build only after you've searched properly**.

---

### Lesson 5: The Learning Was the Real Win

Despite being archived, local-brain paid for itself in learning:

- Context management and prompt shaping
- Smolagents and execution trade-offs
- Model behaviour with tooling vs free-form reasoning
- Claude plugins, marketplaces, and sub-agents
- Recognising when uncertainty outweighs theoretical savings

**local-brain failed as a product — and succeeded completely as R&D.**

---

## 6. Migration (What We Actually Did)

- Adopted LiteLLM
- Enabled prompt caching
- Added Redis caching
- Rolled out gradually

What we did not migrate:

- Custom security layers
- Smolagents execution
- CLI glue code

**Result:** ~78% cost reduction at team scale

---

## Closing

local-brain is archived. The code remains as a learning artefact.

LiteLLM is now our production solution.

The hardest part wasn't letting go of code — it was letting go of an idea that was almost good enough.

Knowing when to move on is part of the job.

---

## Links

- [LiteLLM](https://github.com/BerriAI/litellm)
- [local-brain (archived)](https://github.com/IsmaelMartinez/local-brain)
- [Migration guide](https://github.com/IsmaelMartinez/local-brain/blob/main/MIGRATION.md)

---

*Failures are only wasted if you don't learn from them.*
