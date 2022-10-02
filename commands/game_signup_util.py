import io
from typing import List, Optional, Union

import discord
from discord.ui import Button, View
import PIL
from PIL import Image, ImageDraw, ImageOps

from globals import SIGNUP_BG_IMAGE


async def create_board(bot, message):

	league_button = Button(label="League", color='green')

	embed = create_party_embed('Gamers', 'Sign up')


	return



def create_party_embed(
    title: str,
    description: str,
    thumbnail: Union[None, str] = None,
    icons: Optional[List[io.BytesIO]] = None,
) -> discord.Embed:

    embed = discord.Embed(title=title, description=description)
    embed.set_thumbnail(url=thumbnail if thumbnail else discord.Embed.Empty)

    if icons:
        image = generate_image(icons)
        embed.set_image(file=image)

    return embed


def generate_image(icons: Optional[List[io.BytesIO]] = None) -> PIL.Image:

    if icons is None:
        return discord.File(fp=SIGNUP_BG_IMAGE, filename="join.png")

    # get the predefined background from filesystem
    background = Image.open(SIGNUP_BG_IMAGE)

    # get the size of the background image so that we can calcluate
    # how many icons per row with the expected padding
    canvas_width, canvas_height = background.size  # returns (width, height)

    # calculate how many icons for each row
    # given a padding of 20px and an avatar width of 75px
    padding = 5
    image_width = 50
    img_per_row = canvas_width / (image_width * padding)

    # create image objects for each avatar
    icons = [Image.open(io.BytesIO(icon)) for icon in icons]

    # now let's start placing the avatars on the canvas
    x = padding
    y = padding
    for icon in icons:
        # ensure size that matches image_width
        width, height = icon.size
        # image height will be (height*(new_width/width))
        height = int(height * (image_width / width))

        icon = icon.resize((image_width, height))

        # if there is no more room to the right to add a new image (with padding)
        # wrap to a new line
        if x + padding + image_width >= canvas_width:
            x = padding
            y = padding + height + padding

        background.paste(icon, (x, y))

        # move the x value over to keep equal spacing between icons
        x += padding + image_width + padding

    # converts the completed image to bytes and returns as a File object for the embed
    with io.BytesIO() as binary:
        background.save(binary, "PNG")
        binary.seek(0)

        return discord.File(binary, filename="icons.png")