import re
import base64
import os

md_path = "/Users/sarikalakhani/Downloads/product_report.md"
with open(md_path, "r") as f:
    content = f.read()

def get_base64_image(match):
    caption = match.group(1)
    img_path = match.group(2)
    # Handle file:// prefix if present
    if img_path.startswith("file://"):
        img_path = img_path[7:]
        
    try:
        with open(img_path, "rb") as img_file:
            encoded_string = base64.b64encode(img_file.read()).decode('utf-8')
        extension = os.path.splitext(img_path)[1][1:].lower()
        if extension == "jpg":
            extension = "jpeg"
        return f"![{caption}](data:image/{extension};base64,{encoded_string})"
    except Exception as e:
        print(f"Failed to read image {img_path}: {e}")
        return match.group(0)

# Match markdown images: ![caption](path)
pattern = re.compile(r'!\[(.*?)\]\((.*?)\)')
new_content = pattern.sub(get_base64_image, content)

inline_md_path = "/Users/sarikalakhani/Downloads/product_report_inline.md"
with open(inline_md_path, "w") as f:
    f.write(new_content)

print(f"Successfully created base64 embedded markdown at: {inline_md_path}")
