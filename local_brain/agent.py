"""Agent - the core loop that handles tool calling conversations."""

import ollama
from typing import Any

from .skill_loader import Skill
from .tools import TOOL_REGISTRY, get_tools


def run_agent(
    skill: Skill,
    user_input: str,
    model: str | None = None,
    max_turns: int = 10,
    verbose: bool = False,
) -> str:
    """Run the agent with a skill and user input.
    
    The agent will:
    1. Send the user input to the model with the skill's system prompt
    2. If the model requests tool calls, execute them
    3. Continue the conversation until the model provides a final response
    
    Args:
        skill: The skill to use (defines system prompt and available tools)
        user_input: The user's request
        model: Model to use (overrides skill preference)
        max_turns: Maximum conversation turns (safety limit)
        verbose: If True, print tool calls and intermediate steps
        
    Returns:
        The model's final response
    """
    # Determine model
    model_name = model or skill.model_preference or "qwen3:latest"
    
    # Get tools for this skill
    tools = get_tools(skill.tools) if skill.tools else None
    
    # Render user prompt
    user_prompt = skill.render_user_prompt(input=user_input)
    
    # Initialize conversation
    messages = [
        {"role": "system", "content": skill.system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    
    if verbose:
        print(f"🤖 Using model: {model_name}")
        print(f"🔧 Tools: {skill.tools or 'none'}")
        print(f"📝 Skill: {skill.name}")
        print("-" * 40)
    
    # Conversation loop
    turn = 0
    while turn < max_turns:
        turn += 1
        
        if verbose:
            print(f"\n📍 Turn {turn}")
        
        # Call Ollama
        try:
            response = ollama.chat(
                model=model_name,
                messages=messages,
                tools=tools,
            )
        except ollama.ResponseError as e:
            return f"Error calling Ollama: {e}"
        except Exception as e:
            return f"Error: {e}"
        
        # Get response content and tool calls
        content = response.message.content or ""
        tool_calls = response.message.tool_calls
        
        # Add assistant message to history
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_msg["tool_calls"] = tool_calls
        messages.append(assistant_msg)
        
        # If no tool calls, we're done
        if not tool_calls:
            if verbose:
                print(f"   ✅ Final response ({len(content)} chars)")
            return content
        
        # Execute tool calls
        if verbose:
            print(f"   📞 Tool calls: {len(tool_calls)}")
        
        for call in tool_calls:
            fn_name = call.function.name
            fn_args = call.function.arguments
            
            if verbose:
                args_str = ", ".join(f"{k}={v!r}" for k, v in fn_args.items())
                print(f"      → {fn_name}({args_str})")
            
            # Execute the tool
            if fn_name in TOOL_REGISTRY:
                try:
                    result = TOOL_REGISTRY[fn_name](**fn_args)
                except Exception as e:
                    result = f"Error executing {fn_name}: {e}"
            else:
                result = f"Error: Unknown tool '{fn_name}'"
            
            if verbose:
                result_preview = result[:100] + "..." if len(result) > 100 else result
                print(f"        ← {result_preview}")
            
            # Add tool result to messages
            messages.append({
                "role": "tool",
                "name": fn_name,
                "content": result,
            })
    
    # Max turns reached
    if verbose:
        print(f"   ⚠️ Max turns ({max_turns}) reached")
    
    # Return last content or summary
    return content if content else "Agent reached maximum turns without final response."


def chat(
    message: str,
    model: str = "qwen3:latest",
    tools: list[str] | None = None,
    system: str | None = None,
    verbose: bool = False,
) -> str:
    """Simple chat function with optional tools.
    
    For quick interactions without defining a skill.
    
    Args:
        message: The message to send
        model: Model to use
        tools: List of tool names to enable (None = no tools)
        system: Optional system prompt
        verbose: If True, print intermediate steps
        
    Returns:
        The model's response
    """
    from .skill_loader import Skill
    
    skill = Skill({
        "name": "quick-chat",
        "system_prompt": system or "You are a helpful assistant.",
        "user_prompt_template": "{{ input }}",
        "tools": tools or [],
    })
    
    return run_agent(skill, message, model=model, verbose=verbose)

