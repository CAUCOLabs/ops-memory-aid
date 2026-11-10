# Linux Performance Commands — CPU

A quick reference for investigating CPU pressure. Commands are read-only unless otherwise noted. Run on the relevant Linux host or in the appropriate container context. Tool availability and output differ by distribution.

## Host overview

```sh
uptime                  # Load averages (not CPU percentages)
nproc                   # Processing units visible to this process
cat /proc/loadavg       # Load averages and task counts
```

`nproc` may reflect affinity/cpuset constraints but does not by itself prove usable CPU quota. Load average includes runnable and uninterruptible tasks; interpret it with CPU capacity and I/O observations.

## Identify CPU consumers

```sh
ps -eo pid,ppid,stat,pcpu,pmem,comm --sort=-pcpu | head -n 15
top -b -n 1 | head -n 25
ps -p <PID> -o pid,ppid,etime,stat,pcpu,pmem,args
```

Replace `<PID>` with an actual process ID. `%CPU` in `ps` is not necessarily an instantaneous sample; `top` provides a different sampling model. CPU percentage may exceed 100% for multithreaded workloads depending on tool conventions.

## Observe short-term behavior

```sh
vmstat 1 5
```

Look at `r` (runnable tasks), `us`, `sy`, `id`, and `wa`. The first line may summarize averages since boot. `vmstat` is commonly supplied by `procps`/`procps-ng`, which may need installation in minimal images. If available, `pidstat -u 1 5` provides per-process CPU sampling (`sysstat` package).

## Docker and cgroups

```sh
docker stats --no-stream <container>
docker exec <container> cat /sys/fs/cgroup/cpu.max
docker exec <container> cat /sys/fs/cgroup/cpu.stat
```

The latter two commands assume cgroup v2 and that the target paths are accessible. On cgroup v1 use its corresponding CPU quota and CPU accounting files. In cgroup v2, `cpu.max` contains `quota period`, measured in microseconds; `max` denotes unlimited quota at that cgroup level. `cpu.stat` counters are cumulative; take two readings to analyze a specific time window.

| Field | Interpretation |
| --- | --- |
| `usage_usec` | Accumulated CPU runtime (µs) |
| `user_usec` | Accumulated user-mode CPU runtime (µs) |
| `system_usec` | Accumulated kernel-mode CPU runtime (µs) |
| `nr_periods` | CFS bandwidth enforcement periods (when available) |
| `nr_throttled` | Periods in which throttling occurred |
| `throttled_usec` | Accumulated throttled time (µs) |

A ratio such as `nr_throttled / nr_periods` describes the fraction of periods affected, **not** the fraction of CPU capacity lost. Some fields may be absent depending on kernel and configuration.

## Common interpretation traps

- High CPU usage is not automatically a system-wide bottleneck.
- High load average does not necessarily mean high CPU usage; inspect runnable tasks and I/O wait.
- Container CPU percentages and quotas must be interpreted relative to the container's limits and the host/VM.
- A single snapshot cannot establish a trend or causality.
- Avoid killing or restarting services solely because they appear at the top of a CPU list.

## Related documents

- [High CPU usage playbook](../../playbooks/high-cpu-usage.md)
- [Controlled CPU load lab](../../labs/linux/cpu-load/README.md)
