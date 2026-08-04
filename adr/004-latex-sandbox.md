# ADR-004: LaTeX Sandbox with Podman

## Status
**Accepted**

## Date
2026-08-04

## Context
LaTeX compilation must process user-supplied templates and generated TEX content. This presents several risks:
- **RCE vulnerabilities**: Malicious LaTeX can execute shell commands via `\write18` and `\input`.
- **Resource exhaustion**: Malicious or complex documents can consume excessive CPU/RAM.
- **Timeout issues**: Long compilations can block the agent pipeline.
- **Security isolation**: Compilation should not affect the host system.

Options considered:
- **Direct compilation**: Run `pdflatex` / `xelatex` on the host. Simple but risky.
- **Docker container**: Isolated compilation with Docker. Good isolation but requires Docker.
- **Podman container**: Same as Docker but rootless and more Linux-native.
- **Sandboxed execution (pandoc)**: Convert to PDF via pandoc. Limited LaTeX support.

## Decision
We use **Podman containers** as LaTeX sandbox:
- Each compilation spawns a temporary Podman container with the LaTeX engine (texlive).
- Container runs with:
  - `--network=none` — no network access (prevents downloading malicious packages)
  - CPU/RAM limits — prevents resource exhaustion
  - Read-only root filesystem where possible
  - Temporary volume mount for the TEX input and PDF output
- Compilation timeout: 30 seconds per document.

### Podman Latex Compiler
```python
class PodmanLatexCompiler:
    def compile(self, tex_content: str, template: str) -> bytes:
        # Mount tex_content to container
        # Run pdflatex with limits
        # Return PDF bytes
        pass
```

## Consequences
- **Positive:**
  - Strong isolation from the host system.
  - No RCE risk — user TEX cannot execute commands on the host.
  - Resource limits prevent single user from exhausting host resources.
  - Podman is rootless — works without root privileges.
  - Reproducible — same texlive image ensures consistent compilation.
- **Negative:**
  - Slightly higher overhead per compilation (container startup: ~2-5s).
  - Need to manage the texlive image and updates.
  - Larger disk usage (texlive image is ~1-2 GB).
  - Debugging compilation errors requires inspecting container logs.
- **Rules:**
  - NEVER execute LaTeX compilation directly on the host.
  - ALWAYS use `PodmanLatexCompiler` for sandboxing.
  - Compilation timeout: 30 seconds (configurable).
  - Max TEX size: 10 MB (configurable).

## Authors
Vacancy-Search Team

## References
- [Master Document §ADR-004](../docs/Master%20Document.md#4-latex-sandbox)
- [Master Document §8: Security Spec](../docs/Master%20Document.md#8-security-spec)
