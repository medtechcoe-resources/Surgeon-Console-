import sys
import os
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QImage, QColor

# Ensure QApp exists
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

from shared_networking.config import VIDEO_PORT
import importlib
services_mod = importlib.import_module("Robot-Console.services.video_broadcaster")
VideoBroadcastService = services_mod.VideoBroadcastService
from screens.video_receiver import VideoReceiver


class TestVideoTransport(unittest.TestCase):
    def test_broadcast_and_receive(self):
        # 1. Start broadcaster
        broadcaster = VideoBroadcastService()
        broadcaster.start_server()
        self.assertTrue(broadcaster.is_running)

        # 2. Start receiver
        receiver = VideoReceiver(host="127.0.0.1", port=VIDEO_PORT)
        received_images = []
        receiver.frame_received.connect(lambda img: received_images.append(img))
        receiver.start()

        # Allow time to connect
        time.sleep(1.0)
        self.assertTrue(broadcaster.client_count >= 1)

        # 3. Create a test QImage and broadcast it
        img = QImage(320, 240, QImage.Format.Format_RGB888)
        img.fill(QColor(255, 0, 0))
        broadcaster.broadcast_qimage(img)

        # Allow time for encode, transfer, decode
        time.sleep(1.0)
        app.processEvents()

        # 4. Check that frame was received
        self.assertTrue(len(received_images) >= 1)
        first_frame = received_images[0]
        self.assertFalse(first_frame.isNull())
        self.assertEqual(first_frame.width(), 320)
        self.assertEqual(first_frame.height(), 240)

        # 5. Clean shutdown
        receiver.stop()
        broadcaster.stop_server()


if __name__ == "__main__":
    unittest.main()
