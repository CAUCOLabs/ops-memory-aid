# Linux process and service commands

Use commands on the intended Linux host/container. Prefer read-only inspection; avoid changing or terminating processes without identifying their owner and impact.

## Process discovery and status

```sh
ps -eo pid,ppid,user,stat,etime,comm
ps -o pid,ppid,stat,comm -p <PID>
cat /proc/<PID>/status
cat /proc/<PID>/comm
top
pgrep -a <process-name>
```

In `/proc/<PID>/status`, inspect `Name`, `State`, `Pid`, `PPid`, and `Threads`. Common states: `R` runnable, `S` interruptible sleep, `D` uninterruptible sleep, `T` stopped/traced, `Z` zombie. A state is a snapshot, not a diagnosis.

## Signals and exit codes

```sh
kill -l
kill -TERM <PID>   # request graceful termination; disruptive
kill -KILL <PID>   # force termination; disruptive, last resort
```

Shells commonly report a signal-terminated child as `128 + signal number`: `143` for `SIGTERM` (15), `137` for `SIGKILL` (9). Exit `137` does not independently prove an out-of-memory kill. A zombie cannot be removed with `kill`; its parent must reap it.

## Docker-specific inspection

```sh
docker ps -a
docker logs <container>
docker inspect --format '{{.State.ExitCode}} {{.State.OOMKilled}}' <container>
docker top <container>
```

`docker run --init` adds a minimal PID 1 reaper (`docker-init` in the tested Docker Desktop setup). It does not replace an application's responsibility to wait for its own live children.

## TCP listeners and startup conflicts

```sh
ss -ltnp
```

`ss` may require the `iproute2` package. A bind failure with `EADDRINUSE` means the requested local address/port cannot be bound under the current socket settings. Inspect the existing listener and configuration before making changes.

## User identity and filesystem access

```sh
id <service-user>
ls -ld /path /path/to /path/to/resource
stat /path/to/resource
```

An `EACCES` error may involve directory traversal, ownership, mode bits, ACLs, or additional security policy. Confirm the service's effective identity before altering permissions.

## systemd services (reference only; not tested in this lab)

```sh
systemctl status <service-name> --no-pager
systemctl show <service-name> -p MainPID -p ExecMainStatus -p Result
journalctl -u <service-name> -n 100 --no-pager
systemctl cat <service-name>
```

These commands require a Linux environment with systemd. The Alpine containers used for Stage 4.4 do not run systemd. Do not infer unit behavior from the Docker-only experiments.

## Evidence and safety

Record the timestamp, PID, PPID, process state, relevant log lines, exit status, container OOM metadata if applicable, and any changes made. Never terminate an unidentified production PID or broadly modify file permissions as a first diagnostic step.

See [Linux processes and services troubleshooting](../../playbooks/linux-processes-services-troubleshooting.md) and the [reproducible lab](../../labs/linux/processes-services/README.md).
