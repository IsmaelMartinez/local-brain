# Quick Start

**Prerequisites**: Complete [INSTALLATION.md](INSTALLATION.md) first.

## Review a File

```bash
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain | jq .
```

Output includes:
- `spikes` - Issues to investigate (bugs, complexity)
- `simplifications` - Refactoring opportunities
- `defer_for_later` - Low priority items
- `other_observations` - General notes

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
echo '{"file_path":"src/main.rs"}' | ./target/release/local-brain --model llama3.2:1b

# Balanced (5s) - daily use
./target/release/local-brain --task quick-review

# Thorough (20s) - security audits
./target/release/local-brain --task security
```

See [MODELS.md](MODELS.md) for model details.

## Common Patterns

```bash
# Review specific file
echo '{"file_path":"auth.rs"}' | ./target/release/local-brain

# With focus area
echo '{"file_path":"auth.rs","meta":{"review_focus":"risk"}}' | ./target/release/local-brain

# Extract only spikes
./target/release/local-brain < input.json | jq '.spikes'
```

## Next Steps

- [MODELS.md](MODELS.md) - Choose the right model
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guide
