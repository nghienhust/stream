mport gi
import time

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

Gst.init(None)

PORT = 5000

pipeline_str = f"""
udpsrc port={PORT} caps="application/x-rtp,media=video,encoding-name=H264,payload=96" !
rtpjitterbuffer latency=30 !
rtph264depay !
identity name=net_monitor !
avdec_h264 !
autovideosink sync=false
"""

pipeline = Gst.parse_launch(pipeline_str)
identity = pipeline.get_by_name("net_monitor")

# ===== MONITOR =====
frame_count = 0
byte_count = 0
start_time = time.time()

def probe_callback(pad, info):
    global frame_count, byte_count

    buf = info.get_buffer()
    if not buf:
        return Gst.PadProbeReturn.OK

    frame_count += 1
    byte_count += buf.get_size()

    # ===== DELAY CHUẨN =====
    pts = buf.pts   # timestamp từ Pi
    now_ns = time.time_ns()

    if pts != Gst.CLOCK_TIME_NONE:
        delay_ms = (now_ns - pts) / 1e6
        print(f"Delay: {delay_ms:.2f} ms")

    return Gst.PadProbeReturn.OK

pad = identity.get_static_pad("sink")
pad.add_probe(Gst.PadProbeType.BUFFER, probe_callback)

def print_stats():
    global frame_count, byte_count, start_time

    now = time.time()
    elapsed = now - start_time

    fps = frame_count / elapsed
    bitrate = (byte_count * 8) / elapsed / 1e6

    print(f"[LAPTOP] FPS: {fps:.2f} | Bitrate: {bitrate:.2f} Mbps")

    frame_count = 0
    byte_count = 0
    start_time = now

    return True

GLib.timeout_add_seconds(1, print_stats)

pipeline.set_state(Gst.State.PLAYING)

GLib.MainLoop().run()
