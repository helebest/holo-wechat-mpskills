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
