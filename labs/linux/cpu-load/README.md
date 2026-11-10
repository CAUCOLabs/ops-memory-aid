# Controlled CPU Load Lab

**Purpose:** Demonstrate CPU consumption, a container CPU quota, and cgroup v2 throttling with a time-limited workload. This lab is designed for a local Docker environment, **not** production.

## Prerequisites

- Docker Engine / Docker Desktop with permission to run containers.
- Alpine Linux image `alpine:3.21` (the first run may download it).
- A terminal with `docker` available.
- A Linux container using cgroup v2 to reproduce the exact `cpu.max`/`cpu.stat` commands. If using cgroup v1, adapt the inspection commands and record the difference.

## Safety and scope

The workload is deliberately CPU-intensive. It is constrained with `--cpus=1`, `--memory=256m`, and a 60-second timeout. Run only on a development machine with adequate capacity. Do not run on a production host. Commands below create and remove only the named lab container. Avoid running a second copy concurrently.

## Experiment A — Inspect the environment

```sh
docker run --rm alpine:3.21 sh -c '
  cat /etc/os-release | head -n 3
  nproc
  free -h
  cat /proc/loadavg
'
```

These values describe what the Linux container sees; Docker Desktop on macOS uses a Linux VM. `nproc` is not proof of unrestricted CPU quota.

## Experiment B — Time-limited CPU work

```sh
docker run --rm --cpus=1 --memory=256m alpine:3.21 sh -c '
  echo "Starting controlled CPU workload..."
  timeout 15s sh -c "while :; do :; done"
  echo "Workload finished."
'
```

`timeout` may print `Terminated` when it stops the inner shell. That is expected. The outer shell normally continues to the final echo.

## Experiment C — Observe CPU usage

```sh
docker run -d \
  --name ops-cpu-lab \
  --cpus=1 \
  --memory=256m \
  alpine:3.21 \
  sh -c 'timeout 60s sh -c "while :; do :; done"'

docker stats --no-stream ops-cpu-lab
```

Run `docker stats` promptly: the container exits after at most 60 seconds. The CPU percentage is a snapshot and may vary by host and timing.

## Experiment D — Inspect quota and throttling

If the previous container has already exited, remove it before recreating it. The following sequence also cleans up after itself:

```sh
docker rm -f ops-cpu-lab 2>/dev/null || true

docker run -d \
  --name ops-cpu-lab \
  --cpus=1 \
  --memory=256m \
  alpine:3.21 \
  sh -c 'timeout 60s sh -c "while :; do :; done"'

sleep 5

docker exec ops-cpu-lab sh -c '
  echo "=== CPU quota ==="
  cat /sys/fs/cgroup/cpu.max
  echo "=== CPU statistics ==="
  cat /sys/fs/cgroup/cpu.stat
'

docker rm -f ops-cpu-lab
```

A typical cgroup v2 `cpu.max` value is `100000 100000`: one CPU's worth of quota per scheduling period. Throttling counters are cumulative; compare two readings over a measured interval to quantify changes. A nonzero `nr_throttled` does not by itself prove user-visible performance degradation.

## Recorded results — 2026-11-10

The following were **actually observed** on Docker Desktop for macOS, running Alpine Linux 3.21.10:

| Observation | Recorded value |
| --- | --- |
| CPUs visible to initial container (`nproc`) | 10 |
| Initial memory (`free -h`) | 7.7 GiB total; 7.2 GiB available |
| Initial load average | `0.00 0.00 0.00` |
| `docker stats` CPU under load | `99.43%` |
| `docker stats` memory under load | `680KiB / 256MiB` |
| `cpu.max` | `100000 100000` |
| `usage_usec` | `5064774` |
| `user_usec` | `5059751` |
| `system_usec` | `5023` |
| `nr_periods` | `50` |
| `nr_throttled` | `17` |
| `throttled_usec` | `12623` |
| `nr_bursts` / `burst_usec` | `0` / `0` |

**Interpretation:** the process consumed approximately one CPU, the container had a one-CPU quota, and some enforcement periods were throttled. The 17/50 period ratio is **not** a percentage of lost CPU performance. These are single-run measurements and will vary across systems.

## Cleanup and verification

```sh
docker rm -f ops-cpu-lab 2>/dev/null || true
docker ps -a --filter name=ops-cpu-lab
```

The final command should not show a remaining lab container. If the container already exited and was removed, the first command may be harmlessly unsuccessful.

## Validation status

**Validated manually:** time-limited workload, observed CPU usage, quota inspection, throttling inspection, and container cleanup on 2026-11-10. **Not yet validated:** repeatability on native Linux hosts, cgroup v1 compatibility, or behavior under alternative Docker CPU settings.

## Related documents

- [High CPU usage playbook](../../../playbooks/high-cpu-usage.md)
- [Linux performance commands](../../../references/linux/performance-commands.md)
