from flask import Flask, render_template
from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextSendMessage
)
from firebase import firebase
import convert
from PIL import Image
from io import BytesIO
import json
app = Flask(__name__, template_folder='../templates')

line_bot_api = LineBotApi(
    "2EFeRFjdjj0D7agjnXO8QoKRDtAL5kPovRqRoXbpKqZ0G8QB3CfX7hhbS9aNn4oksBJ3uRXGviT6ypj+DkZP04g+33VYN8gyhLx7K2tyeeczwesMD3Mt/CvZlGVzcngEEtsKqZsfHeawqPX+mOIcbwdB04t89/1O/w1cDnyilFU="
)
handler = WebhookHandler("fd83a08bbb14afc391da01d82011b05a")
url = "https://cloud-system-b85e4-default-rtdb.firebaseio.com/"  # Firebase
fb = firebase.FirebaseApplication(url, None)
ngrok_url = "https://f12a-61-216-173-3.jp.ngrok.io/"
@app.route("/process", methods=["POST"])
def process():
    if request.method=="POST":
        input_dict = json.loads(request.json)
        print(input_dict)
        UserId = input_dict["user_id"]
        if input_dict["method"] == "transform":
            style = input_dict["style"]
            fb.put("/user/" + UserId, "style", style)
            fb.put("/job/" + UserId, "status", "idle")
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
