from fastapi.testclient import TestClient

from commerce_transcript.order_decision import IntentRecord, OrderIntent, TranscriptRequest
from commerce_transcript.order_update_service import classifier_dependency, service


class StatusClassifier:
    def classify(self, request: TranscriptRequest) -> IntentRecord:
        assert "shipped" in request.transcript
        return IntentRecord(
            intent=OrderIntent.STATUS_REQUESTED,
            evidence="whether order 1842 has shipped",
        )


def test_status_question_creates_customer_update() -> None:
    service.dependency_overrides[classifier_dependency] = StatusClassifier
    try:
        response = TestClient(service).post(
            "/transcript-events",
            json={
                "event_id": "call-2026-0042",
                "order_id": "ord-1842",
                "customer_id": "cus-731",
                "transcript": "Can you tell me whether order 1842 has shipped yet?",
            },
        )
    finally:
        service.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "event_id": "call-2026-0042",
        "order_id": "ord-1842",
        "customer_id": "cus-731",
        "action": "send_order_update",
        "next_state": "customer_update_pending",
        "evidence": "whether order 1842 has shipped",
    }
