from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import subprocess
import os
import uuid
import edge_tts

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

VOICE_MAP = {
    "my_male": "my-MM-ThihaNeural",
    "my_female": "my-MM-NilarNeural",
    "en_male": "en-US-ChristopherNeural",
    "en_female": "en-US-JennyNeural",
    "th_male": "th-TH-NiwatNeural",
    "th_female": "th-TH-PremwadeeNeural"
}

@app.get("/")
def read_root():
    return {"status": "Recap MM Audio Server Running Successfully"}

@app.post("/api/generate-audio")
async def generate_audio(text: str = Form(...), voice_key: str = Form("my_male"), speed: float = Form(1.0)):
    voice_name = VOICE_MAP.get(voice_key, "my-MM-ThihaNeural")
    audio_file = f"audio_{uuid.uuid4().hex}.mp3"
    rate_percent = int((speed - 1.0) * 100)
    rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
    communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
    await communicate.save(audio_file)
    return FileResponse(audio_file, media_type="audio/mpeg", filename="output.mp3")

@app.post("/api/merge-video")
async def merge_video(video: UploadFile = File(...), text: str = Form(...), voice_key: str = Form("my_male"), speed: float = Form(1.0)):
    req_id = uuid.uuid4().hex
    input_video = f"input_{req_id}.mp4"
    audio_file = f"audio_{req_id}.mp3"
    output_video = f"final_{req_id}.mp4"
    
    with open(input_video, "wb") as f:
        f.write(await video.read())
        
    voice_name = VOICE_MAP.get(voice_key, "my-MM-ThihaNeural")
    rate_percent = int((speed - 1.0) * 100)
    rate_str = f"+{rate_percent}%" if rate_percent >= 0 else f"{rate_percent}%"
    
    communicate = edge_tts.Communicate(text, voice_name, rate=rate_str)
    await communicate.save(audio_file)
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_video,
        "-i", audio_file,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    if os.path.exists(input_video): os.remove(input_video)
    if os.path.exists(audio_file): os.remove(audio_file)
    
    return FileResponse(output_video, media_type="video/mp4", filename=f"recap_{req_id}.mp4")
  
