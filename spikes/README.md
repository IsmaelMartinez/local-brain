# Python Migration Spikes

Evaluation spikes for migrating local-brain from Rust to Python using the `ollama-python` library.

## Prerequisites

1. **Ollama running locally** with at least one model:
   ```bash
   ollama ps  # Check if Ollama is running
   ollama pull qwen2.5-coder:3b  # Pull a model
   ```

2. **Python 3.10+** installed

3. **Install spike dependencies:**
   ```bash
   cd spikes
   pip install -r requirements.txt
   ```

## Running the Spikes

Run from the project root directory:

```bash
# Spike 1: Validate tool calling works with target models
python spikes/spike_1_tool_calling.py

# Spike 2: Validate skill definition loading with YAML/Jinja2
python spikes/spike_2_skill_loading.py

# Spike 3: Test multi-turn tool execution
python spikes/spike_3_multi_turn.py

# Spike 4: Measure performance (Python vs Rust)
python spikes/spike_4_performance.py

# Spike 5: Read the distribution evaluation (no script)
cat spikes/spike_5_distribution.md
```

## Quick Run All

```bash
# Run all spikes in sequence
for spike in spikes/spike_*.py; do
    echo "Running $spike..."
    python "$spike"
    echo ""
done
```

## Success Criteria

| Spike | Success | Partial | Fail |
|-------|---------|---------|------|
| 1 - Tool Calling | 2+ models work | 1 model works | None work |
| 2 - Skill Loading | All sections appear | 3+ sections | Errors |
| 3 - Multi-Turn | All tests pass | Some pass | None pass |
| 4 - Performance | Startup <1s | Startup <3s | Startup >3s |
| 5 - Distribution | Clear path | Some issues | No viable path |

## Expected Results

Based on research, we expect:
- ✅ Spike 1: qwen2.5-coder and llama3.2 support tool calling
- ✅ Spike 2: YAML/Jinja2 is well-tested, should work
- ⚠️ Spike 3: May need prompt tuning for reliable multi-turn
- ✅ Spike 4: Python startup ~500ms, acceptable
- ✅ Spike 5: pipx is recommended path

## After Spikes

See [../internal/PYTHON_MIGRATION_INVESTIGATION.md](../internal/PYTHON_MIGRATION_INVESTIGATION.md) for:
- Full analysis and architecture proposal
- Migration phases
- Decision criteria
- Risk assessment

