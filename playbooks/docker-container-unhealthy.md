# Docker Container Unhealthy

## 1. Problem / Symptoms

A container remains running, but Docker reports its health status as `unhealthy`. The application process is alive; one or more configured healthchecks are failing. This does not by itself prove that every application endpoint is unavailable.

## 2. Quick Diagnosis

From the directory containing the Compose file:

```bash
docker compose ps
```

For the example service `app`, obtain its container ID and inspect the health state:

```bash
CONTAINER_ID=$(docker compose ps -q app)
if [ -n "$CONTAINER_ID" ]; then
  docker inspect "$CONTAINER_ID" \
    --format 'Status={{.State.Status}} Health={{if .State.Health}}{{.State.Health.Status}}{{else}}not configured{{end}}'
fi
```

Inspect recent healthcheck attempts:

```bash
if [ -n "$CONTAINER_ID" ]; then
  docker inspect "$CONTAINER_ID" \
    --format '{{if .State.Health}}{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}{{else}}No healthcheck configured{{end}}'
fi
```

## 3. Possible Causes

- The health endpoint returns a failure status (for example, HTTP 503).
- The healthcheck targets the wrong port, path, or network address.
- The application is running but cannot serve requests due to dependency or resource problems.
- The healthcheck command depends on a utility absent from the image.
- Healthcheck timing (`start_period`, `interval`, `timeout`, `retries`) does not match application startup behavior.
- The check itself is too strict or does not represent the intended readiness criterion.

## 4. Step-by-Step Investigation

**Step 1 — Distinguish process state from health state.**

```bash
docker compose ps
```

`Up ... (unhealthy)` means the container is running but its configured healthcheck is failing.

**Step 2 — Inspect healthcheck output.**

```bash
CONTAINER_ID=$(docker compose ps -q app)
if [ -n "$CONTAINER_ID" ]; then
  docker inspect "$CONTAINER_ID" \
    --format '{{if .State.Health}}{{range .State.Health.Log}}{{println .ExitCode .Output}}{{end}}{{else}}No healthcheck configured{{end}}'
fi
```

Read exit codes and error text together. A healthcheck's nonzero exit code is distinct from the main process exit code.

**Step 3 — Review application logs.**

```bash
docker compose logs --timestamps --tail=100 app
```

Look for failed requests, startup delays, dependency errors, and resource warnings.

**Step 4 — Test the endpoint through the intended path.**

If the service is intentionally published on the local host as in the linked lab:

```bash
curl -i --max-time 5 http://127.0.0.1:8000/health
```

A host-side HTTP check is complementary to the healthcheck running inside the container. It does not establish reachability from every external client.

**Step 5 — Review the healthcheck definition.**

```bash
docker compose config
```

Check the command, interval, timeout, retries, and start period. **Warning:** this output may include sensitive interpolated configuration; redact before sharing.

## 5. How to Interpret Results

| Observation | Interpretation / next check |
|---|---|
| `Status=running Health=unhealthy` | Process is alive; investigate healthcheck failures separately. |
| Healthcheck output contains HTTP 503 | Endpoint was reachable but returned a server-error response. |
| Healthcheck reports connection refused | Check listener, bind address, port, and startup timing. |
| Healthcheck reports command not found | Check tools available inside the image and healthcheck definition. |
| Host-side `curl` succeeds while healthcheck fails | Compare the two network paths, endpoints, commands, and environments. |
| No health state | A healthcheck may not be configured; inspect the image and Compose configuration. |

## 6. Resolution Options

Fix the failure demonstrated by the evidence: restore a dependency, correct the endpoint or healthcheck command, or tune startup grace periods if measured startup time warrants it. A temporary 503 may indicate a deliberate readiness failure rather than a crashed process.

Do not disable healthchecks, suppress failures, or restart services repeatedly merely to make dashboards green. In plain Docker, an `unhealthy` status does not automatically restart the container; behavior in orchestrated environments depends on the orchestrator and configuration.

## 7. Verification

After an approved fix, verify both the Docker health status and application response:

```bash
docker compose ps
curl -i --max-time 5 http://127.0.0.1:8000/health
```

Use the `curl` command only when the service is published at that local address and port. Review recent healthcheck output if the status remains `starting` or `unhealthy`, and observe long enough to rule out intermittent failures.

## 8. Safety Notes

- Healthcheck output can contain URLs, headers, or other sensitive information; redact before publishing.
- Do not assume a running process means the service is available to end users.
- Do not assume one healthy endpoint proves all dependencies or routes are functioning.
- Avoid modifying production healthchecks without understanding alerting and orchestration consequences.
- Use host-bound `127.0.0.1` only for this isolated laboratory; real deployment network paths vary.

## 9. References

- [Docker: Dockerfile `HEALTHCHECK`](https://docs.docker.com/reference/dockerfile/#healthcheck)
- [Docker: `docker container inspect`](https://docs.docker.com/reference/cli/docker/container/inspect/)
- [Docker Compose: `ps`](https://docs.docker.com/reference/cli/docker/compose/ps/)
- [Docker Compose: `config`](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Container health laboratory](../labs/docker/container-health/README.md)

## 10. Validation Status

**Partially validated — controlled local laboratory, 2026-11-10.**

In the `container-health` lab, `MODE=unhealthy` produced `Up ... (unhealthy)` while the application returned HTTP 503. `docker inspect` showed `Status=running Health=unhealthy`. Healthcheck logs contained nonzero exit codes and `urllib.error.HTTPError: HTTP Error 503: Service Unavailable`. Recreating the container with `MODE=healthy` restored `healthy` status and HTTP 200.

Other failure causes and production remediation paths are **illustrative and not validated by this experiment**. The variable-based inspection commands above were not separately executed during the recorded session.
