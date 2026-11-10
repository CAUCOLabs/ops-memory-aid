#!/usr/bin/env python3
"""Validate Ops Memory Aid Markdown documentation (standard library only)."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

SECTIONS = (
    "Problem / Symptoms",
    "Quick Diagnosis",
    "Possible Causes",
    "Step-by-Step Investigation",
    "How to Interpret Results",
    "Resolution Options",
    "Verification",
    "Safety Notes",
    "References",
    "Validation Status",
)
RISK_PATTERNS = (
    re.compile(r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF]\b"),
    re.compile(r"\bdocker\s+(?:system|volume)\s+prune\b"),
    re.compile(r"\b--privileged\b"),
    re.compile(r"\bchmod\s+777\b"),
    re.compile(r"\b(?:curl|wget)\b[^\n]*\s(?:-k|--insecure)\b"),
    re.compile(r"\bkill\s+-9\b"),
    re.compile(r"\bsystemctl\s+restart\b"),
)
INLINE_LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(\s*(<[^>]+>|[^\s)]+)(?:\s+[^)]*)?\)")
REFERENCE_DEF = re.compile(r"^\s{0,3}\[[^]]+\]:\s*(<[^>]+>|\S+)", re.MULTILINE)
HEADING = re.compile(r"^##\s+(\d+)\.\s+(.+?)\s*$", re.MULTILINE)


def strip_fences(content: str) -> str:
    """Ignore fenced examples while retaining line positions."""
    output = []
    marker = None
    for line in content.splitlines(keepends=True):
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if match:
            run = match.group(1)
            if marker is None:
                marker = run
            elif run[0] == marker[0] and len(run) >= len(marker):
                marker = None
            output.append("\n")
        else:
            output.append("\n" if marker else line)
    return "".join(output)


def local_target(raw: str, file: Path, root: Path) -> tuple[Path | None, str | None]:
    raw = raw.strip().strip("<>")
    if not raw or raw.startswith("#"):
        return None, None
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        return None, None
    target = unquote(parsed.path)
    if not target:
        return None, None
    if target.startswith("/"):
        return None, "absolute filesystem path in Markdown link"
    resolved = (file.parent / target).resolve()
    if not resolved.is_relative_to(root):
        return None, "link escapes repository root"
    if not resolved.exists():
        return None, f"missing target: {target}"
    return resolved, None


def validate(root: Path) -> tuple[list[str], list[str], int]:
    errors: list[str] = []
    warnings: list[str] = []
    documents = sorted(p for p in root.rglob("*.md") if ".git" not in p.parts and ".venv" not in p.parts)
    for file in documents:
        label = file.relative_to(root).as_posix()
        content = file.read_text(encoding="utf-8-sig")
        if not content.strip():
            errors.append(f"{label}: empty Markdown document")
            continue
        clean = strip_fences(content)
        if label.startswith("playbooks/") and file.parent == root / "playbooks":
            found = [(int(n), title.strip()) for n, title in HEADING.findall(clean)]
            expected = list(enumerate(SECTIONS, start=1))
            if found != expected:
                errors.append(f"{label}: expected 10 numbered sections in the standard order; found {found!r}")
        for match in list(INLINE_LINK.finditer(clean)) + list(REFERENCE_DEF.finditer(clean)):
            target = match.group(1)
            _, problem = local_target(target, file, root)
            if problem:
                line = clean.count("\n", 0, match.start()) + 1
                errors.append(f"{label}:{line}: {problem} ({target})")
        for line_no, line in enumerate(content.splitlines(), 1):
            if any(pattern.search(line) for pattern in RISK_PATTERNS):
                warnings.append(f"{label}:{line_no}: review potentially disruptive command/reference")
        if "\t" in clean:
            warnings.append(f"{label}: tab character outside fenced code")
    return errors, warnings, len(documents)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    args = parser.parse_args()
    root = args.root.resolve()
    if not (root / "README.md").is_file() or not (root / "playbooks").is_dir():
        print(f"ERROR: not an Ops Memory Aid repository: {root}", file=sys.stderr)
        return 2
    errors, warnings, count = validate(root)
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"{'FAIL' if errors else 'PASS'}: checked {count} Markdown files; {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
