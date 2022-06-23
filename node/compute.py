import os
import glob
import json
import firebase
from PIL import Image
import numpy as np
import cv2
from convert import string2image, image2string
url = "https://cloud-system-b85e4-default-rtdb.firebaseio.com/"  # Firebase
fb = firebase.FirebaseApplication(url, None)
def cartoon(image):
    HEIGHT_MAX = 500
    height,width,_ = image.shape
    ration = HEIGHT_MAX/height
    width = int(width * ration)
    height = HEIGHT_MAX
    img_resize = cv2.resize(image,(width,height))   
    img_gray = cv2.cvtColor(img_resize,cv2.COLOR_BGR2GRAY)
    img_blur = cv2.medianBlur(img_gray,5)
    img_edge = cv2.Canny(img_blur,80,160,apertureSize=3)
    _,img_mask= cv2.threshold(img_edge,100,255,cv2.THRESH_BINARY_INV)
    img_mask = cv2.cvtColor(img_mask,cv2.COLOR_GRAY2BGR)
    img_cartoon = img_resize
    for x in range(11):
        ksize,sigma_color,sigma_space = 21,11,11
        img_cartoon = cv2.bilateralFilter(img_cartoon,ksize,sigma_color,sigma_space)
    return img_cartoon
def sketch(image):
    HEIGHT_MAX = 500
    height,width,_ = image.shape
    ration = HEIGHT_MAX/height
    width = int(width * ration)
    height = HEIGHT_MAX
    img_resize = cv2.resize(image,(width,height))
    grey_img=cv2.cvtColor(img_resize, cv2.COLOR_BGR2GRAY)
    invert_img=cv2.bitwise_not(grey_img)
    blur_img=cv2.GaussianBlur(invert_img, (111,111),0)
    invblur_img=cv2.bitwise_not(blur_img)
    sketch_img=cv2.divide(grey_img,invblur_img, scale=256.0)
    return sketch_img
def compute_func():
    jobs = fb.get("/job")
    for job in jobs:
        if job["status"] == "idle":
            UserId = job["user_id"]
            images = fb.get("/user/" + UserId, "images")
            for k, v in images.items():
                image = string2image(v)
                # pil to cv2
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                # compute algorithm
                image = cartoon(image)
                # cv2 to pil
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                image_string = image2string(image)
                fb.put("/user/" + UserId, "images", image_string)

if __name__ == '__main__':
    while True:
        compute_func()