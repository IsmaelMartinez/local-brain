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

    // 2. Read stdin into a string
    let mut input = String::new();
    io::stdin()
        .read_to_string(&mut input)
        .context("Failed to read from stdin")?;

    // 3. Deserialize to InputPayload
    let payload: InputPayload =
        serde_json::from_str(&input).context("Failed to parse input JSON")?;

    // 4. Select model based on priority: CLI --model > stdin ollama_model > CLI --task > default
    let selected_model = select_model(&cli, &payload)?;

    // 5. Read file from disk
    let document = std::fs::read_to_string(&payload.file_path)
        .with_context(|| format!("Failed to read file: {:?}", payload.file_path))?;

    // Extract filename for metadata
    let filename = payload
        .file_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("unknown");

    // 6. Build Ollama prompt
    let (system_msg, user_msg) = build_prompt(&document, filename, &payload.meta)?;

    // 7. Call Ollama API with selected model
    let response = call_ollama(&system_msg, &user_msg, &selected_model)?;

    // 8. Parse response into OutputPayload
    let output: OutputPayload = parse_ollama_response(&response)?;

    // 9. Serialize to stdout
    serde_json::to_writer(io::stdout(), &output).context("Failed to write output JSON")?;

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

    registry
        .task_mappings
        .get(task)
        .cloned()
        .ok_or_else(|| anyhow::anyhow!(
            "Unknown task type: '{}'. Available tasks: {}",
            task,
            registry.task_mappings.keys()
                .map(|k| k.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        ))
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

    serde_json::from_str(&models_json)
        .context("Failed to parse models.json")
}

// ============================================================================
// Prompt Building
// ============================================================================

/// Build system and user prompts for Ollama
fn build_prompt(
    document: &str,
    filename: &str,
    meta: &Option<Meta>,
) -> Result<(String, String)> {
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
    let ollama_host = std::env::var("OLLAMA_HOST").unwrap_or_else(|_| "http://localhost:11434".to_string());

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
    let ollama_response: OllamaResponse = serde_json::from_str(&response_text)
        .context(format!("Failed to parse Ollama response. First 200 chars: {}",
            &response_text.chars().take(200).collect::<String>()))?;

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
        let without_start = trimmed.strip_prefix("```json")
            .or_else(|| trimmed.strip_prefix("```"))
            .unwrap_or(trimmed);

        // Remove closing fence
        let without_end = without_start.strip_suffix("```")
            .unwrap_or(without_start);

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
