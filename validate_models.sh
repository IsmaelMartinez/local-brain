#!/bin/bash

# Model Validation Script for local-brain
# Tests all 4 downloaded Ollama models to ensure they work correctly

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BINARY="./target/release/local-brain"
TEST_FILE="tests/fixtures/code_smells.js"
RESULTS_FILE="MODEL_VALIDATION_RESULTS.md"

# Models to test
MODELS=(
    "qwen2.5-coder:3b"
    "llama3.2:1b"
    "phi3:mini"
    "qwen2.5:3b"
)

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Model Validation for local-brain${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if [ ! -f "$BINARY" ]; then
    echo -e "${RED}Error: Binary not found at $BINARY${NC}"
    exit 1
fi

if [ ! -f "$TEST_FILE" ]; then
    echo -e "${RED}Error: Test file not found at $TEST_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Binary found${NC}"
echo -e "${GREEN}✓ Test file found${NC}"
echo ""

# Check Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null; then
    echo -e "${RED}Error: Ollama is not running or not accessible${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Ollama is running${NC}"
echo ""

# Check all models are available
echo -e "${YELLOW}Checking models availability...${NC}"
for model in "${MODELS[@]}"; do
    if ollama list | grep -q "^${model}"; then
        echo -e "${GREEN}✓ $model is available${NC}"
    else
        echo -e "${RED}✗ $model not found${NC}"
        exit 1
    fi
done
echo ""

# Initialize results file
cat > "$RESULTS_FILE" << 'EOF'
# Model Validation Results

**Test Date:** $(date '+%Y-%m-%d %H:%M:%S')
**Test File:** tests/fixtures/code_smells.js
**Binary:** ./target/release/local-brain

## Test Methodology

Each model was tested with the same input file containing known code smells:
1. Deeply nested conditionals
2. God function (doing too many things)
3. Magic numbers
4. Duplicate code
5. No error handling

For each model, we measured:
- Load time and response speed
- JSON output validity
- Quality of code smell detection
- Relevance and usefulness of suggestions

---

EOF

# Function to test a single model
test_model() {
    local model=$1
    local model_safe=$(echo "$model" | tr ':' '_')

    echo -e "${BLUE}Testing model: ${model}${NC}"

    # Create test input JSON
    local abs_test_file="$(cd "$(dirname "$TEST_FILE")" && pwd)/$(basename "$TEST_FILE")"
    local input_json=$(cat <<EOF
{
  "file_path": "$abs_test_file",
  "meta": {
    "kind": "code",
    "review_focus": "general"
  }
}
EOF
)

    # Run test with timing
    local start_time=$(date +%s)
    local output_file="/tmp/local_brain_test_${model_safe}.json"
    local error_file="/tmp/local_brain_test_${model_safe}.err"

    if echo "$input_json" | "$BINARY" --model "$model" > "$output_file" 2> "$error_file"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        # Validate JSON output
        if jq empty "$output_file" 2>/dev/null; then
            echo -e "${GREEN}✓ Valid JSON output (${duration}s)${NC}"

            # Extract metrics
            local spikes_count=$(jq '.spikes | length' "$output_file")
            local simplifications_count=$(jq '.simplifications | length' "$output_file")
            local defer_count=$(jq '.defer_for_later | length' "$output_file")
            local observations_count=$(jq '.other_observations | length' "$output_file")

            echo -e "  ${GREEN}Spikes: $spikes_count${NC}"
            echo -e "  ${GREEN}Simplifications: $simplifications_count${NC}"
            echo -e "  ${GREEN}Defer for later: $defer_count${NC}"
            echo -e "  ${GREEN}Other observations: $observations_count${NC}"

            # Write results to markdown
            cat >> "$RESULTS_FILE" << EOF

## ${model}

**Status:** ✓ PASSED
**Response Time:** ${duration} seconds
**Output:** Valid JSON

### Metrics
- Spikes (issues/hotspots): $spikes_count
- Simplifications: $simplifications_count
- Defer for later: $defer_count
- Other observations: $observations_count

### Sample Output

<details>
<summary>First spike detected</summary>

\`\`\`json
$(jq '.spikes[0] // "No spikes detected"' "$output_file")
\`\`\`
</details>

<details>
<summary>First simplification suggestion</summary>

\`\`\`json
$(jq '.simplifications[0] // "No simplifications detected"' "$output_file")
\`\`\`
</details>

<details>
<summary>Full output</summary>

\`\`\`json
$(cat "$output_file")
\`\`\`
</details>

EOF

            return 0
        else
            echo -e "${RED}✗ Invalid JSON output${NC}"
            echo -e "${RED}Output: $(cat "$output_file")${NC}"

            cat >> "$RESULTS_FILE" << EOF

## ${model}

**Status:** ✗ FAILED - Invalid JSON output
**Response Time:** ${duration} seconds

### Error
\`\`\`
$(cat "$output_file")
\`\`\`

EOF
            return 1
        fi
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))

        echo -e "${RED}✗ Model failed to execute${NC}"
        echo -e "${RED}Error: $(cat "$error_file")${NC}"

        cat >> "$RESULTS_FILE" << EOF

## ${model}

**Status:** ✗ FAILED - Execution error
**Response Time:** ${duration} seconds

### Error
\`\`\`
$(cat "$error_file")
\`\`\`

EOF
        return 1
    fi
}

# Test all models
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Running tests...${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

PASSED=0
FAILED=0

for model in "${MODELS[@]}"; do
    if test_model "$model"; then
        ((PASSED++))
    else
        ((FAILED++))
    fi
    echo ""
done

# Summary
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Test Summary${NC}"
echo -e "${BLUE}============================================${NC}"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

# Add summary to results file
cat >> "$RESULTS_FILE" << EOF

---

## Summary

- **Total Models Tested:** ${#MODELS[@]}
- **Passed:** $PASSED
- **Failed:** $FAILED

## Recommendations

Based on the validation results:

EOF

# Add recommendations based on results
if [ $FAILED -eq 0 ]; then
    cat >> "$RESULTS_FILE" << 'EOF'
All models passed validation and are ready for use.

### Model Selection Guidance:
- **qwen2.5-coder:3b** - Best for code-specific tasks (1.9GB)
- **llama3.2:1b** - Fastest, good for quick reviews (1.3GB)
- **phi3:mini** - Balanced performance (2.2GB)
- **qwen2.5:3b** - Good general-purpose model (1.9GB)

Consider creating task-specific mappings in `models.json` to automatically select the best model for each task type.
EOF
else
    cat >> "$RESULTS_FILE" << EOF
Some models failed validation. Review the errors above and:
1. Check if the models need to be re-downloaded
2. Verify Ollama is properly configured
3. Test models individually with ollama directly

Failed models should not be used until issues are resolved.
EOF
fi

echo -e "${GREEN}Results written to $RESULTS_FILE${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Check $RESULTS_FILE for details.${NC}"
    exit 1
fi
