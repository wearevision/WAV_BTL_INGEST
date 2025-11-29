import json
import os
import tempfile
import unittest

from pipeline.supabase_client import SupabaseClient, SupabaseConfig


class _FakeResponse:
    def __init__(self, status_code: int = 200, json_payload=None, text: str = ""):
        self.status_code = status_code
        self._json_payload = json_payload
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"HTTP {self.status_code}")

    def json(self):
        if self._json_payload is None:
            raise ValueError("no json")
        return self._json_payload


class _FakeSession:
    def __init__(self, responses):
        self.responses = responses
        self.requests = []

    def put(self, url, data=None, headers=None):
        self.requests.append({"method": "PUT", "url": url, "headers": headers})
        return self.responses.pop(0)

    def post(self, url, headers=None, data=None, json=None):
        self.requests.append({"method": "POST", "url": url, "headers": headers, "data": data, "json": json})
        return self.responses.pop(0)

    def delete(self, url, headers=None, params=None):
        self.requests.append({"method": "DELETE", "url": url, "headers": headers, "params": params})
        return self.responses.pop(0)


class SupabaseClientTests(unittest.TestCase):
    def test_upload_file_and_media_paths(self):
        cfg = SupabaseConfig(url="https://example.supabase.co", key="key", bucket="events")
        responses = [_FakeResponse(status_code=200), _FakeResponse(), _FakeResponse()]
        session = _FakeSession(responses)
        client = SupabaseClient(cfg, session=session)

        with tempfile.TemporaryDirectory() as tmp:
            cover = os.path.join(tmp, "cover.webp")
            gallery = os.path.join(tmp, "img1.webp")
            with open(cover, "wb") as f:
                f.write(b"data")
            with open(gallery, "wb") as f:
                f.write(b"data")

            media = {"cover": cover, "logo": "", "gallery": [gallery]}
            uploaded = client.upload_media_paths(media, prefix="event/slug")

        self.assertTrue(uploaded["cover"].startswith(cfg.url))
        self.assertEqual(len(uploaded["gallery"]), 1)
        # Two PUT requests (cover + gallery)
        self.assertEqual(len(session.requests), 3)
        # First request is ensure_bucket (POST)
        self.assertEqual(session.requests[0]["method"], "POST")
        self.assertIn("Bearer key", session.requests[0]["headers"]["Authorization"])

    def test_post_event(self):
        cfg = SupabaseConfig(url="https://example.supabase.co", key="key", bucket="events")
        responses = [_FakeResponse(json_payload={"id": "abc"})]
        session = _FakeSession(responses)
        client = SupabaseClient(cfg, session=session)

        payload = {"id": None, "brand": "x"}
        resp = client.post_event(payload, table="events")

        self.assertEqual(resp["id"], "abc")
        self.assertEqual(session.requests[0]["method"], "POST")
        self.assertIn("Bearer key", session.requests[0]["headers"]["Authorization"])
        self.assertEqual(json.loads(session.requests[0]["data"]), payload)

    def test_delete_all(self):
        cfg = SupabaseConfig(url="https://example.supabase.co", key="key", bucket="events")
        responses = [_FakeResponse(status_code=204)]
        session = _FakeSession(responses)
        client = SupabaseClient(cfg, session=session)

        status = client.delete_all(table="kv_store_c4bb2206_rows")
        self.assertEqual(status, 204)
        self.assertEqual(session.requests[0]["method"], "DELETE")


if __name__ == "__main__":
    unittest.main()
