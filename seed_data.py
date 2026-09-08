import urllib.request
import json
import time

URL_LOGIN = "http://127.0.0.1:8000/api/v1/auth/login"
URL_INGEST = "http://127.0.0.1:8000/api/v1/ingest/single"

logs = [
    # User 1: nikhil
    '2026-09-08T10:00:00Z | GATE-01 | actor=nikhil | remote=10.0.0.5 | task=login | outcome=success | channel=web',
    '2026-09-08T10:05:00Z | GATE-01 | actor=nikhil | remote=10.0.0.5 | task=access_panel | outcome=success | channel=web',
    '2026-09-08T10:10:00Z | DB-MAIN | actor=nikhil | query="SELECT * FROM users" | duration=15ms | outcome=success',
    '2026-09-08T10:15:00Z | DB-MAIN | actor=nikhil | query="DROP TABLE users" | duration=5ms | outcome=denied',
    '2026-09-08T10:16:00Z | DB-MAIN | actor=nikhil | query="DROP TABLE users" | duration=4ms | outcome=denied',
    '2026-09-08T10:17:00Z | GATE-01 | actor=nikhil | remote=10.0.0.5 | task=logout | outcome=success | channel=web',
    
    # User 2: alice
    '2026-09-08T11:00:00Z sshd[1234]: Accepted publickey for alice from 192.168.1.100 port 50000 ssh2',
    '2026-09-08T11:05:00Z sudo[1235]: alice : TTY=pts/0 ; PWD=/home/alice ; USER=root ; COMMAND=/bin/bash',
    '2026-09-08T11:06:00Z | APP-SRV | actor=alice | remote=192.168.1.100 | task=restart_service | outcome=success',
    '2026-09-08T11:15:00Z sshd[1234]: pam_unix(sshd:session): session closed for user alice',

    # User 3: bob (anomalous)
    '2026-09-08T12:00:00Z sshd[5555]: Failed password for invalid user bob from 203.0.113.42 port 4444 ssh2',
    '2026-09-08T12:00:05Z sshd[5555]: Failed password for invalid user bob from 203.0.113.42 port 4444 ssh2',
    '2026-09-08T12:00:10Z sshd[5555]: Failed password for invalid user bob from 203.0.113.42 port 4444 ssh2',
    '2026-09-08T12:00:15Z sshd[5555]: Failed password for invalid user bob from 203.0.113.42 port 4444 ssh2',
    '2026-09-08T12:05:00Z | GATE-07 | actor=bob | remote=203.0.113.42 | task=access_panel | outcome=blocked | channel=ssh | attempts=1',
    '2026-09-08T12:06:00Z | GATE-07 | actor=bob | remote=203.0.113.42 | task=access_panel | outcome=blocked | channel=ssh | attempts=2',
    '2026-09-08T12:07:00Z | GATE-07 | actor=bob | remote=203.0.113.42 | task=access_panel | outcome=blocked | channel=ssh | attempts=3',
    '2026-09-08T12:08:00Z | GATE-07 | actor=bob | remote=203.0.113.42 | task=access_panel | outcome=blocked | channel=ssh | attempts=4'
]

print("Authenticating as demo user...")
auth_payload = json.dumps({"email": "demo@ila.local", "password": "demo12345"}).encode('utf-8')
req = urllib.request.Request(URL_LOGIN, data=auth_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    token = json.loads(r.read())["access_token"]

print(f"Sending {len(logs)} synthetic logs to ILA Engine...")
success = 0
for i, log in enumerate(logs):
    try:
        payload = json.dumps({"log": log}).encode('utf-8')
        req = urllib.request.Request(URL_INGEST, data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req) as r:
            if r.getcode() in (200, 201):
                print(f"[{i+1}/{len(logs)}] SUCCESS")
                success += 1
            else:
                print(f"[{i+1}/{len(logs)}] FAILED: {r.getcode()}")
    except Exception as e:
        print(f"[{i+1}/{len(logs)}] ERROR: {e}")
    time.sleep(0.1)

print(f"Done. Successfully ingested {success}/{len(logs)} logs.")
