# Validation Experiments

Run these experiments before full implementation to validate critical assumptions.

**Total Time**: ~2.5 hours

---

## Phase 1: Foundation (30 min)

### Experiment 1.1: Check Ollama Setup
```bash
which ollama
curl http://localhost:11434/api/tags
ollama list
```

**Success**: Ollama installed, running, has at least one model.

---

### Experiment 1.2: Basic JSON Test
```bash
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "Return ONLY valid JSON. No other text."},
    {"role": "user", "content": "Return: {\"status\": \"ok\", \"value\": 42}"}
  ],
  "stream": false
}'
```

**Success**: Response contains valid JSON in `message.content`, no extra text, consistent across 5 runs.

---

### Experiment 1.3: Review Structure Test
```bash
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {"role": "system", "content": "Output ONLY valid JSON: {\"spikes\": [{\"title\": \"str\", \"summary\": \"str\"}], \"simplifications\": [], \"defer_for_later\": [], \"other_observations\": []}"},
    {"role": "user", "content": "Review: function add(a,b) { return a+b; }"}
  ],
  "stream": false
}'
```

**Success**: Returns valid JSON matching schema, arrays populated appropriately, completes in <10s.

**Go/No-Go**: If JSON unreliable, implement extraction/cleanup layer.

---

## Phase 2: Integration (70 min)

### Experiment 2.1: File Reading Binary
```bash
mkdir -p /tmp/test-binary && cd /tmp/test-binary
cargo init --name file-reader-test

cat > src/main.rs << 'EOF'
use std::io::{self, Read};
use std::fs;
use serde::{Deserialize, Serialize};

#[derive(Deserialize)]
struct Input { file_path: String }

#[derive(Serialize)]
struct Output { content: String, size: usize }

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let payload: Input = serde_json::from_str(&input).unwrap();
    let content = fs::read_to_string(&payload.file_path).unwrap();
    let output = Output { size: content.len(), content };
    println!("{}", serde_json::to_string(&output).unwrap());
}
EOF

cargo add serde --features derive
cargo add serde_json
cargo build --release

echo 'fn main() { println!("test"); }' > /tmp/test.rs
echo '{"file_path": "/tmp/test.rs"}' | ./target/release/file-reader-test
```

**Success**: Binary receives JSON, reads file, returns valid JSON output.

---

### Experiment 2.2: File Error Handling
```bash
# Non-existent file
echo '{"file_path": "/nonexistent/file.rs"}' | ./target/release/file-reader-test

# Permission denied
touch /tmp/noperm.txt && chmod 000 /tmp/noperm.txt
echo '{"file_path": "/tmp/noperm.txt"}' | ./target/release/file-reader-test
chmod 644 /tmp/noperm.txt
```

**Success**: Graceful errors on stderr, non-zero exit codes, no panics.

---

### Experiment 2.3: Model Quality Test
```bash
# Create problematic code
cat > /tmp/test_code.js << 'EOF'
function processUser(user) {
  if (user) {
    if (user.name) {
      if (user.email) {
        if (validateEmail(user.email)) {
          return user;
        }
      }
    }
  }
  return null;
}
EOF

# Test review quality with your model
```

**Success**: Model identifies nested conditionals, suggests improvements, response is relevant, completes in <15s.

**Go/No-Go**: If binary can't read files or model quality poor, re-evaluate approach.

---

## Phase 3: E2E Flow (45 min)

### Experiment 3.1: Skill Creation
Create `.claude/skills/local-context-optimiser/skill.md` with basic instructions.

**Success**: Skill file created and recognized by Claude Code.

---

### Experiment 3.2: Skill Execution
From Claude Code, test calling the binary via the skill.

**Success**: Binary executes, output captured correctly.

---

### Experiment 3.3: File Size Test
Test with files of 100, 500, 1000 lines.

**Success**: 500 line files work well, know practical limits.

**Go/No-Go**: If E2E fails, adjust architecture.

---

## Fallback Strategies

### JSON Output Unreliable
- Add JSON extraction/cleanup step (regex to find JSON)
- Use structured output if Ollama supports
- Add validation loop with retry

### Model Quality Poor
- Try code-focused models (qwen2.5-coder, deepseek-coder)
- Add few-shot examples to prompts
- Chain smaller prompts

### Binary File Reading Fails
- Have subagent read file (defeats optimization but works)
- Use Python instead of Rust
- Use HTTP server instead of CLI

### Context Size Too Small
- Chunk large files
- Add summarization pass
- Set hard file size limit

---

## Success Criteria

Before proceeding with full implementation:

- [ ] Ollama returns valid JSON 90%+ of time
- [ ] Model gives useful, relevant reviews
- [ ] Binary reads files and returns JSON correctly
- [ ] Skill executes binary from Claude Code
- [ ] Files up to 500 lines process in <15s
