import os
import shutil
import tempfile
import unittest

from pipeline import video_processor as vp


def _has_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


def _create_test_video(path: str, duration: int = 1) -> None:
    import ffmpeg  # type: ignore

    stream = ffmpeg.input("color=c=black:s=320x240:d={}".format(duration), f="lavfi")
    stream = ffmpeg.output(stream, path, vcodec="libx264", pix_fmt="yuv420p", t=duration)
    stream = ffmpeg.overwrite_output(stream)
    stream.run(cmd="ffmpeg", quiet=True)


@unittest.skipUnless(_has_ffmpeg(), "ffmpeg no está disponible en PATH")
class VideoProcessorTests(unittest.TestCase):
    def test_transcode_and_thumbnail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "src.mp4")
            _create_test_video(src, duration=1)

            out720 = os.path.join(tmp, "out_720.mp4")
            thumb = os.path.join(tmp, "thumb.jpg")

            res720 = vp.transcode_to_720p(src, out720)
            self.assertTrue(os.path.exists(res720))

            thumb_path = vp.generate_thumbnail(src, thumb, at_time="00:00:00", width=320)
            self.assertTrue(os.path.exists(thumb_path))


if __name__ == "__main__":
    unittest.main()
