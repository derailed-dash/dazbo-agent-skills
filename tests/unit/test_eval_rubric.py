"""Offline unit tests for tiered-rubric-loop's `eval_rubric.py`.

Purpose:
    Verifies Markdown rubric parsing, deterministic target detection, git commit-range
    evidence collection, auto-resolution of verification targets with secret/path guards,
    truncation telemetry, tri-band routing, and safe Rich output rendering offline.

Value:
    Prevents regressions in Tier 1.5 gating logic without requiring network access or a
    live `GEMINI_API_KEY`.

Mechanics:
    Uses `pytest` fixtures (`tmp_path`, `monkeypatch`, `capsys`) and ephemeral local Git
    repositories to exercise CLI and helper interfaces cleanly.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import eval_rubric
import pytest


def _run_git(repo_root: Path, *args: str) -> None:
    """Execute a git command in `repo_root`, failing fast on error."""
    subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_git_repo(repo_root: Path) -> None:
    """Create a committed `main` baseline in `repo_root` with clean status."""
    _run_git(repo_root, "init", "-b", "main")
    _run_git(repo_root, "config", "user.name", "Test User")
    _run_git(repo_root, "config", "user.email", "test@example.com")
    (repo_root / "SPEC.md").write_text("# Spec\n\n- **B1**: Readme exists\n", encoding="utf-8")
    (repo_root / "README.md").write_text("# Demo\n", encoding="utf-8")
    _run_git(repo_root, "add", "SPEC.md", "README.md")
    _run_git(repo_root, "commit", "-m", "chore: initial commit")


def test_parse_rubric_supports_extended_tags_checkboxes_and_preserves_brackets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Extended tags and checkboxes must parse without dropping items or mangling code brackets."""
    rubric = """
| ID | Falsifiable Condition | Verification Target |
| :--- | :--- | :--- |
| `B1 [det]` | Static check passes | `make check` |
| `B2 [mech]` | Docs updated cleanly | Doc review |
| `B3 [perf]` | Avoids quadratic scan | `src/app.py` |
| `B4 [ui]` | Dark palette consistent | Visual review |
| `B5 [arch][security]` | Validates session cookie | `src/auth.py` |
| `B6 [customtag]` | Preserves unknown custom tag item | Doc review |
| `B11a [perf]` | Avoids quadratic interval scan | `src/app.py` |

- [ ] **B7**: Preserves unchecked task item
- [x] **B8 [arch]**: Preserves completed `[concurrency]` task item
- [x] `B4a [docs]`: Canonical registry check
1. `B9 [docs]`: Numbered list docs assertion
- **B10**: Function returns `list[str]` or `dict[str, Any]` over `[lo, hi)` (Section 3 [x])
"""
    items = eval_rubric.parse_rubric_markdown(rubric)
    by_id = {item.id: item for item in items}

    assert set(by_id) == {*(f"B{i}" for i in range(1, 11)), "B4A", "B11A"}
    assert by_id["B1"].category == "det"
    assert by_id["B2"].category == "mech"
    assert by_id["B3"].category == "arch"
    assert by_id["B4"].category == "mech"
    assert by_id["B4A"].category == "mech"
    assert by_id["B5"].category == "arch"
    assert by_id["B6"].category == "mech"
    assert by_id["B7"].category == "mech"
    assert by_id["B8"].category == "arch"
    assert by_id["B9"].category == "mech"
    assert by_id["B11A"].category == "arch"

    assert "`list[str]`" in by_id["B10"].condition
    assert "`dict[str, Any]`" in by_id["B10"].condition
    assert "`[lo, hi)`" in by_id["B10"].condition
    assert "[x]" in by_id["B10"].condition

    stderr_text = capsys.readouterr().err
    assert "customtag" in stderr_text
    assert "unrecognised rubric tag [x]" not in stderr_text


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("pytest tests/unit/test_auth.py", True),
        ("uv run --no-sync pytest src/tests -q", True),
        ("codespell -s", True),
        ("ruff check .", True),
        ("`make check` / `pytest tests/unit/test_foo.py`", True),
        ("bundle exec jekyll build --trace", True),
        ("`tests/unit/test_auth.py` + semantic review", False),
        ("src/auth.py", False),
    ],
)
def test_deterministic_target_classification(target: str, expected: bool) -> None:
    """Slashed test paths and flags classify cleanly without misclassifying prose notes."""
    assert eval_rubric._is_deterministic_target(target) is expected


def test_arch_tag_overrides_deterministic_target_path() -> None:
    """Explicit `[arch]` items with test paths must stay `arch` so Tier 2 reviews them."""
    rubric = "| `B3 [arch]` | Auth invariant holds | `tests/unit/test_auth.py` |\n"
    items = eval_rubric.parse_rubric_markdown(rubric)
    assert len(items) == 1
    assert items[0].category == "arch"


def test_git_range_discovery_for_committed_branches_and_invalid_ranges(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Committed branches are evaluated via `--base`/`--git-range`, while clean HEAD warns."""
    _init_git_repo(tmp_path)
    _run_git(tmp_path, "checkout", "-b", "feat/demo")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "app.py").write_text("def greet() -> str:\n    return 'hi'\n", encoding="utf-8")
    _run_git(tmp_path, "add", "src/app.py")
    _run_git(tmp_path, "commit", "-m", "feat: add app module")

    # Clean working tree without git_range collects 0 changed files and warns.
    clean_bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=tmp_path,
        spec_path=tmp_path / "SPEC.md",
        auto_target_files=False,
    )
    assert clean_bundle.evidence_files == []
    assert clean_bundle.warnings

    # Explicit git_range picks up committed feature branch files + range diff.
    range_bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=tmp_path,
        spec_path=tmp_path / "SPEC.md",
        git_range="main...HEAD",
    )
    assert "src/app.py" in range_bundle.evidence_files
    assert "## Git Diff (main...HEAD)" in range_bundle.text

    # CLI `--base main` works end-to-end in `--dry-run --json`.
    rc = eval_rubric.main(["--repo-root", str(tmp_path), "--base", "main", "--dry-run", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert "src/app.py" in payload["evidence_files"]

    # Invalid range fails cleanly with ValueError / exit code 2.
    with pytest.raises(ValueError, match="git"):
        eval_rubric.collect_repo_evidence_bundle(
            repo_root=tmp_path,
            spec_path=tmp_path / "SPEC.md",
            git_range="nonexistent_ref..HEAD",
        )
    bad_rc = eval_rubric.main(
        ["--repo-root", str(tmp_path), "--git-range", "nonexistent_ref..HEAD", "--dry-run"]
    )
    assert bad_rc == 2


def test_auto_target_resolution_and_secret_traversal_guards(tmp_path: Path) -> None:
    """Repo-relative targets auto-attach, while `.env`, `*.enc`, and outside paths stay blocked."""
    outside = tmp_path / "outside.txt"
    outside.write_text("TOP_SECRET_OUTSIDE", encoding="utf-8")

    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)

    (repo_root / ".env.template").write_text("GEMINI_API_KEY=your-key\n", encoding="utf-8")
    (repo_root / ".env").write_text("GEMINI_API_KEY=real-secret-value\n", encoding="utf-8")
    (repo_root / "secrets.enc").write_bytes(b"\x00GITCRYPT\x00secret")
    (repo_root / "src").mkdir()
    (repo_root / "src" / "app.py").write_text("OK = True\n", encoding="utf-8")
    (repo_root / "docs").mkdir()
    diag = repo_root / "docs" / "diag.png"
    diag.write_bytes(b"\x89PNG\r\n\x1a\n")

    spec_text = """
| ID | Falsifiable Condition | Verification Target |
| :--- | :--- | :--- |
| `B2` | `.env.template` and `README.md` document flags | Doc review |
| `B3 [arch]` | App handles edge cases safely | `src/app.py` |
| `B4` | Diagram `docs/diag.png` matches architecture | Multimodal image review |
| `B5` | Never load `.env`, `secrets.enc`, or `../outside.txt` | `.env` |
"""
    spec_path = repo_root / "SPEC.md"
    spec_path.write_text(spec_text, encoding="utf-8")
    _run_git(repo_root, "add", "SPEC.md", ".env.template", "src/app.py", "docs/diag.png")
    _run_git(repo_root, "commit", "-m", "docs: add spec and targets")

    items = eval_rubric.parse_rubric_markdown(spec_text)
    bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=repo_root,
        spec_path=spec_path,
        items=items,
    )

    assert ".env.template" in bundle.evidence_files
    assert "README.md" in bundle.evidence_files
    assert "src/app.py" in bundle.evidence_files
    assert diag.resolve() in {p.resolve() for p in bundle.auto_images}

    assert ".env" not in bundle.evidence_files
    assert "secrets.enc" not in bundle.evidence_files
    assert "real-secret-value" not in bundle.text
    assert "TOP_SECRET_OUTSIDE" not in bundle.text


def test_truncation_telemetry_and_mechanical_pass_downgrade(tmp_path: Path) -> None:
    """Truncated files populate `truncated_sources` and downgrade mechanical `PASS` to L2."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    big_file = repo_root / "src_big.py"
    big_file.write_text("x = 1\n" * 300, encoding="utf-8")

    bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=repo_root,
        spec_path=repo_root / "SPEC.md",
        explicit_files=[Path("src_big.py")],
        max_file_chars=250,
    )
    assert "src_big.py" in bundle.truncated_sources

    total_bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=repo_root,
        spec_path=repo_root / "SPEC.md",
        explicit_files=[Path("src_big.py")],
        max_file_chars=2_000,
        max_chars=400,
    )
    assert "combined_evidence" in total_bundle.truncated_sources

    mech_item = eval_rubric.RubricItem(id="B2", condition="Big module documented", category="mech")
    arch_item = eval_rubric.RubricItem(id="B3", condition="Big module invariant", category="arch")
    answers: dict[str, Any] = {
        "B2": {"noul": 0.95, "confidence": 0.95},
        "B3": {"noul": 0.95, "confidence": 0.95},
    }

    guarded = eval_rubric.evaluate_answers(
        items=[mech_item, arch_item],
        answers=answers,
        truncated_sources=["src_big.py"],
        allow_truncated_pass=False,
    )
    verdicts_by_id = {v.id: v for v in guarded.verdicts}
    assert verdicts_by_id["B2"].status == "ESCALATE_L2_FLASH"
    assert verdicts_by_id["B2"].l2_model == "flash"
    assert verdicts_by_id["B3"].status == "PROVISIONAL_ARCH_PASS"
    assert guarded.exit_code == 1
    assert guarded.warnings

    allowed = eval_rubric.evaluate_answers(
        items=[mech_item, arch_item],
        answers=answers,
        truncated_sources=["src_big.py"],
        allow_truncated_pass=True,
    )
    assert {v.id: v for v in allowed.verdicts}["B2"].status == "PASS"
    assert allowed.exit_code == 0


def test_render_rich_report_escapes_markup_and_displays_tokens(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    """Rich output must escape `[/...]`/`[det]`/`[arch]` safely and display input tokens."""
    evaluation = eval_rubric.RubricEvaluation(
        verdicts=[
            eval_rubric.ItemVerdict(
                id="B2",
                category="mech",
                condition="Link [/python/] covers [lo, hi) and [x]",
                p_yes=0.95,
                confidence=0.95,
                status="PASS",
            )
        ],
        skipped_det_ids=["B1"],
        ratchet_score=0.95,
        exit_code=0,
        final_l2_arch_ids=["B3"],
        input_tokens=2949,
        latency_ms=580.0,
    )
    eval_rubric.render_rich_report(
        evaluation=evaluation,
        spec_path=tmp_path / "docs" / "[spec].md",
        model="gemini-decision-1",
    )
    out = capsys.readouterr().out
    compact = " ".join(part.strip("│ ") for part in out.splitlines())
    assert "Skipped [det]: B1" in compact
    assert "Final L2 [arch] Sign-Off: ['B3']" in compact
    assert "Tokens: 2,949" in compact
    assert "[/python/]" in compact


def test_zero_key_dry_run_and_decisions_absent_file_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--dry-run --json` succeeds offline with zero API key and criteria guard absent files."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    _init_git_repo(tmp_path)

    rc = eval_rubric.main(["--repo-root", str(tmp_path), "--dry-run", "--json"])
    assert rc == 0
    dry_json = json.loads(capsys.readouterr().out)
    for key in (
        "evidence_files",
        "evidence_chars",
        "truncated_sources",
        "warnings",
        "auto_image_count",
    ):
        assert key in dry_json

    item = eval_rubric.RubricItem(id="B2", condition="README documents all flags", category="mech")
    _, questions, _, _ = eval_rubric.build_decision_payload([item], "## Specification")
    q_b2 = questions["B2"]
    instructions_lower = q_b2["instructions"].lower()
    false_desc_lower = q_b2["criteria"]["false_description"].lower()
    assert "absent" in instructions_lower or "missing" in instructions_lower
    assert "uncertain" in instructions_lower
    assert "present" in false_desc_lower or "omitted" in false_desc_lower


def test_explicit_file_outside_repo_root_accepted_while_secrets_blocked(tmp_path: Path) -> None:
    """Allow explicit --file probes outside repo_root whilst still blocking secrets."""
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _init_git_repo(repo_root)
    scratch_dir = tmp_path / "scratch"
    scratch_dir.mkdir(parents=True)
    probe = scratch_dir / "probe.py"
    probe.write_text("def ok() -> bool:\n    return True\n", encoding="utf-8")
    scratch_env = scratch_dir / ".env"
    scratch_env.write_text("SECRET=1\n", encoding="utf-8")

    bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=repo_root,
        spec_path=repo_root / "SPEC.md",
        explicit_files=[probe, scratch_env],
        auto_target_files=False,
    )

    assert str(probe) in bundle.evidence_files
    assert "def ok() -> bool:" in bundle.text
    assert str(scratch_env) not in bundle.evidence_files
    assert "SECRET=1" not in bundle.text


def test_arch_items_route_to_inherit_and_mechanical_to_flash() -> None:
    """Route [arch] items to inherit (`ESCALATE_L2_ARCH`) and [mech] grey-zones to flash."""
    pass_arch = eval_rubric.RubricItem(id="B3", condition="Token check", category="arch")
    grey_arch = eval_rubric.RubricItem(id="B4", condition="Concurrency guard", category="arch")
    grey_mech = eval_rubric.RubricItem(id="B5", condition="Docs match flags", category="mech")
    answers: dict[str, Any] = {
        "B3": {"noul": 0.96, "confidence": 0.92},
        "B4": {"noul": 0.55, "confidence": 0.70},
        "B5": {"noul": 0.55, "confidence": 0.70},
    }

    evaluation = eval_rubric.evaluate_answers(
        items=[pass_arch, grey_arch, grey_mech],
        answers=answers,
    )
    verdicts_by_id = {v.id: v for v in evaluation.verdicts}

    assert verdicts_by_id["B3"].status == "PROVISIONAL_ARCH_PASS"
    assert verdicts_by_id["B3"].l2_model == "inherit"
    assert verdicts_by_id["B4"].status == "ESCALATE_L2_ARCH"
    assert verdicts_by_id["B4"].l2_model == "inherit"
    assert verdicts_by_id["B5"].status == "ESCALATE_L2_FLASH"
    assert verdicts_by_id["B5"].l2_model == "flash"
    assert evaluation.final_l2_arch_ids == ["B3"]
    assert evaluation.escalate_arch_ids == ["B4"]
    assert evaluation.escalate_flash_ids == ["B5"]
    assert evaluation.exit_code == 1


def test_parse_rubric_supports_backticked_tags_after_bold_id() -> None:
    """Parse bullets and tables with backticked tags like `- **B1** `[det]`:`."""
    md = (
        "- **B1** `[det]`: `make check` exits `0`.\n"
        "- **B2** `[arch]`: Auth middleware rejects expired tokens.\n"
        "| ID | Condition | Target |\n"
        "| :--- | :--- | :--- |\n"
        "| **B3** `[docs]` | README updated | Doc review |\n"
    )
    items = eval_rubric.parse_rubric_markdown(md)
    by_id = {item.id: item for item in items}

    assert set(by_id) == {"B1", "B2", "B3"}
    assert by_id["B1"].category == "det"
    assert by_id["B2"].category == "arch"
    assert by_id["B3"].category == "mech"


def test_parse_rubric_supports_nested_bold_and_code_id_wrappers() -> None:
    """Parse nested bold+code wrappers like `**`B1`**` while rejecting prose ID cells."""
    plain_table = (
        "| ID | Condition | Target |\n"
        "| :--- | :--- | :--- |\n"
        "| **`B1`** | Checks pass | Doc review |\n"
    )
    plain_items = eval_rubric.parse_rubric_markdown(plain_table)
    assert [item.id for item in plain_items] == ["B1"]
    assert plain_items[0].category == "mech"

    md = (
        "| ID | Condition | Target |\n"
        "| :--- | :--- | :--- |\n"
        "| **`B1 [det]`** | Static check runs | Doc review |\n"
        "| **`B2`** `[arch]` | Invariant preserved | `src/sim.py` |\n"
        "| `**B3**` [ui] | HUD stays frameless | Visual review |\n"
        "| B7 extra words | Must not parse as rubric ID | Doc review |\n\n"
        "- **`B4 [arch]`**: Concurrency guard holds\n"
        "- [ ] **`B5`** [det]: Task item parses cleanly\n"
    )
    items = eval_rubric.parse_rubric_markdown(md)
    by_id = {item.id: item for item in items}

    assert set(by_id) == {"B1", "B2", "B3", "B4", "B5"}
    assert "B7" not in by_id
    assert by_id["B1"].category == "det"
    assert by_id["B2"].category == "arch"
    assert by_id["B3"].category == "mech"
    assert by_id["B4"].category == "arch"
    assert by_id["B5"].category == "det"


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("make lint + make test", True),
        ("`make check-fast` + `make test-py`", True),
        ("make test-ts", True),
        ("c++ build + make test", False),
    ],
)
def test_deterministic_target_supports_plus_joins_and_make_variants(
    target: str, expected: bool
) -> None:
    """Split whitespace `+`-joined deterministic gates and recognise `make check-fast`/`test-*`."""
    assert eval_rubric._is_deterministic_target(target) is expected


def test_default_evidence_caps_sized_for_single_batch() -> None:
    """Default caps fit 800-line files and single-batch multi-file rubrics without truncating."""
    assert eval_rubric.DEFAULT_MAX_FILE_CHARS == 48_000
    assert eval_rubric.DEFAULT_MAX_EVIDENCE_CHARS == 500_000


def test_rate_limit_gaos_error_degrades_gracefully_with_exit_3(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Non-APIError google.genai 429/spend-cap exceptions must emit JSON and return exit code 3."""
    import google.genai as real_genai

    _init_git_repo(tmp_path)
    (tmp_path / "SPEC.md").write_text(
        "# Spec\n\n- **B2**: README exists (`README.md`)\n", encoding="utf-8"
    )

    class FakeRateLimitError(Exception):
        """Synthetic google.genai._gaos RateLimitError without inheriting APIError."""

    FakeRateLimitError.__module__ = "google.genai._gaos.lib.compat_errors"

    class _FakeDecisions:
        def create(self, **kwargs: Any) -> Any:
            raise FakeRateLimitError(
                "Error code: 429 - {'error': {'message': "
                "'Your project has exceeded its monthly spending cap.', "
                "'code': 'too_many_requests'}}"
            )

    class _FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            self.decisions = _FakeDecisions()

    monkeypatch.setattr(real_genai, "Client", _FakeClient)

    with pytest.raises(eval_rubric.DecisionsApiError) as exc_info:
        eval_rubric.call_decisions_api(
            api_key="test-key",
            model="gemini-decision-1",
            decision_input="evidence",
            questions={"B2": {"type": "noul"}},
        )
    assert exc_info.value.is_auth_error is False
    assert exc_info.value.is_fallback_error is True

    rc = eval_rubric.main(["--repo-root", str(tmp_path), "--api-key", "test-key", "--json"])
    assert rc == 3
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "quota_exceeded"
    assert "spending cap" in payload["message"]
    assert "Tier 2" in payload["fallback_action"]


def test_target_first_ordering_targets_only_and_per_item_truncation_scoping(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Prioritise active target files ahead of dirty tree files and scope truncation checks."""
    _init_git_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "audio.py").write_text("AUDIO_OK = True\n", encoding="utf-8")
    (tmp_path / "dirty_other.py").write_text("x = 1\n" * 150, encoding="utf-8")
    spec_path = tmp_path / "SPEC.md"
    spec_path.write_text(
        "| ID | Condition | Verification Target |\n"
        "| :--- | :--- | :--- |\n"
        "| `B6` | Audio module ok | `src/audio.py` |\n",
        encoding="utf-8",
    )
    _run_git(tmp_path, "add", "SPEC.md", "src/audio.py")
    _run_git(tmp_path, "commit", "-m", "feat: add audio module and spec")

    items = eval_rubric.parse_rubric_markdown(spec_path.read_text(encoding="utf-8"))
    bundle = eval_rubric.collect_repo_evidence_bundle(
        repo_root=tmp_path,
        spec_path=spec_path,
        items=items,
        max_chars=520,
    )
    assert bundle.evidence_files[0] == "src/audio.py"
    assert "AUDIO_OK = True" in bundle.text
    assert "combined_evidence" in bundle.truncated_sources
    assert bundle.item_target_files["B6"] == {"src/audio.py"}

    rc = eval_rubric.main(["--repo-root", str(tmp_path), "--targets-only", "--dry-run", "--json"])
    assert rc == 0
    dry = json.loads(capsys.readouterr().out)
    assert "src/audio.py" in dry["evidence_files"]
    assert "dirty_other.py" not in dry["evidence_files"]

    item_b2 = eval_rubric.RubricItem(id="B2", condition="HUD tests pass", category="mech")
    item_b6 = eval_rubric.RubricItem(id="B6", condition="Audio module ok", category="mech")
    answers: dict[str, Any] = {
        "B2": {"noul": 0.96, "confidence": 0.95},
        "B6": {"noul": 0.96, "confidence": 0.95},
    }
    target_map = {
        "B2": {"tests/sim/phase1HudAndCampaign.test.ts"},
        "B6": {"src/audio.py"},
    }

    scoped = eval_rubric.evaluate_answers(
        items=[item_b2, item_b6],
        answers=answers,
        truncated_sources=["tests/sim/phase1HudAndCampaign.test.ts"],
        item_target_files=target_map,
        spec_label="SPEC.md",
    )
    scoped_map = {v.id: v for v in scoped.verdicts}
    assert scoped_map["B2"].status == "ESCALATE_L2_FLASH"
    assert scoped_map["B6"].status == "PASS"

    for global_trunc in ("combined_evidence", "SPEC.md", "src/audio.py"):
        hit = eval_rubric.evaluate_answers(
            items=[item_b6],
            answers={"B6": {"noul": 0.96, "confidence": 0.95}},
            truncated_sources=[global_trunc],
            item_target_files=target_map,
            spec_label="SPEC.md",
        )
        assert hit.verdicts[0].status == "ESCALATE_L2_FLASH"
