import os
import tempfile
import unittest

from PIL import Image

from pipeline.classifier_gemini import VisualClassification
from pipeline.text_generator import WavEvent
from pipeline.orchestrator import ingest_event_directory
from pipeline.supabase_client import SupabaseClient


def _create_temp_image(path: str, size=(640, 480), color=(0, 128, 255)) -> None:
    im = Image.new("RGB", size, color)
    im.save(path, format="JPEG")


def _fake_classifier(images, **kwargs):  # type: ignore[override]
    return VisualClassification(
        brand="TestBrand",
        title_base="Titulo Base",
        year=2024,
        category="activaciones-de-marca",
        visual_keywords=["led", "escenario"],
        logo_detected=False,
        dominant_colors=["azul"],
        main_elements=["pantalla"],
        confidence_scores={"brand": 0.9, "category": 0.8, "year": 0.7},
        needs_review=False,
    )


def _fake_text_gen(event_data, **kwargs):  # type: ignore[override]
    return WavEvent(
        brand=event_data.get("brand", ""),
        title="Titulo Final",
        slug="2024-testbrand-evento",
        summary="Resumen",
        description="Descripcion",
        highlights=["h1", "h2"],
        keywords=["k1"],
        hashtags=["#h"],
        instagram_closing="closing",
        alt_instagram="alt",
        linkedin_article="article",
        alt_title_1="alt1",
        alt_title_2="alt2",
        instagram_hook="hook",
        instagram_body="body",
        instagram_hashtags="#tag",
        linkedin_post="post",
        category=event_data.get("category", "activaciones-de-marca"),
        needs_review=True,
    )


class OrchestratorTests(unittest.TestCase):
    def test_ingest_event_directory_builds_payload_and_media(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            img_dir = os.path.join(tmp, "event")
            os.makedirs(img_dir, exist_ok=True)
            img_path = os.path.join(img_dir, "img1.jpg")
            _create_temp_image(img_path)

            output_dir = os.path.join(tmp, "out")
            result = ingest_event_directory(
                img_dir,
                output_dir,
                base_event_data={"slug": "pre-slug"},
                classifier_fn=_fake_classifier,
                text_fn=_fake_text_gen,
            )

            self.assertTrue(result.payload["needs_review"])
            self.assertEqual(result.payload["brand"], "TestBrand")
            self.assertTrue(result.media["cover"].endswith("cover.webp"))
            self.assertTrue(len(result.media["gallery"]) >= 1)
            self.assertIsNone(result.payload["id"])

    def test_ingest_with_supabase_upload(self) -> None:
        class _FakeSupabase(SupabaseClient):  # type: ignore[misc]
            def __init__(self):
                self.upload_called = False
                self.post_called = False

            def upload_media_paths(self, media, prefix, bucket=None):  # type: ignore[override]
                self.upload_called = True
                return {"cover": "https://cdn/cover.webp", "logo": "", "gallery": ["https://cdn/g1.webp"]}

            def post_event(self, payload, table="events"):  # type: ignore[override]
                self.post_called = True
                return {"id": "123"}

        with tempfile.TemporaryDirectory() as tmp:
            img_dir = os.path.join(tmp, "event2")
            os.makedirs(img_dir, exist_ok=True)
            img_path = os.path.join(img_dir, "img1.jpg")
            _create_temp_image(img_path)

            output_dir = os.path.join(tmp, "out2")
            fake_supabase = _FakeSupabase()
            result = ingest_event_directory(
                img_dir,
                output_dir,
                classifier_fn=_fake_classifier,
                text_fn=_fake_text_gen,
                upload_to_supabase=True,
                supabase_client=fake_supabase,
            )

            self.assertEqual(result.media["cover"], "https://cdn/cover.webp")
            self.assertEqual(result.payload["id"], None)
            self.assertEqual(result.supabase_response, {"id": "123"})


if __name__ == "__main__":
    unittest.main()
