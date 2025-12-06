"""Skill loader - load and render skill definitions from YAML files."""

from pathlib import Path
from typing import Any
import yaml
from jinja2 import Template, Environment, BaseLoader


# Default skills directory (can be overridden)
SKILLS_DIR = Path(__file__).parent / "skills"


class Skill:
    """A loaded skill definition."""
    
    def __init__(self, data: dict[str, Any], path: Path | None = None):
        self.name = data.get("name", "unnamed")
        self.description = data.get("description", "")
        self.model_preference = data.get("model_preference")
        self.system_prompt = data.get("system_prompt", "")
        self.user_prompt_template = data.get("user_prompt_template", "{{ input }}")
        self.tools = data.get("tools", [])
        self.output_format = data.get("output_format", "text")
        self.path = path
        self._raw = data
    
    def render_user_prompt(self, **kwargs) -> str:
        """Render the user prompt template with given variables.
        
        Args:
            **kwargs: Variables to pass to the template
            
        Returns:
            Rendered user prompt string
        """
        template = Template(self.user_prompt_template)
        return template.render(**kwargs)
    
    def __repr__(self) -> str:
        return f"Skill(name={self.name!r}, tools={self.tools})"


def load_skill(name: str, skills_dir: Path | None = None) -> Skill:
    """Load a skill definition by name.
    
    Looks for skill.yaml in the skills directory.
    
    Args:
        name: Name of the skill (directory name under skills/)
        skills_dir: Optional custom skills directory
        
    Returns:
        Loaded Skill object
        
    Raises:
        FileNotFoundError: If skill not found
        ValueError: If skill.yaml is invalid
    """
    base_dir = skills_dir or SKILLS_DIR
    skill_path = base_dir / name / "skill.yaml"
    
    if not skill_path.exists():
        # Try without subdirectory
        skill_path = base_dir / f"{name}.yaml"
    
    if not skill_path.exists():
        available = list_skills(base_dir)
        raise FileNotFoundError(
            f"Skill '{name}' not found. Available skills: {', '.join(available) or 'none'}"
        )
    
    try:
        data = yaml.safe_load(skill_path.read_text())
        if not isinstance(data, dict):
            raise ValueError(f"Skill file must contain a YAML mapping, got {type(data)}")
        return Skill(data, skill_path)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {skill_path}: {e}")


def load_skill_from_string(yaml_content: str) -> Skill:
    """Load a skill from a YAML string.
    
    Args:
        yaml_content: YAML content as string
        
    Returns:
        Loaded Skill object
    """
    data = yaml.safe_load(yaml_content)
    if not isinstance(data, dict):
        raise ValueError(f"Skill must be a YAML mapping, got {type(data)}")
    return Skill(data)


def list_skills(skills_dir: Path | None = None) -> list[str]:
    """List available skill names.
    
    Args:
        skills_dir: Optional custom skills directory
        
    Returns:
        List of skill names
    """
    base_dir = skills_dir or SKILLS_DIR
    
    if not base_dir.exists():
        return []
    
    skills = []
    
    # Look for skill.yaml in subdirectories
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "skill.yaml").exists():
            skills.append(item.name)
        elif item.is_file() and item.suffix == ".yaml" and item.stem != "__init__":
            skills.append(item.stem)
    
    return sorted(skills)


# Built-in skills (embedded, no files needed)
BUILTIN_SKILLS = {
    "chat": Skill({
        "name": "chat",
        "description": "General chat with tool access - model decides what to do",
        "system_prompt": """You are a helpful assistant with access to tools for file operations, git commands, and shell execution.

Use the available tools to help the user with their request. You can:
- Read and write files
- List directory contents
- Check git status and diffs
- Run safe shell commands

Be helpful, concise, and use tools when they would help answer the question.""",
        "user_prompt_template": "{{ input }}",
        "tools": ["read_file", "list_directory", "write_file", "git_diff", "git_changed_files", "git_status", "run_command"],
    }),
    
    "code-review": Skill({
        "name": "code-review",
        "description": "Review code files for issues, simplifications, and improvements",
        "system_prompt": """You are a senior code reviewer. When asked to review code, you will:
1. Use tools to read the files if not provided directly
2. Analyze the code thoroughly
3. Provide structured feedback in Markdown format

Output format:
## Issues Found
- **Title**: Description (include line numbers when relevant)

## Simplifications
- **Title**: Description of how to simplify

## Consider Later
- **Title**: Non-urgent improvements to consider

## Other Observations
- General observations and positive notes

Keep feedback actionable and concise (1-3 sentences per item).""",
        "user_prompt_template": "{{ input }}",
        "tools": ["read_file", "list_directory", "git_diff", "git_changed_files"],
    }),
    
    "explain": Skill({
        "name": "explain", 
        "description": "Explain code, files, or concepts in detail",
        "system_prompt": """You are a helpful technical explainer. When asked to explain something:
1. Use tools to read files if needed
2. Provide clear, educational explanations
3. Use examples when helpful
4. Structure with headers for longer explanations

Be thorough but accessible - explain at the level appropriate for the question.""",
        "user_prompt_template": "{{ input }}",
        "tools": ["read_file", "list_directory", "file_info"],
    }),
    
    "commit-message": Skill({
        "name": "commit-message",
        "description": "Generate a git commit message from staged changes",
        "system_prompt": """You are an expert at writing git commit messages following the Conventional Commits specification.

When asked to generate a commit message:
1. Use git_diff(staged=True) to see staged changes
2. Use git_changed_files(staged=True) to see which files changed
3. Analyze the changes and generate an appropriate commit message

Format:
<type>(<scope>): <subject>

<body>

Rules:
- type: feat, fix, docs, style, refactor, test, chore, perf
- scope: optional, indicates the module/component affected
- subject: imperative mood, no period, under 50 characters
- body: optional, explain what and why (not how), wrap at 72 characters

Output ONLY the commit message, no explanations.""",
        "user_prompt_template": "Generate a commit message for the staged changes.",
        "tools": ["git_diff", "git_changed_files", "read_file"],
    }),
    
    "summarize": Skill({
        "name": "summarize",
        "description": "Summarize files, directories, or codebases",
        "system_prompt": """You are a technical summarizer. When asked to summarize:
1. Use tools to explore and read relevant files
2. Provide concise but comprehensive summaries
3. Highlight key components, patterns, and purposes

Structure summaries with:
- Overview (1-2 sentences)
- Key Components
- Notable Patterns/Decisions
- Dependencies (if relevant)""",
        "user_prompt_template": "{{ input }}",
        "tools": ["read_file", "list_directory", "file_info", "git_log"],
    }),
}


def get_builtin_skill(name: str) -> Skill | None:
    """Get a built-in skill by name.
    
    Args:
        name: Name of the built-in skill
        
    Returns:
        Skill object or None if not found
    """
    return BUILTIN_SKILLS.get(name)


def get_skill(name: str, skills_dir: Path | None = None) -> Skill:
    """Get a skill by name, checking built-ins first then files.
    
    Args:
        name: Name of the skill
        skills_dir: Optional custom skills directory
        
    Returns:
        Skill object
        
    Raises:
        FileNotFoundError: If skill not found anywhere
    """
    # Check built-ins first
    if name in BUILTIN_SKILLS:
        return BUILTIN_SKILLS[name]
    
    # Try loading from file
    return load_skill(name, skills_dir)

