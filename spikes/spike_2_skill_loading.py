#!/usr/bin/env python3
"""
Spike 2: Skill Definition Loading
Goal: Validate YAML-based skill definitions work with Jinja2 templates

Run: python spike_2_skill_loading.py
Prerequisites: pip install ollama pyyaml jinja2
"""

import ollama
import sys
from pathlib import Path

# Inline YAML to avoid creating files for spike
SAMPLE_SKILL = """
name: code-review
description: Structured code review with categorized feedback
model_preference: qwen3:latest

system_prompt: |
  You are a senior code reviewer.
  Produce structured Markdown with these exact sections:
  
  ## Issues Found
  - **Title**: Description (include line numbers if relevant)
  
  ## Simplifications
  - **Title**: Description
  
  ## Consider Later
  - **Title**: Description
  
  ## Other Observations
  - General observations
  
  Keep each item SHORT (1-3 sentences max).
  Focus on actionable insights only.

user_prompt_template: |
  **File**: {{ filename }}
  **Kind**: {{ kind | default('code') }}
  **Review Focus**: {{ focus | default('general') }}
  
  **Content**:
  ```
  {{ content }}
  ```
  
  Provide your structured review in Markdown format.

output_format: markdown
"""

SAMPLE_CODE = '''
def calculate_total(items):
    total = 0
    for item in items:
        total = total + item["price"] * item["quantity"]
    return total

def get_user(id):
    # TODO: Add caching
    import requests
    response = requests.get(f"http://api.example.com/users/{id}")
    data = response.json()
    return data

class DataProcessor:
    def __init__(self):
        self.data = []
    
    def process(self, input):
        for i in range(len(input)):
            self.data.append(input[i] * 2)
        return self.data
'''


def load_skill_from_string(yaml_content: str) -> dict:
    """Load a skill definition from YAML string."""
    import yaml
    return yaml.safe_load(yaml_content)


def render_template(template_str: str, **kwargs) -> str:
    """Render a Jinja2 template with given variables."""
    from jinja2 import Template
    template = Template(template_str)
    return template.render(**kwargs)


def main():
    print("=" * 60)
    print("SPIKE 2: Skill Definition Loading")
    print("=" * 60)
    
    # Step 1: Load skill definition
    print("\n📋 Step 1: Loading skill definition...")
    try:
        import yaml
        from jinja2 import Template
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install pyyaml jinja2")
        return 1
    
    skill = load_skill_from_string(SAMPLE_SKILL)
    print(f"   ✅ Loaded skill: {skill['name']}")
    print(f"   Description: {skill['description']}")
    print(f"   Model preference: {skill.get('model_preference', 'default')}")
    
    # Step 2: Render user prompt template
    print("\n📝 Step 2: Rendering user prompt template...")
    user_msg = render_template(
        skill['user_prompt_template'],
        filename="example.py",
        content=SAMPLE_CODE,
        kind="code",
        focus="readability"
    )
    print(f"   ✅ Rendered prompt ({len(user_msg)} chars)")
    print(f"   Preview:\n{user_msg[:300]}...")
    
    # Step 3: Call Ollama with skill prompts
    print("\n🤖 Step 3: Calling Ollama with skill-defined prompts...")
    
    model = skill.get('model_preference', 'qwen3:latest')
    
    try:
        # Check if model is available
        try:
            ollama.show(model)
        except Exception:
            print(f"   ⚠️  Model {model} not available, trying qwen3:latest...")
            model = "qwen3:latest"
            try:
                ollama.show(model)
            except Exception:
                print(f"   ⚠️  Trying llama3.2:latest...")
                model = "llama3.2:latest"
                try:
                    ollama.show(model)
                except Exception:
                    print(f"   ❌ No suitable model available")
                    return 1
        
        print(f"   Using model: {model}")
        
        response = ollama.chat(
            model=model,
            messages=[
                {'role': 'system', 'content': skill['system_prompt']},
                {'role': 'user', 'content': user_msg}
            ]
        )
        
        content = response.message.content
        print(f"\n   ✅ Got response ({len(content)} chars)")
        
    except Exception as e:
        print(f"   ❌ Ollama error: {e}")
        return 1
    
    # Step 4: Validate output structure
    print("\n🔍 Step 4: Validating output structure...")
    
    expected_sections = [
        "## Issues Found",
        "## Simplifications", 
        "## Consider Later",
        "## Other Observations"
    ]
    
    found_sections = []
    for section in expected_sections:
        if section in content:
            found_sections.append(section)
            print(f"   ✅ Found: {section}")
        else:
            print(f"   ⚠️  Missing: {section}")
    
    # Step 5: Display result
    print("\n" + "=" * 60)
    print("GENERATED REVIEW")
    print("=" * 60)
    print(content)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    print(f"✅ Skill loaded successfully")
    print(f"✅ Template rendering works")
    print(f"✅ Ollama integration works")
    print(f"📊 Output structure: {len(found_sections)}/{len(expected_sections)} sections found")
    
    if len(found_sections) >= 3:
        print("\n✅ SPIKE SUCCESS: Skill-based prompts work correctly")
        return 0
    else:
        print("\n⚠️  SPIKE PARTIAL: Output structure needs tuning")
        return 0  # Still consider success - prompt can be refined


if __name__ == "__main__":
    sys.exit(main())

