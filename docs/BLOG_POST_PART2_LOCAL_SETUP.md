# Local-Only LLM Setup: Ollama + LiteLLM

**Status:** DRAFT - Pending validation of LiteLLM (AWS evaluation in progress)
**Target audience:** Developers who want 100% local/free LLM tooling
**Tone:** Practical, step-by-step, honest about limitations
**Prerequisite:** Read Part 1 first (BLOG_POST_LEARNINGS.md)

---

## From Cloud Dependency to Local Independence

*A practical guide to running Claude Code with local models — no API keys, no cloud bills, no internet required*

---

## Why Local-Only?

Part 1 explained why we deprecated local-brain in favour of LiteLLM for cost optimisation.

But some users have different constraints:

- **Privacy:** Source code never leaves your machine
- **Cost:** Literally $0 after hardware investment
- **Offline:** Works on planes, in secure environments, during outages
- **Control:** No rate limits, no API changes, no vendor lock-in

This guide covers the pure local setup: Ollama for model inference, LiteLLM for routing, Claude Code as the interface.

No cloud fallback. No API keys. Just your machine.

---

## What You'll Build

```
Claude Code (familiar interface)
     ↓
LiteLLM (routing + management)
     ↓
Ollama (local model inference)
     ↓
Your hardware (M1/M2/M3 Mac or Linux GPU)
```

**End result:** Type `claude "explain this code"` and get responses from models running entirely on your machine.

---

## Hardware Requirements

### Minimum (7B models)
- Apple M1/M2/M3 with 8GB RAM
- Or: Linux with 8GB VRAM GPU
- 15GB free disk space

### Recommended (32B models)
- Apple M1/M2/M3 with 16GB+ RAM
- Or: Linux with 16GB+ VRAM GPU
- 30GB free disk space

### Optimal (70B models)
- Apple M3 Max/Ultra with 64GB+ RAM
- Or: Linux with 48GB+ VRAM GPU
- 50GB+ free disk space

**Reality check:** Larger models = better quality but slower responses. Start small, scale up based on your patience threshold.

---

## Step 1: Install Ollama (5 minutes)

### macOS

```bash
# Download and install
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

### Linux

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows (WSL2)

```bash
# In WSL2 Ubuntu
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Ollama is running

```bash
# Should return a version number
ollama --version

# Should show empty list (no models yet)
ollama list
```

---

## Step 2: Pull Models (10-30 minutes depending on internet)

### The Essential Model (7B - works on 8GB RAM)

```bash
ollama pull qwen2.5-coder:7b
```

This is your daily driver. Fast, capable for most coding tasks, runs on minimal hardware.

### The Quality Model (32B - needs 16GB+ RAM)

```bash
ollama pull qwen2.5-coder:32b
```

Better reasoning, better code quality, but slower. Use for complex tasks.

### Optional: Specialised Models

```bash
# For general reasoning (not code-specific)
ollama pull llama3.1:8b

# For very long context (up to 128k tokens)
ollama pull qwen2.5:14b
```

### Verify Models Downloaded

```bash
ollama list
# Should show your models with sizes
```

---

## Step 3: Test Ollama Directly (2 minutes)

Before adding LiteLLM, verify Ollama works:

```bash
# Simple test
ollama run qwen2.5-coder:7b "Write a Python function to reverse a string"

# Should output working code
```

If this works, Ollama is ready. If not, troubleshoot before proceeding.

### Common Issues

**"Error: model not found"**
```bash
ollama pull qwen2.5-coder:7b  # Re-download
```

**"Error: insufficient memory"**
- Close other applications
- Use a smaller model (3b instead of 7b)
- Check Activity Monitor for memory usage

**Slow responses**
- Normal for first request (model loading)
- Subsequent requests should be faster
- 7B model: expect 20-50 tokens/second on M1

---

## Step 4: Install LiteLLM (5 minutes)

```bash
# Install with proxy support
pip install 'litellm[proxy]'

# Verify installation
litellm --version
```

### Why LiteLLM for Local-Only?

You might ask: why not just use Ollama directly?

LiteLLM adds:
- **Unified API:** Same interface whether you use Ollama, OpenAI, or Anthropic
- **Model routing:** Automatically choose between 7B and 32B based on task
- **Request logging:** Track what you're asking and how models respond
- **Future flexibility:** Easy to add cloud fallback later if needed

For pure local, these features are optional but useful.

---

## Step 5: Configure LiteLLM (10 minutes)

Create a configuration file:

```bash
mkdir -p ~/.litellm
cat > ~/.litellm/config.yaml << 'EOF'
model_list:
  # Fast model for simple tasks
  - model_name: fast
    litellm_params:
      model: ollama/qwen2.5-coder:7b
      api_base: http://localhost:11434

  # Quality model for complex tasks
  - model_name: quality
    litellm_params:
      model: ollama/qwen2.5-coder:32b
      api_base: http://localhost:11434

  # Default model (Claude Code will use this)
  - model_name: claude-sonnet-4-5-20250929
    litellm_params:
      model: ollama/qwen2.5-coder:7b
      api_base: http://localhost:11434

  # Fallback for opus requests
  - model_name: claude-opus-4-5-20251101
    litellm_params:
      model: ollama/qwen2.5-coder:32b
      api_base: http://localhost:11434

router_settings:
  routing_strategy: simple-shuffle
  num_retries: 2
  timeout: 120

general_settings:
  master_key: local-only-key
EOF
```

### Configuration Explained

The key insight: **map Claude model names to local models**.

When Claude Code asks for `claude-sonnet-4-5-20250929`, LiteLLM serves `qwen2.5-coder:7b` instead.

This is transparent to Claude Code — it thinks it's talking to Claude, but responses come from your local hardware.

---

## Step 6: Start LiteLLM Proxy (1 minute)

```bash
# Start the proxy
litellm --config ~/.litellm/config.yaml --port 4000

# Keep this terminal open, or run in background:
litellm --config ~/.litellm/config.yaml --port 4000 &
```

### Verify LiteLLM is Running

```bash
# Health check
curl http://localhost:4000/health
# Should return: {"status": "healthy"}

# Test a request
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-only-key" \
  -d '{
    "model": "fast",
    "messages": [{"role": "user", "content": "Say hello"}]
  }'
```

---

## Step 7: Connect Claude Code (2 minutes)

```bash
# Point Claude Code to LiteLLM
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=local-only-key

# Test it works
claude "Write a hello world function in Python"
```

If you see a response, congratulations — Claude Code is now running on local models.

### Make It Permanent

Add to your shell profile (`~/.zshrc` or `~/.bashrc`):

```bash
# Local LLM setup
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=local-only-key
```

Then: `source ~/.zshrc`

---

## Step 8: Create Startup Script (Optional)

For convenience, create a script to start everything:

```bash
cat > ~/start-local-llm.sh << 'EOF'
#!/bin/bash

echo "Starting Ollama..."
ollama serve &
sleep 2

echo "Starting LiteLLM..."
litellm --config ~/.litellm/config.yaml --port 4000 &
sleep 2

echo "Testing connection..."
curl -s http://localhost:4000/health

echo ""
echo "Local LLM ready. Use Claude Code normally."
echo "To stop: pkill ollama && pkill litellm"
EOF

chmod +x ~/start-local-llm.sh
```

Usage:
```bash
~/start-local-llm.sh
```

---

## Performance Expectations

### Response Times (M1 MacBook Pro, 16GB RAM)

| Model | First Token | Full Response (100 tokens) |
|-------|-------------|---------------------------|
| qwen2.5-coder:7b | 2-3 seconds | 5-10 seconds |
| qwen2.5-coder:32b | 5-8 seconds | 30-60 seconds |

### Quality Comparison

| Task Type | 7B Quality | 32B Quality | Cloud Claude |
|-----------|------------|-------------|--------------|
| Simple code generation | Good | Good | Excellent |
| Bug fixing | Acceptable | Good | Excellent |
| Code review | Limited | Acceptable | Excellent |
| Architecture decisions | Poor | Limited | Excellent |
| Documentation | Good | Good | Excellent |

**Honest assessment:** Local models are not Claude. They're good enough for many tasks, but complex reasoning and nuanced decisions still favour cloud models.

---

## Limitations (Be Honest With Yourself)

### What Works Well Locally

- Simple code generation
- Boilerplate creation
- Syntax questions
- Documentation writing
- Test scaffolding
- Straightforward refactoring

### What Struggles Locally

- Complex multi-file changes
- Architectural decisions
- Subtle bug detection
- Nuanced code review
- Tasks requiring broad context

### What Doesn't Work Locally

- Tasks requiring internet access (web search, API calls)
- Very long context (>32k tokens)
- Tasks requiring Claude-specific capabilities

---

## Switching Between Local and Cloud

### Temporary Cloud (for complex tasks)

```bash
# Unset local config
unset ANTHROPIC_BASE_URL
unset ANTHROPIC_API_KEY

# Now Claude Code uses real Claude
claude "Complex architectural question..."

# Switch back to local
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=local-only-key
```

### Shell Aliases

```bash
# Add to ~/.zshrc
alias local-llm='export ANTHROPIC_BASE_URL=http://localhost:4000 && export ANTHROPIC_API_KEY=local-only-key'
alias cloud-llm='unset ANTHROPIC_BASE_URL && unset ANTHROPIC_API_KEY'
```

Usage:
```bash
local-llm   # Switch to local
cloud-llm   # Switch to cloud Claude
```

---

## Troubleshooting

### "Connection refused" to localhost:4000

```bash
# Check if LiteLLM is running
ps aux | grep litellm

# If not, start it
litellm --config ~/.litellm/config.yaml --port 4000
```

### "Model not found" errors

```bash
# Check Ollama has the model
ollama list

# If missing, pull it
ollama pull qwen2.5-coder:7b
```

### Very slow responses

- Check Activity Monitor — is RAM maxed out?
- Use smaller model (7b instead of 32b)
- Close memory-hungry applications
- Consider hardware upgrade

### Quality is poor

- Try the 32b model for complex tasks
- Some tasks genuinely need cloud Claude
- Adjust expectations — local ≠ cloud quality

---

## Cost Analysis

### Hardware Investment (One-Time)

| Setup | Cost | Capability |
|-------|------|------------|
| M1 MacBook Air 8GB | Already own? | 7B models |
| M1 MacBook Pro 16GB | ~$1,500 used | 7B-32B models |
| M2 MacBook Pro 32GB | ~$2,500 new | 32B-70B models |
| M3 Max 64GB | ~$4,000 new | All models comfortably |

### Operating Cost

- Electricity: ~$5-10/month if running models frequently
- That's it. No API fees. Forever.

### Break-Even Analysis

If your cloud spend is $50/day ($1,500/month):
- M1 Pro 16GB pays for itself in 1 month
- M3 Max pays for itself in 3 months

After that, it's free.

---

## When to Use Local vs Cloud

### Use Local For

- Privacy-sensitive code
- High-volume simple tasks
- Offline work
- Learning and experimentation
- Tasks where "good enough" is acceptable

### Use Cloud For

- Critical production decisions
- Complex architectural work
- Tasks requiring highest quality
- When time is more valuable than money
- Tasks requiring internet access

### Hybrid Approach

Many users run local for 80% of tasks, cloud for 20%.

That's still 80% cost savings with full quality when it matters.

---

## Summary

**What you've built:**
- Ollama running local models
- LiteLLM proxying requests
- Claude Code connected to local inference

**What it costs:**
- $0/month after hardware

**What you get:**
- Privacy (code never leaves your machine)
- Speed (no network latency)
- Independence (no API keys, no vendor lock-in)

**What you trade:**
- Quality (local < cloud for complex tasks)
- Capability (no internet, limited context)
- Convenience (need to manage local services)

---

## Links

- [Ollama](https://ollama.com/)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [Ollama Model Library](https://ollama.com/library)
- [Part 1: Why We Deprecated local-brain](./BLOG_POST_LEARNINGS.md)

---

*Local models aren't a replacement for cloud. They're an option — and having options is valuable.*
