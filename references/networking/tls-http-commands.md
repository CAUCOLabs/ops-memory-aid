# TLS and HTTP Commands

This reference focuses on safe, read-only checks for TLS certificates and HTTP responses. Initialize values before running examples:

~~~bash
HOST="api.example.test"
PORT=443
URL="https://$HOST/"
~~~

## TLS inspection

### openssl s_client

Purpose: Establish a TLS handshake and display the peer certificate, negotiated session, and verification result.

Example:

~~~bash
HOST="api.example.test"
PORT=443
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -showcerts </dev/null
~~~

What to look for: Protocol, cipher, SNI-selected certificate, certificate chain, verify return code, handshake alerts, and whether the session reaches completion. A successful handshake does not prove the HTTP application is healthy.

### openssl x509

Purpose: Read certificate fields such as subject, issuer, validity dates, and SANs.

Example:

~~~bash
CERTIFICATE_FILE="/path/to/certificate.pem"
openssl x509 -in "$CERTIFICATE_FILE" -noout -subject -issuer -dates -ext subjectAltName
~~~

What to look for: notBefore, notAfter, issuer, and SAN entries matching the requested hostname. Protect private keys; this command only needs a public certificate.

### date -u

Purpose: Display the host's current UTC time for comparison with certificate validity windows and incident timestamps.

Example:

~~~bash
date -u
~~~

What to look for: A correct current time and timezone-independent output. Clock skew can produce expired or not-yet-valid certificate errors.

## HTTP inspection

### curl -v

Purpose: Show verbose DNS, connection, TLS, request, and response details for an HTTP request.

Example:

~~~bash
URL="https://api.example.test/"
curl -v --max-time 10 "$URL"
~~~

What to look for: Selected address, proxy use, TLS verification, request headers, response status, headers, and body. Do not publish authorization headers or cookies from verbose output.

### curl -I

Purpose: Request response headers without downloading the response body, when the server supports HEAD correctly.

Example:

~~~bash
URL="https://api.example.test/health"
curl -I --silent --show-error --max-time 10 "$URL"
~~~

What to look for: HTTP status, redirects, cache headers, Server or Via headers, and TLS or connection errors. Some applications handle HEAD differently from GET, so a header-only result is not a complete health check.

### curl --resolve

Purpose: Send a request to a chosen address while retaining the hostname for DNS-independent testing, TLS SNI, and Host header behavior.

Example:

~~~bash
HOST="api.example.test"
PORT=443
ADDRESS="203.0.113.10"
URL="https://$HOST/"
curl -v --max-time 10 --resolve "$HOST:$PORT:$ADDRESS" "$URL"
~~~

What to look for: Whether the selected endpoint serves the correct certificate and HTTP response for the intended hostname. Use an approved test address; do not publish private infrastructure addresses.

## Interpretation guidance

- A TCP connection failure occurs before HTTP; investigate address selection, routes, firewalls, listeners, and timeouts.
- A TLS verification or handshake failure occurs after connection but before HTTP; investigate time, trust, certificate fields, SNI, protocol, and interception.
- An HTTP status and body prove that an HTTP component responded; determine whether it is a proxy, load balancer, or backend.
- Preserve response headers and bodies during exploration. Add failure-exit behavior only when a script needs it; curl 7.76.0 or newer provides --fail-with-body.

## Safety and validation

These examples are intended for diagnostic use and do not modify certificates, trust stores, routes, or services. Output and options vary by distribution, OpenSSL version, curl version, proxy, and network policy. Validate destinations and redact credentials, cookies, tokens, and private addresses before sharing output.

## References

- [OpenSSL s_client documentation](https://docs.openssl.org/3.0/man1/openssl-s_client/)
- [OpenSSL x509 documentation](https://docs.openssl.org/3.0/man1/openssl-x509/)
- [curl documentation](https://curl.se/docs/)
- [curl SSL certificate documentation](https://curl.se/docs/sslcerts.html)
- [HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110)
