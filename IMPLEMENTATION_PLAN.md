# Local Brain – Implementation Plan

## Current Status

**Phase**: Implementation Complete - Ready for Validation Testing

| Component | Status |
|-----------|--------|
| Rust Binary | ✅ Complete (compiles, tests pass) |
| Documentation | ✅ Complete (README, this plan) |
| Validation Experiments | 📋 Not started |
| Claude Code Integration | 📋 Not started |

**Default Model**: `deepseek-coder-v2-8k`

---

## Overview

This document outlines the implementation plan for a Rust-based local code reviewer that performs structured code and document reviews using a local Ollama model.

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
│   (Main)    │  ◄── Minimal context: just passes path
└──────┬──────┘
       │
       ├─ Passes file path(s) + metadata
       │
       ▼
┌─────────────────┐
│   Subagent      │
│  (Haiku 4.5)    │  ◄── Minimal context: just passes path through
└────────┬────────┘
         │
         ├─ Passes path + metadata as JSON
         │
         ▼
┌─────────────────────────┐
│  Rust Binary            │
│  local-brain│  ◄── Heavy lifting: reads file, calls Ollama
│  - Reads file           │
│  - Calls Ollama         │
│  - Returns review       │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│  Ollama API     │
│  (Local Model)  │
└─────────────────┘
```

**Key Flow**:
1. Main conversation passes **file paths** (not content) - stays lightweight
2. Subagent passes **file paths** (not content) to binary - stays lightweight
3. **Binary reads the file** from disk and loads into memory
4. Binary sends content to Ollama and returns structured review
5. Subagent interprets review and returns human-friendly summary

**Context Efficiency**:
- Main conversation: ~100 tokens (just path + metadata)
- Subagent: ~500 tokens (path in, review out - no file content!)
- Binary: Full file in memory (but disposable process)
- Result: Massive context savings across the board

---

## Binary Interface

### Binary Name
```
local-brain
```

### Input Format (stdin)
```json
{
  "file_path": "/absolute/path/to/file.rs",
  "meta": {
    "kind": "code | design-doc | ticket | other",
    "review_focus": "refactoring | readability | performance | risk | general"
  }
}
```

**Note**: The binary receives a **file path**, not file content. It reads the file itself.

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
local-brain/
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
name = "local-brain"
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
use std::path::PathBuf;

#[derive(Debug, Deserialize)]
struct Meta {
    kind: Option<String>,
    review_focus: Option<String>,
}

#[derive(Debug, Deserialize)]
struct InputPayload {
    file_path: PathBuf,
    meta: Option<Meta>,
}
```

**Note**: `name` is removed from meta since we can derive it from `file_path`

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
3. **Read file** from `file_path` into string
   - Handle file not found, permission errors
   - Extract filename from path for metadata
4. **Build Ollama prompt**:
   - System message: explain the 4 categories and required JSON format
   - User message: include metadata (kind, filename, focus) and document text
5. **Call Ollama chat endpoint** using reqwest blocking client:
   - URL: `OLLAMA_HOST` env var or default `http://localhost:11434`
   - POST `/api/chat`
   - Body: `{ "model": "<model-name>", "messages": [...] }`
6. **Extract response content** (single string from model)
7. **Parse response** as JSON into `OutputPayload`
   - Handle potential text-instead-of-JSON scenarios
   - Implement cleanup if needed
8. **Serialize** `OutputPayload` to stdout using `serde_json::to_writer`
9. **Error handling**: On error, print clear message to stderr and exit with non-zero code

### Pseudocode
```rust
fn main() -> Result<(), anyhow::Error> {
    // 1. Read stdin
    let mut input = String::new();
    io::stdin().read_to_string(&mut input)?;

    // 2. Deserialize input
    let payload: InputPayload = serde_json::from_str(&input)?;

    // 3. Read file from disk
    let document = fs::read_to_string(&payload.file_path)
        .context("Failed to read file")?;

    // Extract filename for metadata
    let filename = payload.file_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");

    // 4. Build prompt
    let (system_msg, user_msg) = build_prompt(&document, filename, &payload.meta)?;

    // 5. Call Ollama
    let response = call_ollama(system_msg, user_msg)?;

    // 6. Parse response
    let output: OutputPayload = parse_ollama_response(&response)?;

    // 7. Write to stdout
    serde_json::to_writer(io::stdout(), &output)?;

    Ok(())
}
```

---

## Ollama Integration

### Environment Variables
- **`OLLAMA_HOST`**: Ollama server URL (default: `http://localhost:11434`)
- **`MODEL_NAME`**: Model to use (default: `deepseek-coder-v2-8k`)

### API Endpoint
```
POST {OLLAMA_HOST}/api/chat
```

### Request Body
```json
{
  "model": "deepseek-coder-v2-8k",
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
**File**: {filename}
**Kind**: {kind}
**Review Focus**: {review_focus}

**Document Content**:
{document_text}

Provide your structured review as JSON only.
```

---

## Claude Code Integration

### Skill: local-brain

**Location**: `.claude/skills/local-brain/skill.md`

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
2. Determine metadata (kind, review_focus) from context or user request
3. Build InputPayload JSON with **file path** (not content!)
4. Run: `echo '<json>' | local-brain`
5. Binary reads file, calls Ollama, returns review
6. Parse JSON output
7. Return concise, human-friendly summary to main conversation

## Categories Explained
- **spikes**: Areas requiring investigation or refactoring
- **simplifications**: Opportunities to reduce complexity
- **defer_for_later**: Low-priority items for future work
- **other_observations**: General notes and ideas

## Example
```bash
# Subagent just passes the path - binary does the reading!
echo '{"file_path":"src/auth.rs","meta":{"kind":"code","review_focus":"refactoring"}}' | local-brain
```

## Important
- **Main conversation**: passes file paths only (minimal context)
- **Subagent**: passes file paths to binary (minimal context)
- **Binary**: reads files and calls Ollama (heavy lifting)
- This keeps BOTH main and subagent contexts lightweight
```

### Subagent: review-optimiser

**Location**: Configure as a subagent in Claude Code

**Model**: Haiku 4.5 (cheap, fast)

**Tools Available**:
- Skill: local-brain
- Read (to fetch documents)

**Behavior**:
1. Receive file path(s) and review focus from main conversation
2. Determine file kind from extension or context (code, design-doc, etc.)
3. Build JSON payload with **file path only** (no reading!)
4. Call the local-brain Skill (which pipes JSON to Rust binary)
5. Binary reads file and calls Ollama (subagent waits for result)
6. Interpret the JSON review from binary output
7. Return a concise, human-friendly summary to main conversation
8. Suggest next steps based on review findings

**Prompt Example**:
```
You are a review assistant that helps analyze documents using a local LLM.

Your role:
- Receive file path(s) from the main conversation (NOT file content)
- Build JSON payload with the file path (DO NOT read the file yourself!)
- Call the local-brain skill which runs a Rust binary
- The binary handles all file reading and Ollama interaction
- Interpret the structured JSON review you receive back
- Return a clear, actionable summary to the main conversation

Workflow:
1. Get file path and review focus from main conversation
2. Determine file kind from extension (e.g., .rs -> code, .md -> design-doc)
3. Build JSON: {"file_path": "/path/to/file", "meta": {"kind": "...", "review_focus": "..."}}
4. Call skill: echo '<json>' | local-brain
5. Wait for binary to read file, call Ollama, and return review JSON
6. Parse JSON output and present in human-friendly format
7. Suggest priorities and next steps

IMPORTANT: Never use the Read tool to fetch file content - the binary does this!
Keep responses concise and actionable. Your context stays minimal because you never load the file.
```

---

## V1 Implementation Checklist

### Phase 1: Rust Binary
- [x] Create Cargo project: `cargo new local-brain`
- [x] Add dependencies to `Cargo.toml`
- [x] Implement data structures (Input/Output structs)
- [x] Implement stdin reading and JSON deserialization
- [x] Implement prompt building logic
- [x] Implement Ollama API client (reqwest blocking)
- [x] Implement response parsing with error handling
- [x] Implement stdout JSON serialization
- [x] Add comprehensive error handling with anyhow
- [x] Add environment variable support (`OLLAMA_HOST`, `MODEL_NAME`)

### Phase 2: Testing
- [ ] Test binary manually with sample JSON
- [ ] Test with various document types (code, design-doc, ticket)
- [ ] Test error cases (invalid JSON, Ollama down, malformed response)
- [ ] Verify JSON output is valid and matches schema
- [ ] Test with different Ollama models
- [ ] Refine prompts until JSON output is stable

### Phase 3: Claude Code Integration
- [ ] Create `.claude/skills/local-brain/` directory
- [ ] Write skill.md with usage instructions
- [ ] Test skill from Claude Code main conversation
- [ ] Configure review-optimiser subagent
- [ ] Test end-to-end: User → Subagent → Skill → Binary → Ollama → User

### Phase 4: Documentation & Refinement
- [x] Write README.md for the Rust binary
- [x] Document installation and setup
- [x] Document environment variables and configuration
- [x] Add example usage and sample output
- [ ] Create troubleshooting guide
- [ ] Refine prompts based on real-world usage

---

## Testing Strategy

### Manual Testing
```bash
# Test 1: Basic functionality with real file
echo '{
  "file_path": "/tmp/test.rs",
  "meta": {
    "kind": "code",
    "review_focus": "refactoring"
  }
}' > /tmp/test_input.json

# Create test file
echo 'fn main() { println!("Hello"); }' > /tmp/test.rs

# Run binary
cat /tmp/test_input.json | local-brain

# Test 2: Minimal input
echo '{
  "file_path": "/tmp/test.rs"
}' | local-brain

# Test 3: File not found (should fail gracefully)
echo '{
  "file_path": "/nonexistent/file.rs",
  "meta": {"kind": "code"}
}' | local-brain

# Test 4: Invalid JSON (should fail gracefully)
echo 'not json' | local-brain
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
1. Receives file path from main conversation: `src/auth.rs`
2. Determines file kind from extension: `.rs` → `code`
3. Builds input JSON (note: just the **path**, not content!):
```json
{
  "file_path": "src/auth.rs",
  "meta": {
    "kind": "code",
    "review_focus": "refactoring"
  }
}
```
4. Calls binary: `echo '<json>' | local-brain`
5. Binary reads file, sends to Ollama, returns review
6. Subagent receives output:
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
- **Main conversation**: Ultra lightweight (~100 tokens - just path + metadata)
- **Subagent**: Also lightweight (~500 tokens - no file content ever loaded!)
- **Binary**: Does ALL heavy lifting (reads file, loads into memory, calls Ollama)
- **Cost optimization**: Haiku subagent uses minimal tokens since it never reads files
- **Memory efficiency**: File content only exists in binary process (disposable)
- **Scalability**: Can review many files by passing multiple paths
- **User experience**: Clean interface, no raw JSON visible

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
