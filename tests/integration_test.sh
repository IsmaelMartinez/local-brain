#!/bin/bash
# Integration test for local-brain
# Tests that the tool correctly identifies code smells

set -e

BINARY="./target/release/local-brain"
TEST_FILE="tests/fixtures/code_smells.js"
RESULTS_FILE="/tmp/local_brain_test_results.json"

echo "========================================"
echo "Local-Brain Integration Test"
echo "========================================"
echo ""

# Check binary exists
if [ ! -f "$BINARY" ]; then
    echo "❌ Binary not found: $BINARY"
    echo "Run: cargo build --release"
    exit 1
fi

# Check test file exists
if [ ! -f "$TEST_FILE" ]; then
    echo "❌ Test file not found: $TEST_FILE"
    exit 1
fi

echo "✅ Binary: $BINARY"
echo "✅ Test file: $TEST_FILE"
echo ""

# Run local-brain on the test file
echo "Running local-brain on code with known smells..."
echo ""

echo "{\"file_path\": \"$(pwd)/$TEST_FILE\", \"meta\": {\"kind\": \"code\", \"review_focus\": \"refactoring\"}}" | \
    $BINARY > "$RESULTS_FILE" 2>&1

# Check if it succeeded
if [ $? -ne 0 ]; then
    echo "❌ local-brain execution failed"
    cat "$RESULTS_FILE"
    exit 1
fi

echo "✅ Execution successful"
echo ""

# Display results
echo "========================================"
echo "Results:"
echo "========================================"
cat "$RESULTS_FILE" | jq .
echo ""

# Parse results
SPIKES_COUNT=$(cat "$RESULTS_FILE" | jq '.spikes | length')
SIMPLIFICATIONS_COUNT=$(cat "$RESULTS_FILE" | jq '.simplifications | length')
DEFER_COUNT=$(cat "$RESULTS_FILE" | jq '.defer_for_later | length')
OBSERVATIONS_COUNT=$(cat "$RESULTS_FILE" | jq '.other_observations | length')

echo "========================================"
echo "Analysis:"
echo "========================================"
echo "Spikes (issues found): $SPIKES_COUNT"
echo "Simplifications: $SIMPLIFICATIONS_COUNT"
echo "Defer for later: $DEFER_COUNT"
echo "Other observations: $OBSERVATIONS_COUNT"
echo ""

# Expected smells in the test file:
# 1. Deeply nested conditionals (validateUser)
# 2. God function (processOrder)
# 3. Magic numbers (calculateDiscount)
# 4. Duplicate code (get* functions)
# 5. No error handling (parseUserData)

TOTAL_FINDINGS=$((SPIKES_COUNT + SIMPLIFICATIONS_COUNT + DEFER_COUNT))

echo "========================================"
echo "Validation:"
echo "========================================"

if [ $TOTAL_FINDINGS -gt 0 ]; then
    echo "✅ PASS: Found $TOTAL_FINDINGS code smell(s)"
    echo ""
    echo "Expected smells in test file:"
    echo "  1. Deeply nested conditionals (validateUser)"
    echo "  2. God function - too many responsibilities (processOrder)"
    echo "  3. Magic numbers (calculateDiscount)"
    echo "  4. Duplicate code (getUserBy* functions)"
    echo "  5. Missing error handling (parseUserData)"
    echo ""
    echo "Model detected issues successfully!"
    exit 0
else
    echo "⚠️  WARNING: No issues detected"
    echo "Expected to find at least one code smell"
    echo "This may indicate:"
    echo "  - Model is not sensitive enough"
    echo "  - Prompt needs adjustment"
    echo "  - Ollama API issue"
    exit 1
fi
