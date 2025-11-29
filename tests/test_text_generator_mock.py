import unittest
from typing import Any, Dict

from pipeline.text_generator import generate_event_content, WavEvent


class _FakeCompletion:
    def __init__(self, payload: Dict[str, Any]):
        self.choices = [_FakeChoice(payload)]


class _FakeChoice:
    def __init__(self, payload: Dict[str, Any]):
        self.message = _FakeMessage(payload)


class _FakeMessage:
    def __init__(self, payload: Dict[str, Any]):
        # Simula que el modelo devolvió JSON en content
        self.content = __import__("json").dumps(payload)
        self.parsed = None


class _FakeOpenAIClient:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload
        self.chat = self.Chat(self)

    class Chat:
        def __init__(self, outer):
            self._outer = outer
            self.completions = self.Completions(outer)

        class Completions:
            def __init__(self, outer):
                self._outer = outer

            def create(self, **_: Any) -> Any:  # pragma: no cover - interface compat
                return _FakeCompletion(self._outer._payload)


class _FakeGeminiModel:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload

    def generate_content(self, *_: Any, **__: Any):
        return _FakeResult(__import__("json").dumps(self._payload))


class _FakeResult:
    def __init__(self, text: str):
        self.text = text


def _base_event_payload() -> Dict[str, Any]:
    return {
        "brand": "Marca",
        "title": "Evento de prueba muy largo" * 3,
        "slug": "2024-marca-evento-prueba",
        "summary": "S" * 200,
        "description": "D" * 900,
        "highlights": ["H" * 120, "Item", "Otro"],
        "keywords": ["k1", "k2", "k3", "k4", "k5", "k6", "k7", "k8", "k9", "k10"],
        "hashtags": ["#uno", "#dos", "#tres", "#cuatro", "#cinco"],
        "instagram_closing": "Cierre" * 50,
        "alt_instagram": "Alt" * 400,
        "linkedin_article": "Articulo" * 400,
        "alt_title_1": "Alternativo 1" * 10,
        "alt_title_2": "Alternativo 2" * 10,
        "instagram_hook": "Hook" * 40,
        "instagram_body": "Body" * 300,
        "instagram_hashtags": "#tag1 #tag2 #tag3 #tag4 #tag5 #tag6 #tag7 #tag8",
        "linkedin_post": "LinkedIn" * 300,
        "category": "activaciones-de-marca",
    }


class TextGeneratorMockTests(unittest.TestCase):
    def test_generate_event_content_openai_enforces_lengths_and_flags_review(self) -> None:
        payload = _base_event_payload()
        result: WavEvent = generate_event_content(
            payload,
            provider="openai",
            client=_FakeOpenAIClient(payload),
            temperature=0.1,
        )

        self.assertTrue(result.needs_review)
        self.assertLessEqual(len(result.title), 60)
        self.assertLessEqual(len(result.summary), 160)
        self.assertLessEqual(len(result.instagram_body), 1000)
        self.assertEqual(len(result.highlights), 3)
        self.assertTrue(all(len(h) <= 100 for h in result.highlights))

    def test_generate_event_content_gemini_enforces_lengths_and_flags_review(self) -> None:
        payload = _base_event_payload()
        result: WavEvent = generate_event_content(
            payload,
            provider="gemini",
            client=_FakeGeminiModel(payload),
            temperature=0.1,
        )

        self.assertTrue(result.needs_review)
        self.assertLessEqual(len(result.description), 800)
        self.assertLessEqual(len(result.linkedin_post), 1300)


if __name__ == "__main__":
    unittest.main()
