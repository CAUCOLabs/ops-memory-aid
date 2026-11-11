# Ops Memory Aid

An open-source technical reference for developers, platform engineers, and IT professionals who need to diagnose problems, recall commands, interpret results, and resolve incidents safely.

> Understand the system. Document the details.

## Why this project exists

Operational troubleshooting often depends on details that are easy to forget under pressure: which signal to check first, what a command actually reveals, and when an apparent fix may hide a deeper problem. Ops Memory Aid collects concise, problem-oriented notes for that work.

This is a practical external memory aid—not an interview preparation course or a collection of generic tutorials.

## Who it is for

- Developers investigating application and API failures
- Platform and site reliability engineers diagnosing infrastructure issues
- IT professionals supporting Linux-hosted services
- Anyone who needs a compact, reviewable reference during technical incidents

## How to use this repository

Start with the playbook that matches the symptom. Use the quick diagnosis section to establish basic facts, then work through the investigation steps in order. Treat commands as diagnostic tools: read their output, form a hypothesis, and choose the next check accordingly.

Use the command references for focused lookup. Adapt examples to the target host, service name, port, and environment. Confirm the scope and safety of any change before applying it.

## Quick navigation

- [Application unresponsive playbook](playbooks/application-unresponsive.md)
- [DNS resolution failure playbook](playbooks/dns-resolution-failure.md)
- [Connection refused or timed out playbook](playbooks/connection-refused-or-timeout.md)
- [TLS certificate verification failure playbook](playbooks/tls-certificate-verification-failure.md)
- [HTTP 502/503 errors playbook](playbooks/http-502-503-errors.md)
- [Docker container exits immediately playbook](playbooks/docker-container-exits-immediately.md)
- [Docker container unhealthy playbook](playbooks/docker-container-unhealthy.md)
- [High CPU usage playbook](playbooks/high-cpu-usage.md)
- [Linux memory pressure playbook](playbooks/linux-memory-pressure.md)
- [Linux disk and filesystem troubleshooting playbook](playbooks/linux-disk-filesystem-troubleshooting.md)
- [Essential Linux commands](references/linux/essential-commands.md)
- [Linux performance commands](references/linux/performance-commands.md)
- [Linux memory commands](references/linux/memory-commands.md)
- [Linux disk and filesystem commands](references/linux/disk-filesystem-commands.md)
- [Essential networking commands](references/networking/essential-commands.md)
- [TLS and HTTP commands](references/networking/tls-http-commands.md)
- [Essential Docker commands](references/docker/essential-commands.md)
- [Docker container health lab](labs/docker/container-health/README.md)
- [CPU load laboratory](labs/linux/cpu-load/README.md)
- [Memory pressure laboratory](labs/linux/memory-pressure/README.md)
- [Disk and filesystem laboratory](labs/linux/disk-filesystem/README.md)
- [Playbook template](templates/playbook-template.md)

## Documentation conventions

- Organize content around a problem, symptom, or operational task.
- Prefer copyable commands followed by what to look for.
- Explain how an observation changes the next diagnostic step.
- Initialize environment-specific values such as SERVICE and PORT before running command examples.
- Do not include credentials, private addresses, or other sensitive information.
- Mark procedures as tested, illustrative, or requiring environment-specific validation.
- Do not recommend disruptive actions, such as restarting a service, without a reason and a verification step.

## Current scope

The repository currently covers Linux-hosted application troubleshooting, DNS and connectivity failures, TLS verification, HTTP 502/503 responses, Docker container diagnostics, CPU usage, and Linux memory troubleshooting. Command references provide focused lookup, while the Docker container health lab reproduces healthy, exited, unhealthy, and recovery scenarios.

The Docker lab scenarios were executed on macOS with Docker Engine 28.3.2 and Docker Compose v2.38.2-desktop.1 on November 10, 2026. This validation applies to the lab scenarios only; other troubleshooting procedures may be illustrative or require environment-specific verification.

## License

This project is available under the [MIT License](LICENSE).
