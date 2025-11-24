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
fn test_dry_run_files_mode() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("## Dry Run Information"))
        .stdout(predicate::str::contains("Model:"))
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
        .stdout(predicate::str::contains("## Dry Run Information"))
        .stdout(predicate::str::contains("Model:"));
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
        .stdout(predicate::str::contains("Model: custom-model:latest"));
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
        .stdout(predicate::str::contains("Model:"));
}

#[test]
fn test_dry_run_with_kind_and_review_focus() {
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .arg("--kind")
        .arg("design-doc")
        .arg("--review-focus")
        .arg("security")
        .assert()
        .success()
        .stdout(predicate::str::contains("## Dry Run Information"));
}

// ============================================================================
// Output Structure Tests
// ============================================================================

#[test]
fn test_output_is_valid_markdown() {
    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);

    // Verify Markdown structure
    assert!(stdout.contains("# Code Review"), "Missing main heading");
    assert!(
        stdout.contains("## Dry Run Information"),
        "Missing dry run section"
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

    // Should have sections for both files
    assert!(
        stdout.contains("test1.rs") && stdout.contains("test2.rs"),
        "Should have sections for both files"
    );
    assert!(stdout.contains("# Code Review"), "Missing main heading");
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
fn test_no_mode_specified_error() {
    let mut cmd = local_brain();
    cmd.assert()
        .failure()
        .stderr(predicate::str::contains(
            "Must specify one of: --files, --git-diff, or --dir",
        ));
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
        .stdout(predicate::str::contains("--dry-run"))
        .stdout(predicate::str::contains("Markdown output"));
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
        .stdout(predicate::str::contains("Model: override-model"));
}

#[test]
fn test_task_overrides_default() {
    // --task should use task mapping instead of default model
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--task")
        .arg("quick-review")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("Model:"));
}

#[test]
fn test_default_model_when_no_flags() {
    // No --model or --task flags should use default model
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("tests/fixtures/code_smells.js")
        .assert()
        .success()
        .stdout(predicate::str::contains("Model:"));
}

// ============================================================================
// File Handling Edge Cases
// ============================================================================

#[test]
fn test_empty_files_list() {
    // Empty --files argument should handle gracefully
    let mut cmd = local_brain();
    cmd.arg("--dry-run")
        .arg("--files")
        .arg("")
        .assert()
        .success();
}

#[test]
fn test_multiple_files_with_mixed_results() {
    // Test multiple files where some may not exist
    let temp_dir = TempDir::new().unwrap();
    let file1 = temp_dir.path().join("exists.rs");
    fs::write(&file1, "fn test() {}").unwrap();

    let files_arg = format!("{},nonexistent.rs", file1.display());

    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--files")
        .arg(&files_arg)
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should process the file that exists
    assert!(stdout.contains("exists.rs"));
    // Should warn about the missing file
    assert!(stderr.contains("Failed to read file"));
}

#[test]
fn test_files_mode_preserves_order() {
    // Verify that multiple files are processed in the order specified
    let temp_dir = TempDir::new().unwrap();
    let file1 = temp_dir.path().join("zzz.rs");
    let file2 = temp_dir.path().join("aaa.rs");
    let file3 = temp_dir.path().join("mmm.rs");

    fs::write(&file1, "fn zzz() {}").unwrap();
    fs::write(&file2, "fn aaa() {}").unwrap();
    fs::write(&file3, "fn mmm() {}").unwrap();

    let files_arg = format!("{},{},{}", file1.display(), file2.display(), file3.display());

    let mut cmd = local_brain();
    let output = cmd
        .arg("--dry-run")
        .arg("--files")
        .arg(&files_arg)
        .output()
        .expect("Failed to execute command");

    let stdout = String::from_utf8_lossy(&output.stdout);

    // Find positions of each filename in output
    let pos_zzz = stdout.find("zzz.rs").expect("Should contain zzz.rs");
    let pos_aaa = stdout.find("aaa.rs").expect("Should contain aaa.rs");
    let pos_mmm = stdout.find("mmm.rs").expect("Should contain mmm.rs");

    // Verify order matches input order, not alphabetical
    assert!(pos_zzz < pos_aaa, "zzz.rs should appear before aaa.rs");
    assert!(pos_aaa < pos_mmm, "aaa.rs should appear before mmm.rs");
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
