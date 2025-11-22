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

### 4. Create and Push Tag

```bash
# Create annotated tag
git tag -a vX.Y.Z -m "Release vX.Y.Z"

# Push tag to trigger release workflow
git push origin vX.Y.Z
```

### 5. Monitor Release Workflow

1. Go to: https://github.com/IsmaelMartinez/local-brain/actions
2. Watch the "Release" workflow run
3. Wait for all platform builds to complete (~10-15 minutes)

### 6. Verify Release

1. Check: https://github.com/IsmaelMartinez/local-brain/releases
2. Verify all platform binaries are attached:
   - `local-brain-x86_64-apple-darwin.tar.gz`
   - `local-brain-aarch64-apple-darwin.tar.gz`
   - `local-brain-x86_64-unknown-linux-gnu.tar.gz`
   - `local-brain-x86_64-pc-windows-msvc.zip`
3. Check SHA256 checksums are included
4. Review auto-generated release notes

### 7. Edit Release Notes (Optional)

If needed, edit the release on GitHub to:
- Add highlights
- Link to issues/PRs
- Add migration guide for breaking changes
- Add known issues

## Troubleshooting

**Workflow fails:**
- Check GitHub Actions logs
- Verify Cargo.toml syntax is valid
- Ensure all tests pass: `cargo test --all-features`

**Missing platform binary:**
- Re-run failed workflow job from GitHub Actions UI

**Tag already exists:**
```bash
# Delete local tag
git tag -d vX.Y.Z

# Delete remote tag
git push origin :refs/tags/vX.Y.Z

# Recreate and push
git tag -a vX.Y.Z -m "Release vX.Y.Z"
git push origin vX.Y.Z
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
