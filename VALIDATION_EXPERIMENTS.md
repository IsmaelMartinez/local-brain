# Validation Experiments - Local Context Optimiser

## Purpose
Identify and validate critical assumptions before full implementation to avoid discovering blockers halfway through development.

---

## Critical Spikes to Validate

### 🔴 **SPIKE 1: Ollama JSON Output Reliability**
**Risk Level**: HIGH
**Why Critical**: The entire system depends on Ollama returning valid, parseable JSON

**Questions**:
- Can Ollama consistently return valid JSON (not text with JSON)?
- Does the model respect JSON schema instructions?
- How often does it hallucinate or add extra text outside JSON?
- What happens with different models (llama3.2 vs mistral vs qwen)?

**Experiment 1.1: Basic JSON Generation Test**
```bash
# Test if Ollama can return pure JSON
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "system",
      "content": "Return ONLY valid JSON. No other text."
    },
    {
      "role": "user",
      "content": "Return this JSON: {\"status\": \"ok\", \"value\": 42}"
    }
  ],
  "stream": false
}'
```

**Success Criteria**:
- [ ] Response contains valid JSON in message.content
- [ ] No extra text before/after JSON
- [ ] Consistent across 5 runs

**Experiment 1.2: Structured Review JSON Test**
```bash
# Test with actual review structure
curl -X POST http://localhost:11434/api/chat -d '{
  "model": "llama3.2",
  "messages": [
    {
      "role": "system",
      "content": "You are a code reviewer. Output ONLY valid JSON matching: {\"spikes\": [{\"title\": \"str\", \"summary\": \"str\"}], \"simplifications\": [], \"defer_for_later\": [], \"other_observations\": []}"
    },
    {
      "role": "user",
      "content": "Review this code: function add(a,b) { return a+b; }"
    }
  ],
  "stream": false
}'
```

**Success Criteria**:
- [ ] Returns valid JSON matching schema
- [ ] Arrays are populated appropriately
- [ ] No hallucinated fields
- [ ] Runs in < 10 seconds

---

### 🔴 **SPIKE 2: Ollama Model Availability & Quality**
**Risk Level**: HIGH
**Why Critical**: Need a model that can do meaningful code review

**Questions**:
- Is Ollama installed and running?
- Which models are available locally?
- Which model gives best reviews vs speed?
- What's the context size limit?

**Experiment 2.1: Check Ollama Setup**
```bash
# Is Ollama installed?
which ollama

# Is it running?
curl http://localhost:11434/api/tags

# What models are available?
ollama list
```

**Success Criteria**:
- [ ] Ollama is installed
- [ ] Service is running
- [ ] At least one suitable model is pulled

**Experiment 2.2: Model Quality Test**
```bash
# Test review quality with a known problematic code sample
# Create test file with obvious issues
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

# Test with different models
for model in llama3.2 mistral qwen2.5-coder; do
  echo "Testing $model..."
  # Send review request
done
```

**Success Criteria**:
- [ ] Model identifies nested conditionals as a spike
- [ ] Suggests guard clauses or early returns
- [ ] Response is relevant (not hallucinated)
- [ ] Review completes in reasonable time (< 15s)

---

### 🟡 **SPIKE 3: stdin/stdout Binary Integration**
**Risk Level**: MEDIUM
**Why Critical**: Skill needs to pipe JSON to binary correctly

**Questions**:
- Can we pipe JSON via echo to a simple Rust binary?
- Does JSON escaping work (quotes, newlines, backslashes)?
- Can we capture stdout correctly?

**Experiment 3.1: Simple Echo Binary Test**
```bash
# Create minimal Rust binary that echoes stdin
mkdir -p /tmp/test-binary
cd /tmp/test-binary
cargo init --name echo-test

# Edit main.rs to read stdin and write stdout
cat > src/main.rs << 'EOF'
use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    println!("{}", input);
}
EOF

cargo build --release

# Test piping
echo '{"test": "value"}' | ./target/release/echo-test
```

**Success Criteria**:
- [ ] Binary receives JSON correctly
- [ ] Output matches input
- [ ] Works from Bash tool in Claude Code

**Experiment 3.2: JSON Escaping Test**
```bash
# Test with problematic characters
cat > /tmp/test.json << 'EOF'
{
  "document": "function test() {\n  console.log(\"hello\");\n  return 'world';\n}",
  "meta": {"kind": "code"}
}
EOF

cat /tmp/test.json | ./target/release/echo-test
```

**Success Criteria**:
- [ ] Quotes are properly escaped
- [ ] Newlines don't break JSON
- [ ] Backslashes work correctly
- [ ] Output is valid JSON

---

### 🟡 **SPIKE 4: Skill → Binary Execution**
**Risk Level**: MEDIUM
**Why Critical**: Subagent needs to invoke binary via Skill

**Questions**:
- Can a Skill execute arbitrary binaries?
- Is PATH configured correctly?
- Can we pass complex JSON via echo?

**Experiment 4.1: Create Test Skill**
```bash
# Create a minimal skill that runs a binary
mkdir -p .claude/skills/test-binary
cat > .claude/skills/test-binary/skill.md << 'EOF'
# Test Binary Skill

This skill tests if we can run a binary and capture output.

## Usage
Run: echo '{"test": "value"}' | /tmp/test-binary/target/release/echo-test
EOF
```

**Experiment 4.2: Test from Claude Code**
```
User: Use the test-binary skill to echo some JSON
```

**Success Criteria**:
- [ ] Skill can locate binary
- [ ] Binary executes successfully
- [ ] Output is captured correctly
- [ ] Works from subagent (if we can test)

---

### 🟢 **SPIKE 5: Subagent → Skill Integration**
**Risk Level**: LOW (assuming Skills work)
**Why Critical**: This is our cost-optimization strategy

**Questions**:
- Can we invoke a subagent with specific tools?
- Can subagent use Skills?
- Does the path-based flow work as intended?

**Experiment 5.1: Simple Subagent Test**
```
Main conversation: Launch a Haiku subagent to read a file and report its size
```

**Success Criteria**:
- [ ] Subagent launches successfully
- [ ] Can use Read tool
- [ ] Returns result to main conversation
- [ ] Uses less context than main doing it

---

### 🟢 **SPIKE 6: Real File Processing**
**Risk Level**: LOW
**Why Critical**: Need to ensure real code works

**Questions**:
- Can we handle typical file sizes?
- Does Ollama context window handle 500+ line files?
- How do we handle very large files?

**Experiment 6.1: File Size Test**
```bash
# Test with files of increasing size
for lines in 100 500 1000 2000; do
  # Create test file
  # Send to Ollama
  # Measure response time and quality
done
```

**Success Criteria**:
- [ ] 500 line files work well
- [ ] 1000 line files work (maybe slower)
- [ ] System gracefully handles oversized files
- [ ] We know the practical limit

---

## Recommended Validation Order

### Phase 1: Foundation (Do First)
1. **Experiment 2.1**: Check Ollama Setup - 5 min
2. **Experiment 1.1**: Basic JSON Test - 10 min
3. **Experiment 1.2**: Review JSON Test - 15 min

**Go/No-Go Decision**: If JSON output is unreliable, stop and pivot strategy

### Phase 2: Integration (Do Second)
4. **Experiment 3.1**: Simple Binary Test - 20 min
5. **Experiment 3.2**: JSON Escaping Test - 15 min
6. **Experiment 2.2**: Model Quality Test - 30 min

**Go/No-Go Decision**: If binary integration fails or model quality poor, re-evaluate

### Phase 3: E2E Flow (Do Third)
7. **Experiment 4.1**: Skill Creation - 10 min
8. **Experiment 4.2**: Skill Execution - 15 min
9. **Experiment 6.1**: File Size Test - 20 min

**Go/No-Go Decision**: If end-to-end doesn't work, adjust architecture

### Phase 4: Polish (Optional)
10. **Experiment 5.1**: Subagent Test - 15 min

**Total Time**: ~2.5 hours

---

## Fallback Strategies

### If JSON Output is Unreliable:
- **Option A**: Add JSON cleanup/extraction step (regex to find JSON in text)
- **Option B**: Use structured output libraries (if Ollama supports)
- **Option C**: Add prompt refinement loop with validation

### If Model Quality is Poor:
- **Option A**: Try different models (qwen2.5-coder, deepseek-coder)
- **Option B**: Improve prompts with few-shot examples
- **Option C**: Chain multiple smaller prompts instead of one big review

### If Binary Integration Fails:
- **Option A**: Use Python script instead (might be easier for JSON)
- **Option B**: Create intermediate temp file instead of stdin/stdout
- **Option C**: Use HTTP server instead of CLI binary

### If Context Size is Too Small:
- **Option A**: Chunk large files into sections
- **Option B**: Use summarization pass before review
- **Option C**: Set hard file size limit and warn users

---

## Success Criteria for Full Implementation

All experiments must meet criteria before proceeding with:
- ✅ Ollama returns valid JSON 90%+ of time
- ✅ At least one model gives useful reviews
- ✅ Binary can receive/return JSON via stdin/stdout
- ✅ Skill can execute binary from Claude Code
- ✅ Files up to 500 lines process successfully
- ✅ End-to-end latency < 15 seconds for typical files

---

## Next Steps After Validation

1. Document results in this file
2. Update IMPLEMENTATION_PLAN.md with learnings
3. Adjust architecture based on discoveries
4. Begin Phase 1 implementation with confidence
