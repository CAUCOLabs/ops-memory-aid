# TCP Socket Commands (Linux)

Focused, mostly read-only commands for examining TCP listeners, connections, and socket counters. Execute in the **same network namespace** as the target service. Commands using `ss` are Linux references; the Alpine 3.21 test container did not include `ss`.

## Linux: listeners and connections

```bash
ss -ltn                 # TCP listening sockets, numeric addresses
ss -tan                 # All TCP sockets, numeric addresses
ss -tan state close-wait
ss -tan state time-wait
ss -tanp                # Include process information when permitted
```

Filter by port after setting a value:

```bash
PORT=8765
ss -tan "( sport = :$PORT or dport = :$PORT )"
```

`ss -p` may not show process details without sufficient permissions. State names and output format vary by tool/version.

## Linux: procfs fallback

```bash
cat /proc/net/tcp       # IPv4 TCP sockets, hex-encoded fields
cat /proc/net/tcp6      # IPv6 TCP sockets
cat /proc/net/sockstat  # Socket counters in current network namespace
```

Relevant TCP state values in the `st` column:

| Hex | State | Notes |
| --- | --- | --- |
| `0A` | LISTEN | Waiting for inbound connections |
| `01` | ESTABLISHED | Connection established |
| `05` | FIN_WAIT2 | Local FIN sent; awaiting remote FIN |
| `06` | TIME_WAIT | Normal post-close TCP state |
| `08` | CLOSE_WAIT | Remote FIN received; local socket not yet closed |

Example from the tested lab: `0100007F:223D` represents IPv4 loopback `127.0.0.1` and port `0x223D = 8765`. IPv4 addresses in `/proc/net/tcp` appear in little-endian byte order on the tested platform. Do not treat the numeric inode column as a PID.

## Linux: correlate with an identified process

```bash
PID=1234  # Replace with an actual process ID
ls -l "/proc/$PID/fd"
cat "/proc/$PID/limits"
```

Only inspect PIDs you are authorized to investigate. File descriptors alone do not establish the cause of a connection problem.

## macOS equivalent

```bash
netstat -an -p tcp
```

`ss` is not installed by default on macOS; the macOS command is **not** a substitute for Linux `/proc` or namespace-specific observations.

## Interpretation and safety

- Compare repeated samples before diagnosing a trend.
- `TIME_WAIT` is commonly normal; `CLOSE_WAIT` can be transient, but sustained growth warrants application-level investigation.
- A listener proves a bound socket, not that application requests succeed.
- Avoid copying production IPs, PIDs, or logs into public reports.

**Validation:** `/proc/net/tcp` and `/proc/net/sockstat` were read in disposable Alpine 3.21 / Python 3.12 Alpine containers on November 11, 2026. `ss` commands and production process correlation are reference-only and were not executed in the lab.
