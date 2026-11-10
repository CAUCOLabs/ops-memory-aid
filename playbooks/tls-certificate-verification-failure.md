# TLS Certificate Verification Failure

## 1. Problem / Symptoms

An HTTPS client cannot establish a trusted TLS connection. Errors may mention an expired certificate, an unknown issuer, an incomplete chain, a hostname mismatch, an unavailable protocol, or a failed handshake.

## 2. Quick Diagnosis

Initialize the target before running the checks:

~~~bash
HOST="api.example.test"
PORT=443
CAFILE="/etc/ssl/certs/ca-certificates.crt"
URL="https://$HOST/"

date -u
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -showcerts </dev/null
curl -v --max-time 10 "$URL"
~~~

- date -u helps identify system-clock errors that can make a valid certificate appear expired or not yet valid.
- s_client shows the negotiated handshake, peer certificates, verification result, and selected SNI response.
- curl -v shows the address, TLS negotiation, certificate checks, and whether the request reached HTTP.
- A failure before an HTTP response points toward TLS, trust, name, time, or proxy inspection rather than application status.

Do not disable certificate verification as a permanent workaround. Preserve the error and certificate details first.

## 3. Possible Causes

- Certificate expired or not yet valid
- Hostname not present in the certificate Subject Alternative Name
- Unknown or untrusted certificate authority
- Incomplete server certificate chain
- Wrong certificate returned because SNI was omitted or misconfigured
- TLS protocol or cipher incompatibility
- Incorrect system clock
- Missing, stale, or incorrect trust store
- TLS interception by a proxy with an untrusted enterprise CA

## 4. Step-by-Step Investigation

### Step 1: Check the client clock

~~~bash
date -u
~~~

Compare UTC time with a trusted time source and the certificate validity window. A clock that is behind can produce not-yet-valid errors; a clock that is ahead can produce expired errors. Correct time through the approved host time procedure before changing certificates.

### Step 2: Inspect the certificate presented for the intended name

~~~bash
HOST="api.example.test"
PORT=443
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -showcerts </dev/null
~~~

Read the verification result, protocol, cipher, peer certificate subject, issuer, validity dates, and certificate chain. The server may present a different certificate when SNI changes, so include the intended hostname with server name indication.

### Step 3: Inspect certificate fields directly

~~~bash
HOST="api.example.test"
PORT=443
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" </dev/null 2>/dev/null |
  openssl x509 -noout -subject -issuer -dates -ext subjectAltName
~~~

Check notBefore and notAfter, issuer, and Subject Alternative Name entries. The requested hostname must match an appropriate SAN entry; the common name alone is not a reliable substitute for SAN validation.

### Step 4: Test the normal client verification path

~~~bash
HOST="api.example.test"
URL="https://$HOST/"
curl -v --max-time 10 "$URL"
~~~

Look for the resolved address, proxy use, TLS handshake messages, certificate verification error, and whether an HTTP status arrives. If curl and openssl differ, compare their trust-store configuration, proxy path, and SNI behavior.

### Step 5: Check trust-store and proxy behavior

~~~bash
HOST="api.example.test"
PORT=443
CAFILE="/etc/ssl/certs/ca-certificates.crt"
openssl s_client -connect "$HOST:$PORT" -servername "$HOST" -CAfile "$CAFILE" </dev/null
~~~

Use the operating system's documented trust-store path; it differs by distribution. If a proxy terminates TLS, the issuer may be an enterprise proxy CA rather than the public service CA. Confirm the proxy's approved trust chain and compare a request from a path that does not use interception when authorized.

### Step 6: Check SNI, chain, and handshake conditions

Compare the SNI-enabled result with a controlled test to the service address only when the environment permits it. A wrong certificate, missing intermediate, or handshake alert can identify a load balancer, virtual host, TLS policy, or deployment configuration problem. Do not treat a successful TCP connection as proof that TLS or HTTP is healthy.

## 5. How to Interpret Results

| Observation | Likely direction |
| --- | --- |
| Certificate expired | Renew or replace the certificate through the approved process; verify all serving nodes. |
| Certificate not yet valid | Check system time, deployment timing, and certificate validity dates. |
| Unknown CA | Check the client trust store and whether a proxy or private CA is expected. |
| Unable to get local issuer or incomplete chain | Configure the server to present the required intermediate certificates in the correct order. |
| Hostname mismatch | Check DNS, SNI, certificate SANs, and the endpoint selected by the client. |
| Different certificate with or without SNI | Investigate virtual-host, load-balancer, or proxy SNI configuration. |
| TLS handshake alert before HTTP | Investigate protocol, cipher, client-authentication, policy, or proxy compatibility. |
| Certificate is valid for a direct test but not through a proxy | Investigate TLS interception and the proxy's enterprise trust chain. |

## 6. Resolution Options

- Renew or replace expired, incomplete, or incorrect certificates through the certificate-management process.
- Configure the server, proxy, or load balancer to present the complete intended chain.
- Correct DNS, SNI, virtual-host, or certificate SAN configuration.
- Install or update an approved CA in the correct client trust store; do not copy arbitrary certificates into system trust.
- Correct the host clock through the approved time-synchronization procedure.
- Align TLS policy or proxy configuration after confirming compatibility and security requirements.

Never make disabling verification the permanent solution. A temporary isolated test may be authorized to confirm a hypothesis, but it must not become production configuration.

## 7. Verification

~~~bash
HOST="api.example.test"
URL="https://$HOST/"
date -u
openssl s_client -connect "$HOST:443" -servername "$HOST" </dev/null 2>/dev/null |
  grep -E 'Verify return code|subject=|issuer='
curl -v --max-time 10 "$URL"
~~~

Confirm the expected certificate, validity window, SAN, issuer, chain verification, negotiated TLS session, and successful HTTP response from the actual client path. Check all proxy or load-balancer nodes when traffic is distributed.

## 8. Safety Notes

- Do not paste private keys, client credentials, or sensitive certificate details into public notes.
- Treat trust-store changes and TLS policy changes as security-sensitive.
- Use SNI and the intended hostname when testing virtual-hosted services.
- Avoid using insecure curl options as a fix; they hide trust problems.
- Certificate output can differ by proxy, load balancer, address family, and backend.

## 9. References

- [TLS and HTTP commands](../references/networking/tls-http-commands.md)
- [OpenSSL s_client documentation](https://docs.openssl.org/3.0/man1/openssl-s_client/)
- [OpenSSL x509 documentation](https://docs.openssl.org/3.0/man1/openssl-x509/)
- [curl TLS documentation](https://curl.se/docs/sslcerts.html)
- [RFC 6125 hostname verification](https://www.rfc-editor.org/rfc/rfc6125)

## 10. Validation Status

Illustrative procedure. Commands were not run against a specific certificate, proxy, trust store, or production endpoint during authoring. Validate paths, OpenSSL and curl versions, proxy behavior, certificate-management procedures, and organizational trust requirements in the target environment.
