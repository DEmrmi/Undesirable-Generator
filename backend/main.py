from flask import Flask, request, send_file
from flask_cors import CORS

from PIL import Image, ImageDraw, ImageFont
import requests
import os


app = Flask(__name__)
CORS(app)


BASE_DIR = os.path.dirname(__file__)

TEMPLATE = os.path.join(
    BASE_DIR,
    "UNDESIRABLE_TEMPLATE.png"
)

FONT_FILE = os.path.join(
    BASE_DIR,
    "UNDESIRABLEFONT.ttf"
)


AVATAR_SIZE = 490
AVATAR_Y = 160
AVATAR_GAP = 20

LINE_TOP_Y = 649
LINE_X_START = 57
LINE_X_END = 525

GAP_ABOVE_LINE = 8

TEXT_MAX_WIDTH = LINE_X_END - LINE_X_START
TEXT_CENTER_X = (LINE_X_START + LINE_X_END)//2

MAX_FONT_SIZE = 55



def get_avatar(username):

    headers = {
        "User-Agent":"Mozilla/5.0"
    }

    response = requests.post(
        "https://users.roblox.com/v1/usernames/users",
        json={
            "usernames":[username],
            "excludeBannedUsers":True
        },
        headers=headers
    )

    data=response.json()

    if not data.get("data"):
        return None


    user_id=data["data"][0]["id"]


    api=(
        "https://thumbnails.roblox.com/v1/users/avatar-headshot?"
        f"userIds={user_id}"
        "&size=420x420"
        "&format=Png"
        "&isCircular=false"
    )


    avatar=requests.get(api).json()

    url=avatar["data"][0]["imageUrl"]


    image=requests.get(url).content


    path=os.path.join(
        BASE_DIR,
        "avatar.png"
    )

    with open(path,"wb") as f:
        f.write(image)


    return path




def create_poster(username):

    poster=Image.open(
        TEMPLATE
    ).convert("RGBA")


    draw=ImageDraw.Draw(
        poster
    )


    text=username.upper()


    size=MAX_FONT_SIZE


    while size > 10:

        font=ImageFont.truetype(
            FONT_FILE,
            size
        )

        box=draw.textbbox(
            (0,0),
            text,
            font=font
        )

        width=box[2]-box[0]

        if width <= TEXT_MAX_WIDTH:
            break

        size-=1



    text_width=width

    text_height=box[3]-box[1]


    text_x=(
        TEXT_CENTER_X -
        text_width//2
    )


    text_y=(
        LINE_TOP_Y -
        GAP_ABOVE_LINE -
        text_height
    )


    avatar_file=get_avatar(username)


    if avatar_file:

        avatar=Image.open(
            avatar_file
        ).convert("RGBA")


        max_height=min(
            AVATAR_SIZE,
            text_y-AVATAR_GAP-AVATAR_Y
        )


        avatar.thumbnail(
            (
                AVATAR_SIZE,
                max_height
            )
        )


        x=(
            poster.width -
            avatar.width
        )//2


        poster.alpha_composite(
            avatar,
            (
                x,
                AVATAR_Y
            )
        )


        os.remove(
            avatar_file
        )


    draw.text(
        (
            text_x,
            text_y
        ),
        text,
        font=font,
        fill=(0,0,0,255)
    )


    output=os.path.join(
        BASE_DIR,
        "result.png"
    )


    poster.convert(
        "RGB"
    ).save(output)


    return output





@app.route("/generate",methods=["POST"])
def generate():

    data=request.json

    username=data.get(
        "username"
    )


    if not username:
        return {
            "error":"No username"
        },400



    file=create_poster(
        username
    )


    return send_file(
        file,
        mimetype="image/png"
    )





app.run(
    host="0.0.0.0",
    port=10000
)
