from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

from holo_wechat_wpskills.build import build
from holo_wechat_wpskills.sync_plugin import compare_skill_trees, sync_plugin_skills
from holo_wechat_wpskills.validate import (
    CLAUDE_PLUGIN_MANIFEST,
    CODEX_PLUGIN_MANIFEST,
    MARKETPLACE_PATH,
    OPENCLAW_PLUGIN_MANIFEST,
    PLUGIN_NAME,
    PLUGIN_SKILLS_DIR,
    ROOT,
    SKILL_NAMES,
    SKILLS_DIR,
    validate_all,
)


EXAMPLE_ARTICLES = [
    "ci-quality-baseline",
    "wechat-draft-workflow",
    "agent-skills-packaging",
]
THEMES = ["minimal", "pier"]


def project_version() -> str:
    match = re.search(
        r'^version\s*=\s*"([^"]+)"',
        (ROOT / "pyproject.toml").read_text(encoding="utf-8"),
        flags=re.MULTILINE,
    )
    assert match is not None
    return match.group(1)


def test_skills_validate() -> None:
    validate_all()


def test_skill_scripts_show_help() -> None:
    scripts = [
        ROOT / "skills/wechat-mp-typeset/scripts/typeset.py",
        ROOT / "skills/wechat-mp-manage/scripts/manage.py",
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


def test_plugin_manifest_versions_match_project_version() -> None:
    version = project_version()
    manifests = [
        CLAUDE_PLUGIN_MANIFEST,
        CODEX_PLUGIN_MANIFEST,
        OPENCLAW_PLUGIN_MANIFEST,
    ]

    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["name"] == PLUGIN_NAME
        assert data["version"] == version


def test_plugin_wrapper_and_codex_marketplace_are_valid() -> None:
    assert not (ROOT / ".claude-plugin/plugin.json").exists()
    assert not (ROOT / ".codex-plugin/plugin.json").exists()
    assert not (ROOT / "openclaw.plugin.json").exists()

    codex = json.loads(CODEX_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    claude = json.loads(CLAUDE_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    openclaw = json.loads(OPENCLAW_PLUGIN_MANIFEST.read_text(encoding="utf-8"))
    marketplace = json.loads(MARKETPLACE_PATH.read_text(encoding="utf-8"))

    assert codex["skills"] == "./skills/"
    assert claude["skills"] == "./skills/"
    assert openclaw["skills"] == ["./skills"]

    assert marketplace["plugins"] == [
        {
            "name": PLUGIN_NAME,
            "source": {"source": "local", "path": f"./plugins/{PLUGIN_NAME}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Productivity",
        }
    ]


def test_generated_plugin_skills_are_ignored_and_syncable(tmp_path: Path) -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert f"plugins/{PLUGIN_NAME}/skills/" in gitignore

    result = subprocess.run(
        ["git", "ls-files", "--", str(PLUGIN_SKILLS_DIR.relative_to(ROOT))],
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    assert result.stdout == ""

    generated = sync_plugin_skills(tmp_path / "skills")
    assert compare_skill_trees(SKILLS_DIR, generated) == []
    for skill_name in SKILL_NAMES:
        assert (generated / skill_name / "SKILL.md").exists()


def test_wechat_manage_does_not_depend_on_dotenv() -> None:
    requirements = ROOT / "skills/wechat-mp-manage/scripts/requirements.txt"
    assert "python-dotenv" not in requirements.read_text(encoding="utf-8")

    forbidden = ["dotenv", "load_dotenv", "find_dotenv", "env_file"]
    for script in (ROOT / "skills/wechat-mp-manage/scripts").glob("*.py"):
        text = script.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{script} must not reference {token}"


def test_wechat_illustrate_does_not_depend_on_dotenv_or_text_planning() -> None:
    requirements = ROOT / "skills/wechat-mp-illustrate/scripts/requirements.txt"
    assert "python-dotenv" not in requirements.read_text(encoding="utf-8")

    forbidden_script_tokens = [
        "dotenv",
        "load_dotenv",
        "find_dotenv",
        "ArticleIllustrator",
        "StoryAnalysis",
        "MAX_DOC_LEN",
        "TEXT_MODEL",
    ]
    for script in (ROOT / "skills/wechat-mp-illustrate/scripts").glob("*.py"):
        text = script.read_text(encoding="utf-8")
        for token in forbidden_script_tokens:
            assert token not in text, f"{script} must not reference {token}"

    docs = "\n".join(
        [
            (ROOT / "skills/wechat-mp-illustrate/SKILL.md").read_text(encoding="utf-8"),
            (ROOT / "skills/wechat-mp-illustrate/references/provider.md").read_text(
                encoding="utf-8"
            ),
            (ROOT / "README.md").read_text(encoding="utf-8"),
        ]
    )
    assert "OPENROUTER_API_KEY" in docs
    assert "OPENROUTER_IMAGE_MODEL" in docs
    assert "gpt-image-2" in docs
    assert "\nTEXT_MODEL=" not in docs
    assert "\nIMAGE_MODEL=" not in docs
    assert "MAX_DOC_LEN" not in docs


def test_tracked_text_uses_wechat_mp_environment_names() -> None:
    result = subprocess.run(
        ["git", "ls-files"],
        text=True,
        capture_output=True,
        check=True,
        cwd=ROOT,
    )
    for relative_path in result.stdout.splitlines():
        path = ROOT / relative_path
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        assert "WECHAT_" + "APPID" not in text, relative_path
        assert "WECHAT_" + "APPSECRET" not in text, relative_path


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
    checksum_entries = (ROOT / "dist/checksums.txt").read_text(encoding="utf-8").splitlines()
    checksummed_artifacts = [
        path for path in artifacts if path.is_file() and path.name != "checksums.txt"
    ]

    for skill_name in SKILL_NAMES:
        assert f"skills/{skill_name}.zip" in artifact_names
        with zipfile.ZipFile(ROOT / "dist" / "skills" / f"{skill_name}.zip") as archive:
            names = archive.namelist()
        assert f"{skill_name}/SKILL.md" in names
        assert not any("/pyproject.toml" in name for name in names)

    plugin_artifacts = {
        "plugins/claude-holo-wechat-mp-plugin.zip": ".claude-plugin/plugin.json",
        "plugins/codex-holo-wechat-mp-plugin.zip": ".codex-plugin/plugin.json",
        "plugins/openclaw-holo-wechat-mp-plugin.zip": "openclaw.plugin.json",
    }
    for artifact_name, manifest_path in plugin_artifacts.items():
        assert artifact_name in artifact_names
        with zipfile.ZipFile(ROOT / "dist" / artifact_name) as archive:
            names = archive.namelist()
        assert manifest_path in names
        for skill_name in SKILL_NAMES:
            assert f"skills/{skill_name}/SKILL.md" in names
        assert not any(name.startswith("src/") for name in names)
        assert not any(name.startswith("tests/") for name in names)
        assert not any(name.startswith(".agents/") for name in names)
        assert not any(name.startswith("plugins/") for name in names)
        assert "pyproject.toml" not in names

    assert "site/.well-known/skills/index.json" in artifact_names
    assert "site/.well-known/agent-skills/index.json" in artifact_names
    for relative in [
        "site/.well-known/skills/index.json",
        "site/.well-known/agent-skills/index.json",
    ]:
        payload = json.loads((ROOT / "dist" / relative).read_text(encoding="utf-8"))
        assert [skill["name"] for skill in payload["skills"]] == SKILL_NAMES

    assert (ROOT / "dist/checksums.txt").exists()
    assert len(checksum_entries) == len(checksummed_artifacts)
    for artifact in checksummed_artifacts:
        assert artifact.relative_to(ROOT / "dist").as_posix() in "\n".join(checksum_entries)
