import os
import tempfile
import unittest

from PIL import Image

from pipeline import media_processor as mp


def _create_temp_image(path: str, size=(800, 600), color=(255, 0, 0)) -> None:
    im = Image.new("RGB", size, color)
    im.save(path, format="JPEG")


class MediaProcessorTests(unittest.TestCase):
    def test_convert_to_webp_and_make_cover(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            img_path = os.path.join(tmp, "sample.jpg")
            _create_temp_image(img_path, size=(2000, 1000))

            webp_path = mp.convert_to_webp(img_path, tmp)
            self.assertTrue(os.path.exists(webp_path))
            self.assertTrue(webp_path.endswith(".webp"))

            cover_path = mp.make_cover(img_path, os.path.join(tmp, "cover.webp"), max_size=1600)
            with Image.open(cover_path) as im:
                self.assertLessEqual(max(im.size), 1600)

    def test_process_images_to_webp_batch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            img1 = os.path.join(tmp, "img1.jpg")
            img2 = os.path.join(tmp, "img2.jpg")
            _create_temp_image(img1, size=(500, 400))
            _create_temp_image(img2, size=(600, 500))

            result = mp.process_images_to_webp([img1, img2], tmp)
            self.assertEqual(len(result["webp"]), 2)
            self.assertTrue(result["cover"].endswith("cover.webp"))


if __name__ == "__main__":
    unittest.main()
