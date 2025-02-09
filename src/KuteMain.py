import uuid

import os

from PIL import Image, ImageEnhance

from src.utils.ImageHandle import ImageHandle

class KuteChangeFabricHandler:
    def __init__(self):
        self.resize_folder =  r"C:\Users\pc\Desktop\kute2025\resize"
        self.layer_preprocess_folder = r"C:\Users\pc\Desktop\kute2025\layer_preprocess"
        self.resize_repeat_folder = r"C:\Users\pc\Desktop\kute2025\resize_repeat"
        self.mask_folder = r"C:\Users\pc\Desktop\kute2025\mask"
        self.bright_folder = r"C:\Users\pc\Desktop\kute2025\bright"
        self.layer_merge_folder = r"C:\Users\pc\Desktop\kute2025\layer_merge"
        self.multiply_folder = r"C:\Users\pc\Desktop\kute2025\multiply"
        self.rembg_folder = r"C:\Users\pc\Desktop\kute2025\rembg"
        self.sdxl_folder = r"C:\Users\pc\Desktop\kute2025\sdxl"

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
        # todo 要根据prompt json进行适配（参数太多，还没搞）
        layer_preprocess_image = "徐京你先写死一个你生成好的本地地址"

        # 第三步骤
        # 3.1.1 resize_repeat
        resize_repeat_image = ImageHandle.tile_image(resize_save_path)
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
        layer_merge_image = ImageHandle.layer_merge(layer_preprocess_image, multiply_save_path, fabric_img_path)
        layer_merge_save_path = os.path.join(self.layer_merge_folder, f"{unique_id}.png")
        layer_merge_image.save(layer_merge_save_path, "PNG")

        # 第四步骤
        # 4.1 comfyUI sdxl
        # todo 要根据json进行适配


        # Final 返回处理完成后的图片在本地的地址(先返回第三步骤最后的文件)
        return layer_merge_save_path



if __name__ == '__main__':
    handle = KuteChangeFabricHandler()
    # 图片地址
    cloth_img_path = "XXXX"
    # 布料图片地址
    fabric_img_path = "XXXX"
    handle.change_fabric(cloth_img_path, fabric_img_path)