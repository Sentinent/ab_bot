import json
import logging
from typing import TypedDict

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

logging.basicConfig(level=logging.INFO,
                    format='[%(levelname)s] (%(name)s) %(message)s (%(asctime)s)')

client = discord.Client()
client.logger = logging.getLogger('Discord Client')
intents = discord.Intents(reactions=True)


@client.event
async def on_ready():
    client.logger.info('Client ready.')


@client.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    global already_pinned

    if payload.guild_id != config['guild_id'] or \
            payload.emoji.name != config['reaction_emoji']:
        return

    guild: discord.Guild = client.get_guild(payload.guild_id)
    if not guild:
        client.logger.warning(f'Could not get guild {payload.guild_id}')
        return

    channel: discord.TextChannel = client.get_channel(payload.channel_id)
    if not channel:
        client.logger.warning(f'Could not find channel {payload.channel_id}.')
        return

    message: discord.Message = await channel.get_partial_message(payload.message_id).fetch()
    if not message:
        client.logger.warning(f'Could not get message {payload.channel_id}.')
        return

    reaction_count = sum(
        1 for reaction in message.reactions if reaction.emoji == config['reaction_emoji'])

    if reaction_count >= config['reactions_needed'] and message.id not in already_pinned:
        pins_channel: discord.TextChannel = client.get_channel(
            config['pins_channel'])

        if not pins_channel:
            client.logger.error('Could not find pins channel.')
            return

        embed = discord.Embed(description=f'{message.content}\n\n[Jump!]({message.jump_url})',
                              timestamp=message.created_at)

        author: discord.Member = payload.member
        name = f'{author.nick} ({author.name})' if author.nick is not None else author.name
        embed.set_author(name=name, icon_url=author.avatar_url)

        if len(message.attachments) > 0:
            embed.set_image(message.attachments[0].url)

        await pins_channel.send(embed=embed)

        already_pinned.append(payload.message_id)
        already_pinned = already_pinned[:10]

client.run(config['token'])
