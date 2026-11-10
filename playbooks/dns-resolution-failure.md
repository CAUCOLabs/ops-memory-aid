# DNS Resolution Failure

## 1. Problem / Symptoms

A hostname does not resolve, resolves to an unexpected address, or resolves inconsistently between hosts or networks. Applications may report name lookup errors, connection failures, or timeouts even though the destination service is running.

## 2. Quick Diagnosis

Initialize the hostname before running the checks:

~~~bash
DOMAIN="api.example.test"
DNS_SERVER="1.1.1.1"

getent hosts "$DOMAIN"
dig "$DOMAIN"
dig @"$DNS_SERVER" "$DOMAIN"
resolvectl query "$DOMAIN"
~~~

- An address from getent confirms that the local name-service path returned a result; it does not prove the record is correct.
- A dig response shows the DNS response code, answer section, server queried, and timing.
- Comparing the configured local resolver with a specified DNS server helps separate local resolver problems from broader DNS or record problems.
- A timeout suggests reachability or resolver problems; NXDOMAIN means the queried server says the name does not exist; SERVFAIL means the server could not complete a valid resolution.

## 3. Possible Causes

- Missing, misspelled, or incorrectly delegated DNS records
- Stale local or recursive resolver data
- Incorrect resolver configuration or an unavailable DNS server
- Search-domain or split-horizon DNS behavior
- DNSSEC, delegation, or authoritative-server failure
- Firewall or network restrictions affecting DNS traffic

## 4. Step-by-Step Investigation

### Step 1: Check the local name-service path

~~~bash
DOMAIN="api.example.test"
getent hosts "$DOMAIN"
~~~

getent uses the host's configured name-service switch and resolver path. A result identifies the address returned to applications using that path. No result means continue with resolver-specific checks; it does not identify whether the problem is the record, local configuration, or upstream DNS.

### Step 2: Inspect the DNS response directly

~~~bash
DOMAIN="api.example.test"
dig "$DOMAIN"
~~~

Read the status line, flags, answer count, answer records, queried server, and query time. The answer section shows what the selected resolver returned. An empty answer with NOERROR can indicate that the name exists but has no record of the requested type; query the needed type explicitly when appropriate.

### Step 3: Compare another resolver

~~~bash
DOMAIN="api.example.test"
DNS_SERVER="1.1.1.1"
dig @"$DNS_SERVER" "$DOMAIN"
~~~

Compare status, answer, TTL, and response time with the local resolver result. A difference can indicate split-horizon DNS, stale cache data, resolver policy, or propagation timing. Use a resolver approved for the environment; a public resolver may not see private records.

### Step 4: Inspect local DNS configuration

~~~bash
resolvectl status
resolvectl dns
~~~

Where systemd-resolved is present, these commands show global and per-link DNS servers, search domains, and resolver state. If resolvectl is unavailable, inspect the platform's configured resolver mechanism rather than assuming systemd-resolved is used.

### Step 5: Query with the local resolver tool

~~~bash
DOMAIN="api.example.test"
resolvectl query "$DOMAIN"
~~~

This shows the result as seen by systemd-resolved, including the interface or server path where available. Compare it with getent and dig. A mismatch suggests different resolver paths or name-service configuration.

### Step 6: Check authoritative DNS when needed

~~~bash
DOMAIN="api.example.test"
dig NS "$DOMAIN"
dig +trace "$DOMAIN"
~~~

An NS query identifies delegated name servers when the queried zone exposes them. A trace follows delegation from the root toward authoritative servers and can reveal delegation or authoritative failures. It may be restricted or unsuitable for some private zones; use the organization's authoritative DNS procedure when applicable.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| NXDOMAIN | The queried DNS view says the name does not exist; check spelling, zone, delegation, and split-horizon configuration. |
| SERVFAIL | The resolver could not complete resolution; investigate upstream reachability, delegation, DNSSEC, or authoritative-server errors. |
| Timeout with no DNS response | Check resolver address, network path, firewall rules, and DNS server availability. |
| NOERROR with no answer | The name may exist without the requested record type; query the expected type and inspect authority information. |
| Local resolver differs from specified resolver | Investigate split DNS, stale cache, resolver policy, or propagation. |
| Authoritative answer is correct but getent is wrong | Investigate local resolver configuration, cache, search domains, or name-service order. |
| DNS resolves correctly but the application still fails | Continue with connectivity, port, TLS, proxy, or application diagnostics. |

## 6. Resolution Options

- Correct the hostname, record type, zone, or authoritative record through the approved DNS change process.
- Correct local resolver or search-domain configuration when the host is using the wrong DNS path.
- Restore or replace an unavailable recursive or authoritative resolver according to its operational procedure.
- Allow required DNS traffic only through approved network and firewall changes.
- After a DNS change, allow for TTL and cache behavior; verify from the relevant client network rather than relying on one resolver.

## 7. Verification

~~~bash
DOMAIN="api.example.test"
getent hosts "$DOMAIN"
dig "$DOMAIN"
curl --silent --show-error --max-time 10 --include "http://$DOMAIN/health"
~~~

Confirm that the expected name resolves through the same path used by the application, that the record is correct, and that a request reaches the intended service. A successful lookup alone does not prove service health.

## 8. Safety Notes

- Use an approved DNS server when testing private or split-horizon names.
- Treat DNS changes as shared infrastructure changes with TTL and caching effects.
- Do not flush caches or edit resolver configuration blindly; capture current state first.
- Avoid publishing private names, addresses, or internal DNS responses in public notes.
- The availability and output of resolvectl depend on the host's resolver implementation.

## 9. References

- [Essential networking commands](../references/networking/essential-commands.md)
- [BIND 9 utilities documentation](https://bind9.readthedocs.io/en/latest/manpages.html)
- [systemd-resolved documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd-resolved.service.html)
- [DNS and IANA terminology](https://www.iana.org/domains)

## 10. Validation Status

Illustrative procedure. Commands were not run against a specific domain, resolver, or production network during authoring. Validate resolver availability, record types, split-horizon behavior, permissions, and organizational DNS procedures in the target environment.
