#!/usr/bin/env python3
"""
Spike 3: Multi-Turn Tool Execution
Goal: Handle multi-step tool calling conversations

Run: python spike_3_multi_turn.py
Prerequisites: pip install ollama
"""

import ollama
import sys
from pathlib import Path


# Define tools
def list_directory(path: str, pattern: str = "*") -> str:
    """List files in a directory matching a pattern.
    
    Args:
        path: Directory path to list
        pattern: Glob pattern to filter files (e.g., "*.py", "*.rs")
        
    Returns:
        Newline-separated list of matching file paths
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: Directory '{path}' does not exist"
        if not p.is_dir():
            return f"Error: '{path}' is not a directory"
        
        files = list(p.glob(pattern))[:10]  # Limit for safety
        if not files:
            return f"No files matching '{pattern}' found in '{path}'"
        return "\n".join(str(f) for f in files)
    except Exception as e:
        return f"Error listing directory: {e}"


def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: Path to the file to read
        
    Returns:
        The file contents (truncated to 2000 chars for safety)
    """
    try:
        content = Path(path).read_text()
        if len(content) > 2000:
            return content[:2000] + f"\n\n... (truncated, {len(content)} total chars)"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def file_info(path: str) -> str:
    """Get information about a file.
    
    Args:
        path: Path to the file
        
    Returns:
        File size and type information
    """
    try:
        p = Path(path)
        if not p.exists():
            return f"Error: File '{path}' does not exist"
        
        stat = p.stat()
        return f"File: {path}\nSize: {stat.st_size} bytes\nType: {p.suffix or 'unknown'}"
    except Exception as e:
        return f"Error getting file info: {e}"


# Tool registry
TOOLS = [list_directory, read_file, file_info]
TOOL_MAP = {
    'list_directory': list_directory,
    'read_file': read_file,
    'file_info': file_info
}


def run_multi_turn_conversation(model: str, initial_prompt: str, max_turns: int = 5):
    """Run a multi-turn conversation with tool calling."""
    
    messages = [{'role': 'user', 'content': initial_prompt}]
    turn = 0
    
    print(f"\n🎯 Initial prompt: {initial_prompt}")
    print("-" * 40)
    
    while turn < max_turns:
        turn += 1
        print(f"\n📍 Turn {turn}")
        
        # Call Ollama
        response = ollama.chat(
            model=model,
            messages=messages,
            tools=TOOLS,
        )
        
        # Get tool calls and content
        tool_calls = response.message.tool_calls
        content = response.message.content
        
        # Add assistant message to history
        assistant_msg = {
            'role': 'assistant',
            'content': content or ''
        }
        if tool_calls:
            assistant_msg['tool_calls'] = tool_calls
        messages.append(assistant_msg)
        
        # If no tool calls, we're done
        if not tool_calls:
            print(f"   📝 Final response (no tool calls)")
            return content, turn
        
        # Execute each tool call
        print(f"   📞 Tool calls: {len(tool_calls)}")
        for call in tool_calls:
            fn_name = call.function.name
            fn_args = call.function.arguments
            print(f"      → {fn_name}({fn_args})")
            
            # Execute the tool
            if fn_name in TOOL_MAP:
                result = TOOL_MAP[fn_name](**fn_args)
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"        ← {result_preview}")
            else:
                result = f"Error: Unknown function '{fn_name}'"
                print(f"        ← {result}")
            
            # Add tool result to messages
            messages.append({
                'role': 'tool',
                'name': fn_name,
                'content': result
            })
    
    # Max turns reached
    print(f"   ⚠️  Max turns ({max_turns}) reached")
    return messages[-1].get('content', ''), turn


def main():
    print("=" * 60)
    print("SPIKE 3: Multi-Turn Tool Execution")
    print("=" * 60)
    
    # Find a model that supports tool calling
    models_to_try = ['qwen3:latest', 'llama3.2:latest', 'llama3.1:8b']
    model = None
    
    for m in models_to_try:
        try:
            ollama.show(m)
            model = m
            print(f"\n✅ Using model: {model}")
            break
        except Exception:
            continue
    
    if not model:
        print("❌ No suitable model found")
        return 1
    
    # Test scenarios
    test_cases = [
        {
            "name": "List and read files",
            "prompt": "List the files in the current directory matching '*.toml' and read one of them to tell me what it's for.",
        },
        {
            "name": "Explore directory structure",
            "prompt": "What files are in the 'src' directory? Give me a brief summary of what this project does based on the files.",
        },
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print("\n" + "=" * 60)
        print(f"TEST {i}: {test['name']}")
        print("=" * 60)
        
        try:
            response, turns = run_multi_turn_conversation(
                model=model,
                initial_prompt=test['prompt'],
                max_turns=5
            )
            
            print("\n" + "-" * 40)
            print("FINAL RESPONSE:")
            print("-" * 40)
            print(response[:500] if response else "(empty)")
            
            success = turns > 1 and response and len(response) > 50
            results.append({
                'name': test['name'],
                'success': success,
                'turns': turns,
                'response_length': len(response) if response else 0
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                'name': test['name'],
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for r in results:
        status = "✅" if r['success'] else "❌"
        print(f"{status} {r['name']}")
        if 'turns' in r:
            print(f"   Turns: {r['turns']}, Response: {r.get('response_length', 0)} chars")
        if 'error' in r:
            print(f"   Error: {r['error']}")
    
    successful = sum(1 for r in results if r['success'])
    print(f"\n🎯 Successful tests: {successful}/{len(results)}")
    
    if successful == len(results):
        print("\n✅ SPIKE SUCCESS: Multi-turn tool calling works!")
        return 0
    elif successful > 0:
        print("\n⚠️  SPIKE PARTIAL: Some multi-turn scenarios work")
        return 0
    else:
        print("\n❌ SPIKE FAILED: Multi-turn tool calling not working")
        return 1


if __name__ == "__main__":
    sys.exit(main())

