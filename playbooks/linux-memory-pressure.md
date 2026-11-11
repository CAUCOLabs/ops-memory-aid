# Linux memory pressure and OOM troubleshooting

## 1. Problem / Symptoms
Applications become slow, allocations fail, containers restart, or processes disappear with exit code 137. High memory usage alone does not prove memory pressure: Linux uses RAM for reclaimable caches.

## 2. Quick Diagnosis
```sh
free -h
cat /proc/pressure/memory
vmstat 1 5
```
For a container, check its memory limit and event counters:
```sh
cat /sys/fs/cgroup/memory.max
cat /sys/fs/cgroup/memory.current
cat /sys/fs/cgroup/memory.events
```
These paths assume cgroup v2. Read them **inside the affected container** or from its correct cgroup on the host.

## 3. Possible Causes
- Working set exceeds the container's cgroup memory limit.
- Application retains memory unexpectedly or leaks allocations.
- Several workloads compete for RAM; reclaim or swapping becomes expensive.
- Page cache, tmpfs, or other charged memory contributes to cgroup usage.
- Host-wide memory pressure or a separate administrator-issued SIGKILL.

## 4. Step-by-Step Investigation
1. Record timestamps, scope (host or container), and the affected process/container.
2. Check `free -h` and `MemAvailable`; do not treat `free` alone as usable memory.
3. Examine `vmstat 1 5` (`si`, `so`, `r`, `b`) and `/proc/pressure/memory` for signs of pressure.
4. Identify processes with `ps -eo pid,comm,rss,%mem --sort=-rss | head` (RSS is not a unique-memory measurement).
5. For a cgroup v2 container, read `memory.max`, `memory.current`, `memory.swap.max`, `memory.events`, and `memory.stat`.
6. Compare `memory.events` at two times to measure new events; counters are cumulative.
7. Inspect container status using `docker inspect CONTAINER --format 'ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'` and `docker logs CONTAINER`.
8. Where permitted, correlate with kernel or service logs (`journalctl -k` or equivalent). Kernel logs may be inaccessible inside containers.

## 5. How to Interpret Results
- `memory.max` is a cgroup memory limit in bytes (`max` means unlimited); `memory.current` is current charged usage.
- `memory.swap.max=0` prevents additional swap use by that cgroup; it does not mean the host has no swap.
- `memory.events:max` counts events at the limit; it is **not** a count of OOM kills.
- `memory.events:oom` counts OOM conditions; `oom_kill` counts processes killed by an OOM killer.
- Exit 137 indicates SIGKILL, **not necessarily OOM**. Combine with `OOMKilled`, event counters, and logs.
- Swap activity or PSI pressure indicates a different condition from simply having little free RAM.

## 6. Resolution Options
After establishing the cause and obtaining authorization: reduce workload concurrency, correct retention/leaks, tune application memory settings, or adjust container limits and host capacity. Do not increase limits blindly or disable OOM protection as a shortcut.

## 7. Verification
Re-run the same workload; compare application responsiveness, `memory.current`, `memory.events` deltas, memory PSI, and swap activity. Confirm no new OOM kills and that changes do not shift pressure to the host.

## 8. Safety Notes
Prefer read-only diagnostics. Do not run memory stress tests on production systems. The linked lab deliberately triggers an OOM **only inside a disposable, memory-limited Docker container**. A cgroup limit reduces risk but is not an absolute guarantee of zero host impact. Avoid `docker rm -f` on containers you do not own.

## 9. References
- [Memory troubleshooting commands](../references/linux/memory-commands.md)
- [Controlled memory pressure lab](../labs/linux/memory-pressure/README.md)
- Linux kernel documentation: cgroup v2 memory controller and pressure stall information.

## 10. Validation Status
**Validated experimentally (2026-11-11):** Docker Desktop on macOS running Linux containers with cgroup v2, 128 MiB memory limit and no additional swap. An attempted 192 MiB allocation caused exit 137, Docker `OOMKilled=true`, and in a supervised run `memory.events` reported `oom=1`, `oom_kill=1`. **Not experimentally validated here:** host-wide pressure, sustained reclaim, or swapping. Other diagnostic commands are references, not claims of execution in this lab.
