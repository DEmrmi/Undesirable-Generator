from PIL import Image, ImageDraw, ImageFont
import requests
import os


# =====================================
# SETTINGS (575x821 TEMPLATE)
# =====================================

BASE_DIR = os.path.dirname(__file__)

TEMPLATE = os.path.join(
    BASE_DIR,
    "UNDESIRABLE_TEMPLATE.png"
)

FONT_FILE = os.path.join(
    BASE_DIR,
    "UNDESIRABLEFONT.ttf"
)


# Avatar settings
AVATAR_SIZE = 490      # max width/height the avatar is allowed to be
AVATAR_Y = 160          # top of the avatar box (title block ends ~154)
AVATAR_GAP = 20         # minimum empty space required between avatar bottom and text

# Username settings
# The username sits directly above the thick black line, sized/centered
# to match it -- these values were measured directly off the template's
# black line (x=57-525, top edge at y=649). If you ever swap templates,
# re-measure the line and update these four numbers.
LINE_TOP_Y = 649
LINE_X_START = 57
LINE_X_END = 525
GAP_ABOVE_LINE = 8          # "rest just slightly above the black line"

TEXT_MAX_WIDTH = LINE_X_END - LINE_X_START   # must not go beyond the line's length
TEXT_CENTER_X = (LINE_X_START + LINE_X_END) // 2

# Prevent short names becoming absurdly large.
# This is the ONE number to tweak if usernames still look too big/small --
# long usernames are already shrunk down by the width check below, but short
# ones (like "ZLHN") never hit that width limit, so they always render at
# this size. Matches the 55pt font size used in the Pixlr reference template.
MAX_FONT_SIZE = 55


# =====================================
# GET ROBLOX AVATAR HEADSHOT
# =====================================

def get_roblox_avatar(username):

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # Get User ID
        response = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json={"usernames": [username], "excludeBannedUsers": True},
            headers=headers,
            timeout=15
        )
        data = response.json()

        if not data.get("data"):
            print("Username not found")
            return None

        user_id = data["data"][0]["id"]

        # Get Avatar Headshot
        avatar_api = (
            "https://thumbnails.roblox.com/v1/users/avatar-headshot?"
            f"userIds={user_id}"
            "&size=420x420"
            "&format=Png"
            "&isCircular=false"
        )

        avatar_data = requests.get(avatar_api, headers=headers, timeout=15).json()
        image_url = avatar_data["data"][0]["imageUrl"]

        image = requests.get(image_url, headers=headers, timeout=15).content
        filename = username + "_avatar.png"

        with open(filename, "wb") as f:
            f.write(image)

        return filename

    except Exception as e:
        print("Could not get avatar:", e)
        return None


# =====================================
# CREATE POSTER
# =====================================

def create_poster(username):

    if not os.path.exists(TEMPLATE):
        print("Missing template file:", TEMPLATE)
        return

    poster = Image.open(TEMPLATE).convert("RGBA")
    draw = ImageDraw.Draw(poster)

    # =================================
    # SMART USERNAME TEXT (measured first)
    # =================================
    # We figure out the text's size/position before the avatar, because the
    # avatar's available height depends on how tall the text ends up being --
    # not the other way around. This is what lets the avatar grow close to
    # AVATAR_SIZE for long usernames (which render shorter/thinner) while
    # still never colliding with short, tall usernames.

    text = username.upper()
    font_size = MAX_FONT_SIZE
    text_width = text_height = 0
    bbox = (0, 0, 0, 0)

    while font_size > 10:

        try:
            font = ImageFont.truetype(FONT_FILE, font_size)
        except Exception:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # Rule: username should be sized up to (but not beyond) the length
        # of the black line. Short usernames don't need to fill it, they
        # just must not exceed it.
        if text_width <= TEXT_MAX_WIDTH:
            break

        font_size -= 1

    # Horizontally centered on the line. Vertically anchored so the text
    # rests just slightly above the line (GAP_ABOVE_LINE).
    text_x = TEXT_CENTER_X - (text_width // 2) - bbox[0]
    text_y = (LINE_TOP_Y - GAP_ABOVE_LINE) - bbox[3]
    text_top_y = (LINE_TOP_Y - GAP_ABOVE_LINE) - text_height

    # =================================
    # AVATAR (sized off the leftover space above the text)
    # =================================

    avatar_file = get_roblox_avatar(username)

    if avatar_file:

        avatar = Image.open(avatar_file).convert("RGBA")

        # --- THE FIX ---
        # Instead of guessing a conservative fixed height, use whatever
        # vertical space is actually left between the avatar's top and the
        # top of the (already-measured) username text, minus a safety gap.
        # This is capped at AVATAR_SIZE (490) but in practice the poster's
        # own geometry -- title ends ~154, line starts at 649 -- is the real
        # ceiling: only ~490px of total vertical room exists for avatar +
        # gap + text + gap-above-line combined, so a name-dependent amount
        # of that gets used by the text itself.
        max_avatar_height = min(AVATAR_SIZE, text_top_y - AVATAR_GAP - AVATAR_Y)

        avatar.thumbnail((AVATAR_SIZE, max_avatar_height))

        avatar_x = (poster.width - avatar.width) // 2

        poster.alpha_composite(avatar, (avatar_x, AVATAR_Y))

        # The downloaded headshot is only needed to build the poster --
        # clean it up now that it's been composited in, so it doesn't pile
        # up in the folder every time this runs.
        try:
            os.remove(avatar_file)
        except OSError:
            pass

    else:
        print("Avatar could not be added")

    # Draw the text last so it's always on top, even though it shouldn't
    # overlap the avatar now.
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0, 255))

    # =================================
    # SAVE
    # =================================

    output = "UNDESIRABLE_" + username.upper() + ".png"
    poster.convert("RGB").save(output)

    print("Saved:", output)


# =====================================
# START
# =====================================

if __name__ == "__main__":

    username = input("Enter Roblox username: ").strip()

    if username:
        create_poster(username)
    else:
        print("No username entered")

    input("Press ENTER to close...")
