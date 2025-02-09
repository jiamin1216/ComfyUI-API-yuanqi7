import os

import cv2
import numpy as np
from PIL import Image, ImageEnhance


class ImageHandle:

    @staticmethod
    def resize_image(image: Image.Image) -> Image.Image:
        """
        调整输入的 Image 对象的大小，并返回调整后的 Image 对象。
        """
        try:
            width, height = image.size

            if min(width, height) >= 1024:
                # 如果最小边大于等于 1024，按最大边为 1024 等比例缩放
                if width > height:
                    new_height = 1024
                    new_width = int((new_height / height) * width)
                else:
                    new_width = 1024
                    new_height = int((new_width / width) * height)
            else:
                # 如果最小边小于 1024，则按最小边为 1024 等比例放大
                if width < height:
                    new_width = 1024
                    new_height = int((new_width / width) * height)
                else:
                    new_height = 1024
                    new_width = int((new_height / height) * width)
            resized_image = image.resize((new_width, new_height))
            return resized_image
        except Exception as e:
            print(f"Failed to resize image: {e}")
            return None

    @staticmethod
    def tile_image(image_path: str, repeat_x=2, ref_image_path=None) -> Image.Image:
        """
        读取指定路径的图像，无缝平铺，等比例缩放（如果提供了参考图片），
        使用 XID 生成唯一 ID，并保存到指定文件夹。
        返回保存的文件路径。
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                repeat_y = repeat_x  # 纵向重复次数等于横向
                new_width = width * repeat_x
                new_height = height * repeat_y

                new_img = Image.new("RGB", (new_width, new_height))
                for i in range(repeat_x):
                    for j in range(repeat_y):
                        new_img.paste(img, (i * width, j * height))

                if ref_image_path:
                    with Image.open(ref_image_path) as ref_img:
                        target_width = ref_img.width
                        scale_factor = target_width / new_width
                        target_height = int(new_height * scale_factor)
                        new_img = new_img.resize((target_width, target_height))
                return new_img
        except Exception as e:
            print(f"Failed to process and save tiled image: {e}")
            return None

    @staticmethod
    def grayscale_adjust_brightness_contrast(image_path, brightness_factor=1.0, contrast_factor=1.0) -> Image.Image:
        try:
            # 打开图片
            img = Image.open(image_path)

            # **1. 转换为灰度图（去色）**
            img = img.convert("L")  # "L" 模式表示灰度图

            # **2. 调整亮度**
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness_factor)  # 1.0 = 原始亮度，>1.0 变亮，<1.0 变暗

            # **3. 调整对比度**
            enhancer = ImageEnhance.Contrast(img)
            final_image = enhancer.enhance(contrast_factor)  # 1.0 = 原始对比度，>1.0 增强对比度，<1.0 降低对比度
            return final_image

        except Exception as e:
            print(f"处理图像时出错: {e}")

    @staticmethod
    def apply_mask_and_fill(mask_path, fill_path) -> Image.Image:
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
        return final_image

    @staticmethod
    def multiply_blend(bright_image_path, mask_image_path) -> Image.Image:
        try:
            # 读取图像并转换为 RGBA 模式
            img1 = Image.open(bright_image_path).convert("RGBA")
            img2 = Image.open(mask_image_path).convert("RGBA")

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

            result = Image.fromarray(blended, mode="RGBA")
            return result

        except Exception as e:
            print(f"处理图像时出错: {e}")

    @staticmethod
    def process_rembg(image_path: str, mask_path: str, output_path: str) -> Image.Image:
        """
        处理单个图像，应用遮罩并保存。
        返回保存的文件路径。
        """
        try:
            # 读取原始图像
            image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            # 读取遮罩图像
            mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)

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
                cv2.imwrite(output_path, image_with_alpha)
            else:
                print(f"Error processing {image_path}: Image or mask not found or size mismatch.")
        except Exception as e:
            print(f"Failed to process image: {e}")
            return None

    @staticmethod
    def layer_merge(button_path: str, multiply_path: str, rawimg_path: str):
        # 打开图片
        button_img = Image.open(button_path).convert("RGBA")
        multiply_img = Image.open(multiply_path).convert("RGBA")
        rawimg_img = Image.open(rawimg_path).convert("RGBA")

        # 确保图片尺寸一致
        base_size = rawimg_img.size
        button_img = button_img.resize(base_size)
        multiply_img = multiply_img.resize(base_size)

        # 叠加图片（从底层到顶层）
        combined_img = Image.alpha_composite(rawimg_img, multiply_img)
        final_image = Image.alpha_composite(combined_img, button_img)
        return final_image


def main():
    print("Image Processing Tool（元七图片处理工具Resize Images）")


if __name__ == "__main__":
    main()
