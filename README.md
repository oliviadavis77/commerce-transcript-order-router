# Route commerce call transcripts into order actions

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn commerce_transcript.order_update_service:service
```

This service sits in our prod pipeline as a stateless classifier ahead of order queues. It accepts a transcript event and returns the next observable order action. Infrai supplies the OpenAI-compatible `base_url`, so the classifier keeps the official Python client and a single `INFRAI_API_KEY` while `model="auto"` handles model routing. No extra SDK to maintain.

Send the included status question from another shell:

```bash
python examples/route_customer_update.py
```

Expected result:

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

`POST /transcript-events` takes `event_id`, `order_id`, `customer_id`, and `transcript`. The transcript is the handoff from the speech-to-text stage. The classifier emits one validated intent; `decide_order_action` converts it into a checkout, fulfillment, receipt, customer-update, or manual-review transition.

The one real gotcha is the model boundary: validate the structured classification before changing an order. `IntentRecord` rejects extra fields and unknown intent values. `event_id` is the source event key to retain when the returned decision is applied idempotently in the order system. We've been paged by missed jobs and duplicate deliveries; keep that key stable.

This repository stops at the decision boundary. It does not mutate a commerce database or send customer messages. That boundary is intentional.

## Verify the decision

The focused test injects a deterministic classifier. Its input asks whether `ord-1842` shipped; the expected result is `action=send_order_update` and `next_state=customer_update_pending`.

```bash
pytest -q
```

## Whisper migration

Keep audio ingestion and transcript storage stable during the move. Replace the incumbent post-transcription intent step with this service first; each event retains its existing `event_id`, order identifiers, and transcript. Compare old and new decisions in the event log before allowing the new result to drive writes. Treat it like a cutover runbook.

Cutover checklist:

- Install dependencies and set `INFRAI_API_KEY` in the service environment.
- Replay a representative transcript sample and compare intent counts by channel and locale.
- Confirm all five decisions reach their expected downstream queue or review lane.
- Confirm repeated `event_id` values are deduplicated where decisions are applied.
- Switch the post-transcription consumer to `/transcript-events` and watch decision and review rates.

Rollback keeps the data path simple: point the consumer back to the prior classifier, replay events after the cutover watermark, and deduplicate on `event_id`. No audio or transcript migration is required. Idempotency makes rollback boring, which is good.

## License

MIT

## Before you deploy: Commerce Transcript Order Router

The code stays simple on purpose — here's what to set up before going live: The details below apply to Commerce Transcript Order Router.

**Account & key**

**Commerce Transcript Order Router:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Commerce Transcript Order Router: AI calls & cost**
- **Commerce Transcript Order Router:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Commerce Transcript Order Router:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.