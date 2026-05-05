# OpenClaw Distribution

OpenClaw uses AgentSkills-compatible skill folders and can load this repository's
canonical `skills/` directory directly. The `holo-wechat-mp` plugin wrapper also
ships `openclaw.plugin.json` under `plugins/holo-wechat-mp/` for plugin-based
distribution.

Recommended options:

1. Copy or symlink individual folders under `skills/` into an OpenClaw workspace `skills/` directory.
2. Publish individual skills with `clawhub skill publish skills/<skill-name>`.
3. Publish the plugin package generated under `dist/plugins/openclaw-holo-wechat-mp-plugin.zip` when a plugin wrapper is needed.

This repository does not keep a separate OpenClaw workspace copy. The local
plugin `skills/` directory is generated with `holo-wechat-sync-plugin` when
wrapper-level testing is needed.
