import os
import numpy as np
from PIL import Image

def multiply_blend(image1_path, image2_path, output_folder):
    try:
        # 确保输出文件夹存在
        os.makedirs(output_folder, exist_ok=True)

        # 读取图像并转换为 RGBA 模式
        img1 = Image.open(image1_path).convert("RGBA")
        img2 = Image.open(image2_path).convert("RGBA")

        # 自动调整 img2 大小以匹配 img1
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.LANCZOS)

        # 转换为 numpy 数组，并归一化到 [0, 1]
        arr1 = np.array(img1, dtype=np.float32) / 255.0
        arr2 = np.array(img2, dtype=np.float32) / 255.0

        # 分离颜色通道和 Alpha 通道
        rgb1, alpha1 = arr1[:, :, :3], arr1[:, :, 3:4]
        rgb2, alpha2 = arr2[:, :, :3], arr2[:, :, 3:4]

        # **正片叠底混合**
        blended_rgb = rgb1 * rgb2

        # **Alpha 通道混合**
        blended_alpha = alpha1 * alpha2  # 更柔和的透明度计算

        # **合并通道并转换回 [0, 255]**
        blended = np.concatenate([blended_rgb, blended_alpha], axis=-1)
        blended = (blended * 255).astype(np.uint8)

        # **保存图片**
        output_path = os.path.join(output_folder, "blended_result.png")
        result = Image.fromarray(blended, mode="RGBA")
        result.save(output_path)

        print(f"图片已成功保存至 {output_path}")

    except Exception as e:
        print(f"处理图像时出错: {e}")

# **输入文件路径**
image1_path = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\brightcon\outsui_1bc.png"
image2_path = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_1mask\maskresult_1\maskresult_1.png"
output_folder = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\multiplyresult"

# **执行正片叠底混合**
multiply_blend(image1_path, image2_path, output_folder)
