import json
import logging
from typing import Optional, TypedDict

import discord


class Config(TypedDict):
    token: str
    guild_id: int
    pins_channel: int
    reaction_emoji: str
    reactions_needed: int


with open('./config.json') as f:
    config: Config = json.load(f)

already_pinned = []

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(name)s) %(message)s (%(asctime)s)')

intents = discord.Intents(reactions=True)
client = discord.Client(intents=intents)
client.logger = logging.getLogger('Discord Client')


@client.event
async def on_ready():
    client.logger.info('Client ready.')


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    global already_pinned
    client.logger.debug(payload)

    if payload.guild_id != config['guild_id'] or \
            payload.emoji.name != config['reaction_emoji']:
        return

    #! An API call for every reaction
    message: discord.Message = await client.get_partial_messageable(
        payload.channel_id, guild_id=payload.guild_id).fetch_message(payload.message_id)

    if not message:
        client.logger.warning(f'Could not get message {payload.message_id}.')
        return

    target_reaction = next(
        (x for x in message.reactions if x.emoji == config['reaction_emoji']), None)

    if target_reaction and target_reaction.count >= config['reactions_needed'] \
       and message.id not in already_pinned:

        pins_channel = client.get_partial_messageable(config['pins_channel'])
        embed = discord.Embed(description=f'{message.content}\n\n[Jump!]({message.jump_url})',
                              timestamp=message.created_at)

        author = message.author
        if type(author) is discord.Member:
            name = f'{author.nick} ({author.name})' if author.nick is not None else author.name
        else:
            # discord.User
            name = message.author.name
        embed.set_author(name=name, icon_url=author.display_avatar.url)

        if len(message.attachments) > 0:
            embed.set_image(url=message.attachments[0].url)

        await pins_channel.send(embed=embed)

        already_pinned.append(payload.message_id)
        already_pinned = already_pinned[:10]

client.run(config['token'])
