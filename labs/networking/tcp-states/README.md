# TCP States Laboratory

**Goal:** observe real TCP state transitions in a disposable Linux container without publishing ports on the host. The experiments were run on November 11, 2026 with Docker Desktop and `python:3.12-alpine`. The commands below use Python's standard library; no packages or repository files are required.

## Safety and environment

- Run from a terminal with Docker available; commands use `docker run --rm` and create no persistent container.
- Bind only to `127.0.0.1` inside the container; **no `-p` host port mapping**.
- Memory and swap are limited to 128 MiB. The code opens a few local sockets only.
- Do not confuse container `/proc/net/tcp` with the Mac host's socket table.
- The observed ephemeral client port and kernel counters may vary between runs.

## 1. Inspect available tools and baseline

```bash
docker run --rm --name ops-network-inspection \
  --memory=128m --memory-swap=128m \
  alpine:3.21 sh -c '
    for cmd in ss netstat ip ping traceroute wget nc; do
      if command -v "$cmd" >/dev/null 2>&1; then
        echo "$cmd: available"
      else
        echo "$cmd: not installed"
      fi
    done
    cat /proc/net/tcp
    cat /proc/net/sockstat
  '
```

**Observed:** `ss` absent; `netstat`, `ip`, `ping`, `traceroute`, `wget`, and `nc` available. `/proc/net/tcp` contained only the header at baseline; `TCP: inuse 0 orphan 0 tw 0` in `/proc/net/sockstat`.

## 2. Observe LISTEN, ESTABLISHED, and TIME_WAIT

```bash
docker run --rm --name ops-tcp-states \
  --memory=128m --memory-swap=128m \
  python:3.12-alpine python -c '
import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 8765

def inspect(label):
    print("\n=== {} ===".format(label), flush=True)
    states = {"0A": "LISTEN", "01": "ESTABLISHED", "06": "TIME_WAIT"}
    with open("/proc/net/tcp") as f:
        for line in f.readlines()[1:]:
            fields = line.split()
            print(states.get(fields[3], fields[3]), fields[1], fields[2], flush=True)
    with open("/proc/net/sockstat") as f:
        print(f.read(), flush=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)
inspect("Server listening")

def client_task():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    time.sleep(2)
    client.close()

thread = threading.Thread(target=client_task)
thread.start()
connection, address = server.accept()
inspect("Client connected")
thread.join()
connection.close()
server.close()
inspect("Connections closed")
print("\n=== Experiment completed ===", flush=True)
'
```

**Observed:** one `LISTEN` entry at first; `LISTEN` plus two `ESTABLISHED` entries while connected; one `TIME_WAIT` entry after close. `/proc/net/sockstat` showed TCP `inuse` 1 → 3 → 0 and `tw` 0 → 0 → 1. `TIME_WAIT` here was normal, not an incident.

## 3. Observe CLOSE_WAIT and FIN_WAIT2

```bash
docker run --rm --name ops-tcp-close-wait \
  --memory=128m --memory-swap=128m \
  python:3.12-alpine python -c '
import socket
import threading
import time

HOST = "127.0.0.1"
PORT = 8765

def inspect(label):
    print("\n=== {} ===".format(label), flush=True)
    states = {
        "01": "ESTABLISHED", "05": "FIN_WAIT2", "06": "TIME_WAIT",
        "08": "CLOSE_WAIT", "0A": "LISTEN",
    }
    with open("/proc/net/tcp") as f:
        for line in f.readlines()[1:]:
            fields = line.split()
            print(states.get(fields[3], fields[3]), fields[1], fields[2], flush=True)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

def client_task():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    time.sleep(1)
    print("\nClient closing connection...", flush=True)
    client.close()

thread = threading.Thread(target=client_task)
thread.start()
connection, address = server.accept()
inspect("Connection established")
thread.join()
time.sleep(1)
inspect("Client closed, server socket still open")
print("\n=== Closing server socket ===", flush=True)
connection.close()
server.close()
time.sleep(1)
inspect("After server cleanup")
print("\n=== Experiment completed ===", flush=True)
'
```

**Observed:** two `ESTABLISHED` entries and one `LISTEN` entry initially. After the client closed but before server cleanup, the server side showed `CLOSE_WAIT` and the client side `FIN_WAIT2`. After `connection.close()`, `CLOSE_WAIT` disappeared and `TIME_WAIT` remained briefly.

## 4. Interpret and clean up

- `CLOSE_WAIT` means the remote peer has sent FIN, but the local application has not yet closed the socket. A short interval is normal; sustained accumulation requires investigation.
- `TIME_WAIT` is part of normal TCP teardown; its presence alone does not prove a leak.
- Both experiments use `--rm`, close their sockets, and publish no host ports.
- For Linux-host troubleshooting, see [TCP socket commands](../../../references/networking/tcp-socket-commands.md) and the [TCP troubleshooting playbook](../../../playbooks/linux-tcp-connection-troubleshooting.md).

## Validation status

**Tested:** tool baseline; `LISTEN`, `ESTABLISHED`, `TIME_WAIT`, `CLOSE_WAIT`, `FIN_WAIT2` transitions; socket counters; application-level socket close. Results were observed in Docker containers on November 11, 2026.

**Not tested:** packet loss, latency injection, production socket leaks, `ss` on a Linux host, kernel tuning, or any disruptive remediation.
