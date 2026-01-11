#!/usr/bin/env python3
"""Spike: PromptTemplates Investigation

Findings:
=========

1. **Simple Solution: `instructions` parameter**

   CodeAgent (and all MultiStepAgent subclasses) accept an `instructions`
   parameter that gets inserted into the system prompt via the
   `{{custom_instructions}}` Jinja2 variable.

   This is the simplest way to add model-specific guidance without needing
   to construct a complex PromptTemplates object.

2. **PromptTemplates Structure**

   The full PromptTemplates TypedDict has these keys:
   - system_prompt: str
   - planning: PlanningPromptTemplate (initial_plan, update_plan_pre_messages, update_plan_post_messages)
   - managed_agent: ManagedAgentPromptTemplate (task, report)
   - final_answer: FinalAnswerPromptTemplate (pre_messages, post_messages)

   Templates are loaded from YAML files:
   - code_agent.yaml (for CodeAgent)
   - toolcalling_agent.yaml (for ToolCallingAgent)
   - structured_code_agent.yaml (for structured outputs)

3. **System Prompt Variables**

   The code_agent.yaml system prompt uses these Jinja2 variables:
   - {{tools}} - tool definitions
   - {{managed_agents}} - managed agent definitions
   - {{authorized_imports}} - list of allowed imports
   - {{custom_instructions}} - from `instructions` param
   - {{code_block_opening_tag}} - e.g., "```python"
   - {{code_block_closing_tag}} - e.g., "```"

Recommendation:
===============

For model-specific guidance in local-brain, use the `instructions` parameter:

```python
# Example navigation guidance for qwen3:30b
NAVIGATION_GUIDANCE = '''
When exploring a codebase:
1. Use list_directory(path=".", pattern="**/*") to discover the FULL structure first
2. Use read_file() with the COMPLETE path from list_directory results
3. For nested projects, always check for common structures: src/, lib/, app/
'''

# Example tool-only guidance for qwen3-coder
TOOL_ONLY_GUIDANCE = '''
IMPORTANT: You are an AI agent with pre-defined tools. Do NOT use Python imports
like os, pathlib, or subprocess. Use ONLY the provided tools:
- list_directory() for listing files
- read_file() for reading files
- search_code() for searching
'''

agent = CodeAgent(
    tools=ALL_TOOLS,
    model=model,
    instructions=NAVIGATION_GUIDANCE,  # <-- Simple!
)
```

This is MUCH simpler than constructing PromptTemplates and achieves the same goal.
"""

# Test the instructions parameter
if __name__ == "__main__":
    from smolagents import CodeAgent, LiteLLMModel

    model = LiteLLMModel(
        model_id="ollama_chat/qwen3:latest",
        api_base="http://localhost:11434",
        num_ctx=8192,
    )

    custom_instructions = """
    When exploring a codebase:
    1. ALWAYS start with list_directory(path=".", pattern="**/*") to see the full structure
    2. Use the COMPLETE path from results when calling read_file()
    """

    agent = CodeAgent(
        tools=[],  # No tools for this test
        model=model,
        instructions=custom_instructions,
    )

    # Print the system prompt to verify instructions are included
    print("System prompt contains custom instructions:")
    print("-" * 60)
    if "ALWAYS start with list_directory" in agent.system_prompt:
        print("SUCCESS: Custom instructions found in system prompt")
    else:
        print("FAILED: Custom instructions NOT found")
    print("-" * 60)
    print(agent.system_prompt[-500:])  # Last 500 chars
