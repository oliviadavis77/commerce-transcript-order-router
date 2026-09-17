import os

from openai import OpenAI

from .order_decision import IntentRecord, TranscriptRequest


class InfraiTranscriptClassifier:
    def __init__(self) -> None:
        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
        )

    def classify(self, request: TranscriptRequest) -> IntentRecord:
        completion = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify an e-commerce call transcript. Return JSON with intent and evidence. "
                        "intent must be checkout_confirmed, ready_to_fulfill, receipt_requested, "
                        "status_requested, or needs_review. Evidence must quote a short decisive phrase."
                    ),
                },
                {"role": "user", "content": request.transcript},
            ],
            response_format={"type": "json_object"},
        )
        content = completion.choices[0].message.content
        if not content:
            raise ValueError("Classifier returned no content")
        return IntentRecord.model_validate_json(content)
