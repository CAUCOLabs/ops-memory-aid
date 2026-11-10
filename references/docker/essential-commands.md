# Essential Docker Troubleshooting Commands

A compact, problem-first reference for investigating Docker containers and Docker Compose services. Commands are diagnostic by default; operations that change state are identified explicitly.

> Understand the system. Document the details.

## 1. Establish the environment

```bash
docker version
docker compose version
docker info --format 'Server={{.ServerVersion}}'
```

If the daemon is unavailable, `docker info` will fail even when the CLI is installed. Check that Docker Engine is running before investigating application behavior.

## 2. Find the affected container

From the directory containing `compose.yaml`:

```bash
docker compose ps -a
docker compose config --services
```

For containers outside the Compose project:

```bash
docker ps -a
```

**Interpretation:** `Up` means the main process is running; `Exited (1)` means it terminated with exit code 1. Neither state alone explains the root cause.

## 3. Read application logs

```bash
docker compose logs --tail=50 app
docker compose logs --timestamps --tail=50 app
```

Replace `app` with the service name shown by `docker compose config --services`. Logs may contain credentials, tokens, or personal data; redact them before sharing.

## 4. Inspect process state and exit code

For the container used in the reproducible lab:

```bash
CONTAINER=container-health-app-1
docker inspect "$CONTAINER" \
  --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'
```

**Interpretation:** a nonzero exit code indicates a failed process, but logs and context are needed to determine why. `OOMKilled=true` is evidence of an out-of-memory kill; do not infer OOM from exit code alone.

For a different project, set `CONTAINER` to its actual name or ID first.

## 5. Inspect healthcheck status and failures

```bash
CONTAINER=container-health-app-1
docker inspect "$CONTAINER" \
  --format '{{if .State.Health}}Status={{.State.Status}} Health={{.State.Health.Status}}{{else}}Status={{.State.Status}} Health=not-configured{{end}}'
```

If a healthcheck is configured, inspect its recent results:

```bash
docker inspect "$CONTAINER" \
  --format '{{if .State.Health}}{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}{{else}}No healthcheck configured{{end}}'
```

**Interpretation:** `running` and `unhealthy` can occur together. Healthcheck exit codes are separate from the main process exit code. A failing Docker healthcheck does not, by itself, restart or terminate a container.

## 6. Check ports and connectivity

```bash
docker compose ps
curl -i --max-time 5 http://127.0.0.1:8000/health
```

The URL is specific to the accompanying lab. For another service, confirm the actual published port and endpoint before running `curl`.

**Interpretation:** an HTTP `503` indicates that an HTTP server responded but reported service unavailability. A connection refusal or timeout is a different symptom; investigate binding, port publishing, network paths, and listeners.

## 7. Check Compose configuration

```bash
docker compose config
```

Review effective environment variables, published ports, restart policy, build context, and service names. **Warning:** rendered configuration may contain secrets; do not paste it into public issues without redaction.

## 8. Reproduce the validated lab scenarios

Run these commands **only** from `labs/docker/container-health/` in this repository. They deliberately recreate the lab container.

```bash
docker compose build
MODE=healthy docker compose up -d --force-recreate
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Expected: `healthy` and HTTP 200.

```bash
MODE=crash docker compose up -d --force-recreate
docker compose ps -a
docker compose logs --tail=30
```

Expected: `Exited (1)` and the simulated startup-failure message.

```bash
MODE=unhealthy docker compose up -d --force-recreate
docker compose ps
curl -i http://127.0.0.1:8000/health
```

Wait for the healthcheck retries to complete. Expected: `running`, `unhealthy`, and HTTP 503.

Restore the healthy mode and verify it before cleanup:

```bash
MODE=healthy docker compose up -d --force-recreate
docker compose ps
curl -i http://127.0.0.1:8000/health
```

## 9. Cleanup (state-changing)

**Only in the lab directory:**

```bash
docker compose down
docker compose ps -a
```

`down` removes the project's containers and network. Do not run it against a production Compose project without understanding its impact. The lab's locally built image remains available.

## 10. Validation status

**Tested in the accompanying lab (2026-11-10):** Compose build and config; `ps` / `ps -a`; application logs; `docker inspect` for process and health status; `curl` responses; healthy, crash, unhealthy, recovery; and Compose cleanup.

**Illustrative / not separately validated here:** general-purpose diagnostic variants such as timestamped logs, OOM inspection, and inspection of containers without a configured healthcheck. Adapt to the target environment.

Lab environment: macOS; Docker Engine 28.3.2; Docker Compose v2.38.2-desktop.1; Python 3.12.16 in `python:3.12-alpine`.

## Related resources

- [Docker Container Health lab](../../labs/docker/container-health/README.md)
- [Container exits immediately](../../playbooks/docker-container-exits-immediately.md)
- [Container unhealthy](../../playbooks/docker-container-unhealthy.md)
- [Docker CLI documentation](https://docs.docker.com/reference/cli/docker/)
- [Docker Compose CLI documentation](https://docs.docker.com/reference/cli/docker/compose/)
