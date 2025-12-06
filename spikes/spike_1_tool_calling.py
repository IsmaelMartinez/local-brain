#!/usr/bin/env python3
"""
Spike 1: Basic Tool Calling
Goal: Verify tool calling works with our target models

Run: python spike_1_tool_calling.py
Prerequisites: pip install ollama
"""

import ollama
import sys
from pathlib import Path


def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        The file contents as a string, or error message if failed
    """
    try:
        return Path(path).read_text()
    except Exception as e:
        return f"Error reading file: {e}"


def main():
    # Test files - use files that exist in the project
    test_file = "Cargo.toml"  # Should exist in the project root
    
    if not Path(test_file).exists():
        print(f"Test file '{test_file}' not found. Run from project root.")
        sys.exit(1)
    
    # Models to test - these should support native tool calling
    # Note: qwen2.5-coder outputs JSON but doesn't use Ollama's tool_calls field
    # Models with native tool calling: llama3.1, llama3.2, qwen3, mistral
    models_to_test = [
        "qwen3:latest",         # Has native tool calling support
        "llama3.2:latest",      # Has native tool calling support
        "qwen2.5-coder:latest", # May output JSON but not native tool_calls
        # "llama3.1",           # Uncomment if available
    ]
    
    print("=" * 60)
    print("SPIKE 1: Tool Calling Validation")
    print("=" * 60)
    
    results = {}
    
    for model in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing model: {model}")
        print("=" * 60)
        
        try:
            # Check if model is available
            try:
                ollama.show(model)
            except Exception:
                print(f"⚠️  Model {model} not available, skipping...")
                results[model] = "NOT_AVAILABLE"
                continue
            
            # Make the request with tool
            response = ollama.chat(
                model=model,
                messages=[{
                    'role': 'user', 
                    'content': f'Read the file "{test_file}" and tell me what package name and version it defines.'
                }],
                tools=[read_file],
            )
            
            # Check results
            tool_calls = response.message.tool_calls
            content = response.message.content
            
            print(f"\n📞 Tool calls made: {len(tool_calls) if tool_calls else 0}")
            
            if tool_calls:
                for i, call in enumerate(tool_calls):
                    print(f"   Call {i+1}: {call.function.name}({call.function.arguments})")
                
                # Execute the tool call
                for call in tool_calls:
                    if call.function.name == "read_file":
                        result = read_file(**call.function.arguments)
                        print(f"\n📄 Tool result preview (first 200 chars):")
                        print(f"   {result[:200]}...")
                
                results[model] = "TOOL_CALLED"
                print(f"\n✅ Model correctly invoked tool!")
            else:
                print(f"\n📝 Response (no tool call):")
                print(f"   {content[:300]}...")
                results[model] = "NO_TOOL_CALL"
                print(f"\n⚠️  Model did not use tool - may not support tool calling")
                
        except Exception as e:
            print(f"\n❌ Error testing {model}: {e}")
            results[model] = f"ERROR: {e}"
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for model, result in results.items():
        status = "✅" if result == "TOOL_CALLED" else "⚠️" if result == "NO_TOOL_CALL" else "❌"
        print(f"{status} {model}: {result}")
    
    # Success criteria
    tool_calling_models = [m for m, r in results.items() if r == "TOOL_CALLED"]
    print(f"\n🎯 Models with working tool calling: {len(tool_calling_models)}")
    
    if len(tool_calling_models) >= 2:
        print("✅ SPIKE SUCCESS: 2+ models support tool calling")
        return 0
    elif len(tool_calling_models) >= 1:
        print("⚠️  SPIKE PARTIAL: 1 model supports tool calling")
        return 0
    else:
        print("❌ SPIKE FAILED: No models support tool calling")
        return 1


if __name__ == "__main__":
    sys.exit(main())

