# OpenClaw Distribution

OpenClaw uses AgentSkills-compatible skill folders and can load this repository's canonical `skills/` directory directly.

Recommended options:

1. Copy or symlink individual folders under `skills/` into an OpenClaw workspace `skills/` directory.
2. Publish individual skills with `clawhub skill publish skills/<skill-name>`.
3. Publish the plugin package generated under `dist/plugins/openclaw-wechat-mp-plugin.zip` when a plugin wrapper is needed.

This repository does not keep a separate OpenClaw workspace copy.
