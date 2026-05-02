from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from holo_wechat_wpskills.build import build
from holo_wechat_wpskills.validate import ROOT, SKILL_NAMES, validate_all


EXAMPLE_ARTICLES = [
    "ci-quality-baseline",
    "wechat-draft-workflow",
    "agent-skills-packaging",
]
THEMES = ["minimal", "pier"]


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


def test_examples_have_complete_metadata_and_assets() -> None:
    sys.path.insert(0, str(ROOT / "skills/wechat-mp-typeset/scripts"))
    from markdown_converter import MarkdownConverter

    converter = MarkdownConverter()
    for slug in EXAMPLE_ARTICLES:
        article_dir = ROOT / "examples" / "articles" / slug
        parsed = converter.parse(str(article_dir / "article.md"))

        assert parsed.meta.title
        assert parsed.meta.summary
        assert parsed.meta.cover
        assert Path(parsed.meta.cover).exists()
        assert parsed.images
        assert all(Path(image).exists() for image in parsed.images)


def test_examples_typeset_and_dry_run_without_credentials(tmp_path: Path) -> None:
    source_root = ROOT / "examples" / "articles"
    work_root = tmp_path / "articles"
    shutil.copytree(source_root, work_root)

    for slug in EXAMPLE_ARTICLES:
        article_dir = work_root / slug
        article = article_dir / "article.md"
        cover = article_dir / "cover.png"

        for theme in THEMES:
            output = article_dir / f"article.{theme}.html"
            preview = article_dir / f"article.{theme}.preview.html"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills/wechat-mp-typeset/scripts/typeset.py"),
                    str(article),
                    "--theme",
                    theme,
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

            html = output.read_text(encoding="utf-8")
            assert "<title>" in html
            assert "<img" in html
            assert 'style="' in html
            assert "<table" in html or "<pre" in html
            assert "article-container" in preview.read_text(encoding="utf-8")

            dry_run = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills/wechat-mp-manage/scripts/submit_html_draft.py"),
                    str(output),
                    "--cover",
                    str(cover),
                    "--dry-run",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            assert dry_run.returncode == 0, dry_run.stderr
            payload = json.loads(dry_run.stdout)
            assert payload["title"]
            assert payload["body_length"] > 0
            assert Path(payload["cover_path"]).exists()
            assert payload["local_image_count"] >= 1


def test_example_draft_command_generates_dry_run_payload(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "holo_wechat_wpskills.example_draft",
            "--work-dir",
            str(tmp_path / "examples"),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    payload = json.loads(result.stdout)
    assert payload["mode"] == "dry-run"
    assert payload["slug"] == "wechat-draft-workflow"
    assert payload["theme"] == "pier"
    assert payload["title"] == "把 Markdown 稳定送进公众号草稿箱"
    assert payload["local_image_count"] >= 1
    assert Path(payload["html_path"]).exists()
    assert Path(payload["preview_path"]).exists()


def test_example_draft_create_requires_ignored_env_before_api(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "holo_wechat_wpskills.example_draft",
            "--work-dir",
            str(tmp_path / "examples"),
            "--env-file",
            str(ROOT / "README.md"),
            "--create-draft",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "credential file is not ignored by git" in result.stderr


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
