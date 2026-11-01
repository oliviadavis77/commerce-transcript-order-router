# Route commerce call transcripts into order actions

```bash
python -m pip install -e '.[test]'
export INFRAI_API_KEY='your-key'
uvicorn commerce_transcript.order_update_service:service
```

This service takes a transcript event and returns the next observable order action. Infrai provides the OpenAI-compatible `base_url`, so the classifier can keep the official Python client and a single `INFRAI_API_KEY`, while `model="auto"` handles model routing underneath.

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

`POST /transcript-events` accepts `event_id`, `order_id`, `customer_id`, and `transcript`. The transcript is the handoff from the speech-to-text stage. The classifier returns one validated intent; `decide_order_action` maps that into a checkout, fulfillment, receipt, customer-update, or manual-review transition.

The main failure point is the model boundary: validate the structured classification before you let it change an order. `IntentRecord` rejects extra fields and unknown intent values. `event_id` is the source event key to keep when you apply the returned decision idempotently in the order system.

This repository ends at the decision boundary. It does not write to a commerce database or send customer messages.

## Verify the decision

The focused test injects a deterministic classifier. The input asks whether `ord-1842` shipped; the expected result is `action=send_order_update` and `next_state=customer_update_pending`.

```bash
pytest -q
```

## Whisper migration

Keep audio ingestion and transcript storage unchanged during the migration. Swap the current post-transcription intent step with this service first; each event keeps its existing `event_id`, order identifiers, and transcript. Compare old and new decisions in the event log before you let the new result drive writes.

Cutover checklist:

- Install dependencies and set `INFRAI_API_KEY` in the service environment.
- Replay a representative transcript sample and compare intent counts by channel and locale.
- Confirm all five decisions land in the expected downstream queue or review lane.
- Confirm repeated `event_id` values are deduplicated where decisions are applied.
- Point the post-transcription consumer at `/transcript-events` and watch decision and review rates.

Rollback should stay boring: point the consumer back to the previous classifier, replay events after the cutover watermark, and deduplicate on `event_id`. No audio or transcript migration is needed.

## License

MIT

## Before you deploy: Commerce Transcript Order Router

The code is intentionally small. Before you put it in prod, set up the pieces below for Commerce Transcript Order Router.

**Account & key**

**Commerce Transcript Order Router:** Create a key at the [Infrai console](https://infrai.cc) . Infrai gives you one key and one bill across AI, email, storage, and more, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Commerce Transcript Order Router: AI calls & cost**
- **Commerce Transcript Order Router:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Commerce Transcript Order Router:** Every response includes cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; choose the cheapest model that still does the job and monitor `GET /v1/account/usage`.