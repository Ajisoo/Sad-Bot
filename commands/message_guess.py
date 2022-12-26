from dataclasses import dataclass, field
import datetime as dt
import random
import textwrap
from typing import Optional

import discord

from globals import (
    IN_PROD,
    BOT_NAME,
    BOT_PREFIX,
    TEST_SPAM_CHANNEL_ID,
)

MGUESS_PLAY_CHANNEL_ID = TEST_SPAM_CHANNEL_ID

# these are secret!
if IN_PROD:
    MGUESS_SOURCE_CHANNEL_IDS = [
        838967989100347392,
        773680929863761941,
        837192973983678484,
        851536811293540362,
        1025186502977789952,
        1023454274883178518,
        779175987786940467,
        900855182311706644,
    ]
else:
    MGUESS_SOURCE_CHANNEL_IDS = [
        486266124351307789,
        834817573748605009,
        756665510900531222,
    ]

# CHANGEME
MGUESS_DINGDONG_SEND_DT = dt.datetime(2022, 12, 25, hour=21, minute=28, second=0)
MGUESS_REACT_THRESH = 1

class MGuessCommands:
    NEW = "mgame"
    SKIP = "mskip"
    HINT = "mhint"
    GUESS = "mguess"

MGUESS_HELP_MESSAGE = textwrap.dedent(
    f"""
    Gather evidence to find the sender of the message (the search function is cheating)!

    To aid in your investigation, {BOT_NAME} will take the following commands:
    - `{BOT_PREFIX}{MGuessCommands.NEW}`: Start a new case, or review the facts of the current case.
    - `{BOT_PREFIX}{MGuessCommands.HINT}`: Get a new hint about the case.
    - `{BOT_PREFIX}{MGuessCommands.GUESS}`: Submit a guess for the sender of the message. Either their current nickname or tag is accepted (no need to ping the suspect).
    - `{BOT_PREFIX}{MGuessCommands.SKIP}`: Give up on the current case. If you issue this command, _you_ will be named the blackened!
    """
)

MGUESS_ALLOWED_GUESSES = 1

# Global state

dingdong_id = None

@dataclass
class MGuessState:
    # Truth
    victim_msg_id: Optional[int] = None
    victim_user_id: Optional[int] = None
    killer_msg_id: Optional[int] = None
    killer_user_id: Optional[int] = None
    channel_id: Optional[int] = None

    # Guess state
    punish_on_fail: bool = False
    guesser_user_ids: set = field(default_factory=set)
    attempts: int = 0
    hinted_channel: bool = False
    hinted_sender_msg: bool = False

curr_state = MGuessState()

async def cmd_mguess_dingdong(client):
    global dingdong_id
    chan = client.get_channel(MGUESS_PLAY_CHANNEL_ID)
    dingdong = await chan.send(textwrap.dedent(
        f"""
        Ding dong bing bong...
        Mm, ahem,
        This is a channel announcement. It is now {dt.datetime.now().strftime("%I%p")}.
        As such, it is officially **nighttime**.
        Happy New Year! Good night, sleep tight, and don't let the bedbugs bite!
        """
    ))
    dingdong_id = dingdong.id


async def cmd_mguess_first_new_game(client, channel):
    """
    Sends messages initiating the first guessing game. This is triggered
    when three people react to the initial "dingdong" message.
    """
    # await channel.send("\\*Ding dong dong ding\\*")
    # time.sleep(5)
    # await channel.send("A body has been discovered!")
    # time.sleep(5)
    # await channel.send(f"Everybody, please gather in {channel.mention}!")
    await cmd_mguess_new_game(client, channel, punish_on_fail=True)


def _make_embed(title, msg):
    embed = discord.Embed(
        title=title,
        description=msg.clean_content,
        timestamp=msg.created_at,
    )
    embed.set_footer(text=f"From {msg.author.nick or msg.author.name} in #{msg.channel.name}")
    return embed


async def _try_timeout(user, seconds, reason=None):
    """discord.py claims timeout can take timedelta, but it lie."""
    until = dt.datetime.now().astimezone() + dt.timedelta(seconds=seconds)
    try:
        await user.timeout(until, reason=reason)
        return True
    except discord.errors.Forbidden:
        return False


async def cmd_mguess_new_game(client, channel, punish_on_fail):
    global curr_state
    await channel.send("starting new game")
    async def choose_random_message():
        """
        Chooses a random message to be a 'victim.'

        Currently, this first chooses a random channel ID, retrieves all its messages within
        the past year, and then randomly picks one after consuming the entire iterator.

        This may not be feasible in production, so here's a couple possible alternatives:
        1. **Prefetch all messages to disk.** When the initial "ding dong bing bong" is sent,
           we can save all messages from all channels to disk and call it a day. This also has the
           advantage of letting us spare computational power to pre-filter messages by sender and
           content, thus easily skipping over images and such and removing the need to mulligan.
        2. **Sample using the "around" flag.** The bot API provides an "around" flag that will
           pull all messages from near the specified timestamp. We can generate a uniform random
           timestamp between 1/1 and 12/31 (perhaps generating date/time separately to favor more
           active times of day).

        TODO Extra persistent state needs to be added regardless to prevent the (unlikely) event
        of repeat messages, or at least repeated consecutive victims/killers.

        We can also further sample by choosing individuals first, rather than choosing a message.

        TODO We may need to set two different modes for choosing victim first vs. choosing killer
        first. If we choose a victim first, it may be in the middle of a string of messages from them;
        if we choose killer first, we'd need to backtrack to find the last message sent by someone
        other than them.

        Returns
        -------
        A pair of message (victim, killer), or (None, None) if this was not possible.

        Reasons for failure include:
        - Nobody else messaged the channel after the victim did,
        - The selected message was on the blacklist (e.g. unattributable remarks like "k"),
        - A message contains undisplayable content? Not sure if photos/videos are an issue.
        """
        channel_id = random.choice(MGUESS_SOURCE_CHANNEL_IDS)
        rand_channel = client.get_channel(channel_id)
        print("chose channel", channel_id, rand_channel)
        # Determine size of sample (this may get expensive)
        all_messages = [m async for m in rand_channel.history(
            before=dt.datetime(2022, 12, 31, 11, 59, 59),
            after=dt.datetime(2022, 1, 1, 0, 0, 0),
        )]
        victim_idx = random.randint(0, len(all_messages) - 1)
        v_author = all_messages[victim_idx].author
        killer_idx = None
        for i in range(victim_idx, len(all_messages)):
            if all_messages[i].author != v_author:
                killer_idx = i
                break
        if killer_idx is None:
            return None, None
        return all_messages[victim_idx], all_messages[killer_idx]
    start_ts = dt.datetime.now()
    v_msg, k_msg = await choose_random_message()
    while v_msg is None:  # mulligan
        v_msg, k_msg = await choose_random_message()
    end_ts = dt.datetime.now()
    print("*** random message choice took", (end_ts - start_ts).total_seconds())
    curr_state = MGuessState(
        victim_msg_id=v_msg.id,
        victim_user_id=v_msg.author.id,
        killer_msg_id=k_msg.id,
        killer_user_id=k_msg.author.id,
        channel_id=v_msg.channel.id,
        punish_on_fail=punish_on_fail,
    )
    prompt_s = f"**Guess the killer (the first person to reply) with `{BOT_PREFIX}{MGuessCommands.GUESS}`!**"
    prompt_s += " Using the search function is cheating."
    if punish_on_fail:
        prompt_s += f"\nIf you find the killer in **{MGUESS_ALLOWED_GUESSES}** tries, then the killer will be timed out for **30 seconds**!"
        prompt_s += f"\nHowever, if you cannot identify the killer by then, then everyone who guessed incorrectly will be timed out instead!"
    await channel.send(prompt_s, embed=_make_embed("The victim's message:", v_msg))


async def cmd_mguess_hint(message):
    ...
    channel = message.channel
    await channel.send("Too bad! That's not implemented yet.")


async def cmd_mguess_guess(message, args):
    channel = message.channel
    all_members = [m async for m in message.guild.fetch_members()]
    # Nicknames need to be space-normalized since `args` gets preprocessed
    # Pray that these are unique.
    member_nicks = [m.nick and " ".join(m.nick.split()).strip().lower() for m in all_members]
    member_names = [m.name.strip().lower() for m in all_members]
    # As funny as the below block of code would be, sometimes nicknames have spaces in them
    # if len(args) > 1:
    #     await channel.send("It looks like you tried guessing more than one name! That's a **penalty**!")
    #     await channel.send(f"{message.author.nick or message.author.name}, you have been timed out for 5 seconds.")
    #     await message.author.timeout(dt.timedelta(seconds=5))
    if len(message.mentions) > 0:
        await channel.send("I told you not to ping anyone when guessing! That's a **penalty**!")
        await channel.send(f"{message.author.nick or message.author.name}, you have been timed out for 5 seconds.")
        await _try_timeout(message.author, 5, reason="pinging during a guessing game")
    elif len(args) == 0:
        await channel.send(textwrap.dedent(
            f"""
            Usage: `{BOT_PREFIX}{MGuessCommands.GUESS} NICKNAME_OR_USERNAME`
            To send a guess, type the person's current nickname in the server, or their username. DO NOT TAG THEM, or else.
            """
        ))
    else:
        # Check guess vs. nicknames first, then usernames
        guess = " ".join(args).strip()
        try:
            idx = member_nicks.index(guess)
        except ValueError:
            try:
                idx = member_names.index(guess)
            except ValueError:
                await channel.send(f"**{guess}**? I don't know a **{guess}** in this server. Please try again.")
                return
        member = all_members[idx]
        if member.id == curr_state.killer_user_id:
            await _on_correct_guess(message, member)
        else:
            await _on_wrong_guess(message, member)

async def _on_correct_guess(message, guess_member):
    global curr_state
    guess = guess_member.nick or guess_member.name
    channel = message.channel
    gz_msg = f"**Congratulations!!!** **{guess}** was the killer. Here's the message they sent:"
    k_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
    await channel.send(gz_msg, embed=_make_embed("**The murderous message:**", k_msg))
    await channel.send("And that brings this trial to a close.")
    if curr_state.punish_on_fail:
        await channel.send("Let's give it everything we've got! It's **PUNISHMENT TIIIME!**")
        k = message.guild.get_member(curr_state.killer_user_id)
        await _try_timeout(k, 30, reason=f"punished by {BOT_NAME}")
        await channel.send(f"_{k.nick or k.name} has been timed out for 30 seconds._")
    curr_state = MGuessState()


async def _on_wrong_guess(message, guess_member):
    global curr_state
    guess = guess_member.nick or guess_member.name
    channel = message.channel
    curr_state.attempts += 1
    curr_state.guesser_user_ids.add(message.author.id)
    bad_msg = f"Shoot! Guess you were wrong. **{guess}** was _not_ the killer."
    remaining_guesses = MGUESS_ALLOWED_GUESSES - curr_state.attempts
    if remaining_guesses == 0:
        bad_msg += " " + random.choice([
            "Uh oh! You're fresh **out of guesses**!",
            "**0 guesses** remain.",
            "You've got **no more guesses** left.",
            "And that's it. I've **not a single guess** to give.",
            "Let me see how many guesses you have remaining... oh wait, it's **zero**.",
        ])
        users = [message.guild.get_member(uid) for uid in curr_state.guesser_user_ids]
        usernames_str = ", ".join(u.nick or u.name for u in users[:-1]) + ", and " + (users[-1].nick or users[-1].name)
        if len(users) == 1:
            u = users[0]
            bad_msg += f"\n{u.nick or u.name}, it looks like YOU were the killer all along!"
        else:
            bad_msg += f"\n{usernames_str}, you are ALL the killers!"
        k_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
        await channel.send(bad_msg, embed=_make_embed("**In truth, here is the real killer's murderous message:**", k_msg))
        await channel.send("And that brings this trial to a close.")
        if curr_state.punish_on_fail:
            await channel.send("Let's give it everything we've got! It's **PUNISHMENT TIIIME!**")
            for u in users:
                await _try_timeout(u, 30, reason=f"punished by {BOT_NAME}")
            if len(users) == 1:
                u = users[0]
                await channel.send(f"_{u.nick or u.name} has been timed out for 30 seconds._")
            else:
                await channel.send(f"_{usernames_str} have each been timed out for 30 seconds._")
        curr_state = MGuessState()

    else:
        if remaining_guesses == 1:
            bad_msg += " " + random.choice([
                "You've got just **1 guess** left! Better make it count.",
                "You're now on your **last guess**!",
                "You have just a **single, lonely guess** remaining.",
                "The next guess is your **final one**. You can't lose hope now!"
            ])
        else:
            bad_msg += f" **{remaining_guesses} guesses** remain."
        # TODO add hints
        await channel.send(bad_msg)

async def cmd_mguess_skip(message):
    global curr_state
    channel = message.channel
    k_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
    await channel.send("All right, fine. We're skipping this one.", embed=_make_embed("**Here's the killer's murderous message:**", k_msg))
    if curr_state.punish_on_fail:
        raise NotImplementedError()
    curr_state = MGuessState()
