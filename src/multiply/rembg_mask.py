import cv2
import os
import numpy as np

# 定义输入目录、遮罩目录和输出目录
input_dir = r'C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\multiplyresult'
mask_dir = r'C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\outsuit\maske_outsuit_1'
output_dir = r'C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\3_2_output'

# 遮罩文件名
mask_filename = 'maske_outsuit_1.png'
mask_path = os.path.join(mask_dir, mask_filename)

# 检查遮罩文件是否存在
if not os.path.exists(mask_path):
    print(f"Mask file {mask_path} not found.")
else:
    # 读取遮罩图像
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

    # 确保输出目录存在
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 遍历输入目录中的所有图像文件
    for filename in os.listdir(input_dir):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            # 读取原始图像
            image_path = os.path.join(input_dir, filename)
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

            # 检查图像和遮罩是否存在且尺寸相同
            if image is not None and mask is not None and image.shape[:2] == mask.shape:
                # 创建一个透明通道
                alpha_channel = np.zeros(mask.shape, dtype=np.uint8)

                # 根据遮罩设置透明通道
                alpha_channel[mask == 0] = 255

                # 将透明通道添加到原始图像
                if image.shape[2] == 3:  # 如果图像没有透明通道
                    image_with_alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
                else:
                    image_with_alpha = image.copy()

                image_with_alpha[:, :, 3] = alpha_channel

                # 保存处理后的图像
                output_path = os.path.join(output_dir, filename.rsplit('.', 1)[0] + '.png')
                cv2.imwrite(output_path, image_with_alpha)
                print(f"Processed {filename} and saved to {output_path}")
            else:
                print(f"Error processing {filename}: Image or mask not found or size mismatch.")