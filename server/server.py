from flask import Flask, render_template
from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextSendMessage,
    ImageSendMessage
)
from firebase import firebase
import convert
from PIL import Image
from io import BytesIO
import json
import uuid
import yaml
from convert import string2image
import os
app = Flask(__name__, template_folder='../templates', static_folder="../static")

with open("config.yaml") as f:
    dict = yaml.load(f, Loader=yaml.FullLoader)
    firebase_url = dict[0]["firebase_config"]["firebase_url"]
    ngrok_url = dict[1]["ngrok_config"]["ngrok_url"]
    line_bot_api_secret = dict[2]["line_bot_config"]["line_bot_api_secret"]
    webhook_secret = dict[2]["line_bot_config"]["webhook_secret"]
line_bot_api = LineBotApi(
    line_bot_api_secret
)
handler = WebhookHandler(webhook_secret)
url = firebase_url  # Firebase
fb = firebase.FirebaseApplication(url, None)
@app.route("/send_msg", methods=["POST"])
def send_msg():
    if request.method=="POST":
        input_dict = json.loads(request.json)
        UserId = input_dict["user_id"]
        JobId = input_dict["job_id"]
        image_dict = fb.get("/job/" + JobId, "images")
        tmp_path = "../static/" + UserId
        os.makedirs(tmp_path, exist_ok=True)
        for k, v in image_dict.items():
            image = string2image(v)
            image.save(f"{tmp_path}/{k}.jpg") 
            try:
                message = ImageSendMessage(
                    original_content_url= f"{ngrok_url}/static/{UserId}/{k}.jpg",
                    preview_image_url= f"{ngrok_url}/static/{UserId}/{k}.jpg"
                )
                line_bot_api.push_message(UserId, message)

            except:
                line_bot_api.reply_message(UserId, TextSendMessage(text="發生錯誤！")) 
    return "Ok"
@app.route("/process", methods=["GET", "POST"])
def process():
    if request.method=="POST":
        input_dict = json.loads(request.json)
        print(input_dict)
        UserId = input_dict["user_id"]
        if input_dict["method"] == "transform":
            style = input_dict["style"]
            job_id = uuid.uuid4()
            fb.put("/user/" + UserId, "style", style)
            fb.put("/job/" + str(job_id), "status", "idle")
            fb.put("/job/" + str(job_id), "user_id", UserId)
        elif input_dict["method"] == "delete":
            for image in input_dict["image_list"]:
                fb.delete("/user/" + UserId + "/images", image)
    return "OK"
@app.route("/<user_id>/show_image")
def show_image(user_id):
    image_dict = fb.get(f"/user/{user_id}/images", '')
    return render_template("show_image.html", user_id=user_id, image_dict=image_dict)
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"


@handler.add(MessageEvent)
def handle_message(event):
    if event.message.type == "image":
        try:
            msg = line_bot_api.get_message_content(event.message.id)
            img = Image.open(BytesIO(msg.content))
            img_str = convert.image2string(img)
            UserId = event.source.user_id
            fb.put("/user/" + UserId + "/images", event.message.id, img_str)
            fb.put("/user/" + UserId, "style", "not assign")
            message = TextSendMessage(
                text=f"收到圖片，請至 {ngrok_url}{UserId}/show_image 檢視"
            )
            line_bot_api.reply_message(event.reply_token, message)

        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="發生錯誤！"))


if __name__ == "__main__":
    app.run(use_reloader=True, debug=True)
