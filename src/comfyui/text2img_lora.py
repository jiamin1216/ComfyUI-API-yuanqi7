import random
from src.comfyui.api_client import *
from typing import Literal
from pydantic import BaseModel
from fastapi import FastAPI, Form, responses

API_URL = "127.0.0.1:8181"

with open("../../prompt/text2img_lora.json", "r") as f:
    prompt = json.load(f)

class Text2imgParams(BaseModel):
    prompt: str = "a cute boy"
    style: Literal["qban", "guofeng", "Clay", "Cyberpunk"] = "Clay"
    seed: int = None
    num: int = 1

app = FastAPI()
@app.post("/text2img_lora")
async def text2img(params: Text2imgParams = Form(...)):
    prompt["2"]["inputs"]["lora_name"] = params.style + ".safetensors"
    prompt["3"]["inputs"]["text"] = params.style + ", " + params.prompt
    prompt["5"]["inputs"]["seed"] = random.randint(0, 1e16)
    if params.seed is not None:
        prompt["5"]["inputs"]["seed"] = params.seed
    prompt["6"]["inputs"]["batch_size"] = params.num

    ws, client_id = open_websocket_connection(API_URL)
    print("client_id: ", client_id)
    response = queue_prompt(API_URL, prompt, client_id)
    prompt_id = response["prompt_id"]
    print("prompt_id: ", prompt_id)
    track_progress(ws, prompt, prompt_id)
    outputs = get_images_files(API_URL, prompt_id, download_preview=True)
    return responses.Response(content=outputs[0].read())

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8183)
