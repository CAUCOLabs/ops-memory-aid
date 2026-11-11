# Linux disk and filesystem troubleshooting

## 1. Problem / Symptoms

Applications cannot write files, report `No space left on device` (`ENOSPC`) or `Read-only file system` (`EROFS`), or experience slow storage operations. An I/O error (`EIO`) is a different failure from a slow operation.

## 2. Quick Diagnosis

Identify the exact failing path before checking the filesystem that contains it:

```sh
TARGET=/var/log
findmnt -T "$TARGET" 2>/dev/null || df -h "$TARGET"
df -h "$TARGET"
df -i "$TARGET"
```

For a container, run these checks **inside the affected container** as well as on the relevant host or volume. Do not assume that `/` and the failing path use the same mount.

## 3. Possible Causes

- Filesystem byte capacity exhausted, including a small `tmpfs` or volume.
- Inodes exhausted by many files, even when `df -h` reports free capacity.
- A mount is intentionally read-only, or a filesystem has been remounted read-only following an error.
- Storage I/O contention, high latency, or an underlying device/filesystem error.
- Quotas, reserved space, or container storage limits; `df` alone may not explain all write failures.

## 4. Step-by-Step Investigation

1. Capture the full error, timestamp, operation, and target path. Avoid cleanup until the cause is understood.
2. Inspect the target mount and its options: `findmnt -T "$TARGET"` (where available), or `mount`.
3. Compare `df -h "$TARGET"` with `df -i "$TARGET"`. Check other affected paths separately.
4. For `EROFS`, look for `ro` mount options and inspect kernel/system logs where permitted: `dmesg` or `journalctl -k`.
5. For slow I/O, collect **interval-based** samples with `iostat -xz 1 3` when `sysstat` supports it; corroborate with application latency and workload context.
6. Check `/proc/diskstats` for cumulative device counters and `/proc/<pid>/io` for process-level counters. Beware of permissions, caching, and shared devices.
7. In Docker Desktop, distinguish Linux VM block devices from the macOS physical disk; device-wide counters cannot be attributed to a single container without additional evidence.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| `df -h` at 100%, `df -i` not exhausted | Byte-capacity exhaustion |
| `df -i` at 100%, `df -h` has space | Inode exhaustion |
| Mount option `ro`, write returns `EROFS` | Read-only mount; investigate why |
| High latency in interval I/O metrics | Possible I/O bottleneck; correlate with workload |
| Kernel logs report I/O errors | Investigate device, filesystem, and infrastructure health |

`ENOSPC` can have causes beyond these two `df` conditions (for example quotas). An exit status or a single metric is not a complete diagnosis.

## 6. Resolution Options

After confirming the cause and impact: reclaim or rotate known-safe files, adjust capacity/retention, reduce file proliferation, fix volume sizing, or correct an intentionally read-only configuration. For unexpected read-only remounts or suspected hardware errors, preserve evidence and follow the platform's recovery procedure; do not blindly remount read-write or run filesystem repair against a mounted production filesystem. Escalate storage/device failures appropriately.

## 7. Verification

Repeat the original failed operation safely, verify the target mount's bytes/inodes/options, inspect application errors, and observe I/O latency over a representative interval. Confirm the issue does not recur.

## 8. Safety Notes

Do not fill a production disk, mass-delete files, run `fsck` on a live mounted filesystem, or generate heavy I/O on a shared host to reproduce an incident. The accompanying lab uses disposable Docker containers and bounded `tmpfs` mounts; it does not simulate physical disk failure.

## 9. References

- [Disk and filesystem command reference](../references/linux/disk-filesystem-commands.md)
- [Reproducible disk/filesystem lab](../labs/linux/disk-filesystem/README.md)

## 10. Validation Status

**Tested on November 11, 2026:** Docker Desktop LinuxKit (`6.10.14-linuxkit`, aarch64), Alpine 3.21. Reproduced byte-capacity `ENOSPC` on 16 MiB `tmpfs`, inode `ENOSPC` with `nr_inodes=32`, and `EROFS` with `docker run --read-only`. Confirmed an 8 MiB write and availability of `/proc/diskstats` and `iostat`. **Not validated:** sustained I/O saturation, I/O latency diagnosis, physical `EIO`, unexpected read-only remounts, and production remediation.
