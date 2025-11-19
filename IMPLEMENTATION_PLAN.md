# Local Context Optimiser – Implementation Plan

## Overview

This document outlines the implementation plan for a Rust-based Local Context Optimiser that performs structured code and document reviews using a local Ollama model.

## Goal

Build a single Rust binary that:
- Reads a document (text) + metadata from stdin as JSON
- Calls a local Ollama model to produce a structured review
- Prints a compact JSON review to stdout
- Can be called by Claude Code via a Skill, preferably from a cheap subagent (e.g., Haiku 4.5)

## Architecture

```
┌─────────────┐
│ Claude Code │
│   (Main)    │
└──────┬──────┘
       │
       ├─ Passes file path(s) + metadata
       │
       ▼
┌─────────────────┐
│   Subagent      │
│  (Haiku 4.5)    │ ◄── Reads file(s) using Read tool
└────────┬────────┘
         │
         ├─ Builds JSON with document content
         │
         ▼
┌─────────────────────────┐
│  Rust Binary            │
│  local-context-optimizer│ ◄── Receives document via stdin
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  Ollama API     │
│  (Local Model)  │
└─────────────────┘
```

**Key Flow**:
1. Main conversation passes **file paths** (not content) to keep context lightweight
2. Subagent uses Read tool to fetch file content
3. Subagent builds JSON payload and pipes to binary
4. Binary processes content with Ollama and returns structured review

---

## Binary Interface

### Binary Name
```
local-context-optimizer
```

### Input Format (stdin)
```json
{
  "document": "full text to review",
  "meta": {
    "kind": "code | design-doc | ticket | other",
    "name": "file-or-doc-name",
    "review_focus": "refactoring | readability | performance | risk | general"
  }
}
```

### Output Format (stdout)
```json
{
  "spikes": [
    {
      "title": "...",
      "summary": "...",
      "lines": "optional line range"
    }
  ],
  "simplifications": [
    {
      "title": "...",
      "summary": "..."
    }
  ],
  "defer_for_later": [
    {
      "title": "...",
      "summary": "..."
    }
  ],
  "other_observations": [
    "short note 1",
    "short note 2"
  ]
}
```

---

## Project Structure

### Rust Crate Layout
```
local-context-optimizer/
├── Cargo.toml
├── src/
│   └── main.rs
└── README.md
```

Start with a simple binary crate (no workspace needed for v1).

---

## Dependencies (Cargo.toml)

```toml
[package]
name = "local-context-optimizer"
version = "0.1.0"
edition = "2021"

[dependencies]
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", features = ["json", "blocking"] }
anyhow = "1"
```

### Dependency Rationale
- **serde/serde_json**: JSON serialization/deserialization
- **reqwest**: HTTP client for Ollama API calls (blocking mode for simplicity)
- **anyhow**: Error handling with context

---

## Data Structures

### Input Structures
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
struct Meta {
    kind: Option<String>,
    name: Option<String>,
    review_focus: Option<String>,
}

#[derive(Debug, Deserialize)]
struct InputPayload {
    document: String,
    meta: Option<Meta>,
}
```

### Output Structures
```rust
#[derive(Debug, Serialize, Deserialize)]
struct ReviewItem {
    title: String,
    summary: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    lines: Option<String>,
}

#[derive(Debug, Serialize)]
struct OutputPayload {
    spikes: Vec<ReviewItem>,
    simplifications: Vec<ReviewItem>,
    defer_for_later: Vec<ReviewItem>,
    other_observations: Vec<String>,
}
```

---

## Main Flow (src/main.rs)

### High-Level Algorithm

1. **Read stdin** into a string
2. **Deserialize** to `InputPayload` using `serde_json::from_str`
3. **Build Ollama prompt**:
   - System message: explain the 4 categories and required JSON format
   - User message: include metadata and document text
4. **Call Ollama chat endpoint** using reqwest blocking client:
   - URL: `OLLAMA_HOST` env var or default `http://localhost:11434`
   - POST `/api/chat`
   - Body: `{ "model": "<model-name>", "messages": [...] }`
5. **Extract response content** (single string from model)
6. **Parse response** as JSON into `OutputPayload`
   - Handle potential text-instead-of-JSON scenarios
   - Implement cleanup if needed
7. **Serialize** `OutputPayload` to stdout using `serde_json::to_writer`
8. **Error handling**: On error, print clear message to stderr and exit with non-zero code

### Pseudocode
```rust
fn main() -> Result<(), anyhow::Error> {
    // 1. Read stdin
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;

    // 2. Deserialize input
    let payload: InputPayload = serde_json::from_str(&input)?;

    // 3. Build prompt
    let (system_msg, user_msg) = build_prompt(&payload)?;

    // 4. Call Ollama
    let response = call_ollama(system_msg, user_msg)?;

    // 5. Parse response
    let output: OutputPayload = parse_ollama_response(&response)?;

    // 6. Write to stdout
    serde_json::to_writer(io::stdout(), &output)?;

    Ok(())
}
```

---

## Ollama Integration

### Environment Variables
- **`OLLAMA_HOST`**: Ollama server URL (default: `http://localhost:11434`)
- **`MODEL_NAME`**: Model to use (e.g., `llama3.2`, `mistral`, etc.)

### API Endpoint
```
POST {OLLAMA_HOST}/api/chat
```

### Request Body
```json
{
  "model": "llama3.2",
  "messages": [
    {
      "role": "system",
      "content": "System prompt here..."
    },
    {
      "role": "user",
      "content": "User prompt with document..."
    }
  ],
  "stream": false
}
```

### Response Handling
```rust
#[derive(Deserialize)]
struct OllamaResponse {
    message: Message,
}

#[derive(Deserialize)]
struct Message {
    content: String,
}
```

---

## Ollama Prompt Design

### System Prompt (Concise)
```
You are a senior code and document reviewer.

You receive a document and metadata, and must produce a structured review.

**CRITICAL**: You MUST output ONLY valid JSON matching this exact structure:
{
  "spikes": [
    { "title": "string", "summary": "string", "lines": "optional string" }
  ],
  "simplifications": [
    { "title": "string", "summary": "string" }
  ],
  "defer_for_later": [
    { "title": "string", "summary": "string" }
  ],
  "other_observations": ["string", "string"]
}

**Field Definitions**:
- spikes: Hotspots, areas to investigate, potential issues or complexity
- simplifications: Areas that could be simplified or optimized
- defer_for_later: Items that are safe to move to future iterations
- other_observations: Extra notes, ideas, or general observations

**Rules**:
- Each item must be SHORT and FOCUSED (1-3 sentences max)
- Do NOT repeat the entire document
- Focus on actionable insights
- Output ONLY the JSON, no explanatory text before or after
```

### User Prompt Template
```
**Metadata**:
- Kind: {kind}
- Name: {name}
- Review Focus: {review_focus}

**Document**:
{document_text}

Provide your structured review as JSON only.
```

---

## Claude Code Integration

### Skill: local-context-optimiser

**Location**: `.claude/skills/local-context-optimiser/skill.md`

**Purpose**: Call the Rust binary to get a structured review of a document using a local LLM.

**Skill Behavior**:
```markdown
# Local Context Optimiser Skill

This skill performs structured reviews of documents using a local Ollama model.

## When to Use
- User asks for a code review that could be context-heavy
- User wants to analyze a document for improvements
- User needs to identify areas to refactor, simplify, or defer

## How to Use (for Subagents)
1. Receive file path(s) from main conversation
2. Use Read tool to fetch document content
3. Determine metadata (kind, name, review_focus)
4. Build InputPayload JSON with document content
5. Run: `echo '<json>' | local-context-optimizer`
6. Parse JSON output
7. Return concise, human-friendly summary to main conversation

## Categories Explained
- **spikes**: Areas requiring investigation or refactoring
- **simplifications**: Opportunities to reduce complexity
- **defer_for_later**: Low-priority items for future work
- **other_observations**: General notes and ideas

## Example
```bash
# Subagent reads the file first, then:
echo '{"document":"<file-content>","meta":{"kind":"code","name":"auth.rs","review_focus":"refactoring"}}' | local-context-optimizer
```

## Important
- Main conversation passes **file paths only**, not content
- Subagent does the heavy lifting of reading files
- This keeps the main conversation context lightweight
```

### Subagent: review-optimiser

**Location**: Configure as a subagent in Claude Code

**Model**: Haiku 4.5 (cheap, fast)

**Tools Available**:
- Skill: local-context-optimiser
- Read (to fetch documents)

**Behavior**:
1. Receive file path(s) and review focus from main conversation
2. Use Read tool to fetch document content
3. Build JSON payload with document content and metadata
4. Call the local-context-optimiser Skill (which pipes JSON to Rust binary)
5. Interpret the JSON review from binary output
6. Return a concise, human-friendly summary to main conversation
7. Suggest next steps based on review findings

**Prompt Example**:
```
You are a review assistant that helps analyze documents using a local LLM.

Your role:
- Receive file path(s) from the main conversation (NOT file content)
- Use the Read tool to fetch file content yourself
- Build the JSON payload with the document content
- Call the local-context-optimiser skill to run the binary
- Interpret the structured JSON review (spikes, simplifications, defer_for_later, other_observations)
- Return a clear, actionable summary to the main conversation

Workflow:
1. Get file path and review focus from main conversation
2. Read the file(s) using the Read tool
3. Build JSON: {"document": "<content>", "meta": {"kind": "...", "name": "...", "review_focus": "..."}}
4. Call skill: echo '<json>' | local-context-optimizer
5. Parse JSON output and present in human-friendly format
6. Suggest priorities and next steps

Keep responses concise and actionable. You handle the context so the main conversation stays lightweight.
```

---

## V1 Implementation Checklist

### Phase 1: Rust Binary
- [ ] Create Cargo project: `cargo new local-context-optimizer`
- [ ] Add dependencies to `Cargo.toml`
- [ ] Implement data structures (Input/Output structs)
- [ ] Implement stdin reading and JSON deserialization
- [ ] Implement prompt building logic
- [ ] Implement Ollama API client (reqwest blocking)
- [ ] Implement response parsing with error handling
- [ ] Implement stdout JSON serialization
- [ ] Add comprehensive error handling with anyhow
- [ ] Add environment variable support (`OLLAMA_HOST`, `MODEL_NAME`)

### Phase 2: Testing
- [ ] Test binary manually with sample JSON
- [ ] Test with various document types (code, design-doc, ticket)
- [ ] Test error cases (invalid JSON, Ollama down, malformed response)
- [ ] Verify JSON output is valid and matches schema
- [ ] Test with different Ollama models
- [ ] Refine prompts until JSON output is stable

### Phase 3: Claude Code Integration
- [ ] Create `.claude/skills/local-context-optimiser/` directory
- [ ] Write skill.md with usage instructions
- [ ] Test skill from Claude Code main conversation
- [ ] Configure review-optimiser subagent
- [ ] Test end-to-end: User → Subagent → Skill → Binary → Ollama → User

### Phase 4: Documentation & Refinement
- [ ] Write README.md for the Rust binary
- [ ] Document installation and setup
- [ ] Document environment variables and configuration
- [ ] Add example usage and sample output
- [ ] Create troubleshooting guide
- [ ] Refine prompts based on real-world usage

---

## Testing Strategy

### Manual Testing
```bash
# Test 1: Basic functionality
echo '{
  "document": "fn main() { println!(\"Hello\"); }",
  "meta": {
    "kind": "code",
    "name": "main.rs",
    "review_focus": "refactoring"
  }
}' | local-context-optimizer

# Test 2: Minimal input
echo '{
  "document": "Some text"
}' | local-context-optimizer

# Test 3: Invalid JSON (should fail gracefully)
echo 'not json' | local-context-optimizer
```

### Integration Testing
1. Test from Claude Code skill directly
2. Test via subagent
3. Test with real codebase files
4. Measure latency and token usage

---

## Configuration

### Environment Setup
```bash
# Required
export MODEL_NAME="llama3.2"           # or your preferred model
export OLLAMA_HOST="http://localhost:11434"  # default

# Optional (for development)
export RUST_LOG="debug"
```

### Ollama Setup
```bash
# Install Ollama (if not already installed)
# See: https://ollama.ai

# Pull a suitable model
ollama pull llama3.2

# Verify it's running
ollama list
```

---

## Performance Considerations

### V1 Scope Limitations
- **Single document at a time**: No batch processing
- **Blocking I/O**: Uses synchronous reqwest (simpler for v1)
- **No caching**: Each call is fresh
- **No timeout handling**: Relies on default reqwest timeout

### Future Optimizations (Post-V1)
- Async I/O for better concurrency
- Response caching based on document hash
- Timeout configuration
- Streaming support for large documents
- Batch processing multiple files

---

## Error Handling Strategy

### Input Validation
- Invalid JSON → stderr: "Failed to parse input JSON"
- Missing document field → stderr: "Missing required field: document"

### Ollama Communication
- Connection failed → stderr: "Failed to connect to Ollama at {url}"
- Model not found → stderr: "Model {name} not available"
- Timeout → stderr: "Ollama request timed out"

### Response Parsing
- Invalid JSON response → Attempt cleanup, then retry parse
- Missing required fields → Return empty arrays/lists
- Malformed structure → stderr: "Failed to parse Ollama response"

### Exit Codes
- 0: Success
- 1: Input/output error
- 2: Ollama communication error
- 3: Response parsing error

---

## Future Enhancements (Post-V1)

### Potential Features
1. **Multiple review modes**: Quick, standard, thorough
2. **Configurable output formats**: JSON, Markdown, HTML
3. **Incremental reviews**: Only review changed sections
4. **Custom prompts**: User-provided prompt templates
5. **Multi-model comparison**: Run same review on multiple models
6. **Review history**: Track changes over time
7. **Integration with CI/CD**: Automated review on commits

### Scalability Improvements
1. **Async processing**: Handle multiple documents concurrently
2. **Distributed execution**: Support remote Ollama instances
3. **Result caching**: Avoid redundant reviews
4. **Progressive disclosure**: Stream results as they're generated

---

## Success Criteria

### V1 Completion
✓ Binary compiles and runs without errors
✓ Accepts valid JSON via stdin
✓ Calls Ollama API successfully
✓ Returns valid JSON via stdout
✓ Handles errors gracefully with clear messages
✓ Works via Claude Code Skill
✓ Subagent can call and interpret results
✓ Produces useful, actionable review output

### Quality Metrics
- Response time: < 10 seconds for typical documents (< 500 lines)
- Accuracy: Review insights are relevant 80%+ of the time
- Stability: JSON output is valid 95%+ of the time
- Usability: No crashes on malformed input

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Rust Binary | Implementation | 4-6 hours |
| Testing | Manual & Integration | 2-3 hours |
| Claude Integration | Skill + Subagent | 1-2 hours |
| Documentation | README, examples | 1-2 hours |
| Refinement | Prompt tuning, fixes | 2-3 hours |
| **Total** | | **10-16 hours** |

---

## Dependencies & Prerequisites

### System Requirements
- Rust toolchain (1.70+)
- Ollama installed and running
- At least one LLM model pulled (e.g., llama3.2)
- Claude Code environment

### Knowledge Requirements
- Basic Rust programming
- JSON handling
- HTTP API interaction
- Claude Code Skills system
- Prompt engineering basics

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Ollama model returns text instead of JSON | High | Implement robust parsing with cleanup |
| Model hallucinations/incorrect reviews | Medium | Refine prompts, test with multiple models |
| Performance too slow for large files | Medium | Set size limits in v1, optimize in v2 |
| Binary not accessible from Skill | High | Test installation path, document setup |
| Model not available locally | High | Clear error messages, installation docs |

---

## Appendix: Example Usage

### End-to-End Example

**User Request (Main Conversation)**:
```
Can you review src/auth.rs for refactoring opportunities?
```

**Main Conversation → Subagent**:
```
Passes: file_path="src/auth.rs", review_focus="refactoring"
(NOTE: Main conversation does NOT pass file content, just the path)
```

**Subagent Actions**:
1. Receives file path from main conversation
2. Uses Read tool to fetch `src/auth.rs` content
3. Builds input JSON:
```json
{
  "document": "// Full auth.rs content here...",
  "meta": {
    "kind": "code",
    "name": "auth.rs",
    "review_focus": "refactoring"
  }
}
```
4. Calls binary: `echo '<json>' | local-context-optimizer`
5. Receives output:
```json
{
  "spikes": [
    {
      "title": "Complex authentication logic in verify_token",
      "summary": "The verify_token function has nested conditionals and multiple concerns. Consider extracting validation steps into separate functions.",
      "lines": "45-78"
    }
  ],
  "simplifications": [
    {
      "title": "Duplicate error handling patterns",
      "summary": "Error handling is repeated across login, logout, and refresh functions. Create a shared error handler."
    }
  ],
  "defer_for_later": [
    {
      "title": "Add rate limiting",
      "summary": "While not critical now, consider adding rate limiting to prevent brute force attacks."
    }
  ],
  "other_observations": [
    "Good use of type safety for tokens",
    "Consider adding more unit tests for edge cases"
  ]
}
```
6. Interprets results and prepares human-friendly summary

**Subagent → Main Conversation (Response)**:
```
Review of src/auth.rs (focus: refactoring)

🔍 Spikes (areas to investigate):
• Complex authentication logic in verify_token (lines 45-78)
  The verify_token function has nested conditionals and multiple concerns...

🔧 Simplifications:
• Duplicate error handling patterns
  Error handling is repeated across login, logout, and refresh functions...

⏳ Defer for later:
• Add rate limiting
  While not critical now, consider adding rate limiting...

💡 Other observations:
• Good use of type safety for tokens
• Consider adding more unit tests for edge cases

Would you like me to start refactoring any of these areas?
```

**Key Benefits of This Flow**:
- Main conversation stays lightweight (only passes paths, not content)
- Subagent handles all heavy context work (reading files, building JSON)
- User never sees raw JSON or binary interaction details
- Cost-effective: Haiku 4.5 subagent handles the expensive operations
- Scalable: Easy to review multiple files by passing multiple paths

---

## Conclusion

This plan provides a clear path to building a focused, efficient document review system that leverages local LLMs through Ollama while integrating seamlessly with Claude Code's Skill and subagent system.

**Key Principles**:
- Keep v1 simple and focused
- Clear interfaces (JSON in/out for binary)
- Path-based flow keeps main conversation lightweight
- Subagent handles context-heavy operations
- Robust error handling
- Easy to test and debug
- Extensible for future enhancements

**Next Steps**:
1. Set up development environment
2. Implement Rust binary
3. Test with sample documents
4. Integrate with Claude Code
5. Iterate based on real usage
