import io
import json
import uuid
import requests
import websocket
from typing import Literal

def open_websocket_connection(server_address):
    try:
        client_id = str(uuid.uuid4())
        ws = websocket.WebSocket()
        ws.connect(f"ws://{server_address}/ws?clientId={client_id}")
        return ws, client_id
    except Exception as e:
        print(f"Error open websocket connection: {e}")

def get_embeddings(server_address):
    response = requests.get(f"http://{server_address}/embeddings")
    return response.json()

def get_models_types(server_address):
    response = requests.get(f"http://{server_address}/models")
    return response.json()

def get_models_folder(server_address, folder):
    response = requests.get(f"http://{server_address}/models/{folder}")
    return response.json()

def get_extensions(server_address):
    response = requests.get(f"http://{server_address}/extensions")
    return response.json()

def upload_image_file(server_address, file, subfolder=None, overwrite=False,
                      type: Literal["input", "temp", "output"] = "input"):
    try:
        files = {"image": file}
        data = {"type": type, "subfolder": subfolder, "overwrite": overwrite}
        response = requests.post(f"http://{server_address}/upload/image", files=files, data=data)
        response.raise_for_status()
        file_info = response.json()
        file_path = file_info["name"]
        if file_info["subfolder"]:
            file_path = file_info["subfolder"] + "/" + file_path
        return file_path
    except Exception as e:
        print(f"Error upload image file: {e}")

def upload_mask_file(server_address, file, subfolder=None, overwrite=False,
                     type: Literal["input", "temp", "output"] = "input"):
    try:
        files = {"image": file}
        data = {"type": type, "subfolder": subfolder, "overwrite": overwrite}
        response = requests.post(f"http://{server_address}/upload/mask", files=files, data=data)
        response.raise_for_status()
        file_info = response.json()
        file_path = file_info["name"]
        if file_info["subfolder"]:
            file_path = file_info["subfolder"] + "/" + file_path
        return file_path
    except Exception as e:
        print(f"Error upload mask file: {e}")

def get_image_file(server_address, filename, subfolder=None, preview=None, channel=None,
                   type: Literal["input", "temp", "output"] = "output"):
    try:
        params = {"filename": filename, "type": type}
        if subfolder:
            params["subfolder"] = subfolder
        if preview:
            params["preview"] = preview
        if channel:
            params["channel"] = channel
        response = requests.get(f"http://{server_address}/view", params=params)
        response.raise_for_status()
        image_file = io.BytesIO()
        image_file.name = filename
        image_file.write(response.content)
        image_file.seek(0)
        return image_file
    except Exception as e:
        print(f"Error get iamge file: {e}")

def get_images_files(server_address, prompt_id, download_preview=False):
    hisstory = get_history_prompt(server_address, prompt_id)[prompt_id]
    images_files = []
    for node_id in hisstory["outputs"]:
        node_output = hisstory["outputs"][node_id]
        if "images" in node_output:
            for image in node_output["images"]:
                if image["type"] == "output" or (image["type"] == "temp" and download_preview):
                    image_file = get_image_file(server_address, image["filename"], image["subfolder"], type=image["type"])
                    images_files.append(image_file)
    return images_files

def get_metadata(server_address, folder_name, filename=".safetensors"):
    params = {"filename": filename}
    response = requests.get(f"http://{server_address}/view_metadata/{folder_name}", params=params)
    return response.json()

def get_system_stats(server_address):
    response = requests.get(f"http://{server_address}/system_stats")
    return response.json()

def get_prompt(server_address):
    response = requests.get(f"http://{server_address}/prompt")
    return response.json()

def get_object_info(server_address):
    response = requests.get(f"http://{server_address}/object_info")
    return response.json()

def get_object_info_node(server_address, node_class):
    response = requests.get(f"http://{server_address}/object_info/{node_class}")
    return response.json()

def get_history(server_address, max_items=None):
    params = {"max_items": max_items}
    response = requests.get(f"http://{server_address}/history", params=params)
    return response.json()

def get_history_prompt(server_address, prompt_id):
    response = requests.get(f"http://{server_address}/history/{prompt_id}")
    return response.json()

def get_queue(server_address):
    response = requests.get(f"http://{server_address}/queue")
    return response.json()

def queue_prompt(server_address, prompt, client_id=None):
    json = {"prompt": prompt}
    if client_id:
        json["client_id"] = client_id
    response = requests.post(f"http://{server_address}/prompt", json=json)
    return response.json()

def queue_clear_or_delete(server_address, clear=False, delete_prompt_id=None):
    json = {"clear": clear}
    if delete_prompt_id: # 删除指定队列
        json["delete"] = delete_prompt_id
    return requests.post(f"http://{server_address}/queue", json=json)

def queue_interrupt(server_address):
    return requests.post(f"http://{server_address}/interrupt")

def queue_free(server_address, unload_models=False, free_memory=False):
    json = {"unload_models": unload_models, "free_memory": free_memory}
    return requests.post(f"http://{server_address}/free", json=json)

def history_clear_or_delete(server_address, clear=False, delete_prompt_id=None):
    json = {"clear": clear}
    if delete_prompt_id: # 删除历史记录
        json["delete"] = delete_prompt_id
    return requests.post(f"http://{server_address}/history", json=json)

def track_progress(ws, prompt, prompt_id):
    node_ids = list(prompt.keys())
    finished_nodes = []
    while True:
        message = ws.recv()
        if isinstance(message, str):
            message = json.loads(message)
            if message["type"] == "progress":
                step = message["data"]["value"]
                max_step = message["data"]["max"]
                print(f"K-Sampler Progress: Step {step} of {max_step}")
            elif message["type"] == "execution_cached":
                node_id = message["data"]["nodes"]
                if node_id not in finished_nodes:
                    finished_nodes.append(node_id)
                print(f"Total Progress: Tasks completed {len(finished_nodes)}/{len(node_ids)}")
                if node_id is None and message["data"]["prompt_id"] == prompt_id:
                    break
            elif message["type"] == "executing":
                node_id = message["data"]["node"]
                if node_id not in finished_nodes:
                    finished_nodes.append(node_id)
                print(f"Total Progress: Tasks completed {len(finished_nodes)}/{len(node_ids)}")
                if node_id is None and message["data"]["prompt_id"] == prompt_id:
                    break
    return