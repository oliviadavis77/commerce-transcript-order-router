import json
import os
import urllib.request


payload = {
    "event_id": "call-2026-0042",
    "order_id": "ord-1842",
    "customer_id": "cus-731",
    "transcript": "Can you tell me whether order 1842 has shipped yet?",
}
request = urllib.request.Request(
    os.environ.get("SERVICE_URL", "http://127.0.0.1:8000/transcript-events"),
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request) as response:
    print(json.dumps(json.load(response), indent=2))
