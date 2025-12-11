#!/bin/bash

# Model Evaluation Test Script
# Usage: ./scripts/test-model.sh [model-name]
# Example: ./scripts/test-model.sh qwen2.5-coder:7b

MODEL=${1:-"qwen3:latest"}
echo "=================================="
echo "Testing model: $MODEL"
echo "=================================="
echo ""

# Test 1.1: File Read
echo "=== Test 1.1: File Read ==="
echo "Command: local-brain -m '$MODEL' 'Read the README.md file'"
local-brain -m "$MODEL" "Read the README.md file"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,1.1,File Read,$score,$(date)" >> test-results.csv

# Test 2.1: Git Status
echo "=== Test 2.1: Git Status ==="
echo "Command: local-brain -m '$MODEL' 'What is the current git status?'"
local-brain -m "$MODEL" "What is the current git status?"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,2.1,Git Status,$score,$(date)" >> test-results.csv

# Test 3.1: TODO Search
echo "=== Test 3.1: Pattern Search (TODO) ==="
echo "Command: local-brain -m '$MODEL' 'Find all TODO comments in the codebase'"
local-brain -m "$MODEL" "Find all TODO comments in the codebase"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,3.1,Pattern Search,$score,$(date)" >> test-results.csv

# Test 4.1: Change Analysis
echo "=== Test 4.1: Multi-Step Reasoning (Changes) ==="
echo "Command: local-brain -m '$MODEL' 'What files changed recently and what do they do?'"
local-brain -m "$MODEL" "What files changed recently and what do they do?"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,4.1,Change Analysis,$score,$(date)" >> test-results.csv

# Test 6.1: Write Operation (Self-Awareness)
echo "=== Test 6.1: Write Operation (Should Decline) ==="
echo "Command: local-brain -m '$MODEL' 'Add a new function to cli.py'"
local-brain -m "$MODEL" "Add a new function to cli.py"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,6.1,Write Op Decline,$score,$(date)" >> test-results.csv

# Test 7.2: General Knowledge (No Tools Needed)
echo "=== Test 7.2: General Knowledge (Efficiency) ==="
echo "Command: local-brain -m '$MODEL' 'What is Python?'"
local-brain -m "$MODEL" "What is Python?"
echo ""
read -p "Score (0-5): " score
echo "$MODEL,7.2,Efficiency,$score,$(date)" >> test-results.csv

echo ""
echo "=================================="
echo "Quick test complete!"
echo "Results saved to test-results.csv"
echo ""
echo "For comprehensive evaluation, see:"
echo "docs/model-evaluation-checklist.md"
echo "=================================="
