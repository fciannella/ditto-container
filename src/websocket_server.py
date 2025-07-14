import asyncio
import numpy as np
import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from stream_pipeline_online import StreamSDK
from core.atomic_components.writer import VideoWriterByImageIO


class StreamingWriter(VideoWriterByImageIO):
    """Video writer that also pushes frames to an asyncio queue."""

    def __init__(self, video_path: str, frame_queue: asyncio.Queue, **kwargs):
        super().__init__(video_path, **kwargs)
        self.frame_queue = frame_queue

    def __call__(self, img, fmt="bgr"):
        super().__call__(img, fmt=fmt)
        if fmt == "bgr":
            frame = img
        else:
            frame = img[..., ::-1]
        try:
            self.frame_queue.put_nowait(frame)
        except asyncio.QueueFull:
            pass


class StreamSession:
    """Handle streaming for a single client."""

    def __init__(self, cfg_pkl: str, data_root: str, source_path: str, chunk_size=(3, 5, 2)):
        self.frame_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.sdk = StreamSDK(cfg_pkl, data_root, online_mode=True)
        self.sdk.setup(source_path, "/tmp/out.mp4")
        # Replace writer with streaming writer
        self.sdk.writer = StreamingWriter(self.sdk.tmp_output_path, self.frame_queue)
        self.chunk_bytes = int(sum(chunk_size) * 0.04 * 16000) * 2  # 16-bit PCM
        self.chunk_size = chunk_size
        self.buffer = bytearray()

    async def push_audio(self, data: bytes):
        self.buffer.extend(data)
        while len(self.buffer) >= self.chunk_bytes:
            chunk = self.buffer[:self.chunk_bytes]
            self.buffer = self.buffer[self.chunk_bytes:]
            # Convert int16 PCM to float32
            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            self.sdk.run_chunk(audio_np, self.chunk_size)

    async def finish(self):
        self.sdk.close()
        await self.frame_queue.put(None)


app = FastAPI()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        init = await websocket.receive_json()
        session = StreamSession(
            init["cfg_pkl"],
            init["data_root"],
            init["source_path"],
        )
        sender = asyncio.create_task(send_frames(websocket, session.frame_queue))
        while True:
            data = await websocket.receive_bytes()
            if data == b"__end__":
                break
            await session.push_audio(data)
    except WebSocketDisconnect:
        pass
    finally:
        await session.finish()
        await sender


async def send_frames(ws: WebSocket, queue: asyncio.Queue):
    while True:
        frame = await queue.get()
        if frame is None:
            break
        _, buf = cv2.imencode(".jpg", frame)
        await ws.send_bytes(buf.tobytes())


html = """
<!DOCTYPE html>
<html>
<body>
<h1>Ditto WebSocket Stream</h1>
<script>
let ws = new WebSocket("ws://" + location.host + "/ws");
ws.onopen = () => {
  ws.send(JSON.stringify({cfg_pkl: '/app/checkpoints/ditto_cfg/v0.4_hubert_cfg_trt_online.pkl', data_root: '/app/checkpoints/ditto_trt_Ampere_Plus', source_path: '/app/data/source_image.png'}));
};
ws.onmessage = (ev) => {
  let img = document.getElementById('img');
  img.src = URL.createObjectURL(new Blob([ev.data]));
};
function send(data){ ws.send(data); }
</script>
<img id="img" />
</body>
</html>
"""


@app.get("/")
async def index():
    return HTMLResponse(html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
