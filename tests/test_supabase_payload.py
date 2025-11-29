import unittest

from pipeline.text_generator import WavEvent
from pipeline.supabase_payload import build_supabase_event_payload


def _mock_wav_event(needs_review: bool = False) -> WavEvent:
    event = WavEvent(
        brand="Marca",
        title="Titulo",
        slug="slug",
        summary="Resumen",
        description="Descripcion",
        highlights=["h1", "h2"],
        keywords=["k1", "k2"],
        hashtags=["#a", "#b"],
        instagram_closing="closing",
        alt_instagram="alt",
        linkedin_article="article",
        alt_title_1="alt1",
        alt_title_2="alt2",
        instagram_hook="hook",
        instagram_body="body",
        instagram_hashtags="#x #y",
        linkedin_post="post",
        category="activaciones-de-marca",
        needs_review=needs_review,
    )
    event.year = 2024
    return event


class SupabasePayloadTests(unittest.TestCase):
    def test_payload_contains_all_fields_and_defaults(self) -> None:
        wav_event = _mock_wav_event(needs_review=True)
        media = {"cover": "https://cdn/cover.webp", "logo": "https://cdn/logo.png", "gallery": ["g1", None, "g2"]}

        payload = build_supabase_event_payload(wav_event, media)

        expected_keys = {
            "id",
            "brand",
            "title",
            "slug",
            "category",
            "year",
            "summary",
            "description",
            "highlights",
            "keywords",
            "hashtags",
            "instagram_hook",
            "instagram_body",
            "instagram_closing",
            "instagram_hashtags",
            "alt_instagram",
            "linkedin_post",
            "linkedin_article",
            "alt_title_1",
            "alt_title_2",
            "needs_review",
            "image",
            "logo",
            "gallery",
        }

        self.assertEqual(set(payload.keys()), expected_keys)
        self.assertTrue(payload["needs_review"])
        self.assertEqual(payload["id"], None)
        self.assertEqual(payload["year"], 2024)
        self.assertEqual(payload["image"], media["cover"])
        self.assertEqual(payload["logo"], media["logo"])
        self.assertEqual(payload["gallery"], ["g1", "g2"])

    def test_override_id_and_empty_media(self) -> None:
        wav_event = _mock_wav_event()
        media = {}

        payload = build_supabase_event_payload(wav_event, media, override_id="abc123")

        self.assertEqual(payload["id"], "abc123")
        self.assertEqual(payload["image"], "")
        self.assertEqual(payload["logo"], "")
        self.assertEqual(payload["gallery"], [])


if __name__ == "__main__":
    unittest.main()
