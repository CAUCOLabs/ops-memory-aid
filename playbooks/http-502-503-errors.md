# HTTP 502 and 503 Errors

## 1. Problem / Symptoms

An HTTP client receives a 502 Bad Gateway or 503 Service Unavailable response. The response may come from a reverse proxy, load balancer, gateway, service mesh, or the backend application. The status alone does not identify the root cause.

## 2. Quick Diagnosis

Initialize the target before running the checks:

~~~bash
SERVICE="my-api.service"
HOST="api.example.test"
PORT=8000
URL="http://$HOST/health"

systemctl status "$SERVICE" --no-pager
ss -ltnp "sport = :$PORT"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

- Record the response status, headers, body, and server or proxy identity.
- Check whether the backend process exists and whether the expected port is listening.
- A proxy-generated 502 or 503 often includes gateway headers or a proxy-specific body; compare it with a direct backend request where authorized.
- A backend-generated 502 or 503 may have application headers, request identifiers, and application logs.

Do not assume that 502 means DNS or that 503 means overload. Both statuses have multiple possible causes.

## 3. Possible Causes

- Reverse proxy cannot connect to the upstream
- Backend refuses connections or times out
- Incorrect upstream hostname, port, protocol, or address family
- Backend process crashed, is starting, or is unhealthy
- Load balancer health checks fail or mark all backends unavailable
- Application dependency failure or resource exhaustion
- Deployment, routing, proxy, or service configuration error

## 4. Step-by-Step Investigation

### Step 1: Capture the client-visible response

~~~bash
URL="http://api.example.test/health"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

Record status, headers, body, timing, request identifiers, and any Server or Via header. A response proves that some HTTP component was reachable; inspect its identity before deciding whether the backend was involved.

### Step 2: Check the backend service

~~~bash
SERVICE="my-api.service"
systemctl status "$SERVICE" --no-pager
systemctl is-active "$SERVICE"
~~~

Check unit state, main PID, recent exit status, and whether the service is managed by systemd. Active means systemd considers the unit running; it does not prove readiness or that the configured upstream address is reachable.

### Step 3: Check the expected listener

~~~bash
PORT=8000
ss -ltnp "sport = :$PORT"
~~~

Inspect local address, port, state, and owning process where permitted. A loopback-only listener may work for a local proxy but fail when the proxy connects through another interface. No listener points toward startup, crash, bind, port, or deployment configuration.

### Step 4: Test the backend locally

~~~bash
PORT=8000
BACKEND_URL="http://127.0.0.1:$PORT/health"
curl --silent --show-error --max-time 10 --include "$BACKEND_URL"
~~~

A successful direct response with a proxy error shifts attention to upstream host, port, routing, proxy protocol, health checks, or network policy. A direct refusal or timeout keeps the investigation on the backend host, service, listener, and local dependencies.

### Step 5: Read service logs

~~~bash
SERVICE="my-api.service"
journalctl -u "$SERVICE" --since '30 minutes ago' --no-pager -o short-iso
~~~

Correlate timestamps with the 502 or 503. Look for crashes, startup loops, dependency errors, bind failures, request timeouts, and resource exhaustion. Also inspect proxy or load-balancer logs using the environment's approved procedure.

### Step 6: Compare proxy and backend behavior

Use a controlled request to the proxy and, where authorized, to the backend. Compare status, headers, body, request identifiers, selected address, and timing. If the proxy sees a refused connection or timeout while a local backend request succeeds, investigate the proxy's route, DNS, firewall, security group, and upstream configuration.

### Step 7: Check health checks and deployment state

Confirm the configured health-check path, method, Host header, protocol, expected status range, timeout, and backend pool membership. Review recent deployments and configuration changes. A deployment can leave a process running while its port, health endpoint, certificate, or dependency configuration is wrong.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| Proxy returns 502 and backend port refuses | Backend is unavailable, misbound, stopped, or the upstream port is wrong. |
| Proxy returns 502 and backend times out | Investigate backend overload, routing, firewall, dependency stalls, or proxy timeout policy. |
| Proxy returns 503 with no healthy backends | Check load-balancer health checks, backend pool state, and deployment readiness. |
| Direct backend request succeeds but proxy fails | Investigate upstream address, proxy route, headers, protocol, DNS, and network policy. |
| Direct backend request fails and service is inactive | Investigate crash, startup, configuration, and service logs. |
| HTTP response identifies the application and has request context | The backend or application path likely generated the response; inspect application logs and dependencies. |
| Error began after deployment or configuration change | Compare the change with upstream, listener, health-check, and resource settings. |

## 6. Resolution Options

- Restore the backend through its normal supervisor or deployment procedure after preserving evidence.
- Correct upstream host, port, protocol, bind address, or proxy route configuration.
- Repair a failing health check or remove only demonstrably unhealthy backends according to load-balancer procedure.
- Restore an unavailable dependency or address resource exhaustion through the approved capacity procedure.
- Roll back or correct a verified deployment or configuration change using change-control procedures.

## 7. Verification

~~~bash
URL="http://api.example.test/health"
PORT=8000
BACKEND_URL="http://127.0.0.1:$PORT/health"
curl --silent --show-error --max-time 10 --include "$BACKEND_URL"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

Verify direct backend health, proxy or load-balancer health, expected HTTP status and body, recent logs, and more than one request. Confirm that the normal client path works and that the backend remains healthy after the change.

## 8. Safety Notes

- Preserve proxy, backend, and deployment evidence before restarting or rolling back.
- Do not expose tokens, cookies, internal addresses, or sensitive headers in notes.
- Do not remove all backends or change health-check thresholds without understanding traffic impact.
- Treat restarts, rollbacks, proxy edits, firewall changes, and scaling actions as potentially disruptive.
- A healthy local request does not prove the proxy-to-backend path is healthy.

## 9. References

- [TLS and HTTP commands](../references/networking/tls-http-commands.md)
- [curl documentation](https://curl.se/docs/)
- [systemctl documentation](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html)
- [journalctl documentation](https://www.freedesktop.org/software/systemd/man/latest/journalctl.html)
- [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)

## 10. Validation Status

Illustrative procedure. Commands were not run against a specific proxy, load balancer, service, or production deployment during authoring. Validate service names, upstream paths, health checks, permissions, proxy behavior, and output in the target environment.
