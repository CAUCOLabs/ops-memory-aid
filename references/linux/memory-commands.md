# Linux memory troubleshooting commands

These are diagnostic references. Availability and output vary by distribution, kernel, privileges, and cgroup version. Commands below are **not all experimentally validated** in this repository.

## Host memory overview
```sh
free -h                     # RAM/swap; focus on available, not just free
cat /proc/meminfo            # MemAvailable, SwapTotal, SwapFree, etc.
vmstat 1 5                   # si/so swap in/out, runnable/blocked processes
cat /proc/pressure/memory    # PSI memory pressure (when supported)
```

## Process-level investigation
```sh
ps -eo pid,comm,rss,%mem --sort=-rss | head
cat /proc/PID/status         # Replace PID with a real process ID
```
RSS may double-count shared pages and is not the same as unique memory. `top`, `smem`, or `pidstat` may provide additional perspectives if installed.

## Cgroup v2 memory controller
Run inside the affected container or locate its specific cgroup:
```sh
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.swap.max
cat /sys/fs/cgroup/memory.events
cat /sys/fs/cgroup/memory.stat
```
`memory.max` and `memory.current` are bytes; `memory.swap.max=0` means no additional swap allowed. `memory.events` contains cumulative counters: `max` is not an OOM kill count; `oom_kill` counts processes killed by an OOM killer. Read twice and subtract to measure changes over time. The exact available keys depend on the kernel.

## Docker inspection
```sh
docker stats --no-stream CONTAINER
docker inspect CONTAINER --format 'ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'
docker logs CONTAINER
```
Exit code 137 indicates SIGKILL; corroborate the cause rather than assuming OOM. A container whose main process survives an OOM-killed child may remain running with `OOMKilled=false` even though cgroup counters show an OOM kill.

## Kernel logs (where authorized)
```sh
journalctl -k --since '30 minutes ago'
```
May require elevated permissions and may not be available inside a container or on Alpine. Avoid changing limits or killing processes during diagnosis without authorization.

## Related material
- [Linux memory pressure playbook](../../playbooks/linux-memory-pressure.md)
- [Controlled memory pressure lab](../../labs/linux/memory-pressure/README.md)
