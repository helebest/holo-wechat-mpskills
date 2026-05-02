# Changelog

## v0.2.0 - 2026-05-03

### Changed

- Refactored `wechat-mp-illustrate` into a prompt-driven text-to-image and
  image-to-image helper.
- Removed `python-dotenv`, article planning, `TEXT_MODEL`, `IMAGE_MODEL`, and
  `MAX_DOC_LEN` from `wechat-mp-illustrate`.
- Added OpenRouter image generation configuration through `OPENROUTER_API_KEY`,
  optional `OPENROUTER_IMAGE_MODEL`, and explicit CLI arguments.
- Documented the Codex-native `gpt-image-2` workflow for generated article
  assets without an OpenRouter key.

### Added

- Added mock-tested OpenRouter image client coverage for credentials, model
  precedence, text-to-image, image-to-image references, file output, and error
  handling.
- Added repository checks that keep `wechat-mp-illustrate` free of dotenv and
  old article planning interfaces.

## v0.1.0 - 2026-05-02

Initial versioned release.

- Added canonical WeChat MP skills for typesetting, draft/material management, illustration, and publishing workflow guidance.
- Added distribution build output for individual skill archives, Claude/Codex/OpenClaw plugin archives, well-known discovery indexes, and checksums.
- Added GitHub Actions CI with Ruff, repository validation, build regression checks, examples, and pytest.
- Added realistic example articles and a guarded local draft validation command.
- Added safe manage CLI commands for listing, inspecting, publishing, and deleting drafts or published articles with explicit confirmation for destructive actions.
- Improved typeset output for image captions, table overflow, code wrapping, and mobile-friendly article layout.
