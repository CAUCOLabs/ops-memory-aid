# Controlled Linux memory-limit / OOM lab

This lab reproduces an **in-container cgroup OOM kill**, not a host-wide memory exhaustion test. Run on a non-production Docker installation. The image may need to be downloaded. Commands assume Docker Desktop or a Docker Engine with cgroup v2; check availability of `/sys/fs/cgroup/memory.events` first.

## Safety boundaries
- Disposable containers with unique names, `--memory=128m`, `--memory-swap=128m` (no extra swap), and bounded allocations.
- Python allocation is capped at 256 MiB by `allocate_memory.py`; it is intentionally larger than the 128 MiB cgroup limit in the OOM scenario.
- The shell supervisor sleeps for at most 60 seconds. Clean up only the named lab containers.
- Do not run on production infrastructure. Resource limits mitigate but do not eliminate all host-side risk.

## Prerequisites
From the **repository root**, ensure Docker is running and the file `labs/linux/memory-pressure/allocate_memory.py` exists. The first image pull may take time.

## Scenario A — Inspect limits (read-only)
```sh
docker run --rm --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  cat /sys/fs/cgroup/memory.max
  cat /sys/fs/cgroup/memory.swap.max
  cat /sys/fs/cgroup/memory.current
  cat /sys/fs/cgroup/memory.events
'
```
Observed on 2026-11-11: `memory.max=134217728`, `memory.swap.max=0`, `memory.current=3325952`, and all displayed event counters zero. Values may vary.

## Scenario B — Observe an OOM-killed main process
```sh
docker run -d --name ops-memory-lab --memory=128m --memory-swap=128m \
  -v "$PWD/labs/linux/memory-pressure/allocate_memory.py:/lab/allocate_memory.py:ro" \
  python:3.12-alpine python /lab/allocate_memory.py --mib 192 --hold-seconds 10

docker wait ops-memory-lab
docker inspect ops-memory-lab --format 'Status={{.State.Status}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'
docker logs ops-memory-lab
docker rm ops-memory-lab
```
**Expected:** often exit 137 and `OOMKilled=true`, but actual results must be observed. The earlier manual experiment using equivalent inline Python produced exit `137`, `OOMKilled=true`, and only `Allocating 192 MiB...` in the logs. **The file-based variant above has not yet been separately executed.**

## Scenario C — Keep supervisor alive to read OOM events
```sh
docker run -d --name ops-memory-events --memory=128m --memory-swap=128m \
  -v "$PWD/labs/linux/memory-pressure/allocate_memory.py:/lab/allocate_memory.py:ro" \
  python:3.12-alpine sh -c '
    python /lab/allocate_memory.py --mib 192 --hold-seconds 10
    echo "Python exit code: $?"
    sleep 60
  '

# Run promptly, before the supervisor exits:
docker exec ops-memory-events cat /sys/fs/cgroup/memory.events
docker exec ops-memory-events cat /sys/fs/cgroup/memory.current
docker logs ops-memory-events
docker rm -f ops-memory-events
```
**Observed with equivalent inline Python on 2026-11-11:** `max=130`, `oom=1`, `oom_kill=1`, `oom_group_kill=0`, `memory.current=4149248`, and `Python exit code: 137`. The shell supervisor survived. These counters are cumulative for that cgroup; `max=130` does **not** mean 130 OOM kills. **The file-based variant has not yet been separately executed.**

## Interpretation and limitations
- `OOMKilled=true` plus exit 137 supports an OOM diagnosis for the container's main process; exit 137 alone is insufficient.
- `memory.events:oom_kill` corroborates an OOM kill within the cgroup, even when the supervisor remains alive.
- These experiments do **not** demonstrate host-wide OOM, sustained memory pressure, swap activity, or a memory leak.
- Docker Desktop on macOS runs Linux containers in a VM; measurements describe the Linux container environment, not native macOS memory accounting.

## Related documentation
- [Linux memory pressure playbook](../../../playbooks/linux-memory-pressure.md)
- [Memory troubleshooting commands](../../../references/linux/memory-commands.md)
