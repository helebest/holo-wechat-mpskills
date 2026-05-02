"""Repository validation for canonical WeChat MP skills."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / "skills"
SKILL_NAMES = [
    "wechat-mp-typeset",
    "wechat-mp-manage",
    "wechat-mp-illustrate",
    "wechat-mp-publish",
]
BANNED_NAMES = {
    ".env",
    ".venv",
    ".wechat_token_cache.json",
    "CHANGELOG.md",
    "README.md",
    "dist",
    "pyproject.toml",
    "uv.lock",
}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ValidationError(Exception):
    """Raised when repository validation fails."""


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValidationError(f"{path} is missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValidationError(f"{path} has unterminated YAML frontmatter")

    data: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise ValidationError(f"{path} has invalid frontmatter line: {line}")
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def validate_skill(skill_dir: Path) -> None:
    name = skill_dir.name
    if not NAME_RE.match(name):
        raise ValidationError(f"Invalid skill directory name: {name}")

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValidationError(f"Missing {skill_md}")

    frontmatter = parse_frontmatter(skill_md)
    if frontmatter.get("name") != name:
        raise ValidationError(f"{skill_md} name must match directory name")
    if not frontmatter.get("description"):
        raise ValidationError(f"{skill_md} description is required")

    scripts_dir = skill_dir / "scripts"
    if scripts_dir.exists() and not (scripts_dir / "requirements.txt").exists():
        raise ValidationError(f"{scripts_dir} must contain requirements.txt")

    for path in skill_dir.rglob("*"):
        if path.name in BANNED_NAMES:
            raise ValidationError(f"Banned file or directory in skill package: {path}")


def validate_plugin_manifests() -> None:
    manifests = [
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / "openclaw.plugin.json",
    ]
    for manifest in manifests:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        if data.get("skills") not in ("./skills/", ["./skills"]):
            raise ValidationError(f"{manifest} must reference the canonical skills directory")


def validate_all() -> None:
    if not SKILLS_DIR.exists():
        raise ValidationError("Missing skills directory")

    actual = sorted(path.name for path in SKILLS_DIR.iterdir() if path.is_dir())
    if actual != sorted(SKILL_NAMES):
        raise ValidationError(f"Unexpected skills: {actual}")

    for skill_name in SKILL_NAMES:
        validate_skill(SKILLS_DIR / skill_name)

    validate_plugin_manifests()


def main() -> int:
    try:
        validate_all()
    except Exception as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        return 1
    print("validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
