# Docker Container Exits Immediately

## 1. Problem / Symptoms

A Docker container starts and then stops, sometimes before an operator can inspect it with `docker compose ps`. The application may never become available. A nonzero exit code is a clue, not a root-cause diagnosis.

## 2. Quick Diagnosis

Run these commands from the directory containing the relevant Compose file:

```bash
docker compose ps -a
docker compose logs --tail=100 app
```

For the example Compose service named `app`, inspect the container state:

```bash
CONTAINER_ID=$(docker compose ps -a -q app)
if [ -n "$CONTAINER_ID" ]; then
  docker inspect "$CONTAINER_ID" \
    --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} Error={{.State.Error}}'
fi
```

If the service has a different name, replace `app` with its actual Compose service name. Do not assume that an empty `docker compose ps` means no container was created; use `-a` to include stopped containers.

## 3. Possible Causes

- The application fails during startup because of configuration or missing environment variables.
- Its entrypoint or command is incorrect or references a missing executable.
- A required file, mount, or dependency is unavailable.
- The process is killed because of resource pressure; inspect `OOMKilled` rather than guessing.
- The process completes its intended task and exits successfully (`ExitCode=0`); this may be normal for a job.
- An external signal or an orchestrator stops the process.

## 4. Step-by-Step Investigation

**Step 1 — Establish what actually stopped.**

```bash
docker compose ps -a
```

Record the service, exit code, and timing. Check whether a restart policy is masking repeated failures.

**Step 2 — Read startup logs before changing anything.**

```bash
docker compose logs --timestamps --tail=100 app
```

Look for the first relevant error and distinguish application messages from Docker's own state reporting. Logs may be absent if the process failed before it could write output.

**Step 3 — Inspect the recorded exit state.**

```bash
CONTAINER_ID=$(docker compose ps -a -q app)
if [ -n "$CONTAINER_ID" ]; then
  docker inspect "$CONTAINER_ID" \
    --format 'Started={{.State.StartedAt}} Finished={{.State.FinishedAt}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}} Error={{.State.Error}}'
fi
```

**Step 4 — Review the effective Compose configuration.**

```bash
docker compose config
```

This can reveal unexpected command, mount, or environment interpolation. **Warning:** rendered configuration can contain secrets; do not paste or publish it without redaction.

**Step 5 — Form a hypothesis.** Compare the logs and state with the configured command, dependencies, and expected workload lifecycle. Only then decide whether a change or controlled reproduction is appropriate.

## 5. How to Interpret Results

| Observation | Interpretation / next check |
|---|---|
| `Exited (1)` and an application `FATAL` message | Application reported failure; investigate the specific logged condition. |
| `Exited (0)` | Process completed successfully; confirm whether this is expected for a long-running service. |
| `OOMKilled=true` | Investigate memory usage and limits; do not infer the root cause from exit code alone. |
| No application logs | Check entrypoint, command, runtime errors, and container creation events. |
| Repeated starts and stops | Review restart policy and the earliest failure, not only the latest attempt. |

## 6. Resolution Options

Choose a resolution only after the evidence supports it: correct invalid configuration, repair a missing dependency, fix an entrypoint or startup error, or address a verified resource constraint. For intentionally short-lived jobs, adjust monitoring expectations rather than forcing the process to remain running.

Do not blindly add `restart: always`, restart production workloads, or change memory limits to conceal an unresolved failure. Apply changes through the normal deployment and rollback process.

## 7. Verification

After an approved fix, verify the intended lifecycle:

```bash
docker compose ps -a
docker compose logs --tail=50 app
```

For a long-running HTTP service, additionally verify its health endpoint and container health status, if configured. Confirm that the original error does not recur over a suitable observation period.

## 8. Safety Notes

- Prefer inspection and logs before recreating containers; recreation can destroy ephemeral state.
- Avoid printing secrets from environment variables or rendered Compose configuration.
- Do not run destructive cleanup (`docker system prune`, volume removal) as a diagnostic shortcut.
- Distinguish an expected batch-job exit from an incident.
- Verify service identity and deployment context before acting on a production container.

## 9. References

- [Docker: `docker container inspect`](https://docs.docker.com/reference/cli/docker/container/inspect/)
- [Docker Compose: `ps`](https://docs.docker.com/reference/cli/docker/compose/ps/)
- [Docker Compose: `logs`](https://docs.docker.com/reference/cli/docker/compose/logs/)
- [Docker Compose: `config`](https://docs.docker.com/reference/cli/docker/compose/config/)
- [Container health laboratory](../labs/docker/container-health/README.md)

## 10. Validation Status

**Partially validated — controlled local laboratory, 2026-11-10.**

In the `container-health` lab, `MODE=crash` caused a container to exit with code `1`. `docker compose ps -a` showed `Exited (1)`; `docker compose logs` showed `FATAL: Simulated application startup failure`; and `docker inspect` confirmed `Status=exited ExitCode=1`.

The broader diagnostic branches (OOM, entrypoint errors, missing mounts, restart loops, and production remediation) are **guidance only and have not been tested in this lab**. The variable-based inspection commands above were not separately executed during the recorded session.
