import json
import websocket
import uuid
import urllib.request
import urllib.parse
import glob
import time

import os
import logging
from flask import jsonify

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 图生图工作流文件
WORKERFLOW = "../../prompt/layer_preprocess.json"
COMFYUI_ENDPOINT = '127.0.0.1:8188'
OUTPUT_FOLDER =  r"C:\Users\pc\Desktop\kute2025\layer_preprocess"

client_id = str(uuid.uuid4())

class ComfyUIPreProcessHandle:

    def generate_image(self, input_image_name: str):
        try:
            # 调用工作流
            generate_file = self.comfy_ui_layer_preprocess(input_image_name)
            print("生成的图片路径:{}", generate_file)
            if generate_file == '' or generate_file is None:
                return jsonify({'error': '图片生成失败，请重试', 'code': 102})
            return jsonify({'data': generate_file, 'code': 0, 'message': '图片生成成功'})
        except Exception as e:
            print("error:{e}")
            return jsonify({'data': '', 'code': 200, 'message': 'generate error'})

    def comfy_ui_layer_preprocess(self, input_image_name):
        # 连接到comfyui
        list_of_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.PNG"))
        previous_latest_file = max(list_of_files, key=os.path.getctime) if list_of_files else None
        print("previous_latest_file:{}".format(previous_latest_file))

        ws = websocket.WebSocket()
        ws.connect("ws://{}/ws?clientId={}".format(COMFYUI_ENDPOINT, client_id))
        prompt_data = self.parse_workflow(WORKERFLOW, input_image_name)
        # 将请求发往comfyui
        prompt_id = self.queue_prompt(prompt_data)
        print('prompt_id:', prompt_id)
        if not prompt_id:
            print("Failed to queue prompt.")
            ws.close()
            return None
        ws.close()
        # 等待生成新文件
        latest_file = None
        max_attempts = 12
        for attempt in range(max_attempts):
            latest_file = self.wait_for_new_file(previous_latest_file)
            if latest_file:
                return latest_file
            print(f"Attempt {attempt + 1} failed. Retrying...")

        if not latest_file:
            print("Failed to detect the newly generated image after multiple attempts.")
            return None


    def queue_prompt(self, prompt):
        '''
            向comfyui 发送请求
        '''
        request_data = {"prompt": prompt, "client_id": client_id}
        data = json.dumps(request_data).encode('utf-8')
        req = urllib.request.Request("http://{}/prompt".format(COMFYUI_ENDPOINT), data=data)
        return json.loads(urllib.request.urlopen(req).read())


    def get_image(self, filename, subfolder, folder_type):
        '''
            获取图片
        '''
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        with urllib.request.urlopen("http://{}/view?{}".format(COMFYUI_ENDPOINT, url_values)) as response:
            return response.read()

    def parse_workflow(self, workflowfile, local_file_name):
        print('workflowfile:', workflowfile)
        with open(workflowfile, 'r', encoding="utf-8") as workflow_api_i2i_file:
            prompt_data = json.load(workflow_api_i2i_file)
            # 用户上传图像
            prompt_data["17"]["inputs"]["image"] = os.path.abspath(local_file_name)
            return prompt_data


    def wait_for_new_file(self, previous_latest_file, timeout=10):
        """等待新的图像文件生成"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            # 获取所有PNG文件，按创建时间排序
            list_of_files = sorted(
                glob.glob(os.path.join(OUTPUT_FOLDER, "*.PNG")),
                key=os.path.getctime,
                reverse=True
            )

            if list_of_files:
                latest_file = list_of_files[0]

                # 严格检查：确保是新文件且文件大小大于 0
                if latest_file != previous_latest_file and os.path.getsize(latest_file) > 0:
                    # 额外的延迟，确保文件完全写入
                    time.sleep(1)

                    print(f"New file detected: {latest_file}")
                    print(f"File size: {os.path.getsize(latest_file)} bytes")
                    return latest_file

            time.sleep(1)

        print("Timeout waiting for new file.")
        return None