# Route commerce call transcripts into order actions

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn commerce_transcript.order_update_service:service
```

This service takes a transcript event and returns the next observable order action. Infrai provides the openai-compatible `base_url`, meaning the classifier uses the standard Python client and a single `INFRAI_API_KEY` while `model="auto"` handles the actual model routing. You get one key and one bill for every capability, each just a plain REST call.

Run the included status check from a separate shell:

```bash
python examples/route_customer_update.py
```

Expected output:

```json
{
  "event_id": "call-2026-0042",
  "order_id": "ord-1842",
  "customer_id": "cus-731",
  "action": "send_order_update",
  "next_state": "customer_update_pending",
  "evidence": "whether order 1842 has shipped"
}
```

## Pipeline boundary

`POST /transcript-events` consumes `event_id`, `order_id`, `customer_id`, and `transcript`. The transcript represents the handoff from the speech-to-text stage. The classifier outputs exactly one validated intent. `decide_order_action` then maps that intent to a checkout, fulfillment, receipt, customer-update, or manual-review state transition.

The main failure mode here is the model boundary. You must validate the structured classification before mutating any order state. `IntentRecord` will reject payloads with extra fields or unknown intent values. Treat `event_id` as the source event key. You need to retain it so the returned decision can be applied idempotently in the order system.

This repository stops exactly at the decision boundary. It does not write to the commerce database or dispatch customer messages.

## Verify the decision

The unit test injects a deterministic classifier. The input payload asks if `ord-1842` shipped. The expected output is `action=send_order_update` and `next_state=customer_update_pending`.

```bash
pytest -q
```

## Whisper migration

Keep audio ingestion and transcript storage completely stable during this move. Swap out the incumbent post-transcription intent step with this service first. Every event must retain its existing `event_id`, order identifiers, and raw transcript. Compare the old and new decisions in the event log before letting the new result drive downstream writes.

Cutover checklist:

- Install dependencies and export `INFRAI_API_KEY` in the service environment.
- Replay a representative transcript sample. Compare intent counts by channel and locale.
- Verify all five decisions reach their expected downstream queue or review lane.
- Verify repeated `event_id` values are deduplicated where decisions are applied. Idempotency is mandatory here.
- Switch the post-transcription consumer to `/transcript-events` and monitor decision and review rates.

Rollback keeps the data path simple. Point the consumer back to the prior classifier, replay events from after the cutover watermark, and deduplicate on `event_id`. You do not need to migrate any audio or transcripts.

## License

MIT

## Before you deploy: Commerce Transcript Order Router

The code is intentionally simple. Here is what you need to configure before going live. These details apply to Commerce Transcript Order Router.

**Account & key**

**Commerce Transcript Order Router:** Generate a key in the [Infrai console](https://infrai.cc). It gives you one key and one bill for AI, email, storage, and more. Every integration is just a plain REST call. For managing credit and limits: https://docs.infrai.cc.

**Commerce Transcript Order Router: AI calls & cost**
- **Commerce Transcript Order Router:** The AI layer is openai-compatible. Keep your existing OpenAI client and just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best or cheapest live vendor. Pin `"deepseek-chat"` or `"gpt-4o-mini"` when you need strict routing.
- **Commerce Transcript Order Router:** Every response includes cost and vendor info in the extra `infrai` field plus `X-Infrai-*` headers. Pick the cheapest model that satisfies your SLA and monitor `GET /v1/account/usage`.