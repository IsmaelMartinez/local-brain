// Local Brain
// A tool for structured code review using local Ollama LLM models
//
// See IMPLEMENTATION_PLAN.md for complete specification

use anyhow::{Context, Result};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::io::{self, Read};
use std::path::PathBuf;
use std::process::Command;

// ============================================================================
// CLI Arguments
// ============================================================================

/// Command-line interface for local-brain
#[derive(Parser, Debug)]
#[command(name = "local-brain")]
#[command(about = "A tool for structured code review using local Ollama LLM models", long_about = None)]
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
}

// ============================================================================
// Model Registry Structures
// ============================================================================

/// Model registry loaded from models.json
#[derive(Debug, Deserialize)]
struct ModelRegistry {
    task_mappings: HashMap<String, String>,
    default_model: String,
}

// ============================================================================
// Data Structures
// ============================================================================

/// Metadata about the file being reviewed
#[derive(Debug, Deserialize)]
struct Meta {
    /// Type of document: code, design-doc, ticket, other
    kind: Option<String>,
    /// Review focus: refactoring, readability, performance, risk, general
    review_focus: Option<String>,
}

/// Input payload received via stdin
#[derive(Debug, Deserialize)]
struct InputPayload {
    /// Absolute path to the file to review
    file_path: PathBuf,
    /// Optional metadata
    meta: Option<Meta>,
    /// Optional model override from JSON input
    ollama_model: Option<String>,
}

/// A single review item with title, summary, and optional line range
#[derive(Debug, Serialize, Deserialize)]
struct ReviewItem {
    title: String,
    summary: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    lines: Option<String>,
}

/// Output payload sent to stdout
#[derive(Debug, Serialize, Deserialize)]
struct OutputPayload {
    /// Hotspots, areas to investigate, potential issues
    spikes: Vec<ReviewItem>,
    /// Areas that could be simplified or optimized
    simplifications: Vec<ReviewItem>,
    /// Low-priority items for future iterations
    defer_for_later: Vec<ReviewItem>,
    /// General notes and observations
    other_observations: Vec<String>,
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

    // Normal mode: read from stdin
    // 2. Read stdin into a string
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .context("Failed to read from stdin")?;

    // 3. Deserialize to InputPayload
    let payload: InputPayload =
        serde_json::from_str(&input).context("Failed to parse input JSON")?;

    // 4. Review the file and output result
    let output = review_file(&cli, &payload)?;

    // 5. Serialize to stdout
    serde_json::to_writer(io::stdout(), &output).context("Failed to write output JSON")?;

    Ok(())
}

/// Review a single file based on InputPayload
fn review_file(cli: &Cli, payload: &InputPayload) -> Result<OutputPayload> {
    // 1. Select model
    let selected_model = select_model(cli, payload)?;

    // 2. Read file from disk
    let document = std::fs::read_to_string(&payload.file_path)
        .with_context(|| format!("Failed to read file: {:?}", payload.file_path))?;

    // Extract filename for metadata
    let filename = payload
        .file_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");

    // 3. Build Ollama prompt
    let (system_msg, user_msg) = build_prompt(&document, filename, &payload.meta)?;

    // 4. Call Ollama API with selected model
    let response = call_ollama(&system_msg, &user_msg, &selected_model)?;

    // 5. Parse response into OutputPayload
    parse_ollama_response(&response)
}

/// Handle git diff mode: get changed files and review each
fn handle_git_diff(cli: &Cli) -> Result<()> {
    // Get list of changed files
    let changed_files = get_git_changed_files()?;

    if changed_files.is_empty() {
        eprintln!("No changed files found");
        return Ok(());
    }

    eprintln!("Reviewing {} changed file(s)...", changed_files.len());

    // Review each file
    let mut all_spikes = Vec::new();
    let mut all_simplifications = Vec::new();
    let mut all_defer = Vec::new();
    let mut all_observations = Vec::new();

    for file_path in &changed_files {
        eprintln!("Reviewing: {}", file_path.display());

        // Create payload for this file
        let payload = InputPayload {
            file_path: file_path.clone(),
            meta: Some(Meta {
                kind: Some("code".to_string()),
                review_focus: Some("general".to_string()),
            }),
            ollama_model: None,
        };

        // Review the file
        match review_file(cli, &payload) {
            Ok(output) => {
                // Add file context to each item
                let file_name = file_path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown");

                for mut spike in output.spikes {
                    spike.title = format!("[{}] {}", file_name, spike.title);
                    all_spikes.push(spike);
                }

                for mut simp in output.simplifications {
                    simp.title = format!("[{}] {}", file_name, simp.title);
                    all_simplifications.push(simp);
                }

                for mut defer in output.defer_for_later {
                    defer.title = format!("[{}] {}", file_name, defer.title);
                    all_defer.push(defer);
                }

                for obs in output.other_observations {
                    all_observations.push(format!("[{}] {}", file_name, obs));
                }
            }
            Err(e) => {
                eprintln!("Error reviewing {}: {}", file_path.display(), e);
            }
        }
    }

    // Aggregate and output results
    let aggregated = OutputPayload {
        spikes: all_spikes,
        simplifications: all_simplifications,
        defer_for_later: all_defer,
        other_observations: all_observations,
    };

    serde_json::to_writer(io::stdout(), &aggregated)
        .context("Failed to write aggregated output JSON")?;

    Ok(())
}

/// Get list of changed files from git
fn get_git_changed_files() -> Result<Vec<PathBuf>> {
    // Try staged files first
    let output = Command::new("git")
        .args(&["diff", "--cached", "--name-only", "--diff-filter=ACMR"])
        .output()
        .context("Failed to execute git diff --cached")?;

    let mut files = String::from_utf8(output.stdout).context("Invalid UTF-8 from git output")?;

    // If no staged files, get all modified files
    if files.trim().is_empty() {
        let output = Command::new("git")
            .args(&["diff", "--name-only", "--diff-filter=ACMR"])
            .output()
            .context("Failed to execute git diff")?;

        files = String::from_utf8(output.stdout).context("Invalid UTF-8 from git output")?;
    }

    // Convert to PathBuf, filtering out empty lines
    let paths: Vec<PathBuf> = files
        .lines()
        .filter(|line| !line.trim().is_empty())
        .map(|line| PathBuf::from(line.trim()))
        .collect();

    Ok(paths)
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
fn matches_pattern(path: &PathBuf, pattern: &str) -> bool {
    // Handle simple cases: *, *.rs, *.{js,ts}
    if pattern == "*" {
        return true;
    }

    let filename = path.file_name().and_then(|n| n.to_str()).unwrap_or("");

    if pattern.starts_with("*.") {
        // Handle *.rs
        let ext = &pattern[2..];
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

    let mut all_spikes = Vec::new();
    let mut all_simplifications = Vec::new();
    let mut all_defer = Vec::new();
    let mut all_observations = Vec::new();

    for file_path in files {
        eprintln!("Reviewing: {}", file_path.display());

        // Create payload for this file
        let payload = InputPayload {
            file_path: file_path.clone(),
            meta: Some(Meta {
                kind: Some("code".to_string()),
                review_focus: Some("general".to_string()),
            }),
            ollama_model: None,
        };

        // Review the file
        match review_file(cli, &payload) {
            Ok(output) => {
                // Add file context to each item
                let file_name = file_path
                    .file_name()
                    .and_then(|n| n.to_str())
                    .unwrap_or("unknown");

                for mut spike in output.spikes {
                    spike.title = format!("[{}] {}", file_name, spike.title);
                    all_spikes.push(spike);
                }

                for mut simp in output.simplifications {
                    simp.title = format!("[{}] {}", file_name, simp.title);
                    all_simplifications.push(simp);
                }

                for mut defer in output.defer_for_later {
                    defer.title = format!("[{}] {}", file_name, defer.title);
                    all_defer.push(defer);
                }

                for obs in output.other_observations {
                    all_observations.push(format!("[{}] {}", file_name, obs));
                }
            }
            Err(e) => {
                eprintln!("Error reviewing {}: {}", file_path.display(), e);
            }
        }
    }

    // Aggregate and output results
    let aggregated = OutputPayload {
        spikes: all_spikes,
        simplifications: all_simplifications,
        defer_for_later: all_defer,
        other_observations: all_observations,
    };

    serde_json::to_writer(io::stdout(), &aggregated)
        .context("Failed to write aggregated output JSON")?;

    Ok(())
}

// ============================================================================
// Model Selection
// ============================================================================

/// Select model based on priority: CLI --model > stdin ollama_model > CLI --task > default
fn select_model(cli: &Cli, payload: &InputPayload) -> Result<String> {
    // Priority 1: CLI --model flag
    if let Some(model) = &cli.model {
        return Ok(model.clone());
    }

    // Priority 2: stdin ollama_model field
    if let Some(model) = &payload.ollama_model {
        return Ok(model.clone());
    }

    // Priority 3: CLI --task flag with model registry lookup
    if let Some(task) = &cli.task {
        return load_model_from_task(task);
    }

    // Priority 4: Environment variable (for backwards compatibility)
    if let Ok(model) = std::env::var("MODEL_NAME") {
        return Ok(model);
    }

    // Priority 5: Default from models.json or fallback
    load_default_model()
}

/// Load model registry and get model for specified task
fn load_model_from_task(task: &str) -> Result<String> {
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

/// Load default model from registry
fn load_default_model() -> Result<String> {
    let registry = load_model_registry()?;
    Ok(registry.default_model)
}

/// Load model registry from models.json
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
fn build_prompt(document: &str, filename: &str, meta: &Option<Meta>) -> Result<(String, String)> {
    // System prompt explaining the JSON structure and review categories
    let system_prompt = r#"You are a senior code and document reviewer.

You receive a document and metadata, and must produce a structured review.

**CRITICAL**: You MUST output ONLY raw JSON. No markdown, no code fences, no explanation. Just the JSON object starting with { and ending with }.

The JSON must match this exact structure:
{
  "spikes": [
    { "title": "string", "summary": "string", "lines": "optional string" }
  ],
  "simplifications": [
    { "title": "string", "summary": "string" }
  ],
  "defer_for_later": [
    { "title": "string", "summary": "string" }
  ],
  "other_observations": ["string", "string"]
}

**Field Definitions**:
- spikes: Hotspots, areas to investigate, potential issues or complexity
- simplifications: Areas that could be simplified or optimized
- defer_for_later: Items that are safe to move to future iterations
- other_observations: Extra notes, ideas, or general observations

**Rules**:
- Each item must be SHORT and FOCUSED (1-3 sentences max)
- Do NOT repeat the entire document
- Focus on actionable insights
- Output ONLY the JSON, no explanatory text before or after"#;

    // User prompt with metadata and document
    let kind = meta
        .as_ref()
        .and_then(|m| m.kind.as_deref())
        .unwrap_or("unknown");
    let focus = meta
        .as_ref()
        .and_then(|m| m.review_focus.as_deref())
        .unwrap_or("general");

    let user_prompt = format!(
        r#"**File**: {filename}
**Kind**: {kind}
**Review Focus**: {focus}

**Document Content**:
{document}

Provide your structured review as JSON only."#
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
fn call_ollama(system_msg: &str, user_msg: &str, model_name: &str) -> Result<String> {
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

    // Make HTTP request
    let client = reqwest::blocking::Client::new();
    let response = client
        .post(format!("{}/api/chat", ollama_host))
        .json(&request_body)
        .send()
        .context("Failed to send request to Ollama")?;

    // Check status
    if !response.status().is_success() {
        anyhow::bail!("Ollama API returned error: {}", response.status());
    }

    // Get response text first for debugging
    let response_text = response.text().context("Failed to read Ollama response")?;

    // Try to parse into OllamaResponse
    let ollama_response: OllamaResponse = serde_json::from_str(&response_text).context(format!(
        "Failed to parse Ollama response. First 200 chars: {}",
        &response_text.chars().take(200).collect::<String>()
    ))?;

    Ok(ollama_response.message.content)
}

// ============================================================================
// Response Parsing
// ============================================================================

/// Parse Ollama response into OutputPayload
/// Handles cases where model returns text instead of pure JSON
fn parse_ollama_response(response: &str) -> Result<OutputPayload> {
    // Try direct parsing first
    match serde_json::from_str::<OutputPayload>(response) {
        Ok(output) => Ok(output),
        Err(_) => {
            // Extract JSON from markdown code fences if present
            let cleaned = extract_json_from_markdown(response);
            serde_json::from_str::<OutputPayload>(&cleaned)
                .context("Failed to parse Ollama response as JSON. Response may not be valid JSON.")
        }
    }
}

/// Extract JSON from markdown code fences
/// Handles formats like ```json\n{...}\n``` or ```\n{...}\n```
fn extract_json_from_markdown(text: &str) -> String {
    let trimmed = text.trim();

    // Check if wrapped in markdown code fences
    if trimmed.starts_with("```") {
        // Remove opening fence (```json or ```)
        let without_start = trimmed
            .strip_prefix("```json")
            .or_else(|| trimmed.strip_prefix("```"))
            .unwrap_or(trimmed);

        // Remove closing fence
        let without_end = without_start.strip_suffix("```").unwrap_or(without_start);

        without_end.trim().to_string()
    } else {
        trimmed.to_string()
    }
}

// ============================================================================
// Tests (to be implemented)
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_input_deserialization() {
        let json = r#"{"file_path": "/tmp/test.rs", "meta": {"kind": "code"}}"#;
        let payload: InputPayload = serde_json::from_str(json).unwrap();
        assert_eq!(payload.file_path, PathBuf::from("/tmp/test.rs"));
    }

    #[test]
    fn test_output_serialization() {
        let output = OutputPayload {
            spikes: vec![],
            simplifications: vec![],
            defer_for_later: vec![],
            other_observations: vec!["test".to_string()],
        };
        let json = serde_json::to_string(&output).unwrap();
        assert!(json.contains("other_observations"));
    }

    // TODO: Add more tests
    // - Test prompt building
    // - Test response parsing
    // - Test error handling
}
