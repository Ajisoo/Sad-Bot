from collections import defaultdict
from dataclasses import dataclass, field
import datetime as dt
from enum import IntEnum, auto
import random
import re
import string
import textwrap
import time
from typing import Optional, List, Set

import discord

from globals import (
    ADMINS,
    IN_PROD,
    BOT_NAME,
    BOT_PREFIX,
    TEST_SPAM_CHANNEL_ID,
)

MGUESS_SLEEPER_PHRASE = "happy new year sad bot"
MGUESS_SLEEPER_CONTACTS = ADMINS + [96079507659694080]

TESTING = True  # CHANGEME


if TESTING:
    MGUESS_PLAY_CHANNEL_ID = TEST_SPAM_CHANNEL_ID
else:
    MGUESS_PLAY_CHANNEL_ID = 900855182311706644


MGUESS_HINT_BLACKLISTED_ROLE_IDS = [
    900626991189987349,
    831263181279854602,
    900638682866925598,
    1049774804187750511,
    1049774857245696051,
    1049774900908412948,
    1049775005715677224,
    1049775021171691540
]

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
    ]


if TESTING:
    # MGUESS_DINGDONG_SEND_DT = dt.datetime.now().astimezone() + dt.timedelta(seconds=10)
    MGUESS_DINGDONG_SEND_DT = dt.datetime(2022, 12, 31, hour=22, minute=0, second=0).astimezone()
else:
    MGUESS_DINGDONG_SEND_DT = dt.datetime(2022, 12, 31, hour=22, minute=0, second=0).astimezone()
MGUESS_REACT_THRESH = 3
MGUESS_ALLOWED_GUESSES = 5

YEAR_START_DT = dt.datetime(2022, 1, 1, 0, 0, 0) 
YEAR_END_DT = dt.datetime(2022, 12, 31, 11, 59, 59) 

if TESTING:
    MGUESS_SUPERDRAMATIC_DELAY = 0
    MGUESS_DRAMATIC_DELAY = 0
    MGUESS_UNDRAMATIC_DELAY = 0
else:
    MGUESS_SUPERDRAMATIC_DELAY = 7
    MGUESS_DRAMATIC_DELAY = 5
    MGUESS_UNDRAMATIC_DELAY = 2

class MGuessCommands:
    NEW = "mgame"
    SKIP = "mskip"
    HINTS = "mhints"
    MESSAGE = "mmessage"
    GUESS = "mguess"
    HELP = "mhelp"

MGUESS_HELP_MESSAGE = textwrap.dedent(
    f"""
    Gather evidence to find the sender of the message (the search function is cheating)!

    To aid in your investigation, {BOT_NAME} will take the following commands:
    - `{BOT_PREFIX}{MGuessCommands.GUESS}`: Submit a guess for the sender of the message. Either their current nickname or tag is accepted (no need to ping the suspect).
    - `{BOT_PREFIX}{MGuessCommands.NEW}`: Start a new case.
    - `{BOT_PREFIX}{MGuessCommands.MESSAGE}`: Show the victim's message again.
    - `{BOT_PREFIX}{MGuessCommands.HINTS}`: Show all hints currently given.
    - `{BOT_PREFIX}{MGuessCommands.SKIP}`: Give up on the current case.
    - `{BOT_PREFIX}{MGuessCommands.HELP}`: See this message again.
    """
)

# Global state

dingdong_id = None


class MGuessHint(IntEnum):
    CHANNEL = auto()  # Channel where message was sent
    K_MSG_ENCLOSED_QUIP = auto()  # Some 'quip' that was included in the K message
    K_MSG_ENCLOSED_SPECIAL = auto()  # An emote sent in the K message
    K_MSG_DT = auto()  # Datetime that the K message was sent at
    K_REACT_FULL_LIST = auto()  # Counts and names of emotes reacted to the K message
    K_REACT_SOMEBODY = auto()  # The name and reactions applied by one person on the message
    # K_USER_MENTIONS = auto()  # Users mentioned in K
    # K_ROLE_MENTIONS = auto()  # Roles mentioned in K
    K_ROLE = auto()  # One role of the 'killer'


# order does matter since we iterate over these and short-circuit
MGUESS_QUIPS = [
    "cringe", "based", "rip", "love that for you", "lmao", "lmfao", "lol", "xd", "kk", "k", "ty",
    "wtf", "thx", "thanks", "skill issue", "fr", "he just like me", "cope", "copium", "built different",
    "sus", "amogus", "among us", "ye", "yeah", "ah", "oh", "ok", "uh", "um", "hm", "hmm",
]


def _find_quip(txt):
    for q in MGUESS_QUIPS:
        if re.search(r'\b' + q + r'\b', txt):
            return q
    return None


def _find_special(txt):
    """
    Returns the int ID of the first custom discord emoji found in txt.
    If there are none, then returns the str of the first unicode special character found.
    If there are neither kind in txt, then returns None.
    """
    # https://stackoverflow.com/questions/54859876/
    custom_emojis = re.findall(r'<:\w*:\d*>', txt)
    if len(custom_emojis) > 0:
        return int(custom_emojis[0].split(":")[2].replace(">", ""))
    # Search for special characters
    for c in txt:
        if c not in (string.ascii_letters + string.digits + string.punctuation + string.whitespace):
            return c
    return None


@dataclass
class MGuessState:
    # Truth
    victim_msg_id: Optional[int] = None
    victim_user_id: Optional[int] = None
    killer_msg_id: Optional[int] = None
    killer_user_id: Optional[int] = None
    channel_id: Optional[int] = None

    # Guess state
    game_started: bool = False
    punish_on_fail: bool = False
    guesser_user_ids: Set[int] = field(default_factory=set)
    attempts: int = 0
    given_hints: Set[int] = field(default_factory=set)
    hint_text_list: List[str] = field(default_factory=list)


curr_state = MGuessState()

async def cmd_mguess_dingdong(client):
    global dingdong_id
    chan = client.get_channel(MGUESS_PLAY_CHANNEL_ID)
    dingdong = await chan.send(textwrap.dedent(
        f"""
        \\*Ding dong, bing bong...\\*
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
    await channel.send("\\*Ding dong, dong ding\\*")
    time.sleep(MGUESS_SUPERDRAMATIC_DELAY)
    await channel.send("A body has been discovered!")
    time.sleep(MGUESS_SUPERDRAMATIC_DELAY)
    await channel.send(f"Everybody, please gather in {channel.mention}!")
    time.sleep(MGUESS_SUPERDRAMATIC_DELAY)
    await cmd_mguess_new_game(client, channel, punish_on_fail=True)
    await channel.send(MGUESS_HELP_MESSAGE)


async def cmd_mguess_help(message):
    if not await _gag_started_check(message.channel): return
    await message.channel.send(MGUESS_HELP_MESSAGE)


def _make_embed(title, msg, include_channel=True):
    embed = discord.Embed(
        title=title,
        description=msg.clean_content,
        timestamp=msg.created_at
    )
    if include_channel:
        embed.set_footer(text=f"From {msg.author.name} in #{msg.channel.name}")
    else:
        embed.set_footer(text=f"From {msg.author.name}")
    return embed


async def _try_timeout(user, seconds, reason=None):
    """discord.py claims timeout can take timedelta, but it lie."""
    until = dt.datetime.now().astimezone() + dt.timedelta(seconds=seconds)
    if not hasattr(user, "timeout"):  # discord.py version issue
        return False
    try:
        await user.timeout(until, reason=reason)
        return True
    except discord.errors.Forbidden:
        return False


async def _message_pool_exhaustive(channel):
    """Gets the channel's entire message history."""
    return [m async for m in channel.history(
        before=YEAR_END_DT,
        after=YEAR_START_DT,
    )]


async def _message_pool_after_random(channel):
    """
    Chooses a uniform random time throughout the year, then retrieves a list of 300 messages
    from after that point.

    This does not actually use the history API's `around` flag, since sparsity of messages in
    certain channels may lead to extreme mulliganing. Instead, the randomly chosen date acts as
    an upper bound to start pulling messages from.
    """
    rand_ofs_s = random.randint(0, (YEAR_END_DT - YEAR_START_DT).total_seconds())
    start_dt = YEAR_START_DT + dt.timedelta(seconds=rand_ofs_s)
    try:
        return [m async for m in channel.history(
            limit=300,
            before=YEAR_END_DT,
            after=start_dt,
            oldest_first=True,
        )]
    except ValueError:  # no messages found near then
        return []


async def _choose_fixed_message_pair(client):
    """Returns a fixed pair of (victim, killer) for testing."""
    channel = client.get_channel(486266124351307789)
    v_id = 1058653171066617937
    k_id = 1058653186262577192
    return [await channel.fetch_message(v_id), await channel.fetch_message(k_id)]


async def cmd_mguess_new_game(client, channel, punish_on_fail):
    global curr_state
    if not await _gag_started_check(channel): return
    if curr_state.game_started:
        await channel.send(
            f"A game is already in progress. Finish the current game, or"
            + f" use `{BOT_PREFIX}{MGuessCommands.SKIP}` before starting a new one."
        )
        return

    await channel.send("Starting a new mystery...")
    async def choose_random_message(victim_first):
        """
        Randomly chooses a pair of 'victim' and 'killer' messages.

        Currently, this first chooses a random channel ID, picks a random timestamp from the year,
        then retrieves the first 300 messages in the channel from after that date. A random message
        from this corpus is then chosen as the 'victim'.

        Rejected alternatives include the following:
        1. **Directly fetch all messages:** This would be too expensive on the main server.
        2. **Prefetch all messages to disk.** When the initial "ding dong bing bong" is sent,
           we can save all messages from all channels to disk and call it a day. This also has the
           advantage of letting us spare computational power to pre-filter messages by sender and
           content, thus easily skipping over images and such and removing the need to mulligan.
           However, since the bot is being run on a pi, we might not even have enough disk space
           to handle the prefetch, and it might end up being prohibitively slow.
        3. **Sample using the "around" flag.** The bot API provides an "around" flag that will
           pull all messages from near the specified timestamp. We can generate a uniform random
           timestamp between 1/1 and 12/31 (perhaps generating date/time separately to favor more
           active times of day). The problem is that in channels with sparse activity, this can
           result in an empty list of messages being returned, and may require extensive
           mulliganing, thus inflating the runtime.

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
        - Not enough messages were found in the channel at the chosen time
        """
        channel_id = random.choice(MGUESS_SOURCE_CHANNEL_IDS)
        rand_channel = client.get_channel(channel_id)
        all_messages = await _message_pool_after_random(rand_channel)
        if len(all_messages) < 2:
            return None, None
        if victim_first:
            victim_idx = random.randint(0, len(all_messages) - 1)
            v_author = all_messages[victim_idx].author
            killer_idx = None
            for i in range(victim_idx, len(all_messages)):
                if all_messages[i].author != v_author:
                    killer_idx = i
                    break
        else:
            killer_idx = random.randint(0, len(all_messages) - 1)
            k_author = all_messages[killer_idx].author
            victim_idx = None
            for i in range(killer_idx - 1, -1, -1):
                if all_messages[i].author != k_author:
                    victim_idx = i
                    # If killer is chosen first, then we must choose the _first_ message
                    # they sent after the victim
                    killer_idx = i + 1
                    break
        if victim_idx is None or killer_idx is None:
            return None, None
        return all_messages[victim_idx], all_messages[killer_idx]
        
    start_ts = dt.datetime.now()
    if TESTING:
        v_msg, k_msg = await _choose_fixed_message_pair(client)
        # v_msg, k_msg = await choose_random_message(False)
    else:
        v_msg, k_msg = await choose_random_message(False)
    mulligan_count = 0
    while v_msg is None:  # mulligan
        mulligan_count += 1
        v_msg, k_msg = await choose_random_message(False)
    end_ts = dt.datetime.now()
    print(
        "MGUESS: random message choice took",
        (end_ts - start_ts).total_seconds(),
        f"({mulligan_count} mulligans)"
    )
    # Some hints may not be valid for this message
    given_hints = set()
    if _find_quip(k_msg.clean_content) is None:
        given_hints.add(MGuessHint.K_MSG_ENCLOSED_QUIP)
    if _find_special(k_msg.clean_content) is None:
        given_hints.add(MGuessHint.K_MSG_ENCLOSED_SPECIAL)
    if set(r.id for r in k_msg.author.roles) - set(MGUESS_HINT_BLACKLISTED_ROLE_IDS):
        given_hints.add(MGuessHint.K_ROLE)
    curr_state = MGuessState(
        game_started=True,
        victim_msg_id=v_msg.id,
        victim_user_id=v_msg.author.id,
        killer_msg_id=k_msg.id,
        killer_user_id=k_msg.author.id,
        channel_id=v_msg.channel.id,
        punish_on_fail=punish_on_fail,
        given_hints=given_hints,
    )
    prompt_s = f"**Guess the killer (the first person to reply) with `{BOT_PREFIX}{MGuessCommands.GUESS}`!**"
    prompt_s += " Using the search function is cheating."
    if punish_on_fail:
        prompt_s += f"\nIf you find the killer in **{MGUESS_ALLOWED_GUESSES}** tries, then the killer will be timed out for **30 seconds**!"
        prompt_s += f"\nHowever, if you cannot identify the killer by then, then everyone who guessed incorrectly will be timed out instead!"
    await channel.send(prompt_s, embed=_make_embed("The victim's message:", v_msg, include_channel=False))

async def _gag_started_check(channel):
    if dingdong_id is None and dt.datetime.now().astimezone() < MGUESS_DINGDONG_SEND_DT:
        # Technically doesn't account for time between dingdong send and react thresh
        embed = discord.Embed(title="Hmm? I don't know what that means.", colour=0xFFFFFF)
        embed.set_image(url="https://static.wikia.nocookie.net/danganronpa/images/a/ad/Danganronpa_1_Monokuma_Halfbody_Sprite_11.png/revision/latest?cb=20170520215152")
        await channel.send(embed=embed)
        return False
    return True

async def _ready_check(channel):
    if not curr_state.game_started:
        await channel.send(f"No game has started yet! Begin with `{BOT_PREFIX}{MGuessCommands.NEW}`, or wait a few seconds if you just tried to start one.")
        return False
    return True

async def cmd_mguess_guess(message, args):
    channel = message.channel
    if not await _gag_started_check(channel): return
    if not await _ready_check(channel): return
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
        timed_out = await _try_timeout(message.author, 5, reason="pinging during a guessing game")
        if not timed_out:
            await channel.send(f"...or at least you would have been, if I had permission to.")
    elif len(args) == 0:
        await channel.send(textwrap.dedent(
            f"""
            Usage: `{BOT_PREFIX}{MGuessCommands.GUESS} NICKNAME_OR_USERNAME`
            To send a guess, type the person's current nickname in the server, or their username. DO NOT TAG THEM, or else.
            """
        ))
    else:
        # Check guess vs. usernames first, then nicknames
        guess = " ".join(args).strip().lower()
        try:
            idx = member_names.index(guess)
        except ValueError:
            try:
                idx = member_nicks.index(guess)
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
        time.sleep(MGUESS_DRAMATIC_DELAY)
        await channel.send("Let's give it everything we've got! It's **PUNISHMENT TIIIME!**")
        k = message.guild.get_member(curr_state.killer_user_id)
        timed_out = await _try_timeout(k, 30, reason=f"punished by {BOT_NAME}")
        time.sleep(MGUESS_DRAMATIC_DELAY)
        await channel.send(f"_{k.nick or k.name} has been timed out for 30 seconds._")
        if not timed_out:
            time.sleep(MGUESS_UNDRAMATIC_DELAY)
            await channel.send(f"...or at least they would have been if I had permissions.")
        await channel.send(f"Use `{BOT_PREFIX}{MGuessCommands.NEW}` to start a new game!")
    curr_state = MGuessState()


async def _new_hint(message):
    """
    Sends a "hint" to the channel.

    The CHANNEL hint is always given first, followed by whatever other remaining hints can be given.
    """
    channel = message.channel
    guild = message.guild
    k_msg = await guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
    if MGuessHint.CHANNEL not in curr_state.given_hints:
        new_hint_e = MGuessHint.CHANNEL
    else:
        possible_hints = list(set(MGuessHint) - set(curr_state.given_hints))
        try:
            new_hint_e = random.choice(possible_hints)
        except IndexError:
            new_hint_e = None
    curr_state.given_hints.add(new_hint_e)
    if new_hint_e == MGuessHint.CHANNEL:
        hint_s = f"The murder took place in #{k_msg.channel.name}!"
    elif new_hint_e == MGuessHint.K_MSG_ENCLOSED_QUIP:
        # If no quip was in the message, then this should have been invalidated at message choice time
        q = _find_quip(k_msg.clean_content)
        try:
            assert q is not None  # This assertion may fail if the message was edited mid-game
            hint_s = f'The murderer said "{q}" in their message!'
        except AssertionError:
            hint_s = f"The message was edited after the game started! {k_msg.author.name} is the killer, and a dirty cheater."
    elif new_hint_e == MGuessHint.K_MSG_ENCLOSED_SPECIAL:
        # If no special char was in the message, then this should have been invalidated at message choice time
        e = _find_special(k_msg.clean_content)
        try:
            assert e is not None  # This assertion may fail if the message was edited mid-game
            if isinstance(e, int):
                hint_s = f'The murderer said "{str(await guild.fetch_emoji(e))}" in their message!'
            else:
                hint_s = f'The murderer said "{e}" in their message!'
        except AssertionError:
            hint_s = f"The message was edited after the game started! {k_msg.author.name} is the killer, and a dirty cheater."
    elif new_hint_e == MGuessHint.K_MSG_DT:
        dt_formatted = k_msg.created_at.astimezone().strftime("%B %d at %I:%M %p %Z")
        hint_s = f"The murderer sent their message on {dt_formatted}!"
    elif new_hint_e == MGuessHint.K_REACT_FULL_LIST:
        # If the react list is empty, then K_REACT_SOMEBODY should also be invalidated
        reacts = k_msg.reactions
        if not reacts:
            curr_state.given_hints.add(MGuessHint.K_REACT_SOMEBODY)
            hint_s = "The murderer's message got zero reacts!"
        else:
            hint_s = "The murderer's message got these reacts: "
            hint_s += " | ".join([str(r.emoji) + "x" + str(r.count) for r in reacts])
    elif new_hint_e == MGuessHint.K_REACT_SOMEBODY:
        # If the react list is empty, then K_REACT_FULL_LIST should also be invalidated
        # This is also the case if there's only a single react to the message
        reacts = k_msg.reactions
        if not reacts:
            curr_state.given_hints.add(MGuessHint.K_REACT_FULL_LIST)
            hint_s = "The murderer's message got zero reacts!"
        else:
            # maps user obj to list of their reacts
            reacted_users = defaultdict(list)
            for r in reacts:
                async for u in r.users():
                    reacted_users[u].append(r.emoji)
            if sum(len(v) for v in reacted_users.values()) == 1:
                curr_state.given_hints.add(MGuessHint.K_REACT_FULL_LIST)
            picked_u = random.choice(list(reacted_users.keys()))
            picked_emoji = reacted_users[u]
            hint_s = f"{u.nick or u.name} put these reactions on the murderer's message: "
            hint_s += " ".join(str(e) for e in picked_emoji)
    elif new_hint_e == MGuessHint.K_ROLE:
        # If the user only has blacklisted roles, then this hint is invalidated at message choice time
        u = await guild.fetch_member(curr_state.killer_user_id)
        role_id = random.choice(list(set(r.id for r in u.roles) - set(MGUESS_HINT_BLACKLISTED_ROLE_IDS)))
        role_s = guild.get_role(role_id).name
        hint_s = f"This is one of the murderer's roles: {role_s}!"
    else:
        await channel.send("I can give no more hints :>")
        return
    curr_state.hint_text_list.append(hint_s)
    hint_lines = curr_state.hint_text_list[:-1] + ["**" + curr_state.hint_text_list[-1] + "**"]
    embed = discord.Embed(title="Hints", description="\n".join("- " + l for l in hint_lines))
    await channel.send("Here's a hint.", embed=embed)


async def cmd_mguess_hints(message):
    if not await _gag_started_check(message.channel): return
    if not await _ready_check(message.channel): return
    nothing = random.choice([
        "`None`", "`null`", "`undefined`", "Nada.", "Zilch.", "Absolutely nothing!", "???", "『　　』",
        "head empty, no hints", "The real hint was the friends we made along the way.",
        "The hint is that which cannot be named.",
    ])
    value = "\n".join("- " + l for l in curr_state.hint_text_list) if curr_state.hint_text_list else nothing
    embed = discord.Embed(title="Hints", description=value)
    embed.set_footer(text="A new hint is revealed after an incorrect guess.")
    await message.channel.send("Here's the story so far:", embed=embed)


async def cmd_mguess_message(message):
    if not await _gag_started_check(message.channel): return
    if not await _ready_check(message.channel): return
    v_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.victim_msg_id)
    await message.channel.send(
        "Here's the victim's message again.",
        embed=_make_embed("The victim's message:", v_msg, include_channel=MGuessHint.CHANNEL in curr_state.given_hints)
    )


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
            bad_msg += f"\n{u.nick or u.name}, it looks like YOU were guilty all along!"
        else:
            bad_msg += f"\n{usernames_str}, you are ALL the killers!"
        k_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
        await channel.send(bad_msg, embed=_make_embed("**In truth, here is the real killer's murderous message:**", k_msg))
        await channel.send("And that brings this trial to a close.")
        if curr_state.punish_on_fail:
            time.sleep(MGUESS_DRAMATIC_DELAY)
            await channel.send("Let's give it everything we've got! It's **PUNISHMENT TIIIME!**")
            timed_out = True
            for u in users:
                timed_out &= await _try_timeout(u, 30, reason=f"punished by {BOT_NAME}")
            time.sleep(MGUESS_DRAMATIC_DELAY)
            if len(users) == 1:
                u = users[0]
                await channel.send(f"_{u.nick or u.name} has been timed out for 30 seconds._")
            else:
                await channel.send(f"_{usernames_str} have each been timed out for 30 seconds._")
            if not timed_out:
                time.sleep(MGUESS_UNDRAMATIC_DELAY)
                await channel.send(f"...or at least they would have been if I had permissions.")
            await channel.send(f"Use `{BOT_PREFIX}{MGuessCommands.NEW}` to start a new game!")
        curr_state = MGuessState()
    else:
        if remaining_guesses == 1:
            bad_msg += " " + random.choice([
                "You've got just **1 guess** left! Better make it count.",
                "You're now on your **last guess**!",
                "You have just a **single, lonely guess** remaining.",
                "The next guess is your **final one**. You can't lose hope now!",
            ])
        else:
            bad_msg += f" **{remaining_guesses} guesses** remain."
        await channel.send(bad_msg)
        await _new_hint(message)


async def cmd_mguess_skip(message):
    global curr_state
    channel = message.channel
    if not await _gag_started_check(channel): return
    if not await _ready_check(channel): return
    k_msg = await message.guild.get_channel(curr_state.channel_id).fetch_message(curr_state.killer_msg_id)
    await channel.send("All right, fine. We're skipping this one.", embed=_make_embed("**Here's the killer's murderous message:**", k_msg))
    curr_state = MGuessState()
