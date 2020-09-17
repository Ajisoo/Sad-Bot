import discord
import random

from Franklin import *

usage = "Usage: \nttt start: Starts a new game.\nstart x: places an O in position x."
messages = {}

ttt_client = None


class TTTData:
    def __init__(self):
        self.data = list("         ")


def check_if_win(game, char):
    if game[0] == char and game[1] == char and game[2] == char: return True
    if game[3] == char and game[4] == char and game[5] == char: return True
    if game[6] == char and game[7] == char and game[8] == char: return True

    if game[0] == char and game[3] == char and game[6] == char: return True
    if game[1] == char and game[4] == char and game[7] == char: return True
    if game[2] == char and game[5] == char and game[8] == char: return True

    if game[0] == char and game[4] == char and game[8] == char: return True
    if game[2] == char and game[4] == char and game[6] == char: return True

    return False


async def user_input(data, player_id, message, reaction):
    if messages.get(player_id) == message:
        if not reaction[0].isdigit(): return
        pos = int(reaction[0]) - 1
        if pos < 0 or pos > 8: return
        if data.data[pos] != ' ': return
        data.data[pos] = "o"
        if check_if_win(data.data, "o"):
            await message.edit(embed=generate_embed(message.embeds[0].title[0:-23], data))
            await remove_remaining_reactions(data.data, message)
            await message.remove_reaction(reaction, ttt_client)
            return

        await message.edit(embed=generate_embed(message.embeds[0].title[0:-23], data))
        await message.remove_reaction(reaction, ttt_client)
        i = put_random_x(data)
        await message.edit(embed=generate_embed(message.embeds[0].title[0:-23], data))
        if check_if_win(data.data, "x"):
            await remove_remaining_reactions(data.data, message)
        await message.remove_reaction(str(i + 1) + "⃣", ttt_client)


async def remove_remaining_reactions(data, message):
    for i in range(9):
        if data[i] == ' ':
            await message.remove_reaction(str(i + 1) + "⃣", ttt_client)


def put_random_x(data):
    valid = []
    for i in range(9):
        if data.data[i] == ' ': valid.append(i)
    i = random.randint(0, len(valid) - 1)
    data.data[valid[i]] = 'x'
    return valid[i]


def generate_embed(name, data):
    if check_if_win(data.data, "o"):
        embed = discord.Embed(title=name + " won!", description="", color=discord.Color.from_rgb(0, 99, 255))
    elif check_if_win(data.data, "x"):
        embed = discord.Embed(title=name + " lost!", description="", color=discord.Color.from_rgb(0, 99, 255))
    else:
        embed = discord.Embed(title=name + "'s game of Tic Tac Toe!", description="", color=discord.Color.from_rgb(0, 99, 255))
    for i in range(9):
        if data.data[i] == ' ':
            s = ":black_large_square::black_large_square::black_large_square::black_large_square::black_large_square:\n" \
                ":black_large_square::black_large_square::black_large_square::black_large_square::black_large_square:\n" \
                ":black_large_square::black_large_square::black_large_square::black_large_square::black_large_square:\n" \
                ":black_large_square::black_large_square::black_large_square::black_large_square::black_large_square:\n" \
                ":black_large_square::black_large_square::black_large_square::black_large_square::black_large_square:"
        else:
            if data.data[i] == 'x':
                s = ":red_square::red_square::red_square::red_square::red_square:\n" \
                    ":red_square::red_square::red_square::red_square::red_square:\n"\
                    ":red_square::red_square::red_square::red_square::red_square:\n" \
                    ":red_square::red_square::red_square::red_square::red_square:\n" \
                    ":red_square::red_square::red_square::red_square::red_square:"
            else:
                s = ":blue_square::blue_square::blue_square::blue_square::blue_square:\n" \
                    ":blue_square::blue_square::blue_square::blue_square::blue_square:\n"\
                    ":blue_square::blue_square::blue_square::blue_square::blue_square:\n" \
                    ":blue_square::blue_square::blue_square::blue_square::blue_square:\n" \
                    ":blue_square::blue_square::blue_square::blue_square::blue_square:"
        embed.add_field(name=str(i+1), value=s, inline=True)
    return embed


async def cmd_tictactoe(bot, client, message, args):
    global ttt_client
    ttt_client = client
    ttt_data = TTTData()
    embed = generate_embed(message.author.name, ttt_data)
    response = await message.channel.send(embed=embed)
    i = put_random_x(ttt_data)
    messages[message.author.id] = response
    reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣"]
    functions = [user_input] * 9
    Franklin(bot, response, reactions, functions, ttt_data)
    for reaction in reactions:
        await response.add_reaction(reaction)

    await response.remove_reaction(str(i+1) + "⃣", ttt_client)
    await response.edit(embed=generate_embed(message.author.name, ttt_data))
