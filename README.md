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
- [Essential Linux commands](references/linux/essential-commands.md)
- [Essential networking commands](references/networking/essential-commands.md)
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

Stage 1 focuses on Linux-hosted application troubleshooting, essential Linux operational commands, and a reusable playbook format. The repository will grow around practical operational problems as they are documented and reviewed.

## License

This project is available under the [MIT License](LICENSE).
