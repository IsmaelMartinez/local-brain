// Local Brain
// A tool for structured code review using local Ollama LLM models
//
// See IMPLEMENTATION_PLAN.md for complete specification

use anyhow::{Context, Result};
use clap::Parser;
use serde::Deserialize;
use std::collections::HashMap;
use std::path::{Path, PathBuf};
use std::process::Command;

// ============================================================================
// CLI Arguments
// ============================================================================

/// Command-line interface for local-brain
#[derive(Parser, Debug)]
#[command(name = "local-brain")]
#[command(version)]
#[command(
    about = "A tool for structured code review using local Ollama LLM models",
    long_about = r#"Local Brain: Structured Code Review with Local LLMs

Local Brain uses Ollama (https://ollama.ai) to perform structured code reviews
locally without sending code to external services. It provides Markdown output with
categorized feedback: issues found, simplifications, items to consider later,
and general observations.

MODES:
  --files          - Review specific files from a comma-separated list
  --git-diff       - Review all changed files in git (staged or unstaged)
  --dir            - Review all files in a directory matching a pattern

EXAMPLES:

  Review specific files:
    local-brain --files "src/main.rs,src/lib.rs"

  Review git changes:
    local-brain --git-diff

  Review all Rust files in src/:
    local-brain --dir src --pattern "*.rs"

  Use specific model:
    local-brain --model "deepseek-coder-v2" --files "src/main.rs"

  Use task-based model selection:
    local-brain --task "security" --files "auth.rs"

  Specify document type and review focus:
    local-brain --files "auth.rs" --kind code --review-focus security

  Dry run (validate without calling Ollama):
    local-brain --dry-run --files "src/main.rs"

For more information, visit: https://github.com/IsmaelMartinez/local-brain"#
)]
struct Cli {
    /// Explicit model name to use (e.g., "qwen2.5-coder:3b")
    #[arg(long)]
    model: Option<String>,

    /// Task type for automatic model selection (e.g., "quick-review", "documentation", "security")
    #[arg(long)]
    task: Option<String>,

    /// Review git diff (staged changes). If no files staged, reviews all changes.
    #[arg(long)]
    git_diff: bool,

    /// Review all files in a directory matching pattern
    #[arg(long)]
    dir: Option<PathBuf>,

    /// File pattern to match (e.g., "*.rs", "*.{js,ts}"). Requires --dir
    #[arg(long)]
    pattern: Option<String>,

    /// Comma-separated list of files to review (e.g., "src/main.rs,src/lib.rs")
    #[arg(long)]
    files: Option<String>,

    /// Dry run mode: validate inputs and show what would be sent to Ollama without making the call
    #[arg(long)]
    dry_run: bool,

    /// Type of document: code, design-doc, ticket, other
    #[arg(long)]
    kind: Option<String>,

    /// Review focus: refactoring, readability, performance, risk, general
    #[arg(long)]
    review_focus: Option<String>,

    /// Timeout for Ollama requests in seconds (default: 120)
    #[arg(long)]
    timeout: Option<u64>,

    /// Number of times to run the review (default: 1)
    #[arg(long, default_value_t = 1)]
    runs: usize,

    /// Enable validation mode: analyze consistency across runs
    #[arg(long)]
    validation_mode: bool,

    /// Show performance metrics for each run
    #[arg(long)]
    show_metrics: bool,
}

// ============================================================================
// Model Registry Structures
// ============================================================================

/// Information about a single model
#[derive(Debug, Deserialize, Clone)]
struct ModelInfo {
    name: String,
    size_gb: f32,
    parameters: String,
    speed: String,
}

/// Model registry loaded from models.json
#[derive(Debug, Deserialize)]
struct ModelRegistry {
    models: Vec<ModelInfo>,
    task_mappings: HashMap<String, String>,
    default_model: String,
}

/// Priority for model selection
/// Represents the different ways a model can be specified, in order of priority
#[derive(Debug, Clone)]
enum ModelPriority {
    /// Highest priority: explicit --model CLI flag
    CliFlag(String),
    /// Second priority: --task flag that maps to a model via registry
    Task(String),
    /// Third priority: MODEL_NAME environment variable (backwards compatibility)
    EnvVar(String),
    /// Lowest priority: default model from registry
    Default,
}

// ============================================================================
// Main Flow
// ============================================================================

fn main() -> Result<()> {
    // 1. Parse CLI arguments
    let cli = Cli::parse();

    // Check which mode to use
    if cli.git_diff {
        // Git diff mode: review changed files
        return handle_git_diff(&cli);
    }

    if cli.files.is_some() {
        // Files mode: review specific files
        return handle_files(&cli);
    }

    if cli.dir.is_some() {
        // Directory mode: review files in directory
        return handle_directory(&cli);
    }

    // No mode specified - error
    anyhow::bail!("Must specify one of: --files, --git-diff, or --dir");
}

// ============================================================================
// Git Diff Handling
// ============================================================================

/// Encapsulates git diff operations and parsing
struct GitDiff {
    stdout: String,
}

impl GitDiff {
    /// Execute git diff command to get changed files
    ///
    /// First tries staged files (--cached), then falls back to all modified files.
    /// Filters for added, copied, modified, and renamed files (ACMR).
    fn fetch_changed_files() -> Result<Self> {
        // Try staged files first
        let output = Command::new("git")
            .args(["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
            .output()
            .context("Failed to execute git diff --cached")?;

        let mut stdout =
            String::from_utf8(output.stdout).context("Invalid UTF-8 from git output")?;

        // If no staged files, get all modified files
        if stdout.trim().is_empty() {
            let output = Command::new("git")
                .args(["diff", "--name-only", "--diff-filter=ACMR"])
                .output()
                .context("Failed to execute git diff")?;

            stdout = String::from_utf8(output.stdout).context("Invalid UTF-8 from git output")?;
        }

        Ok(GitDiff { stdout })
    }

    /// Parse git output into list of PathBufs
    ///
    /// Filters out empty lines and trims whitespace.
    fn parse_changed_files(&self) -> Vec<PathBuf> {
        self.stdout
            .lines()
            .filter(|line| !line.trim().is_empty())
            .map(|line| PathBuf::from(line.trim()))
            .collect()
    }
}

// ============================================================================
// File Review Functions
// ============================================================================

/// Review a file with file count context for adaptive model selection
fn review_file_with_count(cli: &Cli, file_path: &PathBuf, file_count: usize) -> Result<String> {
    // 1. Select model with file count context
    let selected_model = select_model_adaptive(cli, file_count)?;

    // 2. Read file from disk
    let document = std::fs::read_to_string(file_path)
        .with_context(|| format!("Failed to read file: {:?}", file_path))?;

    // Extract filename for metadata
    let filename = file_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");

    // 3. Build Ollama prompt
    let (system_msg, user_msg) = build_prompt(
        &document,
        filename,
        cli.kind.as_deref(),
        cli.review_focus.as_deref(),
    )?;

    // 4. Dry run mode: return mock markdown output
    if cli.dry_run {
        return Ok(format!(
            "## Dry Run Information\n\n\
            - Model: {}\n\
            - File: {} ({} bytes)\n\
            - System prompt: {} chars\n\
            - User prompt: {} chars\n",
            selected_model,
            filename,
            document.len(),
            system_msg.len(),
            user_msg.len()
        ));
    }

    // 5. Call Ollama API with selected model
    let timeout_secs = cli.timeout.unwrap_or(120);
    let response = call_ollama(&system_msg, &user_msg, &selected_model, timeout_secs)?;

    // 6. Return markdown response
    Ok(response)
}

/// Multi-run review with optional validation analysis
fn review_file_multi_run(cli: &Cli, file_path: &PathBuf, file_count: usize) -> Result<String> {
    // If runs == 1, just do single review
    if cli.runs <= 1 {
        return review_file_with_count(cli, file_path, file_count);
    }

    let mut results = Vec::new();
    let mut durations = Vec::new();

    // Run review multiple times
    for run_num in 1..=cli.runs {
        eprintln!("  Run {}/{}", run_num, cli.runs);
        let start = std::time::Instant::now();

        match review_file_with_count(cli, file_path, file_count) {
            Ok(markdown) => {
                let duration = start.elapsed();
                durations.push(duration.as_secs_f64());
                results.push(markdown);
            }
            Err(e) => {
                eprintln!("  Run {} failed: {}", run_num, e);
                // Continue with other runs even if one fails
            }
        }
    }

    if results.is_empty() {
        anyhow::bail!("All validation runs failed");
    }

    // If validation mode, analyze consistency
    if cli.validation_mode {
        return format_validation_report(&results, &durations, cli.show_metrics);
    }

    // Otherwise just show all runs separated
    let mut output = String::new();
    for (i, result) in results.iter().enumerate() {
        if i > 0 {
            output.push_str("\n---\n\n");
        }
        output.push_str(&format!("## Run {}\n\n{}", i + 1, result));
    }

    Ok(output)
}

/// Format validation report from multiple runs
fn format_validation_report(
    results: &[String],
    durations: &[f64],
    show_metrics: bool,
) -> Result<String> {
    let mut output = String::new();

    output.push_str("## Validation Report\n\n");
    output.push_str(&format!("- **Total Runs**: {}\n", results.len()));
    output.push_str(&format!(
        "- **Average Duration**: {:.1}s\n",
        durations.iter().sum::<f64>() / durations.len() as f64
    ));

    if show_metrics {
        output.push_str("\n## Run Metrics\n\n");
        output.push_str("| Run | Duration | Status |\n");
        output.push_str("|-----|----------|--------|\n");
        for (i, duration) in durations.iter().enumerate() {
            output.push_str(&format!("| {} | {:.1}s | ✓ |\n", i + 1, duration));
        }
    }

    output.push_str("\n## All Runs\n\n");
    for (i, result) in results.iter().enumerate() {
        output.push_str(&format!("### Run {}\n\n{}\n\n", i + 1, result));
    }

    Ok(output)
}

/// Handle git diff mode: get changed files and review each
fn handle_git_diff(cli: &Cli) -> Result<()> {
    // Get list of changed files using GitDiff struct
    let git_diff = GitDiff::fetch_changed_files()?;
    let changed_files = git_diff.parse_changed_files();

    if changed_files.is_empty() {
        eprintln!("No changed files found");
        return Ok(());
    }

    eprintln!("Reviewing {} changed file(s)...", changed_files.len());

    // Review each file and collect markdown
    let mut markdown_sections = Vec::new();

    for file_path in &changed_files {
        eprintln!("Reviewing: {}", file_path.display());

        let file_name = file_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        // Review the file (with multi-run support and adaptive model selection)
        match review_file_multi_run(cli, file_path, changed_files.len()) {
            Ok(markdown) => {
                markdown_sections.push(format!("### {}\n\n{}", file_name, markdown));
            }
            Err(e) => {
                eprintln!("Error reviewing {}: {}", file_path.display(), e);
            }
        }
    }

    // Output aggregated markdown
    if markdown_sections.is_empty() {
        println!("# No Reviews Generated\n");
    } else {
        println!("# Git Diff Review\n");
        for section in markdown_sections {
            println!("{}\n", section);
        }
    }

    Ok(())
}

/// Handle --files mode: review comma-separated list of files
fn handle_files(cli: &Cli) -> Result<()> {
    let files_str = cli.files.as_ref().unwrap();

    let file_paths: Vec<PathBuf> = files_str
        .split(',')
        .map(|s| PathBuf::from(s.trim()))
        .collect();

    if file_paths.is_empty() {
        eprintln!("No files specified");
        return Ok(());
    }

    review_multiple_files(cli, &file_paths)
}

/// Handle --dir mode: review files in directory matching pattern
fn handle_directory(cli: &Cli) -> Result<()> {
    let dir = cli.dir.as_ref().unwrap();
    let pattern = cli.pattern.as_deref().unwrap_or("*");

    let files = collect_files_in_dir(dir, pattern)?;

    if files.is_empty() {
        eprintln!(
            "No files found matching pattern '{}' in {}",
            pattern,
            dir.display()
        );
        return Ok(());
    }

    review_multiple_files(cli, &files)
}

/// Collect files in directory matching glob pattern
fn collect_files_in_dir(dir: &PathBuf, pattern: &str) -> Result<Vec<PathBuf>> {
    use std::fs;

    let mut matching_files = Vec::new();

    // Walk directory recursively
    fn visit_dirs(dir: &PathBuf, pattern: &str, files: &mut Vec<PathBuf>) -> Result<()> {
        if dir.is_dir() {
            for entry in fs::read_dir(dir).context("Failed to read directory")? {
                let entry = entry.context("Failed to read directory entry")?;
                let path = entry.path();

                if path.is_dir() {
                    // Skip hidden directories and common ignore patterns
                    if let Some(name) = path.file_name().and_then(|n| n.to_str()) {
                        if name.starts_with('.') || name == "target" || name == "node_modules" {
                            continue;
                        }
                    }
                    visit_dirs(&path, pattern, files)?;
                } else if path.is_file() {
                    // Check if file matches pattern
                    if matches_pattern(&path, pattern) {
                        files.push(path);
                    }
                }
            }
        }
        Ok(())
    }

    visit_dirs(dir, pattern, &mut matching_files)?;
    Ok(matching_files)
}

/// Simple pattern matching for file extensions
fn matches_pattern(path: &Path, pattern: &str) -> bool {
    // Handle simple cases: *, *.rs, *.{js,ts}
    if pattern == "*" {
        return true;
    }

    let filename = path.file_name().and_then(|n| n.to_str()).unwrap_or("");

    if let Some(ext) = pattern.strip_prefix("*.") {
        // Handle *.rs
        if ext.contains(',') || ext.contains('{') {
            // Handle *.{js,ts}
            let extensions: Vec<&str> = if ext.starts_with('{') && ext.ends_with('}') {
                ext[1..ext.len() - 1].split(',').collect()
            } else {
                vec![ext]
            };

            return extensions
                .iter()
                .any(|e| filename.ends_with(&format!(".{}", e)));
        } else {
            return filename.ends_with(&format!(".{}", ext));
        }
    }

    // Default: exact match
    filename == pattern
}

/// Review multiple files and aggregate results
fn review_multiple_files(cli: &Cli, files: &[PathBuf]) -> Result<()> {
    eprintln!("Reviewing {} file(s)...", files.len());

    // Review each file and collect markdown
    let mut markdown_sections = Vec::new();

    for file_path in files {
        eprintln!("Reviewing: {}", file_path.display());

        let file_name = file_path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown");

        // Review the file (with multi-run support and adaptive model selection)
        match review_file_multi_run(cli, file_path, files.len()) {
            Ok(markdown) => {
                markdown_sections.push(format!("### {}\n\n{}", file_name, markdown));
            }
            Err(e) => {
                eprintln!("Error reviewing {}: {}", file_path.display(), e);
            }
        }
    }

    // Output aggregated markdown
    if markdown_sections.is_empty() {
        println!("# No Reviews Generated\n");
    } else {
        println!("# Code Review\n");
        for section in markdown_sections {
            println!("{}\n", section);
        }
    }

    Ok(())
}

// ============================================================================
// Model Selection
// ============================================================================

/// Select model based on priority: CLI --model > CLI --task > ENV > default
///
/// This function determines which model to use by checking in priority order:
/// 1. CLI --model flag (highest priority)
/// 2. CLI --task flag (maps to model via registry)
/// 3. MODEL_NAME environment variable (backwards compatibility)
/// 4. Default model from registry (lowest priority)
///
/// # Examples
/// ```
/// // Using CLI flag:
/// // local-brain --model "qwen2.5-coder:3b" --files "src/main.rs"
///
/// // Using task mapping:
/// // local-brain --task "quick-review" --files "src/main.rs"
/// ```
fn select_model(cli: &Cli) -> Result<String> {
    // Build ModelPriority from CLI args
    let priority = determine_model_priority(cli)?;

    // Resolve priority to actual model name
    resolve_model_priority(&priority)
}

/// Adaptive model selection based on file count
///
/// For multi-file reviews, automatically switch to faster models unless:
/// - User explicitly specified a model with --model flag
/// - The task mapping already specifies a fast model
fn select_model_adaptive(cli: &Cli, file_count: usize) -> Result<String> {
    let selected_model = select_model(cli)?;

    // Only apply adaptive logic if NOT explicitly requested via --model flag
    if cli.model.is_some() {
        // User was explicit, warn if they picked a slow model for multiple files
        if file_count > 1 {
            let registry = load_model_registry()?;
            if let Some(model_info) = registry.models.iter().find(|m| m.name == selected_model) {
                if model_info.speed == "moderate" || model_info.speed == "slow" {
                    eprintln!(
                        "⚠️  Using {} ({} speed, {} parameters, {:.1}GB) for {} files. This may be slow.",
                        selected_model, model_info.speed, model_info.parameters, model_info.size_gb, file_count
                    );
                    eprintln!(
                        "   Consider using --task quick-review for faster multi-file reviews."
                    );
                }
            }
        }
        return Ok(selected_model);
    }

    // Adaptive logic: switch to faster models for multi-file reviews
    if file_count > 1 {
        let registry = load_model_registry()?;
        if let Some(model_info) = registry.models.iter().find(|m| m.name == selected_model) {
            // If using slow/moderate model for multiple files, switch to fast model
            if (model_info.speed == "moderate" || model_info.speed == "slow") && file_count > 1 {
                eprintln!(
                    "ℹ️  Using faster model for {} files (was: {})",
                    file_count, selected_model
                );
                // Return first "fast" model from registry
                if let Some(fast_model) = registry
                    .models
                    .iter()
                    .find(|m| m.speed == "fast" || m.speed == "very-fast")
                {
                    return Ok(fast_model.name.clone());
                }
            }
        }
    }

    Ok(selected_model)
}

/// Determine model priority from CLI arguments
///
/// Checks CLI flags and environment in priority order and returns
/// the appropriate ModelPriority variant.
fn determine_model_priority(cli: &Cli) -> Result<ModelPriority> {
    // Priority 1: CLI --model flag
    if let Some(model) = &cli.model {
        return Ok(ModelPriority::CliFlag(model.clone()));
    }

    // Priority 2: CLI --task flag
    if let Some(task) = &cli.task {
        return Ok(ModelPriority::Task(task.clone()));
    }

    // Priority 3: Environment variable (backwards compatibility)
    if let Ok(model) = std::env::var("MODEL_NAME") {
        return Ok(ModelPriority::EnvVar(model));
    }

    // Priority 4: Default
    Ok(ModelPriority::Default)
}

/// Resolve ModelPriority to actual model name
///
/// For Task and Default priorities, loads the model registry.
/// For CliFlag and EnvVar, returns the model name directly.
fn resolve_model_priority(priority: &ModelPriority) -> Result<String> {
    match priority {
        ModelPriority::CliFlag(model) => Ok(model.clone()),
        ModelPriority::EnvVar(model) => Ok(model.clone()),
        ModelPriority::Task(task) => {
            let registry = load_model_registry()?;
            registry.task_mappings.get(task).cloned().ok_or_else(|| {
                anyhow::anyhow!(
                    "Unknown task type: '{}'. Available tasks: {}",
                    task,
                    registry
                        .task_mappings
                        .keys()
                        .map(|k| k.as_str())
                        .collect::<Vec<_>>()
                        .join(", ")
                )
            })
        }
        ModelPriority::Default => {
            let registry = load_model_registry()?;
            Ok(registry.default_model)
        }
    }
}

/// Load model registry from models.json
///
/// Loads the model configuration file that defines:
/// - Task mappings (task name → model name)
/// - Default model to use when no specific selection is made
///
/// # File Search Order
/// 1. Current working directory (./models.json)
/// 2. Directory containing the binary executable
///
/// # File Format
/// ```json
/// {
///   "task_mappings": {
///     "quick-review": "qwen2.5-coder:3b",
///     "security": "deepseek-coder-v2"
///   },
///   "default_model": "qwen2.5-coder:7b"
/// }
/// ```
///
/// # Returns
/// Returns a ModelRegistry struct with task mappings and default model
///
/// # Errors
/// Returns error if:
/// - models.json not found in either location
/// - File cannot be read
/// - JSON is malformed or doesn't match expected structure
fn load_model_registry() -> Result<ModelRegistry> {
    // Try to load models.json from current directory or binary directory
    let models_json = std::fs::read_to_string("models.json")
        .or_else(|_| {
            // Try in the directory of the executable
            let exe_dir = std::env::current_exe()
                .ok()
                .and_then(|p| p.parent().map(|p| p.to_path_buf()));
            if let Some(dir) = exe_dir {
                std::fs::read_to_string(dir.join("models.json"))
            } else {
                Err(std::io::Error::new(std::io::ErrorKind::NotFound, "models.json not found"))
            }
        })
        .context("Failed to read models.json. Ensure models.json exists in the current directory or next to the binary.")?;

    serde_json::from_str(&models_json).context("Failed to parse models.json")
}

// ============================================================================
// Prompt Building
// ============================================================================

/// Build system and user prompts for Ollama
///
/// Creates structured prompts that guide the LLM to produce Markdown output
/// with specific section headings for categorized feedback.
///
/// # Arguments
/// * `document` - The file content to review
/// * `filename` - Name of the file being reviewed
/// * `kind` - Document type (code, design-doc, ticket, other). Defaults to "unknown"
/// * `review_focus` - Review emphasis (refactoring, readability, performance, risk, general). Defaults to "general"
///
/// # Returns
/// Returns a tuple of (system_prompt, user_prompt) both as Strings
///
/// # Example
/// ```
/// let (system, user) = build_prompt("fn main() {}", "main.rs", Some("code"), Some("readability"))?;
/// // system contains Markdown structure instructions
/// // user contains file metadata and content
/// ```
fn build_prompt(
    document: &str,
    filename: &str,
    kind: Option<&str>,
    review_focus: Option<&str>,
) -> Result<(String, String)> {
    // System prompt explaining the Markdown structure and review categories
    let system_prompt = r#"You are a senior code and document reviewer.

You receive a document and metadata, and must produce a structured review in Markdown format.

Use the following structure with these exact headings:

## Issues Found
- **Title**: Description (lines: X-Y)
- **Title**: Description

## Simplifications
- **Title**: Description

## Consider Later
- **Title**: Description

## Other Observations
- General note
- Another observation

**Rules**:
- Each item must be SHORT and FOCUSED (1-3 sentences max)
- Do NOT repeat the entire document
- Focus on actionable insights
- Output clean Markdown with proper headings
- Use - for bullet points, **bold** for titles
- Include line numbers for issues when relevant"#;

    // User prompt with metadata and document
    let kind = kind.unwrap_or("unknown");
    let focus = review_focus.unwrap_or("general");

    let user_prompt = format!(
        r#"**File**: {filename}
**Kind**: {kind}
**Review Focus**: {focus}

**Document Content**:
{document}

Provide your structured review in Markdown format with the specified headings."#
    );

    Ok((system_prompt.to_string(), user_prompt))
}

// ============================================================================
// Ollama API Integration
// ============================================================================

/// Response from Ollama API
#[derive(Deserialize)]
struct OllamaResponse {
    message: OllamaMessage,
}

#[derive(Deserialize)]
struct OllamaMessage {
    content: String,
}

/// Call Ollama API with the given prompts
///
/// Sends a chat completion request to the local Ollama instance via HTTP POST.
/// Uses the /api/chat endpoint with a non-streaming response.
///
/// # Arguments
/// * `system_msg` - System prompt defining the LLM's role and output format
/// * `user_msg` - User prompt containing the document to review
/// * `model_name` - Name of the Ollama model to use (e.g., "qwen2.5-coder:3b")
///
/// # Environment Variables
/// * `OLLAMA_HOST` - Ollama server URL (default: "http://localhost:11434")
///
/// # Returns
/// Returns the model's response content as a String
///
/// # Errors
/// Returns error if:
/// - HTTP request fails
/// - Ollama returns non-success status
/// - Response cannot be parsed as JSON
///
/// # Example
/// ```
/// let response = call_ollama(
///     "You are a code reviewer",
///     "Review this code: fn main() {}",
///     "qwen2.5-coder:3b"
/// )?;
/// ```
fn call_ollama(
    system_msg: &str,
    user_msg: &str,
    model_name: &str,
    timeout_secs: u64,
) -> Result<String> {
    // Get Ollama configuration from environment
    let ollama_host =
        std::env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".to_string());

    // Build request body
    let request_body = serde_json::json!({
        "model": model_name,
        "messages": [
            {
                "role": "system",
                "content": system_msg
            },
            {
                "role": "user",
                "content": user_msg
            }
        ],
        "stream": false
    });

    // Make HTTP request with timeout
    let timeout_duration = std::time::Duration::from_secs(timeout_secs);
    let client = reqwest::blocking::Client::builder()
        .timeout(timeout_duration)
        .build()
        .context("Failed to build HTTP client")?;

    let response = client
        .post(format!("{}/api/chat", ollama_host))
        .json(&request_body)
        .send()
        .context("Failed to send request to Ollama. Check if Ollama is running on localhost:11434 or set OLLAMA_HOST")?;

    // Check status
    if !response.status().is_success() {
        anyhow::bail!("Ollama API returned error: {}", response.status());
    }

    // Get response text first for debugging
    let response_text = response.text().context("Failed to read Ollama response")?;

    // Validate response is not empty
    if response_text.trim().is_empty() {
        anyhow::bail!(
            "Ollama returned empty response. The model may have crashed or disconnected."
        );
    }

    // Try to parse into OllamaResponse
    let ollama_response: OllamaResponse = serde_json::from_str(&response_text).context(format!(
        "Failed to parse Ollama response. First 200 chars: {}",
        &response_text.chars().take(200).collect::<String>()
    ))?;

    // Validate the content is not empty
    if ollama_response.message.content.trim().is_empty() {
        anyhow::bail!(
            "Ollama returned empty content. The model may not have generated a response."
        );
    }

    Ok(ollama_response.message.content)
}

// ============================================================================
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_prompt() {
        let document = "fn main() { println!(\"hello\"); }";
        let filename = "test.rs";
        let kind = Some("code");
        let review_focus = Some("general");

        let (system, user) = build_prompt(document, filename, kind, review_focus).unwrap();

        assert!(system.contains("Markdown"));
        assert!(system.contains("## Issues Found"));
        assert!(user.contains("test.rs"));
        assert!(user.contains("code"));
        assert!(user.contains("general"));
    }

    #[test]
    fn test_build_prompt_with_defaults() {
        let document = "fn main() {}";
        let filename = "test.rs";

        let (system, user) = build_prompt(document, filename, None, None).unwrap();

        assert!(system.contains("Markdown"));
        assert!(user.contains("unknown")); // default kind
        assert!(user.contains("general")); // default review_focus
    }

    #[test]
    fn test_model_registry_loading() {
        // This test requires models.json to exist
        // It's more of an integration test
        if std::path::Path::new("models.json").exists() {
            let result = load_model_registry();
            assert!(result.is_ok());
        }
    }

    #[test]
    fn test_pattern_matching() {
        use std::path::PathBuf;

        // Test *.rs pattern
        assert!(matches_pattern(&PathBuf::from("test.rs"), "*.rs"));
        assert!(!matches_pattern(&PathBuf::from("test.js"), "*.rs"));

        // Test wildcard
        assert!(matches_pattern(&PathBuf::from("anything.txt"), "*"));

        // Test multiple extensions
        assert!(matches_pattern(&PathBuf::from("test.js"), "*.{js,ts}"));
        assert!(matches_pattern(&PathBuf::from("test.ts"), "*.{js,ts}"));
        assert!(!matches_pattern(&PathBuf::from("test.rs"), "*.{js,ts}"));
    }
}
