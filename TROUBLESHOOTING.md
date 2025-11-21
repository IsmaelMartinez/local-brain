# Troubleshooting Guide

This guide covers common issues and their solutions when using local-brain.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Task Flag Issues](#task-flag-issues)
- [Git Diff Mode Issues](#git-diff-mode-issues)
- [Model Selection Debugging](#model-selection-debugging)
- [Model Issues](#model-issues)
- [Performance Issues](#performance-issues)
- [Integration Issues](#integration-issues)

---

## Installation Issues

### Binary Not Found

**Error**: `bash: local-brain: command not found`

**Solution**:
```bash
# Ensure binary is compiled
cargo build --release

# Use full path or add to PATH
./target/release/local-brain

# Or add to PATH
export PATH="$PATH:$(pwd)/target/release"
```

### Build Fails

**Error**: Cargo build errors

**Solution**:
```bash
# Update Rust toolchain
rustup update

# Clean and rebuild
cargo clean
cargo build --release

# Check Rust version (requires 1.70+)
rustc --version
```

---

## Runtime Errors

### Invalid JSON Input

**Error**: `Error: Failed to parse input JSON`

**Cause**: Malformed JSON sent to stdin

**Solution**:
```bash
# Validate JSON before piping
echo '{"file_path":"/path/to/file"}' | python3 -m json.tool

# Ensure proper quoting
echo '{"file_path":"/tmp/test.rs","meta":{"kind":"code"}}' | ./target/release/local-brain
```

### File Not Found

**Error**: `Error: Failed to read file: "/path/to/file" ... No such file or directory`

**Cause**: Specified file_path doesn't exist

**Solution**:
```bash
# Verify file exists
ls -la /path/to/file

# Use absolute paths
echo '{"file_path":"'$(pwd)'/src/main.rs'"}' | ./target/release/local-brain

# Check file permissions
chmod +r /path/to/file
```

### Missing Required Field

**Error**: `Error: Failed to parse input JSON ... missing field 'file_path'`

**Cause**: Required `file_path` field not provided

**Solution**:
```bash
# Ensure file_path is included
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain

# Meta fields are optional
echo '{"file_path":"/tmp/test.rs","meta":{"kind":"code"}}' | ./target/release/local-brain
```

---

## Task Flag Issues

### Unknown Task Type

**Error**: Task type not recognized or no output

**Cause**: Invalid `--task` flag value

**Solution**:
```bash
# Check available tasks in models.json
cat models.json | jq '.task_mappings | keys'
# Shows: ["quick-review", "security", "summarize", etc.]

# Use valid task type
./target/release/local-brain --task quick-review --git-diff

# If unsure, use --model instead
./target/release/local-brain --model qwen2.5-coder:3b --git-diff
```

### How to List Available Tasks

**Question**: What tasks can I use with `--task`?

**Solution**:
```bash
# View all task mappings
cat models.json | jq '.task_mappings'

# Common tasks:
# - quick-review, syntax-check → qwen2.5-coder:3b
# - summarize, triage → llama3.2:1b
# - documentation, general-review → phi3:mini
# - requirements, prioritization, design-review → qwen2.5:3b
# - thorough-review, security, architecture → deepseek-coder-v2:16b
```

**See**: [MODELS.md](MODELS.md) for complete task documentation

---

## Git Diff Mode Issues

### No Files Found

**Error**: `Reviewing 0 changed file(s)...` or no output

**Cause**: No staged or modified files in git repository

**Solution**:
```bash
# Check git status
git status

# Check for staged files
git diff --cached --name-only

# Check for unstaged changes
git diff --name-only

# Make some changes first
echo "// test" >> src/main.rs
git add src/main.rs

# Then run git-diff mode
./target/release/local-brain --git-diff --task quick-review
```

### Permission Errors

**Error**: `Failed to read file: Permission denied`

**Cause**: Binary lacks permission to read changed files

**Solution**:
```bash
# Check file permissions
ls -la src/main.rs

# Fix permissions
chmod +r src/main.rs

# Or run with appropriate user
sudo -u youruser ./target/release/local-brain --git-diff
```

### Binary Files Included

**Issue**: Git diff includes binary files (images, compiled files)

**Behavior**: local-brain will attempt to read binary files but may produce errors

**Solution**:
```bash
# Git diff filters binary files automatically with --diff-filter=ACMR
# (Add, Copy, Modify, Rename - excludes deletions)

# To exclude specific patterns, use .gitattributes
echo "*.png binary" >> .gitattributes
echo "*.jpg binary" >> .gitattributes
echo "target/** binary" >> .gitattributes

# Or filter manually
git diff --name-only | grep -v "\.png$\|\.jpg$" | while read file; do
    echo "{\"file_path\":\"$file\"}" | ./target/release/local-brain --model qwen2.5-coder:3b
done
```

### Git Diff Shows Deleted Files

**Issue**: Reviewing deleted files that no longer exist

**Behavior**: local-brain uses `--diff-filter=ACMR` which excludes deletions (D flag)

**If still seeing issues**:
```bash
# Manually verify filtered files
git diff --cached --name-only --diff-filter=ACMR

# Or use explicit filter
git diff --name-only --diff-filter=AM  # Add + Modify only
```

---

## Model Selection Debugging

### Which Model Was Selected?

**Question**: I'm not sure which model was actually used

**Solution**:
```bash
# The binary doesn't log which model was selected (by design - clean stdout)
# But you can infer from priority rules (see MODELS.md):

# 1. CLI --model (highest priority)
./target/release/local-brain --model llama3.2:1b
# Used: llama3.2:1b

# 2. JSON ollama_model field
echo '{"file_path":"test.rs","ollama_model":"phi3:mini"}' | ./target/release/local-brain
# Used: phi3:mini

# 3. CLI --task flag
./target/release/local-brain --task quick-review
# Used: qwen2.5-coder:3b (from models.json task_mappings)

# 4. Default
./target/release/local-brain
# Used: deepseek-coder-v2:16b (from models.json default_model)

# To verify task mapping:
cat models.json | jq '.task_mappings["quick-review"]'
```

### Override Priority Not Working

**Issue**: Expected model not being used despite flags

**Debug checklist**:

1. **Check priority order** (CLI --model > JSON > --task > default):
   ```bash
   # This uses llama3.2:1b (CLI flag wins)
   ./target/release/local-brain --model llama3.2:1b --task security

   # This uses qwen2.5-coder:3b (task flag wins over default)
   ./target/release/local-brain --task quick-review
   ```

2. **Verify model name is correct**:
   ```bash
   # List available models
   ollama list

   # Use exact name from list
   ./target/release/local-brain --model qwen2.5-coder:3b  # Correct
   # NOT: qwen2.5-coder  # Wrong (missing version tag)
   ```

3. **Check models.json**:
   ```bash
   # Verify task mapping exists
   cat models.json | jq '.task_mappings'

   # Verify default model
   cat models.json | jq '.default_model'
   ```

4. **Test explicitly**:
   ```bash
   # Force specific model with CLI flag
   ./target/release/local-brain --model llama3.2:1b < input.json

   # Time it to confirm it's the fast model
   time ./target/release/local-brain --model llama3.2:1b < input.json
   # llama3.2:1b should be ~2-10s
   # deepseek-coder-v2:16b should be ~20-30s
   ```

**See**: [MODELS.md - How Model Selection Works](MODELS.md#how-model-selection-works)

---

## Model Issues

### Ollama Connection Failed

**Error**: `Error: Failed to connect to Ollama`

**Cause**: Ollama service not running or wrong host

**Solution**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
# (varies by OS - see ollama.ai docs)

# Check custom host
export OLLAMA_HOST="http://localhost:11434"
echo $OLLAMA_HOST
```

### Model Not Available

**Error**: Model not found or fails to load

**Solution**:
```bash
# List available models
ollama list

# Pull required model
ollama pull deepseek-coder-v2:16b

# Verify model name matches
# Use exact name from 'ollama list'
echo '{"file_path":"/tmp/test.rs","ollama_model":"deepseek-coder-v2:16b"}' | ./target/release/local-brain
```

### Model Returns Non-JSON

**Issue**: Model response isn't valid JSON

**Note**: local-brain includes automatic markdown fence removal (`extract_json_from_markdown` function)

**If issue persists**:
```bash
# Try different model
ollama pull qwen2.5-coder:3b
echo '{"file_path":"/tmp/test.rs","ollama_model":"qwen2.5-coder:3b"}' | ./target/release/local-brain

# Check output manually
./target/release/local-brain < input.json > output.txt
cat output.txt
```

### Out of Memory (OOM)

**Error**: System runs out of memory during model inference

**Cause**: Model too large for available RAM

**Solution**:
```bash
# Check available RAM
free -h  # Linux
vm_stat  # macOS

# Use smaller models
ollama pull qwen2.5-coder:3b  # 1.9GB
ollama pull llama3.2:1b       # 1.3GB

# Avoid models >8GB on 16GB RAM systems
# Safe models for 16GB RAM:
# - qwen2.5-coder:3b (1.9GB)
# - llama3.2:1b (1.3GB)
# - phi3:mini (2.2GB)
# - deepseek-coder-v2:16b (8.9GB) - tested working
```

---

## Performance Issues

### Slow Response Times

**Issue**: Processing takes >60 seconds

**Causes & Solutions**:

1. **Large files**:
   ```bash
   # Check file size
   wc -l /path/to/file

   # Recommended: 100-500 lines
   # Split large files or review sections separately
   ```

2. **Large model**:
   ```bash
   # Use faster models for quick reviews
   ollama pull qwen2.5-coder:3b  # Much faster
   echo '{"file_path":"/tmp/test.rs","ollama_model":"qwen2.5-coder:3b"}' | ./target/release/local-brain
   ```

3. **System resources**:
   ```bash
   # Check CPU/RAM usage
   top
   htop

   # Close other applications
   # Ensure Ollama has sufficient resources
   ```

### High Memory Usage

**Issue**: Binary or Ollama using excessive RAM

**Solutions**:
```bash
# Use smaller models (see Model Issues > Out of Memory)

# Monitor Ollama memory
ps aux | grep ollama

# Restart Ollama to clear memory
ollama serve
```

---

## Integration Issues

### Claude Code Skill Not Working

**Error**: Skill doesn't appear or fails to execute

**Solution**:
```bash
# Verify skill file exists
ls -la .claude/skills/local-brain/SKILL.md

# Check skill file has correct frontmatter
head -n 5 .claude/skills/local-brain/SKILL.md
# Should show:
# ---
# name: local-brain
# description: ...
# ---

# Ensure binary path is correct in SKILL.md
grep "target/release/local-brain" .claude/skills/local-brain/SKILL.md

# Test binary directly first
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain
```

### Subagent Can't Find Binary

**Error**: Subagent reports binary not found

**Solution**:
```bash
# Use absolute path in skill prompt
echo '{"file_path":"'$(pwd)'/src/main.rs"}' | $(pwd)/target/release/local-brain

# Or ensure working directory is project root
cd /path/to/local-brain
./target/release/local-brain
```

### Empty or Missing Output

**Issue**: Binary runs but produces no output

**Debug**:
```bash
# Check stderr for errors
./target/release/local-brain < input.json 2>&1

# Verify JSON input is valid
cat input.json | python3 -m json.tool

# Test with minimal input
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain | jq .
```

---

## Common Workflows

### Test Complete Pipeline

```bash
# 1. Create test file
echo 'fn main() { println!("test"); }' > /tmp/test.rs

# 2. Create JSON input
echo '{"file_path":"/tmp/test.rs","meta":{"kind":"code","review_focus":"general"}}' > /tmp/input.json

# 3. Run binary
cat /tmp/input.json | ./target/release/local-brain | python3 -m json.tool

# 4. Verify output has expected structure
cat /tmp/input.json | ./target/release/local-brain | jq 'keys'
# Should show: ["defer_for_later", "other_observations", "simplifications", "spikes"]
```

### Debug Model Selection

```bash
# Check available models
ollama list

# Test with specific model
echo '{"file_path":"/tmp/test.rs","ollama_model":"qwen2.5-coder:3b"}' | ./target/release/local-brain

# Test default model (from models.json)
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain

# Test with CLI flag
echo '{"file_path":"/tmp/test.rs"}' | ./target/release/local-brain --model phi3:mini
```

### Validate JSON Output

```bash
# Pretty print with jq
./target/release/local-brain < input.json | jq .

# Check specific fields
./target/release/local-brain < input.json | jq '.spikes'
./target/release/local-brain < input.json | jq '.simplifications'

# Validate schema
./target/release/local-brain < input.json | jq 'keys | sort'
# Expected: ["defer_for_later", "other_observations", "simplifications", "spikes"]
```

---

## Getting Help

If you encounter an issue not covered here:

1. **Check logs**: Look for error messages in stderr
2. **Test components separately**: Ollama → Binary → Skill
3. **Verify prerequisites**: Rust 1.70+, Ollama running, models pulled
4. **Review examples**: See README.md for working examples
5. **File an issue**: [GitHub Issues](https://github.com/IsmaelMartinez/local-brain/issues)

### Useful Debug Commands

```bash
# System info
uname -a
rustc --version
ollama --version

# Check binary
file target/release/local-brain
ls -lh target/release/local-brain

# Test Ollama
curl http://localhost:11434/api/tags
ollama list

# Environment variables
echo $OLLAMA_HOST
echo $MODEL_NAME

# Test minimal case
echo '{"file_path":"/tmp/test.rs"}' > /tmp/input.json
echo 'fn main() {}' > /tmp/test.rs
cat /tmp/input.json | ./target/release/local-brain 2>&1 | tee /tmp/output.log
```

---

## Known Limitations

1. **File size**: Best results with 100-500 line files
2. **Model quality**: Smaller models may produce less detailed reviews
3. **JSON parsing**: Model might occasionally output malformed JSON (automatic cleanup included)
4. **Documentation files**: May hallucinate for pure text docs without structure
5. **RAM constraints**: Models >8GB may not work on 16GB RAM systems

See [DOCUMENTATION_PLAN.md](internal/DOCUMENTATION_PLAN.md) for future improvements and roadmap.
