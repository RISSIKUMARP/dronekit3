
import threading
import time
import sys
import cv2
import mss
import pygetwindow as gw
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

"""
Window Grabber Module

This module provides functionality to capture a specific window's content, display an outline around it, and stream the captured frames as an MJPEG video over HTTP.

Install Notes:

Required packages:
- opencv-python
- mss
- pygetwindow
- numpy
- PyQt5

Install with: pip install opencv-python mss pygetwindow numpy PyQt5
"""


class MJPEGHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for serving MJPEG video streams.
    
    Handles GET requests for the root path and /video, streaming frames as multipart data.
    """
    
    def do_GET(self):
        if self.path in ["/", "/video"]:
            self.send_response(200)
            self.send_header('Age', '0')
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                while True:
                    # Access the current frame through the server's frame_provider attribute
                    frame = self.server.frame_provider.frame.copy()
                    ret, jpg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    if not ret:
                        continue
                    self.wfile.write(b"--frame\r\n")
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', str(len(jpg)))
                    self.end_headers()
                    self.wfile.write(jpg.tobytes())
                    self.wfile.write(b"\r\n")
                    time.sleep(1/120)  # Control the frame rate (adjust as needed)
            except Exception:
                # Exceptions can occur if the client disconnects; simply exit the loop.
                pass
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        # Overriding to reduce log spam.
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """
    Threaded HTTP server for handling multiple MJPEG stream requests concurrently.
    """
    daemon_threads = True

class MJPEGServer:
    def __init__(self, host='0.0.0.0', port=8080):
        """
        Initializes the MJPEG server.

        Args:
            host (str): Address where the server listens.
            port (int): Port number for the server.
        """
        self.host = host
        self.port = port
        # Default frame: a 640x480 image in BGR format (as used by OpenCV)
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self._server = None
        self._thread = None

    def start(self):
        """
        Starts the MJPEG server on a separate thread.
        """
        if self._server is not None:
            return  # Server is already running.
        # Create a threaded HTTP server using our standalone MJPEGHandler.
        self._server = ThreadedHTTPServer((self.host, self.port), MJPEGHandler)
        # Pass a reference to this MJPEGServer instance on the server object.
        self._server.frame_provider = self
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        print(f"MJPEG Server started on http://{self.host}:{self.port}/video")
        time.sleep(1/10)

    def shutdown(self):
        """
        Shuts down the MJPEG server.
        """
        if self._server:
            self._server.shutdown()
            self._server.server_close()
            self._server = None
            self._thread = None
            print("MJPEG Server stopped.")


class OutlineWindow(QMainWindow):
    """
    A transparent window that displays a red outline around a specified region.
    
    Used to visually indicate the area being captured.
    """
    
    def __init__(self, x, y, width, height):
        super().__init__()
        self.xywh = (x, y, width, height)
        self.setGeometry(
            self.xywh[0] - 1, 
            self.xywh[1] - 1, 
            self.xywh[2] + 2, 
            self.xywh[3] + 2
            )
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(Qt.red, 2)  # Outline color and thickness
        painter.setPen(pen)
        painter.drawRect(self.rect())  # Draw the outline


class Threaded_Window_Grabber:
    """
    A threaded class for continuously capturing screenshots of a specified screen region.
    
    Uses mss for fast screen capture and runs in a separate thread.
    """
    
    def __init__(self, l, t, w, h, buffers=[0,0,0,0]):
        self.l = l
        self.t = t
        self.w = w
        self.h = h
        self.buffers = buffers
        self.frame = None
        self.run = True
        self.outline = None
        self.thread = threading.Thread(target=self.grabber, daemon=True)
        self.thread.start()
          
    def ltwh(self):
        """Return the left, top, width, height tuple."""
        return (self.l, self.t, self.w, self.h)

    def grabber(self):
        """
        Main loop for capturing screen frames.
        
        Continuously grabs the specified monitor region and converts to BGR format.
        """
        monitor = {"top": self.t,
                   "left": self.l,
                   "width": self.w, 
                   "height": self.h}
        
        with mss.mss() as sct: 
            while self.run:
                loop_start = time.time()
                
                self.frame = cv2.cvtColor(np.array(sct.grab(monitor)), cv2.COLOR_BGRA2BGR)

                fps = 1 / (time.time() - loop_start + 0.002)
                
                time.sleep(0.001)
                
                # cv2.putText(self.frame, f"FPS: {int(fps)}", (10, 10), 1, 1, (0,0,0), 2)
                # cv2.putText(self.frame, f"FPS: {int(fps)}", (10, 10), 1, 1, (255,255,255), 1)
                
                if not self.run:
                    print("Exit grabber.")

def get_window_by_title(title):
    """
    Find a window by its title (case-insensitive prefix match).
    
    Args:
        title (str): The title to search for.
    
    Returns:
        Window object or None if not found.
    """
    window  = gw.getAllTitles()
    for w in window:
        if w.lower().startswith(title.lower()):
            return gw.getWindowsWithTitle(w)[0]
    return None


def threaded_outliner(l, t, w, h):
    """
    Run the outline window in a separate thread.
    
    Args:
        l, t, w, h: Left, top, width, height of the outline.
    """
    global app
    app = QApplication(sys.argv)
    outline = OutlineWindow(l, t, w, h)
    outline.show()
    app.exec()


def launch_grabber(x=1270, y=10, mjpeg_server: tuple[str, int] =("0.0.0.0", 8080)):
    """
    Launch the window grabber, outline, and optionally the MJPEG server.
    
    Args:
        x, y: Top-left coordinates of the grab area.
        mjpeg_server: Tuple of (host, port) for the server, or None to disable.
    
    Returns:
        Tuple of (grabber, outline_thread, server).
    """
    WIN_BAR_HEIGHT = 45
    XNUDGE = 10
    YNUDGE = 4

    grabber = Threaded_Window_Grabber(x, y + WIN_BAR_HEIGHT + YNUDGE, 640, 480)

    time.sleep(1)

    o = threading.Thread(target=threaded_outliner, args=[*grabber.ltwh()], daemon=True)
    o.start()

    if mjpeg_server:
        server = MJPEGServer(host=mjpeg_server[0], port=mjpeg_server[1])
        server.start()
        server.frame[:] = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
    else:
        server = None

    return grabber, o, server



# Test
if __name__ == "__main__":
    """
    Test script to demonstrate window grabbing and MJPEG streaming.
    
    Captures a window titled "Mounts", displays outline, and streams to localhost:8080.
    """

    LEFT = 100           # Pixels from left edge
    WIN_BAR_HEIGHT = 100 # Pixels from top
    XNUDGE = 10
    YNUDGE = 4
    FRAME_WIDTH = 640
    FRAME_HEIGHT = 480
    grabber = Threaded_Window_Grabber(LEFT, WIN_BAR_HEIGHT + YNUDGE, 
                                      FRAME_WIDTH, FRAME_HEIGHT)
    time.sleep(1)

    def threaded_outliner(l, t, w, h):
        global app
        app = QApplication(sys.argv)
        outline = OutlineWindow(l, t, w, h)
        outline.show()
        app.exec()

    o = threading.Thread(target=threaded_outliner, args=[*grabber.ltwh()], daemon=True)
    o.start()

    target_window = get_window_by_title("MountainVillage")
    if target_window:
        print(f"Found window: {target_window.title}")
        target_window.moveTo(
            grabber.l - XNUDGE, 
            grabber.t - WIN_BAR_HEIGHT + YNUDGE
        )
    else:
        print("Window not found.")

    server = MJPEGServer(host="0.0.0.0", port=8080)
    server.start()
    server.frame[:] = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)

    while True:
        

        server.frame = grabber.frame

        cv2.imshow("", grabber.frame)    
        if cv2.waitKey(1) == 27:
            grabber.run = False
            break

        time.sleep(0.005) 
            
    cv2.destroyAllWindows()
    app.quit()
