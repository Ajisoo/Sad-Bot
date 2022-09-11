import datetime as dt

import requests

from globals import get_key, API_ENDPOINTS

from .apex_util import update_apex_map

async def cmd_lfg(message, args):
    apex_map = update_apex_map(dt.datetime.now())
    msg = f"apex (Current map is **{apex_map}**, ) :)"
    if apex_map == "Kings Canyon":
        msg = "not " + msg
    await message.channel.send(msg)
