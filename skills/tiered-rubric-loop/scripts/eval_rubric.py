#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "google-genai>=3.2.0",
#     "rich",
# ]
# ///
"""Calibrated Tier 1.5 Rubric Evaluator via the Gemini Decisions API.

Purpose:
    Automates the Tier 1.5 probabilistic rubric gate inside a tiered SDD + TDD
    engineering loop. Parses numbered binary assertions (`B1`-`Bn`) from
    `SPEC.md`, `docs/SPEC.md`, or `LOOPS.md` and evaluates them in a single
    low-latency prefill pass using `gemini-decision-1` (`client.decisions.create`
    on `v1beta`) with zero output tokens.

Value:
    1. Terminates mechanical/editorial assertions (`PASS`) without spawning
       expensive Layer-2 review subagents, unless evidence was truncated.
    2. Fails fast (`FAIL_FAST`) on clear omissions directly back to the coding
       loop instead of wasting a semantic critic turn.
    3. Escalates grey-zone items (`ESCALATE_L2_FLASH`)
       and gates `[arch]` assertions (`PROVISIONAL_ARCH_PASS`) for one final
       Tier 2 Flash review before declaring success.
    4. Supports both working-tree loops and branch/PR gating (`--base`,
       `--git-range`), auto-attaches repo-relative target files safely, and
       computes a continuous mean `P(yes)` `ratchet_score`.

Mechanics:
    1. Discovers and parses `B1`-`Bn` table/bullet/task items into `det`, `arch`,
       or `mech` categories without dropping extended tags or code brackets.
    2. Bundles the specification, git diff/status (or `--base`/`--git-range`),
       auto-resolved verification target files/images, and explicit `--file`/
       `--image`/`--pdf` inputs while reporting any truncation.
    3. Evaluates all non-`det` questions in one `client.decisions.create()` pass
       and prints either a markup-safe Rich terminal table or structured JSON.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MODEL = "gemini-decision-1"
DEFAULT_MAX_FILE_CHARS = 24_000
DEFAULT_MAX_DIFF_CHARS = 60_000
DEFAULT_MAX_EVIDENCE_CHARS = 180_000
MAX_AUTO_IMAGES = 8
DEFAULT_ENV_FILES: list[Path] = [
    Path.home() / ".gemini" / ".env",
    Path.home() / ".config" / "gemini" / ".env",
]
SPEC_SEARCH_ORDER: tuple[str, ...] = (
    "docs/SPEC.md",
    "SPEC.md",
    "LOOPS.md",
)

_DET_TAGS = frozenset({"det", "deterministic"})
_ARCH_TAGS = frozenset(
    {"arch", "architecture", "security", "sec", "logic", "concurrency", "async", "perf"}
)
_MECH_TAGS = frozenset(
    {"mech", "mechanical", "docs", "doc", "ui", "visual", "multimodal", "editorial", "style"}
)
_KNOWN_TAGS = _DET_TAGS | _ARCH_TAGS | _MECH_TAGS

_ANY_TAG_PATTERN = re.compile(r"\[([a-z0-9_-]+)\]", re.IGNORECASE)
_KNOWN_TAG_PATTERN = re.compile(
    r"(?<!\w)\[(det|deterministic|arch|architecture|security|sec|logic|concurrency|async|"
    r"perf|mech|mechanical|docs|doc|ui|visual|multimodal|editorial|style)\](?!\w)",
    re.IGNORECASE,
)
_TABLE_ID_PATTERN = re.compile(
    r"^\s*(?:\*\*|`)?\s*(B\d+(?:[a-z]\d*)?)(?:\s*`?\[[^\]]+\]`?)*(?:\s*(?:\*\*|`))?(?:\s*`?\[[^\]]+\]`?)*\s*$",
    re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"
    r"(?:\[[ xX]\]\s+)?"
    r"(?:\*\*|`)?\s*(B\d+(?:[a-z]\d*)?)(?:\s*`?\[[^\]]+\]`?)*(?:\s*(?:\*\*|`))?(?:\s*`?\[[^\]]+\]`?)*"
    r"\s*[:\-–—]\s*(.+?)\s*$",
    re.IGNORECASE,
)
_DET_TARGET_TOKEN_PATTERN = re.compile(
    r"^(?:"
    r"make\s+(?:lint|lint-fix|fix|test|test-all|check|ui-test)"
    r"|(?:uv\s+run(?:\s+--[\w-]+)*\s+)?(?:pytest|codespell|ruff|pyright|mypy)"
    r"(?:\s+[^\s&;|,+]+)*"
    r"|(?:npm|pnpm|yarn)\s+(?:test|run\s+(?:lint|test|check|build)|check|lint)"
    r"(?:\s+[^\s&;|,+]+)*"
    r"|go\s+test(?:\s+[^\s&;|,+]+)*"
    r"|cargo\s+(?:test|clippy|check)(?:\s+[^\s&;|,+]+)*"
    r"|bundle\s+exec(?:\s+[^\s&;|,+]+)+"
    r"|(?:eslint|tsc)(?:\s+[^\s&;|,+]+)*"
    r")$",
    re.IGNORECASE,
)
_INLINE_CODE_SPAN_PATTERN = re.compile(r"`([^`\n]+)`")
_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "dist",
        "build",
    }
)
_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif"})
_SAFE_DOTENV_NAMES = frozenset({".env.template", ".env.example", ".env.sample"})
_SKIP_FILE_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".webp",
        ".gif",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".enc",
        ".pyc",
        ".lock",
    }
)


class MissingApiKeyError(RuntimeError):
    """Raised when no Gemini API key can be resolved from flags, env, or .env."""


class DecisionsApiError(RuntimeError):
    """Raised when the Gemini Decisions API request fails."""

    def __init__(self, message: str, is_auth_error: bool = False) -> None:
        super().__init__(message)
        self.is_auth_error = is_auth_error


@dataclass(frozen=True)
class RubricItem:
    """A single parsed binary rubric assertion (`B1`-`Bn`)."""

    id: str
    condition: str
    target: str = ""
    category: str = "mech"  # "det" | "mech" | "arch"


@dataclass(frozen=True)
class ItemVerdict:
    """Calibrated Tier 1.5 verdict and routing action for one rubric item."""

    id: str
    category: str
    condition: str
    p_yes: float
    confidence: float
    status: str
    l2_model: str | None = None


@dataclass
class EvidenceBundle:
    """Collected specification, git/file evidence, auto-attached images, and telemetry."""

    text: str
    evidence_files: list[str] = field(default_factory=list)
    auto_images: list[Path] = field(default_factory=list)
    evidence_chars: int = 0
    truncated_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class RubricEvaluation:
    """Aggregated Tier 1.5 evaluation across all assessed rubric items."""

    verdicts: list[ItemVerdict] = field(default_factory=list)
    skipped_det_ids: list[str] = field(default_factory=list)
    ratchet_score: float = 1.0
    exit_code: int = 0
    final_l2_arch_ids: list[str] = field(default_factory=list)
    fail_fast_ids: list[str] = field(default_factory=list)
    escalate_flash_ids: list[str] = field(default_factory=list)
    latency_ms: float | None = None
    input_tokens: int | None = None
    evidence_files: list[str] = field(default_factory=list)
    evidence_chars: int = 0
    truncated_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _print_err(message: str, style: str = "bold red") -> None:
    """Print a styled stderr diagnostic, falling back cleanly if Rich is unavailable."""
    try:
        from rich.console import Console
        from rich.markup import escape

        Console(stderr=True).print(f"[{style}]{escape(message)}[/{style}]")
    except ImportError:
        sys.stderr.write(f"{message}\n")


def _strip_tags_outside_code(text: str) -> str:
    """Remove known category tags outside inline code spans, preserving code brackets."""
    parts: list[str] = []
    pos = 0
    for match in _INLINE_CODE_SPAN_PATTERN.finditer(text):
        outside = _KNOWN_TAG_PATTERN.sub("", text[pos : match.start()])
        parts.append(outside)
        parts.append(match.group(0))
        pos = match.end()
    parts.append(_KNOWN_TAG_PATTERN.sub("", text[pos:]))
    return re.sub(r"\s{2,}", " ", "".join(parts)).strip()


def _strip_tags_and_ws(text: str) -> str:
    """Remove known category tags from target cells and strip outer whitespace/backticks."""
    return _strip_tags_outside_code(text).strip(" `")


def _strip_tags_preserve_code(text: str) -> str:
    """Remove known category tags while preserving Markdown inline code backticks."""
    return _strip_tags_outside_code(text)


def _is_deterministic_target(target: str) -> bool:
    """Return True if a Verification Target column names only deterministic CLI gates."""
    stripped = target.strip()
    if not stripped:
        return False
    parts = [
        p.strip().strip("`")
        for p in re.split(r"(?:\s+/\s+|\s*(?:&&|;|,)\s*|\s+\band\b\s+)", stripped)
    ]
    parts = [p for p in parts if p]
    if not parts:
        return False
    return all(_DET_TARGET_TOKEN_PATTERN.match(part) is not None for part in parts)


def _extract_known_tags(text: str) -> set[str]:
    """Return lowercased known category tags occurring outside inline code spans."""
    non_code = _INLINE_CODE_SPAN_PATTERN.sub(" ", text)
    return {match.lower() for match in _KNOWN_TAG_PATTERN.findall(non_code)}


def _classify_category(
    raw_text: str,
    target: str = "",
    id_context: str = "",
    item_id: str = "",
) -> str:
    """Classify an assertion into `det`, `arch`, or `mech` without dropping unknown tags."""
    if id_context:
        for raw_tag in _ANY_TAG_PATTERN.findall(id_context):
            if raw_tag.lower() not in _KNOWN_TAGS:
                label = f" on {item_id}" if item_id else ""
                sys.stderr.write(
                    f"Warning: unrecognised rubric tag [{raw_tag}]{label}; "
                    "defaulting to 'mech' if no known tag applies.\n"
                )

    tags = _extract_known_tags(raw_text)
    if id_context:
        tags |= {match.lower() for match in _KNOWN_TAG_PATTERN.findall(id_context)}
    if tags & _DET_TAGS:
        return "det"
    if tags & _ARCH_TAGS:
        return "arch"
    if tags & _MECH_TAGS:
        return "mech"
    if _is_deterministic_target(target):
        return "det"
    return "mech"


def _split_markdown_row(line: str) -> list[str]:
    """Split a Markdown table row on unescaped pipes outside inline code spans."""
    body = line.strip()
    body = body.removeprefix("|")
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]

    cells: list[str] = []
    buf: list[str] = []
    code_delim = ""
    i = 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            buf.append("|")
            i += 2
            continue
        if ch == "`":
            end = i
            while end < len(body) and body[end] == "`":
                end += 1
            ticks = body[i:end]
            if not code_delim:
                if re.search(rf"(?<!`){re.escape(ticks)}(?!`)", body[end:]):
                    code_delim = ticks
            elif ticks == code_delim:
                code_delim = ""
            buf.append(ticks)
            i = end
            continue
        if ch == "|" and not code_delim:
            cells.append("".join(buf).strip())
            buf.clear()
        else:
            buf.append(ch)
        i += 1
    cells.append("".join(buf).strip())
    return cells


def parse_rubric_markdown(text: str) -> list[RubricItem]:
    """Extract `B1`-`Bn` rubric assertions from Markdown tables, bullets, and task items."""
    items: list[RubricItem] = []
    seen_ids: set[str] = set()
    in_fence = False
    fence_marker = ""

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if in_fence:
            continue

        # 1. Markdown table row
        if stripped.startswith("|") and "|" in stripped[1:]:
            cells = _split_markdown_row(stripped)
            if len(cells) >= 2:
                id_match = _TABLE_ID_PATTERN.match(cells[0])
                if id_match:
                    item_id = id_match.group(1).upper()
                    if item_id in seen_ids:
                        continue
                    raw_condition = cells[1]
                    raw_target = cells[2] if len(cells) >= 3 else ""
                    category = _classify_category(
                        f"{raw_condition} {raw_target}",
                        target=raw_target,
                        id_context=cells[0],
                        item_id=item_id,
                    )
                    condition = _strip_tags_preserve_code(raw_condition)
                    target = _strip_tags_and_ws(raw_target)
                    seen_ids.add(item_id)
                    items.append(
                        RubricItem(
                            id=item_id,
                            condition=condition,
                            target=target,
                            category=category,
                        )
                    )
                    continue

        # 2. Bullet, task item, or numbered list assertion
        bullet_match = _BULLET_PATTERN.match(raw_line)
        if bullet_match:
            item_id = bullet_match.group(1).upper()
            if item_id in seen_ids:
                continue
            raw_condition = bullet_match.group(2)
            id_prefix = raw_line[bullet_match.start(1) : bullet_match.start(2)]
            category = _classify_category(
                raw_line[bullet_match.start(1) :],
                id_context=id_prefix,
                item_id=item_id,
            )
            condition = _strip_tags_preserve_code(raw_condition)
            seen_ids.add(item_id)
            items.append(
                RubricItem(
                    id=item_id,
                    condition=condition,
                    target="",
                    category=category,
                )
            )

    return items


def discover_spec_file(repo_root: Path, explicit_spec: Path | None = None) -> Path:
    """Resolve the rubric Markdown file from `--spec` or standard spec locations."""
    if explicit_spec is not None:
        resolved = explicit_spec if explicit_spec.is_absolute() else (repo_root / explicit_spec)
        if not resolved.is_file():
            msg = f"Specification file not found: {resolved}"
            raise FileNotFoundError(msg)
        return resolved

    for rel in SPEC_SEARCH_ORDER:
        candidate = repo_root / rel
        if candidate.is_file():
            return candidate

    searched = ", ".join(SPEC_SEARCH_ORDER)
    msg = f"No specification or loop rubric found under {repo_root} (checked: {searched})."
    raise FileNotFoundError(msg)


def _read_key_from_dotenv(dotenv_path: Path) -> str | None:
    """Read `GEMINI_API_KEY` or `GOOGLE_API_KEY` from a `.env` file."""
    if not dotenv_path.is_file():
        return None
    found: dict[str, str] = {}
    for raw_line in dotenv_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        for key_name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            prefix = f"{key_name}="
            if line.startswith(prefix):
                val = line[len(prefix) :].strip().strip("\"'")
                if val:
                    found[key_name] = val
    return found.get("GEMINI_API_KEY") or found.get("GOOGLE_API_KEY")


def resolve_api_key(
    explicit_key: str | None = None,
    repo_root: Path | None = None,
    env_files: list[Path] | None = None,
) -> str:
    """Resolve a Gemini API key from explicit flag, env vars, or `.env` files."""
    if explicit_key and explicit_key.strip():
        return explicit_key.strip()

    for env_var in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        val = os.environ.get(env_var, "").strip().strip("\"'")
        if val:
            return val

    candidate_files: list[Path] = []
    root = repo_root or Path.cwd()
    candidate_files.append(root / ".env")
    fallback_files = DEFAULT_ENV_FILES if env_files is None else env_files
    for env_file in fallback_files:
        if env_file not in candidate_files:
            candidate_files.append(env_file)

    for dotenv_path in candidate_files:
        key = _read_key_from_dotenv(dotenv_path)
        if key:
            return key

    msg = (
        "No GEMINI_API_KEY or GOOGLE_API_KEY found in environment, project .env, "
        "or fallback ~/.gemini/.env."
    )
    raise MissingApiKeyError(msg)


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run a read-only git command safely, returning None if git fails to launch."""
    try:
        return subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None


def _is_git_repo_root(repo_root: Path) -> bool:
    """Return True when `repo_root` is itself the top-level directory of a Git repo."""
    res = _run_git(repo_root, ["rev-parse", "--show-toplevel"])
    if res is None or res.returncode != 0:
        return False
    return Path(res.stdout.strip()).resolve() == repo_root.resolve()


def _is_sensitive_path(
    path: Path,
    repo_root: Path,
    allow_outside_root: bool = False,
) -> bool:
    """Block secrets (`.env*`, `*.enc`) and ignored cache directories from auto-collection."""
    name = path.name
    if (name == ".env" or name.startswith(".env.")) and name not in _SAFE_DOTENV_NAMES:
        return True
    if path.suffix.lower() in _SKIP_FILE_SUFFIXES:
        return True
    resolved = path.resolve()
    resolved_root = repo_root.resolve()
    if resolved.is_relative_to(resolved_root):
        parts = resolved.relative_to(resolved_root).parts
    elif allow_outside_root:
        parts = resolved.parts
    else:
        return True
    return any(part in _SKIP_DIR_NAMES for part in parts)


def _read_text_with_truncation(
    path: Path, max_file_chars: int = DEFAULT_MAX_FILE_CHARS
) -> tuple[str, bool] | None:
    """Read a UTF-8 text file up to `max_file_chars`, returning `(text, was_truncated)`."""
    if not path.is_file() or path.suffix.lower() in _SKIP_FILE_SUFFIXES:
        return None
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in raw[:4096]:
        return None
    text = raw.decode("utf-8", errors="replace")
    if len(text) > max_file_chars:
        return f"{text[:max_file_chars]}\n... [TRUNCATED after {max_file_chars} chars]", True
    return text, False


def _safe_read_text(path: Path, max_file_chars: int = DEFAULT_MAX_FILE_CHARS) -> str | None:
    """Read a UTF-8 text file up to `max_file_chars`, returning None for binary files."""
    result = _read_text_with_truncation(path, max_file_chars=max_file_chars)
    return None if result is None else result[0]


def _extract_target_candidates(items: list[RubricItem]) -> list[str]:
    """Extract candidate repo-relative paths from assertion targets and inline backticks."""
    candidates: list[str] = []
    seen: set[str] = set()

    def _add_candidate(raw: str) -> None:
        cleaned = raw.strip().strip("`'\"").rstrip(".,;:")
        if not cleaned or cleaned in seen or cleaned.startswith("-"):
            return
        if "://" in cleaned or "*" in cleaned or "?" in cleaned:
            return
        looks_like_path = "/" in cleaned or cleaned.startswith(".") or "." in Path(cleaned).name
        if looks_like_path:
            seen.add(cleaned)
            candidates.append(cleaned)

    for item in items:
        for span_match in _INLINE_CODE_SPAN_PATTERN.finditer(item.condition):
            _add_candidate(span_match.group(1))
        for span_match in _INLINE_CODE_SPAN_PATTERN.finditer(item.target):
            _add_candidate(span_match.group(1))
        stripped_target = _INLINE_CODE_SPAN_PATTERN.sub(" ", item.target)
        for token in re.split(r"[\s,+;|]+", stripped_target):
            _add_candidate(token)

    return candidates


def _resolve_repo_relative_path(raw_token: str, repo_root: Path) -> Path | None:
    """Resolve `raw_token` under `repo_root`, rejecting path traversal and missing files."""
    repo_root_resolved = repo_root.resolve()
    raw_path = Path(raw_token)
    candidate = (raw_path if raw_path.is_absolute() else (repo_root_resolved / raw_path)).resolve()
    if not candidate.is_relative_to(repo_root_resolved) or not candidate.is_file():
        return None
    return candidate


def _add_evidence_file(
    path: Path,
    label: str,
    header: str,
    repo_root: Path,
    max_file_chars: int,
    included_paths: set[Path],
    sections: list[str],
    evidence_files: list[str],
    truncated_sources: list[str],
    allow_outside_root: bool = False,
) -> None:
    """Read a validated text file and append its formatted section and truncation metadata."""
    resolved = path.resolve()
    if resolved in included_paths or _is_sensitive_path(
        resolved,
        repo_root,
        allow_outside_root=allow_outside_root,
    ):
        return
    read_result = _read_text_with_truncation(resolved, max_file_chars=max_file_chars)
    if read_result is None:
        return
    content, was_truncated = read_result
    included_paths.add(resolved)
    evidence_files.append(label)
    if was_truncated:
        truncated_sources.append(label)
    sections.append(f"## {header} ({label})\n\n```\n{content}\n```")


def _collect_git_range_evidence(
    repo_root: Path,
    git_range: str,
    max_file_chars: int,
    included_paths: set[Path],
    sections: list[str],
    evidence_files: list[str],
    auto_images: list[Path],
    truncated_sources: list[str],
) -> bool:
    """Collect changed files and diff for a branch/commit `--git-range` or `--base`."""
    names_res = _run_git(repo_root, ["diff", "--name-only", "--diff-filter=ACMR", git_range])
    if names_res is None or names_res.returncode != 0:
        err_msg = (names_res.stderr if names_res else "failed to execute git").strip()
        msg = f"Invalid git range '{git_range}': {err_msg}"
        raise ValueError(msg)

    for rel_entry in names_res.stdout.splitlines():
        entry = rel_entry.strip()
        if not entry:
            continue
        candidate = _resolve_repo_relative_path(entry, repo_root)
        if candidate is None:
            continue
        if (
            candidate.suffix.lower() in _IMAGE_SUFFIXES
            and candidate not in auto_images
            and len(auto_images) < MAX_AUTO_IMAGES
        ):
            auto_images.append(candidate)
            continue
        _add_evidence_file(
            path=candidate,
            label=entry,
            header="Changed File",
            repo_root=repo_root,
            max_file_chars=max_file_chars,
            included_paths=included_paths,
            sections=sections,
            evidence_files=evidence_files,
            truncated_sources=truncated_sources,
        )

    diff_res = _run_git(repo_root, ["diff", git_range])
    if diff_res and diff_res.returncode == 0 and diff_res.stdout.strip():
        diff_text = diff_res.stdout.strip()
        if len(diff_text) > DEFAULT_MAX_DIFF_CHARS:
            diff_text = f"{diff_text[:DEFAULT_MAX_DIFF_CHARS]}\n... [DIFF TRUNCATED]"
            truncated_sources.append(f"git diff ({git_range})")
        sections.append(f"## Git Diff ({git_range})\n\n```diff\n{diff_text}\n```")
        return True
    return False


def _collect_working_tree_git_evidence(
    repo_root: Path,
    max_file_chars: int,
    included_paths: set[Path],
    sections: list[str],
    evidence_files: list[str],
    truncated_sources: list[str],
) -> bool:
    """Collect uncommitted git status/diff and touched working-tree files."""
    diff_added = False
    status_res = _run_git(repo_root, ["status", "--short"])
    if status_res and status_res.returncode == 0 and status_res.stdout.strip():
        sections.append(f"## Git Status\n\n```text\n{status_res.stdout.strip()}\n```")
        for line in status_res.stdout.splitlines():
            if len(line) < 4:
                continue
            rel_entry = line[3:].strip().split(" -> ")[-1].strip().strip('"')
            candidate = _resolve_repo_relative_path(rel_entry, repo_root)
            if candidate is None:
                continue
            _add_evidence_file(
                path=candidate,
                label=rel_entry,
                header="Changed File",
                repo_root=repo_root,
                max_file_chars=max_file_chars,
                included_paths=included_paths,
                sections=sections,
                evidence_files=evidence_files,
                truncated_sources=truncated_sources,
            )

    diff_res = _run_git(repo_root, ["diff", "HEAD"])
    if diff_res and diff_res.returncode == 0 and diff_res.stdout.strip():
        diff_text = diff_res.stdout.strip()
        if len(diff_text) > DEFAULT_MAX_DIFF_CHARS:
            diff_text = f"{diff_text[:DEFAULT_MAX_DIFF_CHARS]}\n... [DIFF TRUNCATED]"
            truncated_sources.append("git diff (HEAD)")
        sections.append(f"## Git Diff (HEAD)\n\n```diff\n{diff_text}\n```")
        diff_added = True
    return diff_added


def collect_repo_evidence_bundle(
    repo_root: Path,
    spec_path: Path,
    explicit_files: list[Path] | None = None,
    items: list[RubricItem] | None = None,
    git_range: str | None = None,
    max_file_chars: int = DEFAULT_MAX_FILE_CHARS,
    max_chars: int = DEFAULT_MAX_EVIDENCE_CHARS,
    auto_target_files: bool = True,
) -> EvidenceBundle:
    """Assemble spec, git/explicit/target files, auto images, and truncation telemetry."""
    sections: list[str] = []
    evidence_files: list[str] = []
    auto_images: list[Path] = []
    truncated_sources: list[str] = []
    warnings: list[str] = []

    repo_root_resolved = repo_root.resolve()
    spec_resolved = spec_path.resolve()
    spec_rel = (
        spec_resolved.relative_to(repo_root_resolved)
        if spec_resolved.is_relative_to(repo_root_resolved)
        else spec_path
    )
    spec_res = _read_text_with_truncation(spec_resolved, max_file_chars=max(max_file_chars, 48_000))
    spec_text = spec_res[0] if spec_res else ""
    if spec_res and spec_res[1]:
        truncated_sources.append(str(spec_rel))
    sections.append(f"## Specification ({spec_rel})\n\n{spec_text}")

    included_paths: set[Path] = {spec_resolved}

    for file_path in explicit_files or []:
        resolved = file_path if file_path.is_absolute() else (repo_root_resolved / file_path)
        if not resolved.is_file():
            msg = f"Evidence file not found: {resolved}"
            raise FileNotFoundError(msg)
        if _is_sensitive_path(resolved, repo_root_resolved, allow_outside_root=True):
            warnings.append(f"Skipped sensitive/binary explicit file: {file_path}")
            continue
        _add_evidence_file(
            path=resolved,
            label=str(file_path),
            header="Explicit File",
            repo_root=repo_root_resolved,
            max_file_chars=max_file_chars,
            included_paths=included_paths,
            sections=sections,
            evidence_files=evidence_files,
            truncated_sources=truncated_sources,
            allow_outside_root=True,
        )

    is_git_repo = _is_git_repo_root(repo_root_resolved)
    diff_added = False

    if git_range:
        if not is_git_repo:
            msg = (
                f"Cannot evaluate git range '{git_range}': "
                f"{repo_root_resolved} is not a Git repository."
            )
            raise ValueError(msg)
        diff_added = _collect_git_range_evidence(
            repo_root=repo_root_resolved,
            git_range=git_range,
            max_file_chars=max_file_chars,
            included_paths=included_paths,
            sections=sections,
            evidence_files=evidence_files,
            auto_images=auto_images,
            truncated_sources=truncated_sources,
        )
    elif is_git_repo:
        diff_added = _collect_working_tree_git_evidence(
            repo_root=repo_root_resolved,
            max_file_chars=max_file_chars,
            included_paths=included_paths,
            sections=sections,
            evidence_files=evidence_files,
            truncated_sources=truncated_sources,
        )
    elif not explicit_files:
        for root_dir, dir_names, file_names in os.walk(repo_root_resolved):
            dir_names[:] = sorted(d for d in dir_names if d not in _SKIP_DIR_NAMES)
            for fname in sorted(file_names):
                fpath = Path(root_dir) / fname
                rel = str(fpath.relative_to(repo_root_resolved))
                _add_evidence_file(
                    path=fpath,
                    label=rel,
                    header="Workspace File",
                    repo_root=repo_root_resolved,
                    max_file_chars=max_file_chars,
                    included_paths=included_paths,
                    sections=sections,
                    evidence_files=evidence_files,
                    truncated_sources=truncated_sources,
                )

    if auto_target_files and items:
        for token in _extract_target_candidates(items):
            candidate = _resolve_repo_relative_path(token, repo_root_resolved)
            if candidate is None:
                continue
            name = candidate.name
            is_secret_env = (name == ".env" or name.startswith(".env.")) and (
                name not in _SAFE_DOTENV_NAMES
            )
            if is_secret_env or candidate.suffix.lower() == ".enc":
                continue
            if candidate.suffix.lower() in _IMAGE_SUFFIXES:
                if candidate not in auto_images and len(auto_images) < MAX_AUTO_IMAGES:
                    auto_images.append(candidate)
                continue
            rel = str(candidate.relative_to(repo_root_resolved))
            _add_evidence_file(
                path=candidate,
                label=rel,
                header="Target File",
                repo_root=repo_root_resolved,
                max_file_chars=max_file_chars,
                included_paths=included_paths,
                sections=sections,
                evidence_files=evidence_files,
                truncated_sources=truncated_sources,
            )

    if is_git_repo and not evidence_files and not diff_added:
        warnings.append(
            "No changed, staged, or target files were collected from Git; Tier 1.5 is "
            "evaluating from specification text alone. Use --base, --git-range, or --file "
            "when evaluating committed or merged changes."
        )

    combined = "\n\n".join(sections)
    if len(combined) > max_chars:
        combined = (
            f"{combined[:max_chars]}\n\n"
            f"... [EVIDENCE TRUNCATED AT {max_chars} CHARS FOR CONTEXT BUDGET]"
        )
        truncated_sources.append("combined_evidence")

    return EvidenceBundle(
        text=combined,
        evidence_files=evidence_files,
        auto_images=auto_images,
        evidence_chars=len(combined),
        truncated_sources=truncated_sources,
        warnings=warnings,
    )


def collect_repo_evidence(
    repo_root: Path,
    spec_path: Path,
    explicit_files: list[Path] | None = None,
    max_chars: int = DEFAULT_MAX_EVIDENCE_CHARS,
) -> str:
    """Assemble specification, git diff/status, and touched files into a bounded prompt."""
    return collect_repo_evidence_bundle(
        repo_root=repo_root,
        spec_path=spec_path,
        explicit_files=explicit_files,
        max_chars=max_chars,
    ).text


def build_decision_payload(
    items: list[RubricItem],
    evidence_text: str,
    image_paths: list[Path] | None = None,
    pdf_paths: list[Path] | None = None,
    include_det: bool = False,
    image_resolution: str = "medium",
) -> tuple[
    str | list[dict[str, Any]],
    dict[str, dict[str, Any]],
    list[RubricItem],
    list[RubricItem],
]:
    """Build Decisions API `input` and `questions` payloads, filtering `[det]` items."""
    evaluated: list[RubricItem] = []
    skipped: list[RubricItem] = []

    for item in items:
        if item.category == "det" and not include_det:
            skipped.append(item)
        else:
            evaluated.append(item)

    questions: dict[str, dict[str, Any]] = {}
    for item in evaluated:
        target_hint = f" (Verification target: {item.target})" if item.target else ""
        questions[item.id] = {
            "type": "noul",
            "instructions": (
                f"Based strictly on the provided specification, diff, and files, does "
                f"assertion {item.id} hold? If any relevant target file or doc is absent "
                f"or truncated in the provided payload, treat certainty as uncertain rather "
                f"than guessing true or false. Assertion: {item.condition}{target_hint}"
            ),
            "criteria": {
                "true_description": (
                    f"The relevant files or diff are present in the provided evidence "
                    f"and clearly satisfy: {item.condition}"
                ),
                "false_description": (
                    f"The relevant files or diff are present in the provided evidence "
                    f"and contradict, violate, omit a required element of, or fail to "
                    f"satisfy: {item.condition}"
                ),
            },
        }

    imgs = image_paths or []
    pdfs = pdf_paths or []
    if not imgs and not pdfs:
        return evidence_text, questions, evaluated, skipped

    blocks: list[dict[str, Any]] = [{"type": "text", "text": evidence_text}]
    for img_path in imgs:
        if not img_path.is_file():
            msg = f"Image file not found: {img_path}"
            raise FileNotFoundError(msg)
        guessed_mime, _ = mimetypes.guess_type(str(img_path))
        mime_type = guessed_mime or "image/png"
        b64_data = base64.b64encode(img_path.read_bytes()).decode("ascii")
        blocks.append(
            {
                "type": "image",
                "data": b64_data,
                "mime_type": mime_type,
                "resolution": image_resolution,
            }
        )

    for pdf_path in pdfs:
        if not pdf_path.is_file():
            msg = f"PDF document not found: {pdf_path}"
            raise FileNotFoundError(msg)
        b64_data = base64.b64encode(pdf_path.read_bytes()).decode("ascii")
        blocks.append(
            {
                "type": "document",
                "data": b64_data,
                "mime_type": "application/pdf",
            }
        )

    return blocks, questions, evaluated, skipped


def _extract_noul_metrics(answer: Any) -> tuple[float, float]:
    """Extract `(p_yes, confidence)` from an SDK answer object or dict."""
    if answer is None:
        return 0.5, 0.0
    if isinstance(answer, dict):
        return float(answer.get("noul", 0.5)), float(answer.get("confidence", 0.0))
    return float(getattr(answer, "noul", 0.5)), float(getattr(answer, "confidence", 0.0))


def evaluate_answers(
    items: list[RubricItem],
    answers: dict[str, Any],
    skipped_det_ids: list[str] | None = None,
    pass_threshold: float = 0.90,
    fail_threshold: float = 0.20,
    min_confidence: float = 0.80,
    truncated_sources: list[str] | None = None,
    allow_truncated_pass: bool = False,
    evidence_files: list[str] | None = None,
    evidence_chars: int = 0,
    warnings: list[str] | None = None,
) -> RubricEvaluation:
    """Apply tri-band routing, truncation safety guard, and mean `P(yes)` ratchet score."""
    verdicts: list[ItemVerdict] = []
    final_l2_arch_ids: list[str] = []
    fail_fast_ids: list[str] = []
    escalate_flash_ids: list[str] = []
    trunc_list = list(truncated_sources or [])
    warn_list = list(warnings or [])
    downgraded_ids: list[str] = []

    for item in items:
        p_yes, confidence = _extract_noul_metrics(answers.get(item.id))
        if p_yes >= pass_threshold and confidence >= min_confidence:
            if item.category == "arch":
                status = "PROVISIONAL_ARCH_PASS"
                l2_model = "flash"
                final_l2_arch_ids.append(item.id)
            elif trunc_list and not allow_truncated_pass:
                status = "ESCALATE_L2_FLASH"
                l2_model = "flash"
                escalate_flash_ids.append(item.id)
                downgraded_ids.append(item.id)
            else:
                status = "PASS"
                l2_model = None
        elif p_yes <= fail_threshold and confidence >= min_confidence:
            status = "FAIL_FAST"
            l2_model = None
            fail_fast_ids.append(item.id)
        else:
            status = "ESCALATE_L2_FLASH"
            l2_model = "flash"
            escalate_flash_ids.append(item.id)

        verdicts.append(
            ItemVerdict(
                id=item.id,
                category=item.category,
                condition=item.condition,
                p_yes=p_yes,
                confidence=confidence,
                status=status,
                l2_model=l2_model,
            )
        )

    if downgraded_ids:
        warn_list.append(
            f"Downgraded mechanical PASS ({', '.join(downgraded_ids)}) to "
            f"ESCALATE_L2_FLASH because evidence was truncated "
            f"({', '.join(trunc_list)}). Pass --allow-truncated-pass or shard via --only."
        )

    ratchet_score = sum(v.p_yes for v in verdicts) / len(verdicts) if verdicts else 1.0
    has_blocking = bool(fail_fast_ids or escalate_flash_ids)

    return RubricEvaluation(
        verdicts=verdicts,
        skipped_det_ids=list(skipped_det_ids or []),
        ratchet_score=ratchet_score,
        exit_code=1 if has_blocking else 0,
        final_l2_arch_ids=final_l2_arch_ids,
        fail_fast_ids=fail_fast_ids,
        escalate_flash_ids=escalate_flash_ids,
        evidence_files=list(evidence_files or []),
        evidence_chars=evidence_chars,
        truncated_sources=trunc_list,
        warnings=warn_list,
    )


def call_decisions_api(
    api_key: str,
    model: str,
    decision_input: str | list[dict[str, Any]],
    questions: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], float, int | None]:
    """Call `client.decisions.create` on `v1beta` and return answers, latency, and tokens."""
    from google import genai
    from google.genai import errors as genai_errors

    client = genai.Client(
        api_key=api_key,
        vertexai=False,
        http_options={"api_version": "v1beta"},
    )
    started = time.perf_counter()
    try:
        response = client.decisions.create(
            model=model,
            input=decision_input,  # type: ignore[arg-type]
            questions=questions,  # type: ignore[arg-type]
        )
    except genai_errors.APIError as exc:
        err_text = str(exc)
        status_code = getattr(exc, "code", None)
        is_auth = status_code in (401, 403) or any(
            marker in err_text for marker in ("401", "403", "API_KEY_INVALID")
        )
        raise DecisionsApiError(err_text, is_auth_error=is_auth) from exc
    except (OSError, TimeoutError, ValueError) as exc:
        raise DecisionsApiError(str(exc)) from exc

    latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
    answers = getattr(response, "answers", None) or {}
    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "total_tokens", None)
    return dict(answers), latency_ms, input_tokens


def render_rich_report(evaluation: RubricEvaluation, spec_path: Path, model: str) -> None:
    """Print a markup-safe Rich summary table of Tier 1.5 verdicts and routing actions."""
    from rich.console import Console
    from rich.markup import escape
    from rich.panel import Panel
    from rich.table import Table

    stdout_console = Console()
    table = Table(title=f"Tier 1.5 Rubric Gate ({escape(model)})")
    table.add_column("ID", style="bold cyan", no_wrap=True)
    table.add_column("Cat", style="magenta", no_wrap=True)
    table.add_column("P(yes)", justify="right")
    table.add_column("Conf", justify="right")
    table.add_column("Status", style="bold")
    table.add_column("L2 Route", no_wrap=True)
    table.add_column("Assertion")

    status_styles = {
        "PASS": "green",
        "PROVISIONAL_ARCH_PASS": "cyan",
        "FAIL_FAST": "bold red",
        "ESCALATE_L2_FLASH": "yellow",
    }

    for verdict in evaluation.verdicts:
        style = status_styles.get(verdict.status, "white")
        table.add_row(
            escape(verdict.id),
            escape(verdict.category),
            f"{verdict.p_yes:.2f}",
            f"{verdict.confidence:.2f}",
            f"[{style}]{escape(verdict.status)}[/{style}]",
            escape(verdict.l2_model or "-"),
            escape(verdict.condition),
        )

    stdout_console.print(table)
    latency_part = f" | Latency: {evaluation.latency_ms:.0f} ms" if evaluation.latency_ms else ""
    tokens_part = (
        f" | Tokens: {evaluation.input_tokens:,}" if evaluation.input_tokens is not None else ""
    )
    skipped_part = (
        f"\nSkipped \\[det]: {escape(', '.join(evaluation.skipped_det_ids))}"
        if evaluation.skipped_det_ids
        else ""
    )
    escalate_ids = evaluation.escalate_flash_ids
    extra_lines: list[str] = []
    if evaluation.truncated_sources:
        extra_lines.append(f"Truncated: {escape(', '.join(evaluation.truncated_sources))}")
    if evaluation.warnings:
        extra_lines.append(f"Warnings: {escape(' ; '.join(evaluation.warnings))}")
    extra_suffix = ("\n" + "\n".join(extra_lines)) if extra_lines else ""

    summary = (
        f"Spec: {escape(str(spec_path))}\n"
        f"Ratchet Mean P(yes): {evaluation.ratchet_score:.3f}"
        f"{latency_part}{tokens_part}{skipped_part}\n"
        f"Fail-Fast: {escape(str(evaluation.fail_fast_ids or 'none'))} | "
        f"Escalate L2: {escape(str(escalate_ids or 'none'))} | "
        f"Final L2 \\[arch] Sign-Off: {escape(str(evaluation.final_l2_arch_ids or 'none'))}"
        f"{extra_suffix}"
    )
    border = "green" if evaluation.exit_code == 0 else "red"
    stdout_console.print(Panel(summary, title="Tier 1.5 Summary", border_style=border))


def _parse_only_ids(raw_only: list[str] | None) -> set[str]:
    """Normalise `--only B1,B3 --only B4` arguments into uppercase assertion IDs."""
    selected: set[str] = set()
    for entry in raw_only or []:
        for token in entry.split(","):
            cleaned = token.strip().upper()
            if cleaned:
                selected.add(cleaned)
    return selected


def _merge_image_paths(
    explicit_images: list[Path],
    auto_images: list[Path],
    repo_root: Path,
) -> list[Path]:
    """Combine explicit `--image` paths with auto-resolved image targets, deduplicating."""
    merged: list[Path] = []
    seen: set[Path] = set()
    for raw_path in explicit_images:
        resolved_candidate = (
            raw_path if raw_path.exists() or raw_path.is_absolute() else (repo_root / raw_path)
        )
        key = resolved_candidate.resolve()
        if key not in seen:
            seen.add(key)
            merged.append(resolved_candidate)
    for auto_path in auto_images:
        key = auto_path.resolve()
        if key not in seen:
            seen.add(key)
            merged.append(auto_path)
    return merged


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser for `eval_rubric.py`."""
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate numbered binary rubric assertions (B1-Bn) from SPEC.md/LOOPS.md "
            "using Gemini Decisions API (gemini-decision-1)."
        )
    )
    parser.add_argument(
        "--spec",
        type=Path,
        default=None,
        help="Path to SPEC.md, docs/SPEC.md, or LOOPS.md (auto-discovered if omitted).",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Repository or module root directory (default: current directory).",
    )
    range_group = parser.add_mutually_exclusive_group()
    range_group.add_argument(
        "--base",
        default=None,
        help="Evaluate committed branch changes against <ref>...HEAD (e.g. --base main).",
    )
    range_group.add_argument(
        "--git-range",
        default=None,
        help="Explicit git diff revision range (e.g. origin/main...HEAD or abc..def).",
    )
    parser.add_argument(
        "--file",
        type=Path,
        action="append",
        dest="files",
        default=[],
        help="Additional text/source file to include in evidence (repeatable).",
    )
    parser.add_argument(
        "--image",
        type=Path,
        action="append",
        dest="images",
        default=[],
        help="Image file to attach as a multimodal Decisions API block (repeatable).",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        action="append",
        dest="pdfs",
        default=[],
        help="PDF document to attach as a multimodal Decisions API block (repeatable).",
    )
    parser.add_argument(
        "--include-det",
        action="store_true",
        help="Include [det] deterministic assertions instead of skipping them.",
    )
    parser.add_argument(
        "--only",
        action="append",
        default=[],
        help="Evaluate only specific assertion IDs (comma-separated or repeatable).",
    )
    parser.add_argument(
        "--pass-threshold",
        type=float,
        default=0.90,
        help="Minimum P(yes) required for PASS / PROVISIONAL_ARCH_PASS (default: 0.90).",
    )
    parser.add_argument(
        "--fail-threshold",
        type=float,
        default=0.20,
        help="Maximum P(yes) classified as high-confidence FAIL_FAST (default: 0.20).",
    )
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.80,
        help="Minimum calibrated confidence for terminal PASS/FAIL_FAST (default: 0.80).",
    )
    parser.add_argument(
        "--max-file-chars",
        type=int,
        default=DEFAULT_MAX_FILE_CHARS,
        help=f"Per-file character cap before truncation (default: {DEFAULT_MAX_FILE_CHARS}).",
    )
    parser.add_argument(
        "--max-evidence-chars",
        type=int,
        default=DEFAULT_MAX_EVIDENCE_CHARS,
        help=(
            f"Combined text evidence character cap before truncation "
            f"(default: {DEFAULT_MAX_EVIDENCE_CHARS})."
        ),
    )
    parser.add_argument(
        "--allow-truncated-pass",
        action="store_true",
        help="Allow terminal mechanical PASS even when evidence sources were truncated.",
    )
    parser.add_argument(
        "--no-auto-target-files",
        action="store_true",
        help="Disable automatic loading of repo-relative files referenced in assertions.",
    )
    parser.add_argument(
        "--image-resolution",
        choices=("low", "medium", "high", "ultra_high"),
        default="medium",
        help="Resolution hint for attached images (default: medium).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Decisions API model identifier (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Optional explicit Gemini API key (overrides env and .env).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse rubric and inspect constructed payload offline without calling API.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Print structured JSON output to stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Tier 1.5 rubric evaluation."""
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    git_range = args.git_range or (f"{args.base}...HEAD" if args.base else None)

    try:
        spec_path = discover_spec_file(repo_root, args.spec)
        items = parse_rubric_markdown(spec_path.read_text(encoding="utf-8"))
        only_ids = _parse_only_ids(args.only)
        if only_ids:
            items = [item for item in items if item.id in only_ids]

        if not items:
            _print_err(f"No B1-Bn assertions found in {spec_path}")
            return 2

        bundle = collect_repo_evidence_bundle(
            repo_root=repo_root,
            spec_path=spec_path,
            explicit_files=args.files,
            items=items,
            git_range=git_range,
            max_file_chars=args.max_file_chars,
            max_chars=args.max_evidence_chars,
            auto_target_files=not args.no_auto_target_files,
        )
        merged_images = _merge_image_paths(args.images, bundle.auto_images, repo_root)
        decision_input, questions, evaluated_items, skipped_items = build_decision_payload(
            items=items,
            evidence_text=bundle.text,
            image_paths=merged_images,
            pdf_paths=args.pdfs,
            include_det=args.include_det,
            image_resolution=args.image_resolution,
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        _print_err(f"Input error: {exc}")
        return 2

    skipped_det_ids = [item.id for item in skipped_items]

    for warn in bundle.warnings:
        if not args.json_output:
            _print_err(f"Warning: {warn}", style="yellow")

    if bundle.truncated_sources and not args.json_output:
        _print_err(
            f"Warning: truncated evidence sources: {', '.join(bundle.truncated_sources)}",
            style="yellow",
        )

    if args.dry_run:
        dry_payload = {
            "dry_run": True,
            "model": args.model,
            "spec_path": str(spec_path),
            "skipped_det_ids": skipped_det_ids,
            "question_ids": [item.id for item in evaluated_items],
            "question_count": len(evaluated_items),
            "input_is_multimodal": isinstance(decision_input, list),
            "evidence_chars": bundle.evidence_chars,
            "evidence_files": bundle.evidence_files,
            "auto_image_count": len(bundle.auto_images),
            "auto_images": [str(p) for p in bundle.auto_images],
            "truncated_sources": bundle.truncated_sources,
            "warnings": bundle.warnings,
        }
        if args.json_output:
            print(json.dumps(dry_payload, indent=2))
        else:
            try:
                from rich.console import Console

                Console().print_json(data=dry_payload)
            except ImportError:
                print(json.dumps(dry_payload, indent=2))
        return 0

    if not evaluated_items:
        empty_eval = RubricEvaluation(
            skipped_det_ids=skipped_det_ids,
            ratchet_score=1.0,
            exit_code=0,
            evidence_files=bundle.evidence_files,
            evidence_chars=bundle.evidence_chars,
            truncated_sources=bundle.truncated_sources,
            warnings=bundle.warnings,
        )
        if args.json_output:
            print(json.dumps(asdict(empty_eval), indent=2))
        else:
            render_rich_report(empty_eval, spec_path=spec_path, model=args.model)
        return 0

    try:
        api_key = resolve_api_key(explicit_key=args.api_key, repo_root=repo_root)
    except MissingApiKeyError as exc:
        if args.json_output:
            print(
                json.dumps(
                    {
                        "error": "missing_api_key",
                        "message": str(exc),
                        "fallback_action": "Skip Tier 1.5 and proceed directly to Tier 2.",
                    },
                    indent=2,
                )
            )
        else:
            _print_err(f"Tier 1.5 skipped (no API key): {exc}", style="bold yellow")
        return 3

    try:
        answers, latency_ms, input_tokens = call_decisions_api(
            api_key=api_key,
            model=args.model,
            decision_input=decision_input,
            questions=questions,
        )
    except DecisionsApiError as exc:
        _print_err(f"Decisions API call failed: {exc}")
        return 3 if exc.is_auth_error else 1

    evaluation = evaluate_answers(
        items=evaluated_items,
        answers=answers,
        skipped_det_ids=skipped_det_ids,
        pass_threshold=args.pass_threshold,
        fail_threshold=args.fail_threshold,
        min_confidence=args.min_confidence,
        truncated_sources=bundle.truncated_sources,
        allow_truncated_pass=args.allow_truncated_pass,
        evidence_files=bundle.evidence_files,
        evidence_chars=bundle.evidence_chars,
        warnings=bundle.warnings,
    )
    evaluation.latency_ms = latency_ms
    evaluation.input_tokens = input_tokens

    if args.json_output:
        print(json.dumps(asdict(evaluation), indent=2))
    else:
        render_rich_report(evaluation, spec_path=spec_path, model=args.model)

    return evaluation.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
