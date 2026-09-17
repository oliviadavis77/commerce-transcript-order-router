from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class OrderIntent(StrEnum):
    CHECKOUT_CONFIRMED = "checkout_confirmed"
    READY_TO_FULFILL = "ready_to_fulfill"
    RECEIPT_REQUESTED = "receipt_requested"
    STATUS_REQUESTED = "status_requested"
    NEEDS_REVIEW = "needs_review"


class TranscriptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    order_id: str = Field(min_length=1)
    customer_id: str = Field(min_length=1)
    transcript: str = Field(min_length=1)


class IntentRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    intent: OrderIntent
    evidence: str = Field(min_length=1, max_length=240)


class OrderAction(BaseModel):
    event_id: str
    order_id: str
    customer_id: str
    action: str
    next_state: str
    evidence: str


def decide_order_action(request: TranscriptRequest, record: IntentRecord) -> OrderAction:
    transitions = {
        OrderIntent.CHECKOUT_CONFIRMED: ("record_checkout", "checkout_confirmed"),
        OrderIntent.READY_TO_FULFILL: ("release_fulfillment", "fulfillment_queued"),
        OrderIntent.RECEIPT_REQUESTED: ("send_receipt", "receipt_pending"),
        OrderIntent.STATUS_REQUESTED: ("send_order_update", "customer_update_pending"),
        OrderIntent.NEEDS_REVIEW: ("queue_manual_review", "review_pending"),
    }
    action, next_state = transitions[record.intent]
    return OrderAction(
        event_id=request.event_id,
        order_id=request.order_id,
        customer_id=request.customer_id,
        action=action,
        next_state=next_state,
        evidence=record.evidence,
    )
