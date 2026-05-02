from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from holo_wechat_wpskills.build import build
from holo_wechat_wpskills.validate import ROOT, SKILL_NAMES, validate_all


def test_skills_validate() -> None:
    validate_all()


def test_skill_scripts_show_help() -> None:
    scripts = [
        ROOT / "skills/wechat-mp-typeset/scripts/typeset.py",
        ROOT / "skills/wechat-mp-manage/scripts/submit_html_draft.py",
        ROOT / "skills/wechat-mp-illustrate/scripts/illustrate.py",
    ]
    for script in scripts:
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "usage:" in result.stdout


def test_typeset_smoke(tmp_path: Path) -> None:
    article = tmp_path / "article.md"
    article.write_text(
        "---\ntitle: Smoke Test\nauthor: holo\n---\n\n# Heading\n\nBody text.\n",
        encoding="utf-8",
    )
    output = tmp_path / "article.html"
    preview = tmp_path / "article.preview.html"
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "skills/wechat-mp-typeset/scripts/typeset.py"),
            str(article),
            "--output",
            str(output),
            "--preview",
            str(preview),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Heading" in output.read_text(encoding="utf-8")
    assert "article-container" in preview.read_text(encoding="utf-8")


def test_manage_dry_run_does_not_require_credentials(tmp_path: Path) -> None:
    cover = tmp_path / "cover.png"
    cover.write_bytes(b"fake image")
    html = tmp_path / "article.html"
    html.write_text(
        "<html><head><title>Draft</title></head><body><p>Body</p></body></html>",
        encoding="utf-8",
    )
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "skills/wechat-mp-manage/scripts/submit_html_draft.py"),
            str(html),
            "--cover",
            str(cover),
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["title"] == "Draft"
    assert payload["local_image_count"] == 0


def test_build_outputs_are_generated_from_canonical_skills() -> None:
    artifacts = build(clean=True)
    artifact_names = {path.relative_to(ROOT / "dist").as_posix() for path in artifacts}

    for skill_name in SKILL_NAMES:
        assert f"skills/{skill_name}.zip" in artifact_names
        with zipfile.ZipFile(ROOT / "dist" / "skills" / f"{skill_name}.zip") as archive:
            names = archive.namelist()
        assert f"{skill_name}/SKILL.md" in names
        assert not any("/pyproject.toml" in name for name in names)

    assert "plugins/claude-wechat-mp-plugin.zip" in artifact_names
    assert "plugins/codex-wechat-mp-plugin.zip" in artifact_names
    assert "plugins/openclaw-wechat-mp-plugin.zip" in artifact_names
    assert "site/.well-known/skills/index.json" in artifact_names
    assert "site/.well-known/agent-skills/index.json" in artifact_names
    assert (ROOT / "dist/checksums.txt").exists()
