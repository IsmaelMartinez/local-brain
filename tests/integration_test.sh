#!/bin/bash
# Integration test for local-brain
# Tests that the tool correctly identifies code smells

set -e

BINARY="./target/release/local-brain"
TEST_FILE="tests/fixtures/code_smells.js"
RESULTS_FILE="/tmp/local_brain_test_results.md"

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

$BINARY --files "$TEST_FILE" --kind code --review-focus refactoring > "$RESULTS_FILE" 2>&1

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
cat "$RESULTS_FILE"
echo ""

# Parse results (check for markdown sections)
ISSUES_COUNT=$(grep -c "^## Issues Found" "$RESULTS_FILE" || echo "0")
SIMPLIFICATIONS_COUNT=$(grep -c "^## Simplifications" "$RESULTS_FILE" || echo "0")
LATER_COUNT=$(grep -c "^## Consider Later" "$RESULTS_FILE" || echo "0")
OBSERVATIONS_COUNT=$(grep -c "^## Other Observations" "$RESULTS_FILE" || echo "0")

# Count actual findings (lines starting with - or * under sections)
TOTAL_FINDINGS=$(grep -cE "^[*-] " "$RESULTS_FILE" || echo "0")

echo "========================================"
echo "Analysis:"
echo "========================================"
echo "Markdown sections found:"
echo "  Issues Found: $ISSUES_COUNT"
echo "  Simplifications: $SIMPLIFICATIONS_COUNT"
echo "  Consider Later: $LATER_COUNT"
echo "  Other Observations: $OBSERVATIONS_COUNT"
echo ""
echo "Total findings (bullet points): $TOTAL_FINDINGS"
echo ""

# Expected smells in the test file:
# 1. Deeply nested conditionals (validateUser)
# 2. God function (processOrder)
# 3. Magic numbers (calculateDiscount)
# 4. Duplicate code (get* functions)
# 5. No error handling (parseUserData)

echo "========================================"
echo "Validation:"
echo "========================================"

if [ $TOTAL_FINDINGS -gt 0 ]; then
    echo "✅ PASS: Found $TOTAL_FINDINGS issue(s) in markdown output"
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
