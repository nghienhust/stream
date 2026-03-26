
import gi
import time
import psutil

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

LAPTOP_IP = "192.168.88.155"
PORT = 5000

pipeline_str = f"""
v4l2src device=/dev/video0 io-mode=2 !
video/x-h264,width=1280,height=720,framerate=30/1 !
h264parse config-interval=1 !
identity name=tagger !
rtph264pay pt=96 !
udpsink host={LAPTOP_IP} port={PORT} sync=false
"""

pipeline = Gst.parse_launch(pipeline_str)
identity = pipeline.get_by_name("tagger")

# ===== MONITOR =====
frame_count = 0
byte_count = 0
start_time = time.time()

def probe_callback(pad, info):
    global frame_count, byte_count

    buf = info.get_buffer()
    if not buf:
        return Gst.PadProbeReturn.OK

    # ===== TIMESTAMP CHUẨN =====
    now_ns = time.time_ns()
    buf.pts = now_ns   # override PTS = capture time

    frame_count += 1
    byte_count += buf.get_size()

    return Gst.PadProbeReturn.OK

pad = identity.get_static_pad("src")
pad.add_probe(Gst.PadProbeType.BUFFER, probe_callback)

def print_stats():
    global frame_count, byte_count, start_time

    now = time.time()
    elapsed = now - start_time

    fps = frame_count / elapsed
    bitrate = (byte_count * 8) / elapsed / 1e6
    cpu = psutil.cpu_percent()

    print(f"[PI] FPS: {fps:.2f} | Bitrate: {bitrate:.2f} Mbps | CPU: {cpu:.1f}%")

    frame_count = 0
    byte_count = 0
    start_time = now

    return True

GLib.timeout_add_seconds(1, print_stats)

pipeline.set_state(Gst.State.PLAYING)

GLib.MainLoop().run()
