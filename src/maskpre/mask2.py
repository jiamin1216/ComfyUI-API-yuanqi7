from PIL import Image
import numpy as np
import os

def apply_mask_and_fill(mask_path, fill_path, output_path):
    # 读取遮罩图片和填充图片
    mask_image = Image.open(mask_path).convert('L')  # 转换为灰度图
    fill_image = Image.open(fill_path).convert('RGB')

    # 将遮罩图转换为NumPy数组
    mask_array = np.array(mask_image)

    # 生成黑色部分的掩码（黑色为0，其他为1）
    black_mask = mask_array == 0

    # 调整填充图片的大小以适应遮罩图片
    fill_image_resized = fill_image.resize(mask_image.size)
    fill_array = np.array(fill_image_resized)

    # 创建最终合成图像（与遮罩图相同的尺寸）
    result_image = Image.new('RGB', mask_image.size)
    result_array = np.array(result_image)

    # 将填充图片的内容复制到黑色区域
    result_array[black_mask] = fill_array[black_mask]

    # 将遮罩图片的非黑色部分保持原样
    mask_rgb = Image.open(mask_path).convert('RGB')
    mask_rgb_array = np.array(mask_rgb)
    result_array[~black_mask] = mask_rgb_array[~black_mask]

    # 保存合成后的图片
    final_image = Image.fromarray(result_array)
    final_image.save(output_path)

# 文件路径设置
mask_path = r'C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\outsuit\maske_outsuit_1\maske_outsuit_1.png'  # 遮罩图片路径
fill_path = r'C:\Users\pc\Desktop\kute2025\step3maskpre\3_1mask\fill_1\fabric1.jpg'  # 填充图片路径
output_path = r'C:\Users\pc\Desktop\kute2025\step3maskpre\3_1mask\maskresult_1\maskresult_1.png'  # 输出图片路径

# 执行函数
apply_mask_and_fill(mask_path, fill_path, output_path)
