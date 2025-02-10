import json
import websocket
import uuid
import urllib.request
import urllib.parse
import glob
import time
import random
import base64


import oss2
from oss2.credentials import EnvironmentVariableCredentialsProvider
from itertools import islice

import os
import subprocess
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, send_from_directory

app = Flask(__name__, static_folder = './static', template_folder='./template')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 检查环境变量是否已设置
required_env_vars = ['OSS_ACCESS_KEY_ID', 'OSS_ACCESS_KEY_SECRET']
for var in required_env_vars:
    if var not in os.environ:
        logging.error(f"Environment variable {var} is not set.")
        exit(1)

# 设置Endpoint和Region
endpoint = "https://oss-cn-hangzhou.aliyuncs.com"
region = "cn-hangzhou"
accessKeyId = os.environ.get('OSS_ACCESS_KEY_ID')
accessKeySecret = os.environ.get('OSS_ACCESS_KEY_SECRET')
default_bucket_name = "yefeng-file"

auth = oss2.ProviderAuthV4(EnvironmentVariableCredentialsProvider())
bucket = oss2.Bucket(auth, endpoint, default_bucket_name, region=region)


# 图生图工作流文件
WORKERFLOW_FILE = "workflow_API_0.5.json"
# WORKERFLOW_FILE = "速写工作流.json"
UPLOAD_FOLDER = 'uploads'
DOWNLOAD_FOLDER = 'downloads'
OUTPUT_FOLDER =  r"C:\Users\pc\Desktop\kute2025\layer_preprocess"
COMFYUI_ENDPOINT = '127.0.0.1:8188'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)


client_id = str(uuid.uuid4())


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/activate')
def activate():
    return "server is active"

@app.route('/generate_image', methods=['POST'])
def generate_image():
    try:
        image_file_name = request.json.get('image_name')
        print('请求参数image_name:{}'.format(image_file_name))
        if image_file_name == '':
            return jsonify({'error': '请输入图片', 'code': -1})

        # 下载文件到本地
        image_file_name = format_file_name(image_file_name)
        file_exist = bucket.object_exists(image_file_name)
        if not file_exist:
            return jsonify({'error': '参数输入错误, 图片不存在，请重新输入', 'code': 100})
        local_file_name = download_file(image_file_name)
        if local_file_name is None:
            return jsonify({'error': '图片下载失败，请重试', 'code': 101})
        # 调用工作流
        generate_file = comfy_ui_i2i(local_file_name)
        print("生成的图片路径:{}", generate_file)
        if generate_file == '' or generate_file is None:
            return jsonify({'error': '图片生成失败，请重试', 'code': 102})
        oss_file_name = upload_file(generate_file)
        print('上传的oss_file_name:{}'.format(oss_file_name))
        file_url = get_file_url(oss_file_name)
        return jsonify({'data': file_url, 'code': 0, 'message': '图片生成成功'})
    except Exception as e:
        print("error:{e}")
        return jsonify({'data': '', 'code': 200, 'message': 'generate error'})


def comfy_ui_i2i(local_file_name):
    # 连接到comfyui

    list_of_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*.PNG"))
    previous_latest_file = max(list_of_files, key=os.path.getctime) if list_of_files else None
    print("previous_latest_file:{}".format(previous_latest_file))

    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(COMFYUI_ENDPOINT, client_id))
    prompt_data = parse_worflow(WORKERFLOW_FILE, local_file_name)
    # 将请求发往comfyui
    prompt_id = queue_prompt(prompt_data)
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
        latest_file = wait_for_new_file(previous_latest_file)
        if latest_file:
            return latest_file
        print(f"Attempt {attempt + 1} failed. Retrying...")

    if not latest_file:
        print("Failed to detect the newly generated image after multiple attempts.")
        return None


def queue_prompt(prompt):
    '''
        向comfyui 发送请求
    '''
    request_data = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(request_data).encode('utf-8')
    req = urllib.request.Request("http://{}/prompt".format(COMFYUI_ENDPOINT), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_history(prompt_id):
    '''
        获取历史记录
    '''
    with urllib.request.urlopen("http://{}/history/{}".format(COMFYUI_ENDPOINT, prompt_id)) as response:
        return json.loads(response.read())
    
def get_image(filename, subfolder, folder_type):
    '''
        获取图片
    '''
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen("http://{}/view?{}".format(COMFYUI_ENDPOINT, url_values)) as response:
        return response.read()
    


def parse_worflow(workflowfile, local_file_name):
    print('workflowfile:', workflowfile)
    with open(workflowfile, 'r', encoding="utf-8") as workflow_api_i2i_file:
        prompt_data = json.load(workflow_api_i2i_file)
        # 设置文本提示
        prompt_data["28"]["inputs"]["image"] = os.path.abspath(local_file_name)
        return prompt_data
    

def wait_for_new_file(previous_latest_file, timeout=10):
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


def get_current_time():
    '''
        获取当前时间
    '''
    return datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]


def list_objects():
    try:
        objects = list(islice(oss2.ObjectIterator(bucket), 1000))
        for obj in objects:
            logging.info(obj.key)
    except oss2.exceptions.OssError as e:
        logging.error(f"Failed to list objects: {e}")

def upload_file(local_file_name):
    '''
        上传文件，返回oss文件名称
    '''
    current_date = datetime.now().strftime("%Y%m%d")
    oss_file_name = current_date + "/comfyui/" + local_file_name.split(os.sep)[-1]
    print('上传文件到oss,file_path:{}, oss_file_name:{}'.format(local_file_name, oss_file_name))
    with open(local_file_name, 'rb') as fileobj:
            bucket.put_object(oss_file_name, fileobj)
    return oss_file_name

def download_file(oss_file_name):
    file_name = oss_file_name.split('/')[-1]
    current_date = datetime.now().strftime("%Y%m%d")
    print("从oss下载文件 oss_file:{}".format(file_name))
    local_path = os.path.join(DOWNLOAD_FOLDER, current_date)
    if not os.path.exists(local_path):
        os.makedirs(local_path)
    # 每次下载的文件都是不重名的，即使指定的文件相同
    rename_file_name = str(int(time.time())) + "_" + file_name
    local_file_name = os.path.join(local_path, rename_file_name)
    print('文件下载本地路径:{}'.format(local_file_name))
    try:
        bucket.get_object_to_file(oss_file_name, local_file_name)
        return local_file_name
    except oss2.exceptions.OssError as e:
        logging.error(f"Failed to download file: {e}")
    return None

def get_file_url(oss_file_name):
    # 设置10年不过期
    return bucket.sign_url('GET', oss_file_name, 315360000)

def format_file_name(original_file_name):
    oss_file_name = urllib.parse.unquote(original_file_name)
    oss_file_name = oss_file_name.split('?')[0]
    index = oss_file_name.find('aliyuncs.com')
    if index!= -1:
        oss_file_name = oss_file_name[index + len('aliyuncs.com') + 1:]
    print("original_file_name:{} oss_file_name:{}".format(original_file_name, oss_file_name))

    return oss_file_name

def generate_test():
    current_date = datetime.now().strftime("%Y%m%d")
    image_file_name = "04368.png"
    local_file_name = os.path.join(DOWNLOAD_FOLDER, current_date, image_file_name)
    generate_file = comfy_ui_i2i(local_file_name, 1)
    oss_file_name = upload_file(generate_file)
    print('oss_file_name:{}'.format(oss_file_name))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8688)
