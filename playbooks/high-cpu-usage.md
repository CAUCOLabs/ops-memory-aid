# High CPU Usage

## 1. Problem / Symptoms
A Linux host or application becomes slow, latency increases, or monitoring reports sustained high CPU usage. High CPU usage alone is not proof of a problem: determine whether it correlates with degraded service and whether the workload is CPU-bound, constrained by a container quota, or waiting on other resources.

## 2. Quick Diagnosis
Run read-only commands on the affected Linux host:

```sh
uptime
nproc
ps -eo pid,ppid,stat,pcpu,pmem,comm --sort=-pcpu | head -n 15
top -b -n 1 | head -n 25
```

`top -b` and GNU `ps --sort` are Linux-oriented; availability and output vary by distribution. For containers, check `docker stats --no-stream <container>` from the Docker host. Record timestamps, host/container identity, and service symptoms.

## 3. Possible Causes
- Legitimate compute-heavy work, background jobs, or an unexpected traffic spike.
- Busy loops, runaway processes, excessive retries, or inefficient application code.
- CPU quota exhaustion or throttling in a container.
- Excessive context switching, interrupt activity, or many runnable tasks.
- Misleading interpretation of load average, which can also reflect tasks waiting in uninterruptible sleep (often I/O).

## 4. Step-by-Step Investigation
1. **Establish impact and baseline.** Check request latency, error rate, and the time the issue began. Compare with previous measurements where possible.
2. **Inspect host-level load and CPU use.** Run `uptime`, `top`, and `ps` above. If installed, use `vmstat 1 5` to inspect runnable tasks (`r`), CPU idle (`id`), I/O wait (`wa`), and system/user CPU; the first `vmstat` line can be a since-boot average.
3. **Identify the process.** Capture PID, command, parent, and duration. For example: `ps -p <PID> -o pid,ppid,etime,stat,pcpu,pmem,args`.
4. **Check for container constraints.** Run `docker stats --no-stream <container>`; on cgroup v2, inspect `/sys/fs/cgroup/cpu.max` and `/sys/fs/cgroup/cpu.stat` **inside the target container**. On cgroup v1 these paths and metrics differ.
5. **Measure a time interval.** Read `cpu.stat`, wait a known interval, then read it again. Compare differences in `usage_usec`, `nr_periods`, `nr_throttled`, and `throttled_usec`; raw counters are cumulative.
6. **Correlate with application evidence.** Review logs, request volume, deployments, and relevant profiling traces. Do not assume the highest CPU process is the root cause.

## 5. How to Interpret Results
- **CPU %:** A process near 100% often uses about one logical CPU, but conventions differ across tools. A host with multiple CPUs may still have spare capacity.
- **Load average:** Counts runnable and uninterruptible tasks over approximately 1, 5, and 15 minutes; it is not CPU utilization percentage. Compare with available CPU capacity and investigate I/O waits.
- **`cpu.max`:** On cgroup v2, `100000 100000` means 100,000 µs of CPU runtime per 100,000 µs period, approximately one CPU of quota. `max 100000` means no quota imposed by that cgroup.
- **Throttling:** `nr_throttled` counts throttled periods; it does **not** directly measure percentage of lost throughput. `throttled_usec` is accumulated throttled time; compare counter deltas and application impact.
- **Virtualization:** Docker Desktop on macOS runs Linux containers inside a VM. Container-visible CPU and memory values are not direct measurements of the macOS kernel.

## 6. Resolution Options
Only after establishing cause and authorization: reduce unintended work, correct retry loops, optimize hot paths, schedule background jobs, or adjust container CPU quotas based on measured demand. Increasing quotas can move contention elsewhere. Avoid immediately killing processes or restarting production services without understanding the impact.

## 7. Verification
After an authorized change, repeat the same measurements over comparable intervals. Confirm improved user-facing latency/error rate, lower sustained CPU pressure where appropriate, and reduced throttling if that was the bottleneck. Verify no new errors or regressions.

## 8. Safety Notes
- Prefer observation before intervention; do not terminate or renice unfamiliar production processes.
- Do not run synthetic busy loops on production hosts.
- Use explicit CPU, memory, and time limits for labs; clean up only the containers created for the experiment.
- Treat `/proc` and cgroup values as environment-specific; document kernel, cgroup version, and tool versions.

## 9. References
- [Linux performance commands](../references/linux/performance-commands.md)
- [Controlled CPU load lab](../labs/linux/cpu-load/README.md)
- [Essential Linux commands](../references/linux/essential-commands.md)

## 10. Validation Status
**Documentation status:** Draft, awaiting repository validation and review. **Lab evidence:** A controlled Alpine 3.21 container experiment on Docker Desktop/macOS was executed on 2026-11-10. Observed `docker stats` CPU 99.43%, `cpu.max` `100000 100000`, and cgroup v2 throttling counters. These observations validate the lab example, **not** every diagnostic command or remediation option above. See the lab for recorded evidence and limitations.
