import base64
from PIL import Image
from io import BytesIO


def image2string(image):
    buf = BytesIO()
    image.save(buf, format='JPEG')
    image_byte = buf.getvalue()
    img_str = base64.b64encode(image_byte).decode('ascii')
    return img_str

def string2image(image_string):
    image_bytes = base64.b64decode(image_string)
    image_data = BytesIO(image_bytes)
    image = Image.open(image_data)
    return image