# Troubleshooting Guide

This guide covers common issues and their solutions when using local-brain.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
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

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for future improvements and roadmap.
