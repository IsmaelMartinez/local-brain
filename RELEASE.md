# Release Process

This document describes how to create a new release of local-brain.

## Prerequisites

- Write access to the repository
- Clean working tree (no uncommitted changes)
- All tests passing locally

## Versioning

We follow [Semantic Versioning](https://semver.org/) (SemVer):
- **MAJOR.MINOR.PATCH** (e.g., `1.2.3`)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Release Steps

### 1. Update Version

Edit `Cargo.toml`:
```toml
[package]
version = "X.Y.Z"  # Update to new version
```

### 2. Update CHANGELOG (Optional)

If you maintain a CHANGELOG.md, add release notes:
```markdown
## [X.Y.Z] - YYYY-MM-DD
### Added
- New feature description
### Changed
- Modified behavior description
### Fixed
- Bug fix description
```

### 3. Commit Changes

```bash
git add Cargo.toml Cargo.lock CHANGELOG.md
git commit -m "chore: bump version to vX.Y.Z"
git push origin main
```

### 4. Create Release with GitHub CLI

Using `gh` CLI (recommended):

```bash
# Create release with tag (triggers release workflow automatically)
gh release create vX.Y.Z \
  --title "Release vX.Y.Z" \
  --notes "Release notes here" \
  --draft

# Or generate notes automatically from commits
gh release create vX.Y.Z \
  --title "Release vX.Y.Z" \
  --generate-notes \
  --draft
```

**Note**: Using `--draft` allows you to review before publishing. The workflow will still build binaries.

When ready to publish:
```bash
gh release edit vX.Y.Z --draft=false
```

### Alternative: Manual Tag Push

If you prefer manual workflow:
```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Push tag to trigger release workflow
git push origin vX.Y.Z
```

### 5. Monitor Release Workflow

```bash
# Watch workflow status
gh run watch

# Or view in browser
gh run list --limit 5
```

Or visit: https://github.com/IsmaelMartinez/local-brain/actions

### 6. Verify Release

```bash
# View release details
gh release view vX.Y.Z

# Download and test binaries
gh release download vX.Y.Z
```

Verify all platform binaries are attached:
- `local-brain-x86_64-apple-darwin.tar.gz`
- `local-brain-aarch64-apple-darwin.tar.gz`
- `local-brain-x86_64-unknown-linux-gnu.tar.gz`
- `local-brain-x86_64-pc-windows-msvc.zip`

### 7. Edit Release Notes

```bash
# Edit release notes
gh release edit vX.Y.Z --notes "Updated release notes"

# Or open in editor
gh release edit vX.Y.Z
```

## Troubleshooting

**Workflow fails:**
```bash
# View failed run logs
gh run view --log-failed

# Re-run failed jobs
gh run rerun <run-id> --failed
```

**Missing platform binary:**
```bash
# Re-run specific workflow
gh run rerun <run-id>
```

**Tag already exists:**
```bash
# Delete release and tag
gh release delete vX.Y.Z --yes
git tag -d vX.Y.Z
git push origin :refs/tags/vX.Y.Z

# Recreate
gh release create vX.Y.Z --generate-notes
```

**View workflow logs:**
```bash
# List recent runs
gh run list --workflow=release.yml

# View specific run
gh run view <run-id>

# Download logs
gh run view <run-id> --log
```

## Publishing to crates.io (Future)

When ready to publish to crates.io:

```bash
# Dry run
cargo publish --dry-run

# Publish
cargo publish
```

**Note**: Once published to crates.io, versions cannot be deleted. Test thoroughly first.

## Release Checklist

- [ ] Version updated in Cargo.toml
- [ ] Changelog updated (if applicable)
- [ ] Changes committed and pushed to main
- [ ] Tag created and pushed
- [ ] Release workflow completed successfully
- [ ] All platform binaries present in release
- [ ] Release notes reviewed
- [ ] Installation instructions tested on at least one platform
