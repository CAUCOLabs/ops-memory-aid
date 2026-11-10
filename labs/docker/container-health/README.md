# Docker Container Health — Troubleshooting Lab

A small, reproducible Docker Compose lab demonstrating why **a running container is not necessarily a healthy application**.

Part of **Ops Memory Aid** — *Understand the system. Document the details.*

## Purpose

This lab reproduces three distinct operational states and verifies recovery:

| Scenario | Main process | Docker health | `/health` response |
| --- | --- | --- | --- |
| Healthy | Running | `healthy` | HTTP 200 |
| Startup crash | Exited with code 1 | Not applicable after exit | Not served |
| Unhealthy application | Running | `unhealthy` | HTTP 503 |
| Recovery | Running | `healthy` | HTTP 200 |

The failures are deliberately simulated. The results do **not** establish how every production workload or orchestrator behaves.

## Requirements

- Docker Engine with the Docker Compose v2 plugin
- `curl` on the host
- An available host port `127.0.0.1:8000`

No Python installation or third-party Python packages are needed on the host. The image uses `python:3.12-alpine` and Python's standard library.

## Files

```text
container-health/
├── .gitignore
├── Dockerfile
├── README.md
├── app.py
└── compose.yaml
```

`app.py` reads the `MODE` environment variable:

- `healthy` (default): starts an HTTP server and returns HTTP 200 at `/health`.
- `crash`: logs a simulated fatal startup error and exits with code 1.
- `unhealthy`: keeps the HTTP server running but returns HTTP 503 at `/health`.

The Dockerfile defines a healthcheck that requests `http://127.0.0.1:8000/health` **inside the container**. Compose publishes the service on the host's loopback interface only and disables automatic restarts.

## Setup

Run every command below from `labs/docker/container-health/`:

```bash
cd labs/docker/container-health

docker compose config
docker compose build
```

If you are already in this directory, omit the `cd` command. The examples assume Compose's default project name (`container-health`), which produces the container name `container-health-app-1`.

## Experiment 1 — Healthy

```bash
MODE=healthy docker compose up -d --force-recreate
```

Allow enough time for the healthcheck to complete, then inspect:

```bash
docker compose ps
curl -i http://127.0.0.1:8000/health
docker compose logs --tail=20
```

**Expected:** `Up ... (healthy)`, HTTP 200, and successful `/health` requests in the application logs.

**Observed on 2026-11-10:** Docker reported `Up ... (healthy)`; `curl` returned `HTTP/1.0 200 OK` with body `OK`; the logs showed successful health requests. **PASS.**

## Experiment 2 — Startup crash

```bash
MODE=crash docker compose up -d --force-recreate
```

The `up -d` command can report that the container started even if its main process exits immediately afterward. Inspect the **stopped** container as well:

```bash
docker compose ps -a
docker compose logs --tail=30
docker inspect container-health-app-1 \
  --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}}'
```

**Expected:** `Exited (1)` and an application log explaining the simulated startup failure.

**Observed on 2026-11-10:**

```text
Status=exited ExitCode=1
FATAL: Simulated application startup failure
```

**PASS.** Exit code 1 establishes that the process failed; the log supplies the lab-specific explanation. In real incidents, do not assume every exit code 1 has the same cause.

## Experiment 3 — Running but unhealthy

```bash
MODE=unhealthy docker compose up -d --force-recreate
```

Wait for repeated healthchecks (approximately 20 seconds with the supplied Dockerfile), then inspect:

```bash
docker compose ps
curl -i http://127.0.0.1:8000/health
docker inspect container-health-app-1 \
  --format 'Status={{.State.Status}} Health={{.State.Health.Status}}'
docker inspect container-health-app-1 \
  --format '{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}'
```

**Expected:** the container remains running, Docker reports `unhealthy`, the endpoint returns HTTP 503, and healthcheck attempts fail with a nonzero exit code.

**Observed on 2026-11-10:**

```text
Status=running Health=unhealthy
HTTP/1.0 503 Service Unavailable
urllib.error.HTTPError: HTTP Error 503: Service Unavailable
```

Healthcheck records showed exit code `1`. **PASS.** The Python traceback is expected here: `urllib.request.urlopen()` raises `HTTPError` on HTTP 503. The failing healthcheck did not, by itself, stop the container.

## Experiment 4 — Recovery

```bash
MODE=healthy docker compose up -d --force-recreate
```

After healthchecks have run:

```bash
docker compose ps
curl -i http://127.0.0.1:8000/health
```

**Expected:** the recreated container returns to `healthy` and the endpoint returns HTTP 200.

**Observed on 2026-11-10:** Docker reported `Up ... (healthy)` and `curl` returned `HTTP/1.0 200 OK` with body `OK`. **PASS.** This validates recovery by **recreating the lab container with a corrected mode**, not an in-place repair of a production application.

## Cleanup

```bash
docker compose down
docker compose ps -a
```

**Observed on 2026-11-10:** Compose removed the lab container and its network, and `docker compose ps -a` displayed no containers. **PASS.** The built image remains available locally; `down` does not remove it by default.

## How to interpret the evidence

1. **Process state and application health are different signals.** `running` means the container's main process is alive; it does not guarantee successful requests.
2. **An exit code is not a root-cause analysis.** Use `docker compose logs` and relevant application evidence to understand a failure.
3. **A healthcheck failure does not automatically restart a Docker container.** Restart behavior depends on the runtime and orchestration configuration.
4. **A successful host request and a successful in-container healthcheck test different paths.** The host request uses the published port; the healthcheck targets loopback inside the container.
5. **Verify remediation.** Recheck both Docker state and the application endpoint after a change.

## Safety and limitations

- This lab is intended for local, isolated learning, not production deployment.
- Compose publishes only `127.0.0.1:8000` on the host. Do not change this to a public bind address without considering exposure.
- The lab uses no credentials, persistent data, or external Python dependencies.
- `--force-recreate` intentionally replaces the lab container; do not copy that step into a production runbook without assessing its impact.
- The image tag `python:3.12-alpine` may resolve to a newer patch release on a later build. For strict reproducibility, pin an immutable image digest.
- Container names may differ if the Compose project name is overridden. Use `docker compose ps -a` to find the actual name before running `docker inspect`.
- The test demonstrates HTTP health and startup behavior only; it does not test DNS, TLS, multi-container networking, resource exhaustion, Kubernetes, or production readiness policies.

## Validation record

| Item | Observed environment |
| --- | --- |
| Date | 2026-11-10 |
| Host | macOS |
| Docker Engine | 28.3.2 |
| Docker Compose | v2.38.2-desktop.1 |
| Base image | `python:3.12-alpine` |
| Python in container | 3.12.16 |
| Scenarios executed | Healthy, crash, unhealthy, recovery, cleanup |
| Overall result | **PASS — for these specific lab scenarios** |

These observations were reported from a real local run. They should not be represented as automated CI coverage or as validation on Linux hosts or other Docker versions.
