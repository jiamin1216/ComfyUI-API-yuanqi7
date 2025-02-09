from PIL import Image, ImageEnhance

def grayscale_adjust_brightness_contrast(image_path, output_path, brightness_factor=1.0, contrast_factor=1.0):
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
        img = enhancer.enhance(contrast_factor)  # 1.0 = 原始对比度，>1.0 增强对比度，<1.0 降低对比度

        # **4. 保存图片**
        img.save(output_path)
        print(f"图片已成功保存至: {output_path}")

    except Exception as e:
        print(f"处理图像时出错: {e}")

# **使用示例**
image_path = r"C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\outsuit\mutiplypre_1\mutiplypre_1.png"  # 替换为你的图片路径
output_path = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\brightcon\outsui_1bc.png"  # 结果保存路径

brightness_factor = 2.9  # 亮度增强 1.2 倍
contrast_factor = 1.7  # 对比度增强 1.5 倍

grayscale_adjust_brightness_contrast(image_path, output_path, brightness_factor, contrast_factor)
