# Hermes Distribution

Hermes can consume the canonical `skills/` directory directly.

Recommended options:

1. Add this repository's `skills/` directory to `~/.hermes/config.yaml` as an external skill directory.
2. Install from a GitHub path after the repository is published.
3. Host `dist/site/.well-known/skills/index.json` and install through Hermes well-known discovery.

This repository does not keep a separate Hermes skill copy. Build outputs are generated from `skills/`.
