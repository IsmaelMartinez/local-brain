# Quick Start

**Prerequisites**: Complete [INSTALLATION.md](INSTALLATION.md) first.

## Review a File

```bash
./target/release/local-brain --files src/main.rs
```

Output is structured Markdown with these sections:
- `## Issues Found` - Bugs, complexity, potential problems
- `## Simplifications` - Refactoring opportunities
- `## Consider Later` - Low priority items
- `## Other Observations` - General notes

## Review Git Changes

```bash
./target/release/local-brain --git-diff --task quick-review
```

Reviews all staged files (or unstaged if nothing staged).

## Review Directories

```bash
# Review all Rust files in src/
./target/release/local-brain --dir src --pattern "*.rs"

# Review all JavaScript/TypeScript files
./target/release/local-brain --dir app --pattern "*.{js,ts}"

# Review all files (no pattern filter)
./target/release/local-brain --dir lib
```

## Review Multiple Files

```bash
./target/release/local-brain --files src/main.rs,src/lib.rs,tests/integration.rs
```

## Choose a Model

```bash
# Fast (2s) - quick checks
./target/release/local-brain --files src/main.rs --model llama3.2:1b

# Balanced (5s) - daily use
./target/release/local-brain --files src/main.rs --task quick-review

# Thorough (20s) - security audits
./target/release/local-brain --files src/auth.rs --task security
```

See [MODELS.md](MODELS.md) for model details.

## Common Patterns

```bash
# Review specific file with document type
./target/release/local-brain --files auth.rs --kind code

# With focus area
./target/release/local-brain --files auth.rs --review-focus security

# Multiple files with custom focus
./target/release/local-brain --files app.js,server.js --kind code --review-focus performance

# Design document review
./target/release/local-brain --files architecture.md --kind design-doc --review-focus architecture
```

## Markdown Output Example

```markdown
# Code Review

### main.rs

## Issues Found
- **Unused variable**: Variable `x` is declared but never used (lines: 42)
- **Complex function**: Function `process_data` has high cyclomatic complexity

## Simplifications
- **Extract method**: Lines 100-150 could be extracted into separate function

## Consider Later
- **Add caching**: Frequently called function could benefit from memoization

## Other Observations
- Code is well-documented
- Consider adding more unit tests
```

## Next Steps

- [MODELS.md](MODELS.md) - Choose the right model
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
