# Essential Linux Commands

This reference focuses on safe, read-only checks used during operational troubleshooting. Initialize values before running a command:

~~~bash
SERVICE="my-api.service"
APP_NAME="my-api"
PID=1234
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/health"
~~~

## Processes and services

### ps

Purpose: Display running processes and details.

Example:

~~~bash
ps -ef
ps -o pid,ppid,%cpu,%mem,stat,etime,cmd -p "$PID"
~~~

What to look for: Expected process, PID and parent, CPU and memory percentages, state, elapsed time, and command line. Confirm the PID belongs to the intended application.

### systemctl status

Purpose: Show the state and recent status of a systemd unit.

Example:

~~~bash
systemctl status "$SERVICE" --no-pager
~~~

What to look for: active or failed state, exit status, main PID, and recent hints. Active means systemd considers the unit running; it does not prove process readiness or application health. A missing unit may mean another supervisor is used.

### systemctl is-active

Purpose: Return a compact systemd service state.

Example:

~~~bash
systemctl is-active "$SERVICE"
~~~

What to look for: active, inactive, failed, or unknown. This is systemd's view, not application readiness or external accessibility.

## Network connections

### ss

Purpose: Inspect sockets, listening ports, and connections.

Example:

~~~bash
ss -ltnp "sport = :$PORT"
ss -tan
~~~

What to look for: State, Local Address:Port, Peer Address:Port, and the owning process where permitted. A 127.0.0.1 or ::1 listener is loopback-only; 0.0.0.0 or :: listens on all interfaces, subject to firewall and routing. A listening socket proves a process accepted the bind, not that the application is healthy.

### curl

Purpose: Test HTTP connectivity and inspect a response.

Example:

~~~bash
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

What to look for: Connection refusal or timeout means no completed response; an HTTP 4xx or 5xx means a server responded and its status and body should be investigated; a 2xx response supports health for that endpoint. Local success does not prove remote access. For scripts that need a nonzero exit on HTTP errors while retaining the body, curl 7.76.0 or newer supports --fail-with-body; it is not needed for this exploratory check.

## Logs

### journalctl

Purpose: Read systemd service or kernel logs.

Example:

~~~bash
journalctl -u "$SERVICE" --since '30 minutes ago' --no-pager -o short-iso
journalctl -k -n 100 --no-pager
~~~

What to look for: ISO timestamp, unit, priority, process identity where present, and message. Correlate startup failures, crashes, dependency errors, permission problems, and OOM events with the incident time.

## CPU and memory

### free

Purpose: Show memory and swap usage.

Example:

~~~bash
free -h
~~~

What to look for: Total, used, free, shared, buff/cache, available memory, and swap. Available memory and swap use are more useful pressure signals than free alone; correlate them with application errors.

### uptime

Purpose: Show uptime and load averages.

Example:

~~~bash
uptime
~~~

What to look for: Load relative to CPU capacity, recent reboot timing, and changes around the incident.

### dmesg

Purpose: Read kernel messages when permissions allow.

Example:

~~~bash
dmesg -T | tail -n 100
~~~

What to look for: OOM kills, disk or filesystem errors, hardware messages, and network-driver failures. Use the kernel journal when restricted.

## Disk and filesystem

### df

Purpose: Show filesystem space and inode usage.

Example:

~~~bash
df -h
df -i
~~~

What to look for: Filesystem, size, used, available, percentage used, and mount point. With df -i, inspect inode totals, used, available, and percentage used. A full data or inode filesystem can block writes even when another mount has space.

### du

Purpose: Estimate directory or file space usage.

Example:

~~~bash
LOG_DIR="/var/log/my-api"
du -sh "$LOG_DIR"
du -xhd1 /var 2>/dev/null | sort -h
~~~

What to look for: Large directories on the affected filesystem. Confirm paths before any cleanup.

## Permissions

### id

Purpose: Show a user's UID, groups, and identity.

Example:

~~~bash
USER_NAME="my-api"
id
id "$USER_NAME"
~~~

What to look for: Account and groups relevant to file, socket, or service access.

### ls -l

Purpose: Inspect file ownership and permission bits.

Example:

~~~bash
ls -ld /path/to/directory
ls -l /path/to/file
~~~

What to look for: Owner, group, mode bits, symlink targets, and service-account access.

### namei

Purpose: Inspect permissions on every component of a path.

Example:

~~~bash
namei -l /path/to/file
~~~

What to look for: Restrictive directory permission or unexpected symlink anywhere in the path. The service account needs execute permission on directories to traverse the path.

## System information

### hostnamectl

Purpose: Show host identity and OS information where supported.

Example:

~~~bash
hostnamectl
~~~

What to look for: Hostname, kernel, architecture, and OS details needed to identify the target.

### uname

Purpose: Display kernel and architecture information.

Example:

~~~bash
uname -a
~~~

What to look for: Kernel version and architecture when comparing hosts or checking compatibility.

### /etc/os-release

Purpose: Identify the Linux distribution and release.

Example:

~~~bash
cat /etc/os-release
~~~

What to look for: Distribution and version, which influence package names, service defaults, and tooling.

## Safety and validation

These examples are intended for diagnostic use. Output, permissions, and options vary by distribution, curl version, and environment. Validate paths, service names, and endpoints before use. Treat state-changing commands such as systemctl restart, kill, package operations, file deletion, and permission changes as separate, authorized actions.
