# Linux Application or API Is Unresponsive

## 1. Problem / Symptoms

A Linux-hosted application or API does not respond, times out, returns errors, or appears unavailable. It may be managed by systemd, another supervisor, a container runtime, or a manually started process.

## 2. Quick Diagnosis

Initialize environment-specific values before running the checks:

~~~bash
SERVICE="my-api.service"
APP_NAME="my-api"
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/health"

systemctl status "$SERVICE" --no-pager
pgrep -af "$APP_NAME"
ss -ltnp "sport = :$PORT"
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

Treat these as separate signals:

- A process running means a process exists; it does not prove the application is healthy.
- An application is healthy when it handles a suitable request correctly, such as a health endpoint.
- A service is accessible only when the intended client path can reach it; local success does not prove proxy, firewall, DNS, or routing success.
- A failed systemd unit points to service state or startup failure, but systemd may not manage the application.
- No process or listening socket suggests a crash, failed start, different supervisor, or wrong configuration.
- A connection failure or timeout from curl supports investigating the process, logs, dependencies, or host resources.
- An HTTP response, including an error response, proves that something accepted and handled the request; inspect its status and body.

Do not restart the service solely because it is unresponsive. Collect evidence first.

## 3. Possible Causes

- Crash or failed startup
- Service managed outside systemd or under another name
- Wrong bind address or port, or a port conflict
- Memory pressure, OOM kill, CPU saturation, or full filesystem
- Unavailable database, queue, DNS, certificate, or other dependency
- Failing reverse proxy, firewall, load balancer, or network path

## 4. Step-by-Step Investigation

### Step 1: Check service state when systemd is used

~~~bash
SERVICE="my-api.service"
systemctl status "$SERVICE" --no-pager
systemctl is-active "$SERVICE"
~~~

This shows unit state, recent status, main PID, and hints from systemd. Active means systemd considers the unit running; it does not prove that the process is ready, healthy, or reachable. If the unit is missing, identify the actual supervisor rather than assuming the service is stopped.

### Step 2: Inspect running processes

~~~bash
APP_NAME="my-api"
pgrep -af "$APP_NAME"
PID=1234
ps -o pid,ppid,%cpu,%mem,stat,etime,cmd -p "$PID"
~~~

pgrep shows matching PIDs and command lines; confirm the match is the intended process before assigning its PID to PID. ps shows the PID, parent PID, CPU and memory percentages, state, elapsed time, and command line. A process that exists but consumes excessive resources needs resource checks before any restart.

### Step 3: Check listening ports

~~~bash
PORT=8000
ss -ltnp "sport = :$PORT"
~~~

Read State, Local Address:Port, and the process column where permissions allow. 127.0.0.1:8000 or [::1]:8000 is loopback-only; it accepts local clients but is not directly reachable through the host's external interfaces. 0.0.0.0:8000 or [::]:8000 listens on all interfaces, subject to firewall, routing, and application controls. No listener suggests a bind, startup, configuration, or process problem. An unexpected owner suggests a port conflict or wrong routing.

### Step 4: Test HTTP locally

~~~bash
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/health"
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

Do not use --fail for this exploratory check: preserve HTTP error status and response body. A connection refusal, DNS error, or timeout means the request was not completed; curl reports an error and exits nonzero. An HTTP 4xx or 5xx means a server responded, so inspect the status, headers, body, and timing. A 2xx response supports application health for that endpoint, but does not prove the full service path is accessible. Use a safe read-only endpoint if no health endpoint exists.

### Step 5: Read logs

~~~bash
SERVICE="my-api.service"
journalctl -u "$SERVICE" --since '30 minutes ago' --no-pager -o short-iso
journalctl -u "$SERVICE" -n 100 --no-pager -o short-iso
~~~

Read the timestamp, unit, priority, process identity where present, and message. Look for crashes, bind errors, dependency timeouts, configuration errors, and permission failures, correlating timestamps with the symptom. If systemd does not manage the application, use its documented log location or supervisor. An empty journal does not prove there are no logs.

### Step 6: Check memory and kernel messages

~~~bash
free -h
dmesg -T | grep -Ei 'out of memory|oom|killed process'
journalctl -k --since '30 minutes ago' --no-pager | grep -Ei 'out of memory|oom|killed process'
~~~

free -h reports total, used, free, shared, buff/cache, available memory, and swap. Pay particular attention to available memory and swap use; low free alone is not proof of pressure. Kernel messages can show an OOM event or killed process; dmesg may require privileges. Correlate timestamps with application logs.

### Step 7: Check disk usage

~~~bash
df -h
df -i
~~~

df -h reports filesystem, size, used, available, percentage used, and mount point; df -i reports inode totals, used, available, and percentage used. A full data column or inode percentage can prevent logs, sockets, temporary files, or database writes. Identify the affected mount before considering an approved cleanup; do not delete files blindly.

### Step 8: Check dependencies and the network path

Use documented dependency checks and inspect proxy, firewall, DNS, database, queue, or certificate evidence as applicable. Compare a local request with the normal client-facing endpoint. Local success with external failure points toward the path in front of the application.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| Failed unit and exception in logs | Investigate the named exception, configuration, or dependency. |
| No process and no listening port | Investigate crash, startup, supervisor, or deployment state. |
| Process exists but no expected port | Check bind address, port configuration, and conflicts. |
| Port listens but local curl cannot connect | Check bind address, protocol, endpoint, readiness, and local firewall behavior. |
| Local curl returns an HTTP error | The application or an upstream local component responded; inspect status, body, and logs. |
| Local curl succeeds but remote access fails | Investigate interface binding, proxy, load balancer, DNS, firewall, and routing. |
| OOM evidence | Correlate timestamps and identify memory consumers before changing limits. |
| Full space or inode usage | Identify the filesystem and follow an approved capacity or cleanup plan. |

## 6. Resolution Options

Choose an evidence-supported action with appropriate approval:

- Correct a documented configuration, dependency, certificate, permission, or port conflict, then validate it.
- Restore an unavailable dependency or network path using its procedure.
- For a confirmed crash or failed startup, use the normal start or deployment procedure and inspect the result. Record evidence first because a restart can remove useful state.
- For exhausted resources, follow the host or application capacity procedure; do not delete data or kill processes indiscriminately.
- For a non-systemd application, use its actual supervisor or deployment mechanism.

## 7. Verification

~~~bash
SERVICE="my-api.service"
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/health"
systemctl is-active "$SERVICE"
ss -ltnp "sport = :$PORT"
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

Check recent logs for new errors and, where possible, test through the normal proxy or client path. Observe long enough to confirm the issue does not recur.

## 8. Safety Notes

- Confirm the host, service, port, and environment before acting.
- Do not expose credentials, tokens, private addresses, or sensitive logs.
- Prefer read-only checks and preserve timestamps and evidence.
- Do not delete logs, temporary files, or application data as a first response to disk pressure.
- Treat kill, systemctl restart, package, configuration, and firewall changes as potentially disruptive and authorized actions.
- Output and options vary by distribution, permissions, supervisor, curl version, and application.

## 9. References

- [Essential Linux commands](../references/linux/essential-commands.md)
- [systemctl documentation](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [journalctl documentation](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)
- [ss manual](https://man7.org/linux/man-pages/man8/ss.8.html)

## 10. Validation Status

Illustrative procedure. The commands were not run against a specific application, distribution, or production host during authoring. Validate service names, endpoints, permissions, supervisor behavior, curl version, and output in the target environment.
