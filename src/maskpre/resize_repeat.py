import os
from PIL import Image

def get_reference_width(ref_folder):
    """ 获取 `suit` 目录中第一张图片的宽度 """
    for filename in os.listdir(ref_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            ref_path = os.path.join(ref_folder, filename)
            with Image.open(ref_path) as ref_img:
                return ref_img.width  # 获取宽度
    raise ValueError(f"❌ 目录 {ref_folder} 内没有有效的图片！")

def tile_image(image_path, output_path, repeat_x=2, target_width=None):
    """ 读取图片 -> 无缝平铺 -> 等比例缩放 -> 保存 """
    try:
        # **1. 读取原始图片**
        img = Image.open(image_path)

        # **2. 计算新画布大小**
        width, height = img.size
        repeat_y = repeat_x  # 纵向重复次数等于横向
        new_width = width * repeat_x
        new_height = height * repeat_y

        # **3. 创建新画布并平铺**
        new_img = Image.new("RGB", (new_width, new_height))
        for i in range(repeat_x):
            for j in range(repeat_y):
                new_img.paste(img, (i * width, j * height))

        # **4. 如果提供了 target_width，则等比例缩放**
        if target_width:
            scale_factor = target_width / new_width  # 计算缩放比例
            target_height = int(new_height * scale_factor)  # 保持比例缩放
            new_img = new_img.resize((target_width, target_height), Image.LANCZOS)

        # **5. 保存结果**
        new_img.save(output_path)
        print(f"✅ 处理完成: {output_path}")

    except Exception as e:
        print(f"❌ 处理 {image_path} 出错: {e}")

def process_folder(input_folder, output_folder, ref_folder, repeat_x=2):
    """ 处理文件夹内的所有图片，并调整宽度 """
    os.makedirs(output_folder, exist_ok=True)  # 确保输出文件夹存在
    target_width = get_reference_width(ref_folder)  # 获取 `suit` 目录中的参考宽度

    for filename in os.listdir(input_folder):
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif")):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)
            tile_image(input_path, output_path, repeat_x, target_width)

# **📂 设定输入/输出文件夹**
input_folder = r"C:\Users\pc\Desktop\kute2025\input\1\fabric1"
output_folder = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_1mask\fill_1"
ref_folder = r"C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\outsuit\maske_outsuit_1"  # 参考宽度的目录

# **🚀 执行批量处理**
repeat_x = 8  # 设定平铺次数
process_folder(input_folder, output_folder, ref_folder, repeat_x)
