import shutil
import uuid

import os

from PIL import Image, ImageEnhance

from src.utils.ComfyUIControlnetHandle import ComfyUIControlnetHandle
from src.utils.ComfyUIPreProcessHandle import ComfyUIHandle, ComfyUIPreProcessHandle
from src.utils.ImageHandle import ImageHandle

class KuteChangeFabricHandler:
    def __init__(self):
        self.resize_folder = r"E:\ComfyUI-API-yuanqi7\test1\resize"
        self.layer_preprocess_folder = r"E:\ComfyUI-API-yuanqi7\test1\layer_preprocess"
        self.resize_repeat_folder = r"E:\ComfyUI-API-yuanqi7\test1\resize_repeat"
        self.mask_folder = r"E:\ComfyUI-API-yuanqi7\test1\mask"
        self.masked_folder = r"E:\ComfyUI-API-yuanqi7\test1\masked"
        self.bright_folder = r"E:\ComfyUI-API-yuanqi7\test1\bright"
        self.layer_merge_folder = r"E:\ComfyUI-API-yuanqi7\test1\layer_merge"
        self.multiply_folder = r"E:\ComfyUI-API-yuanqi7\test1\multiply"
        self.rembg_folder = r"E:\ComfyUI-API-yuanqi7\test1\rembg"
        self.sdxl_folder = r"E:\ComfyUI-API-yuanqi7\test1\sdxl"
        self.ref_image_path = r"E:\ComfyUI-API-yuanqi7\test1\mask"


        self.preProcessHandle = ComfyUIPreProcessHandle()
        self.controlnetHandle = ComfyUIControlnetHandle()


    def change_fabric(self, cloth_img_path, fabric_img_path):
        # 这个图像的唯一ID
        unique_id = uuid.uuid4().hex

        cloth_img = Image.open(cloth_img_path)     # 衣服

        # 第一步骤 resize
        resize_image =  ImageHandle.resize_image(cloth_img)
        # 将resize后的图片存储到一个固定的文件夹里
        resize_save_path = os.path.join(self.resize_folder, f"{unique_id}.png")
        resize_image.save(resize_save_path, "PNG")

        # 第二步骤 调用一个comfyUI layer preprocess
        layer_preprocess_response =  self.preProcessHandle.generate_image(resize_save_path)
        code = layer_preprocess_response.get('code')
        # 根据返回的 code 进行不同的处理
        if code == 0:
            # 图片生成成功，返回路径
            data = layer_preprocess_response.get('data')
            if data:
                layer_preprocess_image_name = data
            else:
                return {"status": "error", "message": "layer_preprocess没有返回图片路径"}
        else:
            return {"status": "error", "message": "未知错误，layer_preprocess 返回了未知的 code"}
        layer_preprocess_image_final_name = os.path.join(self.layer_preprocess_folder, f"{unique_id}.png")
        shutil.move(layer_preprocess_image_name, layer_preprocess_image_final_name)

        # add by xujing for test
        layer_preprocess_image_name = r"E:\ComfyUI-API-yuanqi7\test1\layer_preprocess\suit1fabric1\button\button_1.png"

        # 第三步骤
        # 3.1.1 resize_repeat
        resize_repeat_image = ImageHandle.tile_image(layer_preprocess_image_name)
        # 将resize_repeat后的图片存储到一个固定的文件夹里
        resize_repeat_save_path = os.path.join(self.resize_repeat_folder, f"{unique_id}.png")
        resize_repeat_image.save(resize_repeat_save_path, "PNG")

        # 3.1.2 mask2
        mask_image = ImageHandle.apply_mask_and_fill(resize_repeat_save_path, fabric_img_path)
        mask_save_path = os.path.join(self.mask_folder, f"{unique_id}.png")
        mask_image.save(mask_save_path, "PNG")

        # 3.2.1 bright
        bright_image = ImageHandle.grayscale_adjust_brightness_contrast(mask_save_path, 2.9, 1.7)
        bright_save_path = os.path.join(self.bright_folder, f"{unique_id}.png")
        bright_image.save(bright_save_path, "PNG")

        # 3.2.2 multiply
        multiply_image = ImageHandle.multiply_blend(bright_save_path, mask_save_path)
        multiply_save_path = os.path.join(self.multiply_folder, f"{unique_id}.png")
        multiply_image.save(multiply_save_path, "PNG")

        # 3.2.3 rembg
        rembg_save_path = os.path.join(self.rembg_folder, f"{unique_id}.png")
        ImageHandle.process_rembg(multiply_save_path, mask_save_path, rembg_save_path)

        # 3.3 layer_merge
        layer_merge_image = ImageHandle.layer_merge(layer_preprocess_image_final_name, multiply_save_path, fabric_img_path)
        layer_merge_save_path = os.path.join(self.layer_merge_folder, f"{unique_id}.png")
        layer_merge_image.save(layer_merge_save_path, "PNG")

        # 第四步骤
        # 4.1 comfyUI sdxl
        controlnet_response = self.controlnetHandle.generate_image(layer_merge_save_path)
        code = controlnet_response.get('code')

        # 根据返回的 code 进行不同的处理
        if code == 0:
            # 图片生成成功，返回路径
            data = controlnet_response.get('data')
            if data:
                controlnet_image_name = data
            else:
                return {"status": "error", "message": "controlnet comfyUI 没有返回图片路径"}
        else:
            return {"status": "error", "message": "未知错误，controlnet comfyUI  返回了未知的 code"}
        controlnet_image_final_name = os.path.join(self.sdxl_folder, f"{unique_id}.png")
        shutil.move(controlnet_image_name, controlnet_image_final_name)

        # Final 返回处理完成后的图片在本地的地址(先返回第三步骤最后的文件)
        return controlnet_image_final_name

if __name__ == '__main__':
    handle = KuteChangeFabricHandler()
    # 图片地址
    cloth_img_path = "XXXX"
    # 布料图片地址
    fabric_img_path = "XXXX"
    handle.change_fabric(cloth_img_path, fabric_img_path)