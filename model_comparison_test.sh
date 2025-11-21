#!/bin/bash

# Model Comparison Test Script
# Tests different Ollama models on the same file to compare performance

TEST_FILE="src/main.rs"
BINARY="./target/release/local-brain"
MODELS=("qwen2.5-coder:3b" "llama3.2:1b" "phi3:mini" "qwen2.5:3b" "deepseek-coder-v2-8k:latest")

echo "=== Model Comparison Test ==="
echo "Test file: $TEST_FILE"
echo "File size: $(wc -l < $TEST_FILE) lines"
echo ""

for MODEL in "${MODELS[@]}"; do
    echo "----------------------------------------"
    echo "Testing model: $MODEL"
    echo "Model size: $(ollama list | grep "$MODEL" | awk '{print $3, $4}')"
    echo ""

    # Create temp input with model override
    TEMP_INPUT=$(mktemp)
    cat > "$TEMP_INPUT" <<EOF
{
  "file_path": "$TEST_FILE",
  "ollama_model": "$MODEL"
}
EOF

    # Measure execution time
    START=$(date +%s)
    RESULT=$(cat "$TEMP_INPUT" | $BINARY 2>&1)
    END=$(date +%s)
    DURATION=$((END - START))

    # Check if successful
    if echo "$RESULT" | jq -e '.spikes' > /dev/null 2>&1; then
        SPIKE_COUNT=$(echo "$RESULT" | jq '.spikes | length')
        SIMPLIFICATION_COUNT=$(echo "$RESULT" | jq '.simplifications | length')
        DEFER_COUNT=$(echo "$RESULT" | jq '.defer_for_later | length')
        OBSERVATION_COUNT=$(echo "$RESULT" | jq '.observations | length')
        TOTAL_FINDINGS=$((SPIKE_COUNT + SIMPLIFICATION_COUNT + DEFER_COUNT + OBSERVATION_COUNT))

        echo "✅ Success"
        echo "Duration: ${DURATION}s"
        echo "Findings: $TOTAL_FINDINGS ($SPIKE_COUNT spikes, $SIMPLIFICATION_COUNT simplifications, $DEFER_COUNT deferred, $OBSERVATION_COUNT observations)"
    else
        echo "❌ Failed"
        echo "Duration: ${DURATION}s"
        echo "Error: $(echo "$RESULT" | head -n 5)"
    fi

    rm "$TEMP_INPUT"
    echo ""
done

echo "========================================"
echo "Test complete"
