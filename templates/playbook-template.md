# [Problem or incident title]

## 1. Problem / Symptoms

Describe the observable symptoms, affected scope, and relevant context.

## 2. Quick Diagnosis

Run the smallest set of safe checks that helps distinguish the main failure modes.

~~~bash
SERVICE="my-api.service"
APP_NAME="my-api"
PORT=8000
HEALTH_URL="http://127.0.0.1:$PORT/health"

systemctl status "$SERVICE" --no-pager
pgrep -af "$APP_NAME"
ss -ltnp "sport = :$PORT"
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

Initialize environment-specific values before running the checks below.

Keep process running, application health, and client accessibility as separate observations.

Expected signals:

- What a normal result looks like
- What an abnormal result suggests

## 3. Possible Causes

- Cause: symptom or evidence that supports it
- Cause: symptom or evidence that supports it

## 4. Step-by-Step Investigation

### Step 1: [Check]

~~~bash
systemctl status "$SERVICE" --no-pager
~~~

What it reveals and what to check in the output.

### Step 2: [Check]

~~~bash
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

What the result means and how it determines the next step.

## 5. How to Interpret Results

Record useful output patterns, likely meanings, and conditions that require escalation or a different investigation path.

## 6. Resolution Options

Describe the least disruptive appropriate action first. State prerequisites, risks, and any required approval. Do not treat a restart or other disruptive action as a default fix.

## 7. Verification

List checks that confirm recovery and checks that help detect recurrence.

~~~bash
curl --silent --show-error --max-time 10 --include "$HEALTH_URL"
~~~

## 8. Safety Notes

- Confirm the target host and service before making changes.
- Avoid exposing credentials or sensitive output in notes.
- Capture relevant evidence before changing state when practical.

## 9. References

- Add relevant official documentation, runbook, or incident reference.

## 10. Validation Status

State whether the procedure is tested, partially tested, or illustrative. Include the environment and date when a procedure has been tested.
