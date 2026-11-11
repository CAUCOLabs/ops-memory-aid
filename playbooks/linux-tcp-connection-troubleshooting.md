# Linux TCP Connection Troubleshooting

## 1. Problem / Symptoms

A Linux application cannot accept TCP connections, connections remain open after clients disconnect, or socket counts increase unexpectedly. This playbook focuses on **socket lifecycle and TCP states**, not DNS resolution, TLS certificate validation, or general connection-refused/timeout diagnosis (covered by existing playbooks).

Typical evidence includes many sockets in `CLOSE_WAIT`, unexpected listeners, or an increasing number of open file descriptors. A single `TIME_WAIT` or short-lived `CLOSE_WAIT` is not sufficient evidence of a fault.

## 2. Quick Diagnosis

On a Linux host with `ss` installed, start with read-only checks:

```bash
ss -ltn
ss -tan
cat /proc/net/sockstat
```

For a specific service, define the port first:

```bash
PORT=8765
ss -tan "( sport = :$PORT or dport = :$PORT )"
```

If `ss` is unavailable, inspect `/proc/net/tcp` (IPv4) and `/proc/net/tcp6` (IPv6). Entries use hexadecimal addresses, ports, and state codes; see the command reference for decoding guidance. These commands inspect the current network namespace; container observations may not represent the host.

## 3. Possible Causes

- Application fails to close accepted sockets after a peer sends FIN (`CLOSE_WAIT` persists).
- Client or server intentionally maintains long-lived connections (`ESTABLISHED`).
- Normal TCP connection teardown creates transient `TIME_WAIT` entries.
- Listener binds to the wrong interface or port, or no listener exists.
- Process runs out of file descriptors or other resources, causing failures to accept connections.
- Network namespace differences hide the expected sockets from the current view.

Do not infer packet loss, kernel faults, or a resource leak from a TCP state alone.

## 4. Step-by-Step Investigation

1. **Establish the symptom and scope.** Record the service, port, host/container, time window, and whether the problem affects new or existing connections.
2. **Check listeners.** Run `ss -ltn` on Linux; confirm the intended address and port are present. `127.0.0.1` only accepts local connections.
3. **Inspect connection states.** Run `ss -tan` and look for patterns over time. For restricted containers, use `/proc/net/tcp` and `/proc/net/tcp6`.
4. **Correlate with the process.** Where permitted, `ss -tanp` can show owning processes; visibility may require privileges. Inspect `/proc/<PID>/fd` and `/proc/<PID>/limits` only for an identified PID.
5. **Inspect socket counters.** Read `/proc/net/sockstat`; compare snapshots rather than treating one sample as a trend.
6. **Check application logs.** Look for client disconnects, unhandled exceptions, missing socket cleanup, or file-descriptor exhaustion.
7. **Verify the environment.** Confirm that observations come from the same network namespace as the service. Docker port publishing is distinct from listening inside the container.
8. **Reproduce safely.** Use the disposable laboratory in `labs/networking/tcp-states/README.md` to observe known-good state transitions before interpreting production behavior.

## 5. How to Interpret Results

| State | Linux `/proc/net/tcp` code | Interpretation |
| --- | --- | --- |
| `LISTEN` | `0A` | Local socket awaits incoming connections. |
| `ESTABLISHED` | `01` | TCP connection is established. |
| `TIME_WAIT` | `06` | A normal TCP teardown state; a single entry is not an error. |
| `CLOSE_WAIT` | `08` | Peer sent FIN; local application has not yet closed its socket. |
| `FIN_WAIT2` | `05` | Local endpoint has sent FIN and awaits the peer's FIN. |

A sustained accumulation of `CLOSE_WAIT` *may* indicate missing application-level socket cleanup; confirm with repeated measurements and application evidence. `TIME_WAIT` is generally expected after certain close sequences. A `LISTEN` socket does not prove application-level health.

## 6. Resolution Options

- Correct application socket lifecycle: close connections in success and error paths, and use timeouts appropriate to the protocol.
- If a listener binds only to loopback but should serve remote clients, correct its bind configuration after verifying exposure and security requirements.
- Address confirmed file-descriptor exhaustion at the application and resource-management level; do not blindly increase limits.
- Restart a service **only if operationally justified**, with approval, expected impact, and a rollback plan. Restarting can hide the underlying cause.
- Do not indiscriminately kill connections or change kernel TCP parameters based on one state snapshot.

## 7. Verification

- Confirm the intended listener exists and accepts a test connection from the appropriate network namespace.
- Repeat state and socket-counter measurements; check that unexpected counts stop growing.
- Verify application logs, error rates, and resource consumption after any change.
- If a fix targets `CLOSE_WAIT`, confirm the application closes its accepted socket after the peer disconnects.

## 8. Safety Notes

- The diagnostic commands above are read-only; some process attribution requires elevated permissions.
- Avoid sharing raw IP addresses, socket ownership, or production logs containing sensitive data.
- The laboratory binds only to container loopback (`127.0.0.1`) and publishes no host ports.
- Do not assume that `ss` exists on macOS; use `netstat -an -p tcp` there, or run Linux-specific checks inside Linux.

## 9. References

- [TCP socket command reference](../references/networking/tcp-socket-commands.md)
- [TCP states laboratory](../labs/networking/tcp-states/README.md)
- Linux kernel `/proc/net/tcp` and `/proc/net/sockstat` interfaces; `ss(8)` manual on Linux.

## 10. Validation Status

**Tested in disposable Docker containers on November 11, 2026:** Alpine 3.21 tool availability; Python 3.12 Alpine TCP loopback listener and client; observed `LISTEN`, two `ESTABLISHED` entries, and `TIME_WAIT` after close; separately observed `CLOSE_WAIT` on the server and `FIN_WAIT2` on the client after client close, followed by disappearance of `CLOSE_WAIT` after server cleanup. `/proc/net/sockstat` counters were observed during the first experiment.

**Illustrative / not tested here:** `ss` commands on a Linux host, process-to-socket attribution, real-world socket leaks, file-descriptor exhaustion, packet loss, and production recovery actions. No host ports were published.
