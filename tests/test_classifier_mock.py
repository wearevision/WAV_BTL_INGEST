import json
import unittest

from pipeline.classifier_gemini import classify_event_visual, VisualClassification


class _DummyResult:
    def __init__(self, text: str):
        self.text = text


class _DummyModel:
    def __init__(self):
        self.calls = []

    def generate_content(self, parts, request_options=None):
        self.calls.append({"parts": parts, "request_options": request_options})
        payload = {
            "brand": "TestBrand",
            "title_base": "Test Title",
            "year": 2024,
            "category": "activaciones-de-marca",
            "visual_keywords": ["stand", "led"],
            "logo_detected": True,
            "dominant_colors": ["azul", "negro"],
            "main_elements": ["escenario", "pantalla"],
            "confidence_scores": {"brand": 0.9, "category": 0.8, "year": 0.7},
            "needs_review": False,
        }
        return _DummyResult(json.dumps(payload))


class ClassifierMockTests(unittest.TestCase):
    def test_classify_event_visual_uses_timeout_and_parses_payload(self) -> None:
        dummy_model = _DummyModel()
        result: VisualClassification = classify_event_visual([b"binary"], client=dummy_model, timeout=5.0)

        self.assertEqual(result.brand, "TestBrand")
        self.assertEqual(dummy_model.calls[0]["request_options"]["timeout"], 5.0)
        self.assertEqual(len(dummy_model.calls[0]["parts"]), 1)


if __name__ == "__main__":
    unittest.main()
