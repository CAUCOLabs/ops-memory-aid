# Connection Refused or Timed Out

## 1. Problem / Symptoms

A client cannot connect to a host and port. The client may report connection refused, a timeout, or an HTTP failure. The distinction helps determine whether the target host rejected the connection, whether traffic reached the target at all, or whether an application responded with an error.

## 2. Quick Diagnosis

Initialize the destination before running the checks:

~~~bash
HOST="api.example.test"
PORT=8443
URL="https://$HOST:$PORT/health"

ss -ltnp "sport = :$PORT"
nc -vz -w 5 "$HOST" "$PORT"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

- Connection refused usually means the destination was reachable but no process accepted the port, or an active device rejected it.
- A timeout means no usable response arrived within the deadline; investigate routing, firewall policy, filtering, service overload, or a wrong address.
- A listening socket does not prove the application is healthy or accessible through the relevant interface.
- A completed HTTP response means the request reached an HTTP-speaking component; inspect its status and body before blaming the network.

## 3. Possible Causes

- No service is listening on the expected port
- Service is bound only to loopback or another address
- Port conflict or wrong service configuration
- Host firewall, network firewall, security group, or ACL restriction
- Missing route, asymmetric routing, or unreachable network
- Service overload, dependency delay, or application-level failure
- Wrong hostname, address family, port, protocol, proxy, or TLS configuration

## 4. Step-by-Step Investigation

### Step 1: Test the local service when you have host access

~~~bash
PORT=8443
ss -ltnp "sport = :$PORT"
~~~

Read the local address and port, state, and owning process where permitted. A loopback listener accepts only local clients. A listener on all interfaces is still subject to host firewall, network policy, and application controls. No listener points toward service state, startup, bind, or configuration.

### Step 2: Test TCP from the affected client

~~~bash
HOST="api.example.test"
PORT=8443
nc -vz -w 5 "$HOST" "$PORT"
~~~

nc in zero-I/O mode attempts the TCP connection without sending application data. A successful connection proves that a TCP handshake completed from this client; it does not prove that HTTP, TLS, authentication, or the application is healthy. Refused and timed-out results should be correlated with server-side evidence.

### Step 3: Compare local and remote HTTP behavior

~~~bash
HOST="api.example.test"
PORT=8443
URL="https://$HOST:$PORT/health"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

Do not use --fail for this exploratory request. Connection refusal or timeout means no completed HTTP response. An HTTP 4xx or 5xx means an HTTP component responded and its body and headers may identify an application, proxy, or authorization issue. A 2xx response supports health for that endpoint but does not prove every client path works.

### Step 4: Check name and address selection

~~~bash
HOST="api.example.test"
getent ahosts "$HOST"
~~~

Compare the resolved IPv4 and IPv6 addresses with the service's bind addresses and network path. A client may select IPv6 while the service listens only on IPv4, or may resolve an unexpected address.

### Step 5: Check routes and path behavior

~~~bash
HOST="api.example.test"
ip route get "$(getent ahostsv4 "$HOST" | awk 'NR==1 {print $1}')"
tracepath "$HOST"
~~~

The route lookup shows the selected interface, source address, and next hop when available. tracepath can reveal path MTU and where responses stop, but a missing response does not by itself prove the next hop is the failure because devices may filter probes.

### Step 6: Correlate with host and network controls

Check host firewall logs, cloud security rules, network ACLs, load balancer listeners, proxy configuration, and routing policy using the environment's approved procedures. Compare server-side packet, firewall, service, and application logs at the same timestamp. Do not infer a firewall problem solely from a timeout.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| Refused immediately | Host or active network device responded, but no permitted listener accepted the port; check service state, bind address, and rejection policy. |
| Timeout | No usable response arrived; check route, filtering, ACLs, security groups, overload, and destination address. |
| Local TCP succeeds, remote TCP fails | Investigate bind scope, host firewall, network policy, routing, and client path. |
| TCP succeeds, HTTP returns 4xx or 5xx | Network path reached an HTTP component; investigate application, proxy, authentication, or dependency behavior. |
| Local and remote TCP both fail | Check listener, service state, port configuration, and host-side controls first. |
| Correct service works by IP but not hostname | Investigate DNS, address selection, proxy, TLS name, or client configuration. |
| Listener exists on loopback only | Bind the service to an approved reachable interface or use the intended local proxy path. |

## 6. Resolution Options

- Start or repair the intended service through its normal supervisor after collecting evidence.
- Correct the service port or bind address through the approved configuration and deployment process.
- Correct an approved firewall, security-group, ACL, route, proxy, or load-balancer rule.
- Restore a dependency or reduce application load according to the service procedure.
- Correct hostname, address-family, protocol, TLS, or proxy configuration.

## 7. Verification

~~~bash
HOST="api.example.test"
PORT=8443
URL="https://$HOST:$PORT/health"
nc -vz -w 5 "$HOST" "$PORT"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

Verify from the affected client path and, where possible, from the server itself. Confirm the expected listener, HTTP status and body, recent logs, and behavior over more than one request.

## 8. Safety Notes

- Confirm the destination host, address, port, protocol, and environment before changing anything.
- Use nc with zero-I/O mode for a port check; do not send arbitrary data to an unknown service.
- Treat firewall, route, proxy, load-balancer, bind, and service changes as potentially disruptive.
- Preserve timestamps and error output before restarting or changing network policy.
- A successful TCP check does not authorize access or prove application health.

## 9. References

- [Essential networking commands](../references/networking/essential-commands.md)
- [ss manual](https://man7.org/linux/man-pages/man8/ss.8.html)
- [curl documentation](https://curl.se/docs/)
- [OpenBSD nc manual](https://man.openbsd.org/nc)
- [iproute2 documentation](https://iproute2.org/)

## 10. Validation Status

Illustrative procedure. Commands were not run against a specific host, network, service, or production environment during authoring. Validate command options, address-family behavior, permissions, firewall procedures, and application endpoints in the target environment.
