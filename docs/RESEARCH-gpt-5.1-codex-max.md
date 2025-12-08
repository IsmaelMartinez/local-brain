# Local Brain – Research Note (gpt-5.1-codex-max)

## Repository snapshot
- **Purpose:** CLI to chat with local Ollama models; exposes a fixed, read-only toolset (file read/info, dir list, git status/log/diff/changed, allow-listed `run_command`).
- **Architecture:** Thin `ollama.chat` loop with tool-calling; no indexing, chunking, memory, or planning beyond a max-turn loop. Tools live in `local_brain/tools/*`; CLI prompt hardcodes tool descriptions.
- **Safety posture:** Default-deny shell allowlist with blocked commands/metacharacters. Still permits wide read access (`find/rg/grep`) without path jail or sandbox.
- **Gaps:** No semantic search or embeddings, no chunked reads, no tests, no repo-scoped sandboxing, no per-repo config, no telemetry or retries, no edit/apply workflows (read-only).

## Nearby open-source options (can replace or subsume)
- **aider** (MIT): CLI code assistant with git-aware diffs, file selection, commit message generation; supports Ollama/local models. Richer workflow and guardrails; likely a superset for code review/edit use cases.
- **Continue** (Apache-2.0/MIT): VS Code/JetBrains extension with workspace-aware context, quick actions, and Ollama support. Not CLI, but offers indexing and better UX.
- **OpenInterpreter** (MIT): General-purpose local agent that runs code/shell with LLM guidance; broader scope, less repo-specific safety by default.
- **Qwen-Agent** (Apache-2.0): Agent framework with tool schemas and orchestration examples; can run with Ollama backends. Requires wiring tools but offers better planning.
- **LangChain / LlamaIndex code agents** (permissive): Frameworks to compose tools + retrievers (embeddings over code), reranking, and guardrails. More boilerplate but adds semantic search and context management.

## Fit analysis
- If the goal is a turnkey CLI for code Q&A/review: **aider** already delivers the needed workflows; adopting it could make this project redundant unless custom safety constraints are required.
- For editor-integrated productivity and indexing: **Continue** is stronger than a custom CLI.
- For customizable orchestration while reusing current tools: **Qwen-Agent** or **LangChain/LlamaIndex** provide a richer agent loop with planning and retrieval.
- For broad local execution agents: **OpenInterpreter** is an option but would need repo-specific guardrails.

## Suggestions if continuing this project
- Add repo-scoped sandboxing (enforce project root for tools/commands).
- Add semantic code search (local embeddings + reranking) and chunked readers to avoid context bloat.
- Add tests for allow/deny behavior, truncation, and tool outputs.
- Add per-repo config (tool enablement, limits, model defaults) and retries/telemetry.
- Consider reusing an agent framework to reduce maintenance while keeping the curated tool surface.

