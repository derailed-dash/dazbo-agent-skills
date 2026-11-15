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
       expensive Layer-2 review subagents.
    2. Fails fast (`FAIL_FAST`) on clear omissions directly back to the coding
       loop instead of wasting a semantic critic turn.
    3. Escalates only grey-zone items (`ESCALATE_L2_FLASH` / `ESCALATE_L2_INHERIT`)
       and gates `[arch]` assertions (`PROVISIONAL_ARCH_PASS`) for one final
       frontier review before declaring success.
    4. Computes a continuous mean `P(yes)` `ratchet_score` across passes so
       bounded loops can distinguish genuine progress from stagnation.

Mechanics:
    1. Discovers and parses `B1`-`Bn` rows/bullets, classifying each item as
       `det` (deterministic Tier 1), `arch` (`[arch]`/`[security]`/`[logic]`), or
       `mech` (default mechanical/editorial).
    2. Bundles the specification, `git status`/`git diff` (or directory files),
       and optional `--file`/`--image`/`--pdf` inputs within token limits.
    3. Evaluates all non-`det` questions in one `client.decisions.create()` pass
       and outputs either a Rich terminal table or machine-readable JSON.
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(stderr=True)
stdout_console = Console()

DEFAULT_MODEL = "gemini-decision-1"
DEFAULT_MAX_EVIDENCE_CHARS = 180_000
DEFAULT_ENV_FILES: list[Path] = [
    Path.home() / ".gemini" / ".env",
    Path.home() / ".config" / "gemini" / ".env",
]
SPEC_SEARCH_ORDER: tuple[str, ...] = (
    "docs/SPEC.md",
    "SPEC.md",
    "LOOPS.md",
)

_TAG_PATTERN = re.compile(r"\[(det|arch|security|logic)\]", re.IGNORECASE)
_TABLE_ID_PATTERN = re.compile(
    r"^\s*(?:\*\*|`)?\s*(B\d+)(?:\s*\[(?:det|arch|security|logic)\])?\s*(?:\*\*|`)?"
    r"(?:\s*\[(?:det|arch|security|logic)\])?\s*$",
    re.IGNORECASE,
)
_BULLET_PATTERN = re.compile(
    r"^\s*(?:[-*+]|\d+[.)])\s+"
    r"(?:\*\*|`)?\s*(B\d+)(?:\s*\[(?:det|arch|security|logic)\])?\s*(?:\*\*|`)?"
    r"(?:\s*\[(?:det|arch|security|logic)\])?\s*[:\-–—]\s*(.+?)\s*$",
    re.IGNORECASE,
)
_DET_TARGET_TOKEN_PATTERN = re.compile(
    r"^(?:"
    r"make\s+(?:lint|lint-fix|fix|test|test-all|check|ui-test)"
    r"|(?:uv\s+run\s+)?(?:pytest|codespell|ruff|pyright|mypy)(?:\s+[^\s/&]+)?"
    r"|npm\s+(?:test|run\s+(?:lint|test|check|build))"
    r"|pnpm\s+(?:test|lint)"
    r"|go\s+test(?:\s+\./\.\.\.)?"
    r"|cargo\s+(?:test|clippy|check)"
    r"|eslint|tsc"
    r")$",
    re.IGNORECASE,
)
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
class RubricEvaluation:
    """Aggregated Tier 1.5 evaluation across all assessed rubric items."""

    verdicts: list[ItemVerdict] = field(default_factory=list)
    skipped_det_ids: list[str] = field(default_factory=list)
    ratchet_score: float = 1.0
    exit_code: int = 0
    final_l2_arch_ids: list[str] = field(default_factory=list)
    fail_fast_ids: list[str] = field(default_factory=list)
    escalate_flash_ids: list[str] = field(default_factory=list)
    escalate_inherit_ids: list[str] = field(default_factory=list)
    latency_ms: float | None = None
    input_tokens: int | None = None


def _strip_tags_and_ws(text: str) -> str:
    """Remove `[det]`/`[arch]`/`[security]`/`[logic]` markers and normalise whitespace."""
    cleaned = _TAG_PATTERN.sub("", text)
    return re.sub(r"\s{2,}", " ", cleaned).strip(" `")


def _strip_tags_preserve_code(text: str) -> str:
    """Remove category tags while preserving Markdown inline code backticks."""
    cleaned = _TAG_PATTERN.sub("", text)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _is_deterministic_target(target: str) -> bool:
    """Return True if a Verification Target column names only deterministic CLI gates."""
    stripped = target.strip()
    if not stripped:
        return False
    parts = [
        p.strip().strip("`") for p in re.split(r"\s*(?:/|&&|,|\band\b)\s*", stripped)
    ]
    parts = [p for p in parts if p]
    if not parts:
        return False
    return all(_DET_TARGET_TOKEN_PATTERN.match(part) is not None for part in parts)


def _classify_category(raw_text: str, target: str = "") -> str:
    """Classify an assertion into `det`, `arch`, or `mech`."""
    tags = {match.lower() for match in _TAG_PATTERN.findall(raw_text)}
    if "det" in tags:
        return "det"
    if tags & {"arch", "security", "logic"}:
        return "arch"
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
    """Extract `B1`-`Bn` rubric assertions from Markdown tables and bullet lists."""
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
                    raw_condition = cells[1]
                    raw_target = cells[2] if len(cells) >= 3 else ""
                    if item_id in seen_ids:
                        continue
                    category = _classify_category(
                        f"{cells[0]} {raw_condition} {raw_target}",
                        target=raw_target,
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

        # 2. Bullet or numbered list assertion
        bullet_match = _BULLET_PATTERN.match(raw_line)
        if bullet_match:
            item_id = bullet_match.group(1).upper()
            if item_id in seen_ids:
                continue
            raw_condition = bullet_match.group(2)
            category = _classify_category(raw_line)
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
        resolved = (
            explicit_spec
            if explicit_spec.is_absolute()
            else (repo_root / explicit_spec)
        )
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
    for raw_line in dotenv_path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
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


def _run_git(
    repo_root: Path, args: list[str]
) -> subprocess.CompletedProcess[str] | None:
    """Run a read-only git command safely, returning None if git fails."""
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


def _safe_read_text(path: Path, max_file_chars: int = 24_000) -> str | None:
    """Read a UTF-8 text file up to `max_file_chars`, returning None for binary files."""
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
        return f"{text[:max_file_chars]}\n... [TRUNCATED after {max_file_chars} chars]"
    return text


def collect_repo_evidence(
    repo_root: Path,
    spec_path: Path,
    explicit_files: list[Path] | None = None,
    max_chars: int = DEFAULT_MAX_EVIDENCE_CHARS,
) -> str:
    """Assemble specification, git diff/status, and touched files into a bounded prompt."""
    sections: list[str] = []
    spec_rel = (
        spec_path.relative_to(repo_root)
        if spec_path.resolve().is_relative_to(repo_root.resolve())
        else spec_path
    )
    spec_text = _safe_read_text(spec_path, max_file_chars=48_000) or ""
    sections.append(f"## Specification ({spec_rel})\n\n{spec_text}")

    included_paths: set[Path] = {spec_path.resolve()}

    if explicit_files:
        for file_path in explicit_files:
            resolved = file_path if file_path.is_absolute() else (repo_root / file_path)
            if not resolved.is_file():
                msg = f"Evidence file not found: {resolved}"
                raise FileNotFoundError(msg)
            content = _safe_read_text(resolved)
            if content is not None:
                included_paths.add(resolved.resolve())
                sections.append(
                    f"## Explicit File ({file_path})\n\n```\n{content}\n```"
                )

    if _is_git_repo_root(repo_root):
        status_res = _run_git(repo_root, ["status", "--short"])
        if status_res and status_res.returncode == 0 and status_res.stdout.strip():
            sections.append(
                f"## Git Status\n\n```text\n{status_res.stdout.strip()}\n```"
            )

            # Gather modified/untracked files listed by git status
            for line in status_res.stdout.splitlines():
                if len(line) < 4:
                    continue
                rel_entry = line[3:].strip().split(" -> ")[-1].strip().strip('"')
                candidate = repo_root / rel_entry
                if candidate.resolve() in included_paths:
                    continue
                content = _safe_read_text(candidate)
                if content is not None:
                    included_paths.add(candidate.resolve())
                    sections.append(
                        f"## Changed File ({rel_entry})\n\n```\n{content}\n```"
                    )

        diff_res = _run_git(repo_root, ["diff", "HEAD"])
        if diff_res and diff_res.returncode == 0 and diff_res.stdout.strip():
            diff_text = diff_res.stdout.strip()
            if len(diff_text) > 60_000:
                diff_text = f"{diff_text[:60_000]}\n... [DIFF TRUNCATED]"
            sections.append(f"## Git Diff (HEAD)\n\n```diff\n{diff_text}\n```")
    elif not explicit_files:
        # Standalone non-git directory (e.g. scoped module or scratch smoke directory)
        for root_dir, dir_names, file_names in os.walk(repo_root):
            dir_names[:] = sorted(d for d in dir_names if d not in _SKIP_DIR_NAMES)
            for fname in sorted(file_names):
                fpath = Path(root_dir) / fname
                if fpath.resolve() in included_paths:
                    continue
                content = _safe_read_text(fpath)
                if content is not None:
                    included_paths.add(fpath.resolve())
                    rel = fpath.relative_to(repo_root)
                    sections.append(f"## Workspace File ({rel})\n\n```\n{content}\n```")

    combined = "\n\n".join(sections)
    if len(combined) > max_chars:
        combined = (
            f"{combined[:max_chars]}\n\n"
            f"... [EVIDENCE TRUNCATED AT {max_chars} CHARS FOR CONTEXT BUDGET]"
        )
    return combined


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
                f"Based strictly on the provided specification, diff, and files, "
                f"does assertion {item.id} hold? Assertion: {item.condition}{target_hint}"
            ),
            "criteria": {
                "true_description": (
                    f"The provided evidence clearly satisfies: {item.condition}"
                ),
                "false_description": (
                    f"The provided evidence contradicts, omits, leaves incomplete, or "
                    f"fails to satisfy: {item.condition}"
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
    return float(getattr(answer, "noul", 0.5)), float(
        getattr(answer, "confidence", 0.0)
    )


def evaluate_answers(
    items: list[RubricItem],
    answers: dict[str, Any],
    skipped_det_ids: list[str] | None = None,
    pass_threshold: float = 0.90,
    fail_threshold: float = 0.20,
    min_confidence: float = 0.80,
) -> RubricEvaluation:
    """Apply tri-band routing and compute the continuous mean `P(yes)` ratchet score."""
    verdicts: list[ItemVerdict] = []
    final_l2_arch_ids: list[str] = []
    fail_fast_ids: list[str] = []
    escalate_flash_ids: list[str] = []
    escalate_inherit_ids: list[str] = []

    for item in items:
        p_yes, confidence = _extract_noul_metrics(answers.get(item.id))
        if p_yes >= pass_threshold and confidence >= min_confidence:
            if item.category == "arch":
                status = "PROVISIONAL_ARCH_PASS"
                l2_model = "inherit"
                final_l2_arch_ids.append(item.id)
            else:
                status = "PASS"
                l2_model = None
        elif p_yes <= fail_threshold and confidence >= min_confidence:
            status = "FAIL_FAST"
            l2_model = None
            fail_fast_ids.append(item.id)
        elif item.category == "arch":
            status = "ESCALATE_L2_INHERIT"
            l2_model = "inherit"
            escalate_inherit_ids.append(item.id)
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

    ratchet_score = sum(v.p_yes for v in verdicts) / len(verdicts) if verdicts else 1.0
    has_blocking = bool(fail_fast_ids or escalate_flash_ids or escalate_inherit_ids)

    return RubricEvaluation(
        verdicts=verdicts,
        skipped_det_ids=list(skipped_det_ids or []),
        ratchet_score=ratchet_score,
        exit_code=1 if has_blocking else 0,
        final_l2_arch_ids=final_l2_arch_ids,
        fail_fast_ids=fail_fast_ids,
        escalate_flash_ids=escalate_flash_ids,
        escalate_inherit_ids=escalate_inherit_ids,
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
    input_tokens = getattr(usage, "input_tokens", None) or getattr(
        usage, "total_tokens", None
    )
    return dict(answers), latency_ms, input_tokens


def render_rich_report(
    evaluation: RubricEvaluation, spec_path: Path, model: str
) -> None:
    """Print a Rich summary table of Tier 1.5 verdicts and routing actions."""
    table = Table(title=f"Tier 1.5 Rubric Gate ({model})")
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
        "ESCALATE_L2_INHERIT": "yellow",
    }

    for verdict in evaluation.verdicts:
        style = status_styles.get(verdict.status, "white")
        table.add_row(
            verdict.id,
            verdict.category,
            f"{verdict.p_yes:.2f}",
            f"{verdict.confidence:.2f}",
            f"[{style}]{verdict.status}[/{style}]",
            verdict.l2_model or "-",
            verdict.condition,
        )

    stdout_console.print(table)
    latency_part = (
        f" | Latency: {evaluation.latency_ms:.0f} ms" if evaluation.latency_ms else ""
    )
    skipped_part = (
        f" | Skipped [det]: {', '.join(evaluation.skipped_det_ids)}"
        if evaluation.skipped_det_ids
        else ""
    )
    summary = (
        f"Spec: {spec_path}\n"
        f"Ratchet Mean P(yes): {evaluation.ratchet_score:.3f}{latency_part}{skipped_part}\n"
        f"Fail-Fast: {evaluation.fail_fast_ids or 'none'} | "
        f"Escalate L2: {evaluation.escalate_flash_ids + evaluation.escalate_inherit_ids or 'none'} | "
        f"Final L2 [arch] Sign-Off: {evaluation.final_l2_arch_ids or 'none'}"
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

    try:
        spec_path = discover_spec_file(repo_root, args.spec)
        items = parse_rubric_markdown(spec_path.read_text(encoding="utf-8"))
        only_ids = _parse_only_ids(args.only)
        if only_ids:
            items = [item for item in items if item.id in only_ids]

        if not items:
            console.print(
                f"[bold red]No B1-Bn assertions found in {spec_path}[/bold red]"
            )
            return 2

        evidence_text = collect_repo_evidence(
            repo_root=repo_root,
            spec_path=spec_path,
            explicit_files=args.files,
        )
        decision_input, questions, evaluated_items, skipped_items = (
            build_decision_payload(
                items=items,
                evidence_text=evidence_text,
                image_paths=args.images,
                pdf_paths=args.pdfs,
                include_det=args.include_det,
                image_resolution=args.image_resolution,
            )
        )
    except (FileNotFoundError, ValueError, OSError) as exc:
        console.print(f"[bold red]Input error:[/bold red] {exc}")
        return 2

    skipped_det_ids = [item.id for item in skipped_items]

    if args.dry_run:
        dry_payload = {
            "dry_run": True,
            "model": args.model,
            "spec_path": str(spec_path),
            "skipped_det_ids": skipped_det_ids,
            "question_ids": [item.id for item in evaluated_items],
            "question_count": len(evaluated_items),
            "input_is_multimodal": isinstance(decision_input, list),
            "evidence_chars": len(evidence_text),
        }
        if args.json_output:
            print(json.dumps(dry_payload, indent=2))
        else:
            stdout_console.print_json(data=dry_payload)
        return 0

    if not evaluated_items:
        empty_eval = RubricEvaluation(
            skipped_det_ids=skipped_det_ids, ratchet_score=1.0, exit_code=0
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
            console.print(
                f"[bold yellow]Tier 1.5 skipped (no API key):[/bold yellow] {exc}"
            )
        return 3

    try:
        answers, latency_ms, input_tokens = call_decisions_api(
            api_key=api_key,
            model=args.model,
            decision_input=decision_input,
            questions=questions,
        )
    except DecisionsApiError as exc:
        console.print(f"[bold red]Decisions API call failed:[/bold red] {exc}")
        return 3 if exc.is_auth_error else 1

    evaluation = evaluate_answers(
        items=evaluated_items,
        answers=answers,
        skipped_det_ids=skipped_det_ids,
        pass_threshold=args.pass_threshold,
        fail_threshold=args.fail_threshold,
        min_confidence=args.min_confidence,
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
