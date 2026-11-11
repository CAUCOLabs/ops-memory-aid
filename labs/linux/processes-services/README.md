# Linux processes and services lab (Stage 4.4)

Reproduce process lifecycle and startup failures safely in **disposable Docker containers**. Tested with Docker Desktop and `alpine:3.21` (observed Alpine 3.21.10) and `python:3.12-alpine`. Commands do not publish ports or alter host processes. Run from a shell with Docker available. Each command uses `--rm` and limits container memory where relevant.

> These are controlled demonstrations, not production recovery commands. No systemd service was run in this lab.

## 1. Inspect PID 1 and available tools

```sh
docker run --rm --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  echo "PID 1:"; cat /proc/1/comm
  ps
  grep -E "^(Name|State|Pid|PPid|Threads):" /proc/1/status
  for cmd in ps top kill killall pgrep pkill; do
    command -v "$cmd" || true
  done
  kill -l
'
```

**Observed:** PID 1 was `sh`; state `S (sleeping)`; `ps`, `top`, `kill`, `killall`, `pgrep`, `pkill` were available.

## 2. Normal and application-defined exit codes

```sh
docker run --rm alpine:3.21 sh -c 'echo "Success"; exit 0'
echo "Exit code: $?"
docker run --rm alpine:3.21 sh -c 'echo "Intentional failure"; exit 42'
echo "Exit code: $?"
```

**Observed:** `0` and `42`, respectively.

## 3. Child termination: SIGTERM and SIGKILL

```sh
docker run --rm --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  sleep 300 & child=$!
  kill -TERM "$child"
  wait "$child"
  echo "Child exit code: $?"
'

docker run --rm --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  sleep 300 & child=$!
  kill -KILL "$child"
  wait "$child"
  echo "Child exit code: $?"
'
```

**Observed:** child codes `143` and `137`. Shell messages `Terminated` / `Killed` are expected. The shell remains the container's main process; the child's exit code is not automatically the container exit code.

## 4. Process states: sleeping, stopped, resumed

```sh
docker run --rm --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  sleep 300 & child=$!
  grep -E "^(Name|State|Pid|PPid):" /proc/$child/status
  kill -STOP "$child"; sleep 1
  grep -E "^(Name|State|Pid|PPid):" /proc/$child/status
  kill -CONT "$child"; sleep 1
  grep -E "^(Name|State|Pid|PPid):" /proc/$child/status
  kill -TERM "$child"; wait "$child" || true
'
```

**Observed:** `S (sleeping)` → `T (stopped)` → `S (sleeping)`.

## 5. Zombie and waitpid()

```sh
docker run --rm --memory=128m --memory-swap=128m python:3.12-alpine python -c '
import os
import time
pid = os.fork()
if pid == 0:
    os._exit(42)
time.sleep(1)
print("=== Before waitpid ===", flush=True)
with open("/proc/{}/status".format(pid)) as f:
    for line in f:
        if line.startswith(("Name:", "State:", "Pid:", "PPid:")):
            print(line.strip())
reaped, status = os.waitpid(pid, 0)
print("Reaped PID:", reaped)
print("Exit code:", os.waitstatus_to_exitcode(status))
print("Child process entry exists:", os.path.exists("/proc/{}".format(pid)))
'
```

**Observed:** `Z (zombie)`, exit `42`, then `Child process entry exists: False`. An earlier version of this test had a shell-quoting error in the final print statement; the corrected version above was rerun successfully.

## 6. Docker init and orphan adoption

First inspect the init process:

```sh
docker run --rm --init --memory=128m --memory-swap=128m alpine:3.21 sh -c '
  cat /proc/1/comm
  ps
  echo "Shell PID: $$"
  grep -E "^(Name|State|Pid|PPid):" /proc/1/status
  grep -E "^(Name|State|Pid|PPid):" /proc/$$/status
'
```

**Observed:** `docker-init` was PID 1 and the shell was its child (PID 6 in that run).

Next, keep the main Python process alive while an intermediate parent exits:

```sh
docker run --rm --init --memory=128m --memory-swap=128m python:3.12-alpine python -c '
import os
import time
print("Main PID:", os.getpid(), flush=True)
intermediate = os.fork()
if intermediate == 0:
    child = os.fork()
    if child == 0:
        print("Child PID:", os.getpid(), flush=True)
        print("Initial PPID:", os.getppid(), flush=True)
        time.sleep(2)
        print("New PPID:", os.getppid(), flush=True)
        os._exit(0)
    print("Intermediate PID:", os.getpid(), flush=True)
    time.sleep(1)
    os._exit(0)
os.waitpid(intermediate, 0)
time.sleep(4)
print("Experiment completed", flush=True)
'
```

**Observed:** the child's PPID changed from the intermediate process (PID 8 in that run) to `1` (`docker-init`). Keeping the main process alive was necessary to observe the transition reliably. `--init` cannot reap children still owned by a live application.

## 7. Startup failure: port already in use

```sh
docker run --rm --memory=128m --memory-swap=128m python:3.12-alpine python -c '
import errno
import socket
host, port = "127.0.0.1", 8765
first = socket.socket()
second = socket.socket()
try:
    first.bind((host, port))
    first.listen(1)
    print("First service listening", flush=True)
    try:
        second.bind((host, port))
        print("Unexpected second bind success")
    except OSError as error:
        print("Errno:", error.errno)
        print("Error:", error)
        print("EADDRINUSE confirmed:", error.errno == errno.EADDRINUSE)
finally:
    second.close()
    first.close()
'
```

**Observed:** `errno 98`, `EADDRINUSE confirmed: True`. The socket was bound only inside the container; no host port was published.

## 8. Startup failure: permission denied

```sh
docker run --rm --memory=128m --memory-swap=128m python:3.12-alpine sh -c '
  mkdir /protected
  chmod 700 /protected
  ls -ld /protected
  su nobody -s /bin/sh -c "python -c '\''import os
import errno
print(\"Application UID:\", os.getuid())
try:
    with open(\"/protected/service.log\", \"w\") as f:
        f.write(\"Service started\")
    print(\"Unexpected write success\")
except OSError as error:
    print(\"Errno:\", error.errno)
    print(\"Error:\", error)
    print(\"EACCES confirmed:\", error.errno == errno.EACCES)
'\''"
'
```

**Observed:** UID `65534` (`nobody`), `errno 13`, `EACCES confirmed: True`.

## What this lab does not prove

- No actual `systemd` unit, `systemctl`, or `journalctl` failure was reproduced.
- No uninterruptible `D` state, production deadlock, or real outage was reproduced.
- Exit `137` alone cannot distinguish an explicit `SIGKILL` from an OOM kill.
- Docker `--init` helps with adopted orphaned children; it does not fix an application's failure to reap its own children.

See the [troubleshooting playbook](../../../playbooks/linux-processes-services-troubleshooting.md) and [command reference](../../../references/linux/process-service-commands.md).
