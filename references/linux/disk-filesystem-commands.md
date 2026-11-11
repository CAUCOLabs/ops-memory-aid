# Linux disk and filesystem commands

Use these commands on the **affected mount and path**, not automatically on `/`.

## Filesystem capacity and inodes

```sh
TARGET=/var/log
df -h "$TARGET"   # byte capacity
df -i "$TARGET"   # inode capacity
```

`ENOSPC` with `df -h` at 100% suggests byte exhaustion; `ENOSPC` with `df -i` at 100% suggests inode exhaustion. Quotas and other limits can also produce `ENOSPC`.

## Mount identity and access mode

```sh
findmnt -T "$TARGET"   # util-linux; may not exist in minimal images
mount                  # look for the affected mount and ro/rw options
```

`ro` means read-only; `rw` means read-write. `EROFS` on an unexpected read-only mount requires investigation before changing mount options.

## Inspecting likely space consumers

```sh
du -sh /var/log/* 2>/dev/null
```

This is an example for a known directory; inspect scope and permissions first. `du` and `df` can disagree because of deleted-but-open files, mount boundaries, filesystem metadata, or other accounting differences. Avoid destructive cleanup without evidence.

## Device and process I/O counters

```sh
cat /proc/diskstats
cat /proc/self/io
# For a specific process, if permitted:
# cat /proc/<PID>/io
```

`/proc/diskstats` is device-wide and cumulative. `/proc/self/io` reports the process reading it, not all container or host I/O. `read_bytes` and `write_bytes` can differ from application read/write calls due to caching.

## I/O activity and errors

```sh
iostat              # often cumulative since boot; not a latency benchmark
iostat -xz 1 3      # interval samples, where supported by installed sysstat
dmesg               # kernel messages; access may be restricted
journalctl -k       # on systems with systemd journal
```

Correlate device latency and utilization with application response times. On Docker Desktop, LinuxKit virtual-device counters are **not** direct macOS SSD measurements. A successful small `dd` write does not establish storage throughput or absence of I/O problems.

## Safe lab pointers

See [Disk/filesystem lab](../../labs/linux/disk-filesystem/README.md) for isolated `ENOSPC`, inode exhaustion, `EROFS`, and a small I/O-observation exercise.

## Validation status

`df`, `mount`, `dd`, `/proc/diskstats`, `/proc/self/io`, and `iostat` were observed in Alpine 3.21 on Docker Desktop (November 11, 2026). `findmnt`, `journalctl`, extended `iostat` options, and production incident procedures are environment-dependent and were **not** validated in this lab.
