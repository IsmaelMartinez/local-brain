"""Agent - the core loop that handles tool calling conversations."""

from typing import Any

import ollama

from .tools import TOOL_REGISTRY


def run_agent(
    prompt: str,
    system: str = "You are a helpful assistant.",
    model: str = "qwen3:latest",
    tools: list | None = None,
    max_turns: int = 10,
    verbose: bool = False,
) -> str:
    """Run a conversation with tool calling.

    Args:
        prompt: User's request
        system: System prompt
        model: Ollama model name
        tools: List of tool functions (None = no tools)
        max_turns: Safety limit for conversation turns
        verbose: Print tool calls as they happen

    Returns:
        The model's final response
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    if verbose:
        print(f"🤖 Model: {model}")
        print(f"🔧 Tools: {len(tools) if tools else 0}")
        print("-" * 40)

    for turn in range(max_turns):
        if verbose:
            print(f"\n📍 Turn {turn + 1}")

        try:
            response = ollama.chat(model=model, messages=messages, tools=tools)
        except Exception as e:
            return f"Error: {e}"

        content = response.message.content or ""
        tool_calls = response.message.tool_calls

        # Add assistant message
        msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            msg["tool_calls"] = tool_calls
        messages.append(msg)

        # No tool calls = done
        if not tool_calls:
            if verbose:
                print(f"   ✅ Done ({len(content)} chars)")
            return content

        # Execute tools
        if verbose:
            print(f"   📞 {len(tool_calls)} tool call(s)")

        for call in tool_calls:
            name = call.function.name
            args = call.function.arguments

            if verbose:
                args_str = ", ".join(f"{k}={v!r}" for k, v in args.items())
                print(f"      → {name}({args_str})")

            # Execute
            tool_fn = TOOL_REGISTRY.get(name)
            if tool_fn:
                try:
                    result = tool_fn(**args)
                except Exception as e:
                    result = f"Error: {e}"
            else:
                result = f"Unknown tool: {name}"

            if verbose:
                preview = result[:80] + "..." if len(result) > 80 else result
                print(f"        ← {preview}")

            messages.append({"role": "tool", "name": name, "content": result})

    return content or "Max turns reached."
