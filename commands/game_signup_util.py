import io
import os
from typing import List, Optional, Union

import discord
from discord.ui import Button, View
import PIL
from PIL import Image, ImageDraw, ImageOps
from typing import Dict
from collections import defaultdict

from globals import (
    BACKGROUND_ATTACHMENT_URL,
    GAME_THUMBNAILS_FOLDER,
    SIGNUP_BG_IMAGE,
    SIGNUP_BG_IMAGE_UPDATED,
    THUMBNAIL_ATTACHMENT_URL,
    THUMBNAIL_IMAGE,
)

LEAGUE_GAME_KEY = "league"
APEX_GAME_KEY = "apex"


async def game_button_callback(view, interaction, _, game_key):
    if interaction.user.id in view.games[game_key]:
        await interaction.response.send_message(
            "Don't try that again you psycho", ephemeral=True
        )
    else:
        view.games[game_key][interaction.user.id] = io.BytesIO(
            await interaction.user.display_avatar.read()
        )
        view.icons[interaction.user.id] = io.BytesIO(
            await interaction.user.display_avatar.read()
        )
        (files, embed) = create_party_embed(
            "Gamers", "Sign up", thumbnail=True, icons=view.icons, games=view.games
        )

        await interaction.response.edit_message(
            attachments=files, embed=embed, view=view
        )


class GameView(View):
    def __init__(self):
        super().__init__(timeout=86400)
        self.icons: Dict[str, io.BytesIO] = {}

        self.games: Dict[str, Dict[str, io.BytesIO]] = defaultdict(dict)

    @discord.ui.button(label="League gamer", style=discord.ButtonStyle.green)
    async def button_callback_league(self, interaction, _):
        await game_button_callback(self, interaction, _, LEAGUE_GAME_KEY)

    @discord.ui.button(label="Apex gamer", style=discord.ButtonStyle.blurple)
    async def button_callback_apex(self, interaction, _):
        await game_button_callback(self, interaction, _, APEX_GAME_KEY)

    async def on_timeout(self) -> None:
        return await super().on_timeout()


async def create_board(message):
    (files, embed) = create_party_embed("Gamers", "Sign up", thumbnail=True)

    view = GameView()

    await message.channel.send(files=files, embed=embed, view=view)


def create_party_embed(
    title: str,
    description: str,
    thumbnail: bool = False,
    icons: Optional[Dict[str, io.BytesIO]] = None,
    games: Dict[str, Dict[str, io.BytesIO]] = None,
) -> discord.Embed:

    embed = discord.Embed(title=title, description=description)
    file_attachments = []

    if thumbnail:
        embed.set_thumbnail(url=THUMBNAIL_ATTACHMENT_URL)
        file_attachments.append(discord.File(THUMBNAIL_IMAGE, filename="thumbnail.png"))

    # if icons:
    file = generate_image(icons, games)
    embed.set_image(url=BACKGROUND_ATTACHMENT_URL)

    file_attachments.append(file)

    return (file_attachments, embed)


def generate_image(
    icons: Optional[Dict[str, io.BytesIO]] = None,
    games: Dict[str, Dict[str, io.BytesIO]] = None,
) -> discord.File:

    if icons is None or len(icons) == 0:
        with Image.open(SIGNUP_BG_IMAGE) as bg:
            bg.save(SIGNUP_BG_IMAGE_UPDATED, "PNG")
            return discord.File(SIGNUP_BG_IMAGE_UPDATED, filename="background.png")

    # get the predefined background from filesystem
    background = Image.open(SIGNUP_BG_IMAGE).convert(mode="RGB")

    # get the size of the background image so that we can calcluate
    # how many icons per row with the expected padding
    canvas_width, canvas_height = background.size  # returns (width, height)

    # calculate how many icons for each row
    # given a padding of 20px and an avatar width of 75px
    padding = 40
    image_size = 200
    overlap_mask_size_increase = 1 / 8 * image_size
    x_increment = int(padding + (5 / 8) * image_size)
    img_per_row = canvas_width / (image_size * padding)
    x_starting_value = 2 * padding + image_size

    games = {
        name: [Image.open(icon) for icon in players.values()]
        for name, players in games.items()
    }

    # create image objects for each avatar
    # icons = [Image.open(icon) for icon in icons.values()]

    # now let's start placing the avatars on the canvas

    for i, (name, icons) in enumerate(games.items()):
        x = padding
        y = padding + i * (image_size + padding)

        game_icon = Image.open(os.path.join(GAME_THUMBNAILS_FOLDER, name + ".png"))
        game_icon = game_icon.resize((image_size, image_size))

        mask_im = Image.new("L", (image_size, image_size))
        draw = ImageDraw.Draw(mask_im)
        draw.ellipse((0, 0, image_size, image_size), fill=255)
        background.paste(game_icon, (x, y), mask=mask_im)

        x += padding + image_size + padding

        for icon in icons:
            # ensure size that matches image_size
            width, height = icon.size
            # image height will be (height*(new_width/width))

            is_last = icon == icons[-1]

            icon = icon.resize((image_size, image_size))

            # if there is no more room to the right to add a new image (with padding)
            # wrap to a new line
            if x + padding + image_size >= canvas_width:
                x = x_starting_value
                y = padding + 2 * height + padding

            mask_im = Image.new("L", (image_size, image_size))
            draw = ImageDraw.Draw(mask_im)
            draw.ellipse((0, 0, image_size, image_size), fill=255)
            if not is_last:
                draw.ellipse(
                    (
                        x_increment - overlap_mask_size_increase,
                        -overlap_mask_size_increase,
                        x_increment + image_size + overlap_mask_size_increase,
                        image_size + overlap_mask_size_increase,
                    ),
                    fill=0,
                )
            background.paste(icon, (x, y), mask=mask_im)

            # move the x value over to keep equal spacing between icons
            x += x_increment

    background.save(SIGNUP_BG_IMAGE_UPDATED, "PNG")
    return discord.File(SIGNUP_BG_IMAGE_UPDATED, filename="background.png")
