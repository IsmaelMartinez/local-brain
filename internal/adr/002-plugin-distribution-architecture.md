# ADR-002: Plugin Distribution Architecture

**Status**: Accepted

**Date**: November 2025

**Deciders**: Project maintainer

---

## Context

With the core functionality complete and validated, we needed to decide on the distribution architecture for local-brain as a Claude Code plugin. The key question was:

**Should we keep the Rust binary, or migrate to Python/TypeScript for better plugin integration?**

### Initial Concerns

1. **Plugin File Discovery**: Can Claude Code discover and load plugin files (skill.md, plugin.json) if they're bundled with a Rust binary?
2. **Installation Complexity**: Would users need to compile Rust, or could we provide pre-built binaries?
3. **Cross-Platform Support**: How to distribute binaries for macOS (Intel/ARM), Linux, Windows?
4. **Runtime Dependencies**: Would a Python/TypeScript implementation be easier to distribute?

### Investigation Findings

Research into Claude Code plugin architecture revealed:
- Plugin files (`.claude-plugin/plugin.json`, `SKILL.md`) must be **separate files** in the repository
- Binary tools and plugin files can coexist in the **same repo**
- Claude Code discovers plugins via marketplace/repo structure, not binary format
- The binary is a **tool** the skill invokes, not part of the plugin system itself

## Decision

**Keep the Rust binary. Do not migrate to Python/TypeScript.**

### Architecture

```
local-brain/
├── src/                          # Rust binary source
│   └── main.rs
├── .claude-plugin/
│   ├── plugin.json              # Plugin metadata
│   ├── SKILL.md                 # Claude instructions
│   └── scripts/
│       └── install.sh           # Auto-install script
├── target/release/local-brain   # Compiled binary (gitignored)
└── models.json                  # Model registry
```

**Distribution**:
1. Users install via Claude Code marketplace: `/plugin install local-brain`
2. SessionStart hook runs `install.sh` on first session
3. Script detects platform (macOS/Linux/Windows, Intel/ARM)
4. Downloads appropriate binary from GitHub Releases
5. Installs to `~/.local/bin` (added to PATH)
6. Skill invokes binary as needed

### Implementation Details

**GitHub Actions CI/CD**:
- Cross-platform builds (6 platforms)
- Automated releases on git tags
- Binary optimization (strip, panic=abort)
- cargo-binstall support

**SessionStart Hook**:
```json
{
  "hooks": {
    "SessionStart": {
      "command": "bash .claude-plugin/scripts/install.sh"
    }
  }
}
```

## Rationale

### Why Rust (Not Python/TypeScript)

1. **Performance**: Rust binary is faster, starts instantly, no runtime overhead
2. **No Runtime Dependencies**:
   - Python requires Python interpreter (version management complexity)
   - TypeScript requires Node.js (version management complexity)
   - Rust compiles to standalone executable (zero dependencies)
3. **Binary Size**:
   - Rust: ~2-3MB (optimized with strip)
   - Python: Needs interpreter + dependencies
   - TypeScript: Needs Node.js runtime
4. **Cross-Platform**:
   - Rust: Single binary per platform
   - Python: Virtual environments, pip dependencies
   - TypeScript: Node modules, platform-specific builds
5. **Plugin Discovery**:
   - All approaches require separate plugin files
   - Language choice doesn't affect Claude Code's plugin detection
   - Binary format is irrelevant to plugin system

### Why Auto-Install via SessionStart Hook

1. **True One-Command Installation**: User runs `/plugin install local-brain`, nothing else
2. **Platform Detection**: Script handles macOS/Linux/Windows, Intel/ARM automatically
3. **Transparent Updates**: Future releases can trigger re-installation
4. **User Experience**: No manual binary download/compilation

## Consequences

### Positive

- **Fast execution**: Rust binary starts in <10ms vs 100-500ms for Python
- **Simple deployment**: Single binary, no dependency hell
- **Portable**: Works on any platform without runtime installation
- **Secure**: Statically linked, no external dependencies to exploit
- **Professional**: Production-grade tool, not a script
- **Auto-install**: One command (`/plugin install`), everything else automatic

### Negative

- **Compilation required for development**: Contributors need Rust toolchain
- **Binary size**: 2-3MB per platform (vs source files)
- **Release complexity**: Must build for 6 platforms (mitigated by GitHub Actions)
- **Update mechanism**: Requires reinstallation (mitigated by auto-install script)

### Neutral

- **Language barrier**: Rust less common than Python, but tool is small/focused
- **Learning curve**: New contributors need Rust knowledge (documented in CONTRIBUTING.md)

## Alternatives Considered

### 1. Python Implementation
**Pros**: Easier for contributors, simpler packaging
**Cons**: Runtime dependency (Python 3.x), slower startup, dependency management (pip, venv)
**Decision**: Rejected - performance and dependency concerns

### 2. TypeScript/Node.js Implementation
**Pros**: Good Claude Code integration examples, JavaScript familiarity
**Cons**: Node.js runtime required, npm dependency hell, slower than Rust
**Decision**: Rejected - still has runtime dependency

### 3. Go Implementation
**Pros**: Similar to Rust (compiled, fast, single binary)
**Cons**: No significant advantage over Rust, team already invested in Rust
**Decision**: Rejected - no compelling reason to switch

### 4. Manual Binary Installation (No Auto-Install)
**Pros**: Simpler, no SessionStart hook needed
**Cons**: Worse user experience, manual steps error-prone
**Decision**: Rejected - auto-install is a major UX improvement

## References

- **Implementation**: GitHub Actions workflows (`.github/workflows/ci.yml`, `.github/workflows/release.yml`)
- **Auto-Install**: `.claude-plugin/scripts/install.sh`
- **Plugin Structure**: `.claude-plugin/plugin.json`
- **Distribution Guide**: [RELEASE.md](../../RELEASE.md)
- **Analysis**: [PRIORITIZATION_ANALYSIS.md](../PRIORITIZATION_ANALYSIS.md#plugin-distribution-consideration)

## Notes

This decision aligns with the project's core value proposition: **minimize context usage by offloading to local tools**. A fast, standalone Rust binary achieves this better than any interpreted language.

The separation of **tool** (Rust binary) from **plugin** (Claude instructions) is intentional - they serve different purposes:
- **Tool**: Fast, efficient code review execution
- **Plugin**: Human-readable instructions for Claude Code

**Future Consideration**: If the binary becomes too large or complex, we could extract the Ollama API interaction into a library and provide language bindings (Rust, Python, TypeScript), but current implementation is sufficient.
