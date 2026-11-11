# Linux processes and services troubleshooting

## 1. Problem / Symptoms

Diagnose Linux processes that exit unexpectedly, appear stuck, leave zombie children, or fail to start because of port conflicts or permissions. Collect evidence before restarting or killing a process. This playbook focuses on process-level diagnosis. For container-specific lifecycle and health checks, see [Docker container exits immediately](docker-container-exits-immediately.md) and [Docker container unhealthy](docker-container-unhealthy.md). For broader outages, see [Application unresponsive](application-unresponsive.md).

Typical symptoms:

- A service exits immediately, restarts repeatedly, or returns a nonzero exit code.
- A process exists but appears unresponsive or stopped.
- `ps` shows `Z` (zombie) children.
- A server fails with `Address in use` (`EADDRINUSE`).
- A service fails to read or write a required path with `Permission denied` (`EACCES`).

## 2. Quick Diagnosis

Identify the affected host, service or container, start time, and last known good state. Capture read-only evidence before changing anything:

```sh
ps -eo pid,ppid,user,stat,etime,comm
ps -o pid,ppid,stat,comm -p <PID>
cat /proc/<PID>/status
```

Inspect application logs. For a systemd-managed host (reference only; not tested in this lab):

```sh
systemctl status <service-name> --no-pager
journalctl -u <service-name> -n 100 --no-pager
```

If a TCP bind fails, check listeners (requires `ss` on the target system):

```sh
ss -ltnp
```

For access errors, inspect the actual service user and every relevant directory:

```sh
id <service-user>
ls -ld /path /path/to /path/to/resource
```

## 3. Possible Causes

- The application intentionally exits with a success or error status.
- A signal such as `SIGTERM` or `SIGKILL` terminates a process.
- A process is sleeping normally (`S`), stopped (`T`), or waiting on kernel activity (`D`).
- A parent fails to collect terminated children with `wait()` or `waitpid()`, leaving zombies (`Z`).
- A process loses its parent and requires adoption by PID 1 or a subreaper.
- Another listener already owns the requested address and TCP port (`EADDRINUSE`).
- The service identity lacks access to a required resource (`EACCES`).
- A systemd unit or its dependencies are misconfigured (reference only; not reproduced here).

## 4. Step-by-Step Investigation

1. **Record the process and parent:** collect PID, PPID, UID, state, command, elapsed time, and relevant logs before restarting anything.
2. **Determine how it ended:** distinguish application exit codes from signal-derived shell statuses. On Docker, inspect `State.ExitCode` and `State.OOMKilled` together with logs and cgroup evidence.
3. **Interpret state:** `S` is often normal; `T` means stopped; `Z` means the child exited but was not reaped. Do not diagnose a hang from a state letter alone.
4. **For zombies:** inspect the parent PID and whether it waits for children. A zombie cannot be fixed by sending it `SIGKILL`.
5. **For orphaned processes:** inspect PID 1 and any configured init/subreaper. Docker `--init` can adopt and reap orphans, but cannot reap children still owned by a live application.
6. **For startup errors:** inspect the exact bind address/port or denied filesystem path, then verify listener ownership or directory permissions.
7. **For systemd services:** review unit status and logs on an actual systemd host; do not treat these commands as validated by the Alpine container experiments.

## 5. How to Interpret Results

| Evidence | Interpretation | Next check |
| --- | --- | --- |
| Exit `0` | Process reported success; this can still be unexpected for a long-running service. | Was the service expected to remain active? |
| Exit `42` (example) | Application-defined nonzero exit. | Application logs and documented exit codes. |
| Exit `143` | Often shell convention `128 + SIGTERM (15)`. | Who requested termination? |
| Exit `137` | Often shell convention `128 + SIGKILL (9)`; **not proof of OOM**. | OOM state, cgroup events, operator actions. |
| `S` | Interruptible sleep; frequently normal. | Is work progressing? |
| `T` | Stopped or traced process. | Signal history, debugger or job control. |
| `Z` | Child exited; parent has not reaped it. | Parent PID and `wait()` handling. |
| `D` | Uninterruptible sleep, often kernel/I/O wait; not reproduced here. | Storage and kernel evidence. |
| `EADDRINUSE` (errno `98` in tested Linux) | Requested address/port already in use. | Existing listener and binding configuration. |
| `EACCES` (errno `13` in tested Linux) | Insufficient resource access. | UID/GID, path traversal, ownership and permissions. |

Exit codes and process states are clues, not complete root-cause diagnoses.

## 6. Resolution Options

- Preserve diagnostic evidence before any restart or termination.
- For `EADDRINUSE`, identify the existing listener; correct configuration or coordinate port ownership rather than killing processes indiscriminately.
- For `EACCES`, grant only necessary access. Avoid defaulting to root or broad recursive permission changes.
- When authorized to terminate a process, prefer graceful `SIGTERM`. Use `SIGKILL` deliberately as a last resort because cleanup handlers cannot run.
- For zombies, correct the parent's reaping logic or use a suitable init/reaper architecture. `SIGKILL` cannot remove a zombie.
- For a failing systemd unit, address the actual error identified in its configuration and logs; systemd recovery steps are not lab-validated here.

## 7. Verification

After an authorized fix:

1. Confirm the intended process starts and remains active when appropriate.
2. Recheck its PID, parent, state, and logs.
3. For a network service, verify the intended listener and an application-level health check.
4. For permissions, confirm access works under the actual service UID without unnecessary privileges.
5. For child-process issues, confirm terminated children are reaped and no new zombie accumulation occurs.
6. For Docker, confirm container status and inspect exit/OOM metadata where relevant.

## 8. Safety Notes

- `kill`, service restarts, permission changes, and port ownership changes may disrupt production. Obtain authorization and capture evidence first.
- Do not equate exit `137` with OOM without independent evidence.
- Do not kill an existing port listener without identifying its owner and impact.
- Do not attempt to kill a zombie; investigate the parent instead.
- Avoid using root or permissive filesystem modes as a shortcut for `EACCES`.
- The accompanying lab uses disposable containers; no production remediation was tested.

## 9. References

- [Process and service commands](../references/linux/process-service-commands.md)
- [Processes and services lab](../labs/linux/processes-services/README.md)
- [Application unresponsive](application-unresponsive.md)
- [Docker container exits immediately](docker-container-exits-immediately.md)
- [Docker container unhealthy](docker-container-unhealthy.md)

## 10. Validation Status

**Reproduced in disposable Docker containers:** exit codes `0` and `42`; child termination via `SIGTERM` (`143`) and `SIGKILL` (`137`); state transitions `S` → `T` → `S`; a zombie (`Z`) removed by `waitpid()`; orphan adoption by `docker-init` PID 1; TCP `EADDRINUSE`; and filesystem `EACCES` under an unprivileged user.

**Reference only, not reproduced:** real systemd unit failures, `journalctl` results, `D` state, production outages, and production recovery procedures. Docker `--init` does not reap children that still belong to a living application.
