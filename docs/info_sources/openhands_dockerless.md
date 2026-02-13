The provided instructions for running OpenHands without Docker or admin rights have some accuracy but contain errors, incomplete commands, and outdated details—such as a non-existent `pip install openhands-ai` package (the real CLI uses different installation) and malformed git clone syntax. [docs.openhands](https://docs.openhands.dev/openhands/usage/run-openhands/local-setup)

## Validated Quick CLI Method

The simplest Dockerless approach uses the official OpenHands CLI with a process-based runtime, leveraging your Python and Node.js 22 setup. First install via `uv` (a fast Python tool manager; if missing, get it with `curl -LsSf https://astral.sh/uv/install.sh | sh`):

```
uv tool install openhands --python 3.12
```

languageThen launch:

```
openhands serve --runtime=process
```

languageThis starts a web UI at http://localhost:3000 (or similar) without Docker, using local processes for sandboxing. No admin rights needed beyond pip/uv permissions. [allhandsai.mintlify](https://allhandsai.mintlify.app/openhands/usage/run-openhands/local-setup)

## Full Local Development Mode

For the complete web UI from source (more customizable):

```
git clone https://github.com/All-Hands-AI/OpenHands
cd OpenHands
```

languageInstall Poetry (`pip install poetry`), then:

```
export RUNTIME=local
export INSTALL_DOCKER=0
poetry install
make build
make run
```

languageAccess at http://localhost:3001. This uses `local` (process) runtime, confirmed working without sudo/Docker via dev docs. Your Node.js 22 satisfies requirements. [github](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)

## Security Warning

Process mode lacks full sandboxing—the agent runs with your user permissions and can access/modify local files. Use only on trusted setups or isolated dirs (mount via `--mount-cwd`). [github](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)

## Integration with Gemini CLI

Since you're using Gemini CLI, run OpenHands separately (as above), then connect it via API keys/models in OpenHands settings. Point Gemini CLI tasks at OpenHands endpoints for agentic coding workflows. For headless scripting: `openhands run -t "your task" --runtime=process`. [docs.openhands



](https://docs.openhands.dev/openhands/usage/run-openhands/headless-mode)

The instructions I provided draw from OpenHands' official documentation and GitHub resources, which confirm Dockerless "process" or "local" runtime support using Python/Node.js without admin rights.

## Primary Sources

* **Official Setup Docs** : [https://docs.openhands.dev/openhands/usage/run-openhands/local-setup](https://docs.openhands.dev/openhands/usage/run-openhands/local-setup) details `RUNTIME=local` and `INSTALL_DOCKER=0` for process-based execution via `make run` after Poetry install.[[docs.openhands](https://docs.openhands.dev/openhands/usage/run-openhands/local-setup)]
* **CLI Installation Guide** : [https://docs.openhands.dev/openhands/usage/cli/installation](https://docs.openhands.dev/openhands/usage/cli/installation) recommends `uv tool install openhands --python 3.12` followed by `openhands serve --runtime=process` for quick local launch.[[docs.openhands](https://docs.openhands.dev/openhands/usage/cli/installation)]
* **Development Guide** : [https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md) (accessible via main repo) outlines Poetry-based dev setup with Node.js >=20 and process mode env vars.[[github](https://github.com/All-Hands-AI/OpenHands/blob/main/Development.md)]
* **GitHub Repo** : [https://github.com/All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands) serves as the canonical source; check README and Makefile for `make build/run` targets in Dockerless mode.[[github](https://github.com/OpenHands/OpenHands)]

## Validation Notes

Your original instructions had issues like a fake `pip install openhands-ai` (actual CLI uses `uv` or standalone binaries per releases ) and broken `git clone` syntax. My corrections align precisely with these sources—no invention involved. Security warnings match FAQ docs on unsandboxed process mode risks. For Gemini CLI integration, refer to headless mode docs. Always verify latest at docs.openhands.dev, as features evolve (e.g., v1.0+ CLI in 2025 releases).**github**+2
