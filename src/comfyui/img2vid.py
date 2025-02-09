import random
from src.comfyui.api_client import *
from pydantic import BaseModel
from fastapi import FastAPI, UploadFile, File, Form, responses

API_URL = "127.0.0.1:8181"

with open("../../prompt/img2vid.json", "r") as f:
    prompt = json.load(f)

class Img2vidParams(BaseModel):
    file: UploadFile = File(...) #  图片文件
    width: int = 512
    height: int = 512
    video_frames: int = 25 # 视频帧数
    motion_bucket_id: int = 100 # 视频动作量
    fps: int = 8 # 视频流畅度
    seed: int = None
    steps: int = 20
    cfg: float = 2.0
    save_fps: int = 8 # 视频帧率

app = FastAPI()
@app.post("/img2vid")
async def img2vid(params: Img2vidParams = Form(...)):
    image_file = io.BytesIO()
    image_file.name = params.file.filename
    image_file.write(await params.file.read())
    image_file.seek(0)
    image_path = upload_image_file(API_URL, image_file)
    prompt["4"]["inputs"]["image"] = image_path

    prompt["3"]["inputs"]["width"] = params.width
    prompt["3"]["inputs"]["height"] = params.height
    prompt["3"]["inputs"]["video_frames"] = params.video_frames
    prompt["3"]["inputs"]["motion_bucket_id"] = params.motion_bucket_id
    prompt["3"]["inputs"]["fps"] = params.fps
    prompt["5"]["inputs"]["seed"] = random.randint(0, 1e16)
    if params.seed is not None:
        prompt["5"]["inputs"]["seed"] = params.seed
    prompt["5"]["inputs"]["steps"] = params.steps
    prompt["5"]["inputs"]["cfg"] = params.cfg
    prompt["7"]["inputs"]["save_fps"] = params.save_fps

    ws, client_id = open_websocket_connection(API_URL)
    print("client_id: ", client_id)
    response = queue_prompt(API_URL, prompt, client_id)
    prompt_id = response["prompt_id"]
    print("prompt_id: ", prompt_id)
    track_progress(ws, prompt, prompt_id)
    outputs = get_images_files(API_URL, prompt_id)
    return responses.Response(content=outputs[0].read())

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8182)
