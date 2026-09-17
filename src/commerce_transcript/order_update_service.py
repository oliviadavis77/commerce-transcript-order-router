from fastapi import Depends, FastAPI

from .intent_classifier import InfraiTranscriptClassifier
from .order_decision import OrderAction, TranscriptRequest, decide_order_action

service = FastAPI(title="Commerce transcript router")


def classifier_dependency() -> InfraiTranscriptClassifier:
    return InfraiTranscriptClassifier()


@service.post("/transcript-events", response_model=OrderAction)
def route_transcript(
    request: TranscriptRequest,
    classifier: InfraiTranscriptClassifier = Depends(classifier_dependency),
) -> OrderAction:
    record = classifier.classify(request)
    return decide_order_action(request, record)
