# Disk and filesystem troubleshooting lab

Reproducible, bounded Linux filesystem experiments using disposable Docker containers. **Tested November 11, 2026** with Alpine 3.21 on Docker Desktop (LinuxKit 6.10.14, aarch64). These experiments do not write to host bind mounts or Docker volumes.

> Safety: run only the commands shown on a machine where Docker is available. `--rm` removes each disposable container. The `tmpfs` mounts are limited to 16 MiB; do not substitute a host directory. The I/O example writes 8 MiB to the container writable layer and is not a disk benchmark.

## A. Byte-capacity exhaustion (`ENOSPC`) — tested

```sh
docker run --rm --name ops-disk-lab \
  --memory=128m --memory-swap=128m \
  --mount type=tmpfs,destination=/mnt/disk-lab,tmpfs-size=16777216 \
  alpine:3.21 sh -c '
    df -h /mnt/disk-lab
    dd if=/dev/zero of=/mnt/disk-lab/test.bin bs=1M count=24
    df -h /mnt/disk-lab
    df -i /mnt/disk-lab
  '
```

**Observed:** `dd: ... No space left on device`; 16 MiB written, `df -h` showed 16 MiB used / 0 available (100%), while `df -i` still showed 1,003,176 available inodes. The `dd` failure is intentional; subsequent commands still execute because the shell does not use `set -e`.

## B. Inode exhaustion (`ENOSPC`) — tested

```sh
docker run --rm --name ops-inode-limit \
  --memory=128m --memory-swap=128m \
  --tmpfs /mnt/inode-lab:rw,size=16m,nr_inodes=32 \
  alpine:3.21 sh -c '
    mount | grep /mnt/inode-lab
    df -i /mnt/inode-lab
    i=1
    while [ "$i" -le 100 ]; do
      if ! touch "/mnt/inode-lab/file_$i"; then
        echo "File creation failed at file_$i"
        break
      fi
      i=$((i + 1))
    done
    df -i /mnt/inode-lab
    df -h /mnt/inode-lab
  '
```

**Observed:** mount included `nr_inodes=32`; `file_32` failed with `No space left on device`; `df -i` showed 32/32 inodes used (100%) while `df -h` showed 16 MiB available (0% byte use). The mount itself consumed one inode; 31 files were created.

## C. Read-only filesystem (`EROFS`) — tested

```sh
docker run --rm --name ops-readonly-lab \
  --read-only --memory=128m --memory-swap=128m \
  alpine:3.21 sh -c '
    mount | grep " on / type "
    if touch /readonly-test.txt; then
      echo "UNEXPECTED: write succeeded"
    else
      echo "EXPECTED: write failed"
    fi
    df -h /
    df -i /
  '
```

**Observed:** root OverlayFS mounted `ro`; `touch` failed with `Read-only file system`, despite available bytes and inodes. This is an intentionally read-only container, **not** a simulation of an automatic read-only remount caused by filesystem corruption.

## D. Small write and I/O visibility — tested as observation only

```sh
docker run --rm --name ops-io-lab \
  --memory=128m --memory-swap=128m \
  alpine:3.21 sh -c '
    cat /proc/self/io
    dd if=/dev/zero of=/tmp/io-test.bin bs=1M count=8 conv=fsync
    ls -lh /tmp/io-test.bin
    grep -E " (vda|vda1|vdb) " /proc/diskstats
    iostat
  '
```

**Observed:** 8,388,608 bytes written successfully; virtual devices `vda`, `vda1`, and `vdb` appeared in `/proc/diskstats` and `iostat`. The displayed `iostat` CPU `%iowait` was 0.01% and `%idle` 99.87% for its reporting interval. **Do not interpret** the reported 1.1 GB/s `dd` rate as a validated physical disk benchmark, or the cumulative device counters as I/O attributable only to this container. `/proc/self/io` read before the write showed `read_bytes: 0` and `write_bytes: 0` for the shell process at that instant.

## Interpretation matrix

| Failure | `df -h` | `df -i` | Mount | Evidence |
| --- | --- | --- | --- | --- |
| Byte exhaustion | 100% | Inodes available | `rw` | `ENOSPC` |
| Inode exhaustion | Space available | 100% | `rw` | `ENOSPC` |
| Read-only | Space available | Inodes available | `ro` | `EROFS` |

## Validation boundary

**Validated:** byte-capacity exhaustion, inode exhaustion, intentional read-only filesystem, and access to basic I/O counters after a small write. **Not validated:** device `EIO`, sustained I/O saturation, production filesystem recovery, or unexpected kernel remounts. See the [playbook](../../../playbooks/linux-disk-filesystem-troubleshooting.md) and [command reference](../../../references/linux/disk-filesystem-commands.md).
