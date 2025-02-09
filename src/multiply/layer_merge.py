from PIL import Image
import os

# 定义目录路径
button_dir = r"C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\button"
multiply_dir = r"C:\Users\pc\Desktop\kute2025\step3maskpre\3_2multiply\3_2_output"
rawimg_dir = r"C:\Users\pc\Desktop\kute2025\step2layerpre\suit1fabric1\rawimg"
output_dir = r"C:\Users\pc\Desktop\kute2025\step3maskpre\step3_output"

# 确保输出目录存在
os.makedirs(output_dir, exist_ok=True)

# 获取目录中的所有图片文件
button_files = sorted(os.listdir(button_dir))
multiply_files = sorted(os.listdir(multiply_dir))
rawimg_files = sorted(os.listdir(rawimg_dir))

# 获取已存在的输出文件数量，确定起始编号
existing_outputs = [f for f in os.listdir(output_dir) if f.startswith("step3_output") and f.endswith(".png")]
start_index = len(existing_outputs) + 1

# 遍历文件，假设文件名在不同目录中是匹配的
for offset, (button_file, multiply_file, rawimg_file) in enumerate(zip(button_files, multiply_files, rawimg_files)):
    button_path = os.path.join(button_dir, button_file)
    multiply_path = os.path.join(multiply_dir, multiply_file)
    rawimg_path = os.path.join(rawimg_dir, rawimg_file)

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
    combined_img = Image.alpha_composite(combined_img, button_img)

    # 保存结果，自动命名为 step3_output+数字
    output_index = start_index + offset
    output_path = os.path.join(output_dir, f"step3_output{output_index}.png")
    combined_img.save(output_path)

    print(f"已保存: {output_path}")