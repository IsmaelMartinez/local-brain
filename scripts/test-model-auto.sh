#!/bin/bash
set -euo pipefail

# Non-interactive Model Evaluation Test Script
# Usage: ./scripts/test-model-auto.sh [model-name]
# Example: ./scripts/test-model-auto.sh mistral-small:22b

MODEL=${1:-"qwen3:30b"}
# Use uv run if available, otherwise fall back to direct command
if command -v uv &> /dev/null; then
    LB="uv run local-brain"
else
    LB="local-brain"
fi

echo "=================================="
echo "Testing model: $MODEL"
echo "=================================="
echo ""

# Test 1.1: File Read
echo "=== Test 1.1: File Read ==="
$LB -m "$MODEL" "Read the README.md file"
echo ""
echo "---"
echo ""

# Test 2.1: Git Status
echo "=== Test 2.1: Git Status ==="
$LB -m "$MODEL" "What is the current git status?"
echo ""
echo "---"
echo ""

# Test 3.1: TODO Search
echo "=== Test 3.1: Pattern Search (TODO) ==="
$LB -m "$MODEL" "Find all TODO comments in the codebase"
echo ""
echo "---"
echo ""

# Test 4.1: Change Analysis
echo "=== Test 4.1: Multi-Step Reasoning (Changes) ==="
$LB -m "$MODEL" "What files changed recently and what do they do?"
echo ""
echo "---"
echo ""

# Test 6.1: Write Operation (Self-Awareness)
echo "=== Test 6.1: Write Operation (Should Decline) ==="
$LB -m "$MODEL" "Add a new function to cli.py"
echo ""
echo "---"
echo ""

# Test 7.2: General Knowledge (No Tools Needed)
echo "=== Test 7.2: General Knowledge (Efficiency) ==="
$LB -m "$MODEL" "What is Python?"
echo ""

echo "=================================="
echo "Test complete for: $MODEL"
echo "=================================="
