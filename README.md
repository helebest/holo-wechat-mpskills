# holo-wechat-mpskills

Canonical Agent Skills for WeChat Official Account article production.

The source of truth is the `skills/` directory:

- `wechat-mp-typeset`
- `wechat-mp-manage`
- `wechat-mp-illustrate`
- `wechat-mp-publish`

The repository uses `uv` for development and testing only. Deployable skills do not include `pyproject.toml`; Python dependencies are declared in each skill's `scripts/requirements.txt`.

Build release artifacts:

```bash
uv run holo-wechat-build
```

Release artifacts are written to ignored `dist/` paths:

- `dist/skills/*.zip`
- `dist/plugins/*-wechat-mp-plugin.zip`
- `dist/site/.well-known/skills/index.json`
- `dist/site/.well-known/agent-skills/index.json`
- `dist/checksums.txt`

Prepare a versioned release:

```bash
uv sync --locked
uv run ruff check .
uv run ruff format --check .
uv run holo-wechat-validate
uv run python -m pytest --basetemp .tmp/pytest -p no:cacheprovider
uv run holo-wechat-build
git tag v0.1.0
```

Validate the repository:

```bash
uv run holo-wechat-validate
```

Run the local quality baseline used by CI:

```bash
uv sync
uv run ruff check .
uv run ruff format --check .
uv run holo-wechat-validate
uv run python -c "from pathlib import Path; Path('.tmp').mkdir(exist_ok=True)"
uv run python -m pytest --basetemp .tmp/pytest -p no:cacheprovider
```

Generate and validate the default example article without credentials:

```bash
uv run holo-wechat-example-draft
```

Create a real WeChat draft locally after copying ignored credentials into `.env`:

```bash
uv run holo-wechat-example-draft --create-draft
```

The real draft command prints only the created draft `media_id` on success. It does not publish.
