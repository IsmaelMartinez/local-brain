use assert_cmd::Command;
use predicates::prelude::*;
use std::fs;
use tempfile::TempDir;

/// Helper to get the binary command
fn local_brain() -> Command {
    Command::cargo_bin("local-brain").unwrap()
}

// ============================================================================
// Dry Run Mode Tests
// ============================================================================

#[test]
fn test_dry_run_stdin_mode() {
    let test_file = "tests/fixtures/code_smells.js";
    let input = format!(
        r#"{{"file_path": "{}", "meta": {{"kind": "code"}}}}"#,
        fs::canonicalize(test_file).unwrap().display()
    );

    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .write_stdin(input)
        .assert()
        .success()
        .stdout(predicate::str::contains("DRY RUN - Model:"))
        .stdout(predicate::str::contains("DRY RUN - File: code_smells.js"));
}

#[test]
fn test_dry_run_files_mode() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("DRY RUN - Model:"))
        .stdout(predicate::str::contains("code_smells.js"));
}

#[test]
fn test_dry_run_dir_mode() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--dir")
        .arg("tests/fixtures")
        .arg("--pattern")
        .arg("*.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("DRY RUN - Model:"));
}

#[test]
fn test_dry_run_with_model_override() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--model")
        .arg("custom-model:latest")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains(
            "DRY RUN - Model: custom-model:latest",
        ));
}

#[test]
fn test_dry_run_with_task_selection() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--task")
        .arg("quick-review")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("DRY RUN - Model:"));
}

// ============================================================================
// Output Structure Tests
// ============================================================================

#[test]
fn test_output_is_valid_json() {
    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);
    let parsed: serde_json::Value =
        serde_json::from_str(&stdout).expect("Output should be valid JSON");

    // Verify expected fields exist
    assert!(parsed.get("spikes").is_some(), "Missing 'spikes' field");
    assert!(
        parsed.get("simplifications").is_some(),
        "Missing 'simplifications' field"
    );
    assert!(
        parsed.get("defer_for_later").is_some(),
        "Missing 'defer_for_later' field"
    );
    assert!(
        parsed.get("other_observations").is_some(),
        "Missing 'other_observations' field"
    );
}

#[test]
fn test_multiple_files_aggregation() {
    // Create temp directory with multiple test files
    let temp_dir = TempDir::new().unwrap();
    let file1 = temp_dir.path().join("test1.rs");
    let file2 = temp_dir.path().join("test2.rs");

    fs::write(&file1, "fn main() { println!(\"hello\"); }").unwrap();
    fs::write(&file2, "fn foo() { let x = 1; }").unwrap();

    let files_arg = format!("{},{}", file1.display(), file2.display());

    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--files")
        .arg(&files_arg)
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);
    let parsed: serde_json::Value =
        serde_json::from_str(&stdout).expect("Output should be valid JSON");

    // Should have observations from both files
    let observations = parsed["other_observations"].as_array().unwrap();
    assert!(
        observations.len() >= 8,
        "Should have observations from both files"
    );
}

// ============================================================================
// Error Handling Tests
// ============================================================================

#[test]
fn test_missing_file_error() {
    // Note: --files mode continues on errors (logs to stderr, returns empty result)
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("nonexistent_file.rs")
        .assert()
        .success()
        .stderr(predicate::str::contains("Failed to read file"));
}

#[test]
fn test_invalid_stdin_json() {
    let mut cmd = local_brain();
    cmd.write_stdin("not valid json")
        .assert()
        .failure()
        .stderr(predicate::str::contains("Failed to parse input JSON"));
}

#[test]
fn test_invalid_task_type() {
    // Note: --files mode continues on errors (logs to stderr, returns empty result)
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--task")
        .arg("nonexistent-task")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stderr(predicate::str::contains("Unknown task type"));
}

#[test]
fn test_empty_dir_no_matches() {
    let temp_dir = TempDir::new().unwrap();

    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--dir")
        .arg(temp_dir.path())
        .arg("--pattern")
        .arg("*.rs")
        .assert()
        .success()
        .stderr(predicate::str::contains("No files found"));
}

// ============================================================================
// CLI Argument Tests
// ============================================================================

#[test]
fn test_help_flag() {
    let mut cmd = local_brain();
    cmd.arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("structured code review"))
        .stdout(predicate::str::contains("--dry-run"));
}

#[test]
fn test_model_flag_priority() {
    // --model should override everything
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--model")
        .arg("override-model")
        .arg("--task")
        .arg("quick-review")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("DRY RUN - Model: override-model"));
}

// ============================================================================
// Directory Pattern Matching Tests
// ============================================================================

#[test]
fn test_dir_pattern_matching() {
    let temp_dir = TempDir::new().unwrap();

    // Create files with different extensions
    fs::write(temp_dir.path().join("file1.rs"), "fn main() {}").unwrap();
    fs::write(temp_dir.path().join("file2.rs"), "fn test() {}").unwrap();
    fs::write(temp_dir.path().join("file3.js"), "const x = 1;").unwrap();

    // Should only match .rs files
    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--dir")
        .arg(temp_dir.path())
        .arg("--pattern")
        .arg("*.rs")
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);

    // Should contain .rs files but not .js
    assert!(stdout.contains("file1.rs") && stdout.contains("file2.rs"));
    assert!(!stdout.contains("file3.js"));
}

#[test]
fn test_dir_skips_hidden_directories() {
    let temp_dir = TempDir::new().unwrap();

    // Create a hidden directory with a file
    let hidden_dir = temp_dir.path().join(".hidden");
    fs::create_dir(&hidden_dir).unwrap();
    fs::write(hidden_dir.join("secret.rs"), "fn secret() {}").unwrap();

    // Create a normal file
    fs::write(temp_dir.path().join("visible.rs"), "fn visible() {}").unwrap();

    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--dir")
        .arg(temp_dir.path())
        .arg("--pattern")
        .arg("*.rs")
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);

    // Should find visible.rs but not secret.rs
    assert!(stdout.contains("visible.rs"));
    assert!(!stdout.contains("secret.rs"));
}
