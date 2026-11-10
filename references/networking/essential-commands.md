# Essential Networking Commands

This reference focuses on safe, read-only networking checks. Initialize values before running examples:

~~~bash
HOST="api.example.test"
PORT=8443
DOMAIN="api.example.test"
DNS_SERVER="1.1.1.1"
URL="https://$HOST:$PORT/health"
~~~

## DNS lookup

### dig

Purpose: Query DNS records and inspect the complete DNS response.

Example:

~~~bash
DOMAIN="api.example.test"
dig "$DOMAIN"
dig "$DOMAIN" A
dig @"1.1.1.1" "$DOMAIN"
~~~

What to look for: Status such as NOERROR, NXDOMAIN, or SERVFAIL; answer and authority sections; queried server; TTL; flags; and query time. Compare a local resolver with a specified resolver when results differ.

### getent

Purpose: Query the host's configured name-service path, which is the path applications commonly use.

Example:

~~~bash
HOST="api.example.test"
getent hosts "$HOST"
getent ahosts "$HOST"
~~~

What to look for: Returned addresses and address families. A result confirms the local name-service path returned an address, not that the record is correct or the destination is reachable.

### resolvectl

Purpose: Inspect and query systemd-resolved when that resolver is in use.

Example:

~~~bash
resolvectl status
resolvectl dns
resolvectl query "$DOMAIN"
~~~

What to look for: Configured DNS servers, per-link servers, search domains, resolver state, selected address, and errors. The command may be unavailable when another resolver implementation is used.

## Connections and ports

### ss

Purpose: Inspect listening sockets and network connection state.

Example:

~~~bash
PORT=8443
ss -ltnp "sport = :$PORT"
ss -tan
~~~

What to look for: State, local and peer addresses, port, and owning process where permitted. A loopback listener is local-only; 0.0.0.0 or :: indicates all interfaces, still subject to firewall and routing. A listener proves a bind, not application readiness.

### nc

Purpose: Test whether a TCP or UDP endpoint can be reached without using a full application client.

Example:

~~~bash
HOST="api.example.test"
PORT=8443
nc -vz -w 5 "$HOST" "$PORT"
~~~

What to look for: Successful TCP handshake, refusal, or timeout. Zero-I/O mode avoids sending application payload. A successful check does not prove HTTP, TLS, authentication, or application health.

### curl

Purpose: Test an HTTP or HTTPS request and inspect the response.

Example:

~~~bash
URL="https://api.example.test:8443/health"
curl --silent --show-error --max-time 10 --include "$URL"
~~~

What to look for: Connection or TLS errors, timeout, HTTP status, headers, body, and timing. Without --fail, HTTP errors remain visible. curl 7.76.0 or newer supports --fail-with-body when scripts need a nonzero exit for HTTP errors while retaining the body.

## Routes and path

### ip

Purpose: Inspect interfaces, addresses, routes, and route selection.

Example:

~~~bash
HOST="api.example.test"
ADDRESS="$(getent ahostsv4 "$HOST" | awk 'NR==1 {print $1}')"
ip address show
ip route
ip route get "$ADDRESS"
~~~

What to look for: Interface state, assigned addresses, default route, selected interface, source address, and next hop. A route lookup is local evidence and does not prove return traffic works.

### traceroute or tracepath

Purpose: Inspect the path toward a destination and identify where replies stop or path MTU changes.

Example:

~~~bash
HOST="api.example.test"
tracepath "$HOST"
traceroute "$HOST"
~~~

What to look for: Hops, latency, packet-loss indications, and path-MTU information from tracepath. Probes may be filtered or deprioritized, so missing replies do not prove that the next hop is broken. Use the available command and the network's approved diagnostic policy.

## Safety and validation

These examples are intended for diagnostic use and do not change service, route, firewall, or DNS state. Output and options vary by distribution, privileges, resolver, curl version, and network policy. Validate destinations and use approved procedures before making any change.

## References

- [BIND 9 utilities documentation](https://bind9.readthedocs.io/en/latest/manpages.html)
- [systemd-resolved documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html)
- [iproute2 documentation](https://iproute2.org/)
- [curl documentation](https://curl.se/docs/)
- [OpenBSD nc manual](https://man.openbsd.org/nc)
- [Linux man-pages project](https://man7.org/linux/man-pages/)
