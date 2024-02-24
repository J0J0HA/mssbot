import os
import re
import random
import dotenv
import nextcord
from nextcord.ext import commands
from nextcord.ext import tasks
from config import Config


dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

config = Config()
lang = Config(default_to="id")
tags = Config(default_to="none")

config.data = {}
lang.data = {}
tags.data = {}

config.load("config.yaml")
lang.load("language.yaml")
tags.load("tags.yaml")


intents = nextcord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True
bot = commands.Bot(intents=intents)


def format_string(string, sender=None, thisis=None):
    string = string.replace(r"@!sender", sender or "@here")

    def replace1(match):
        end = "" if match.group(2) == ">>" else " "
        if match.group(1) not in config["roles"]:
            return f"@{match.group(1)}{end}"
        return f"<@&{config['roles'][match.group(1)]}>{end}"

    string = re.sub(r"\@\&(\S*)(\s|\>\>)", replace1, string)

    def replace2(match):
        end = "" if match.group(2) == ">>" else " "
        if match.group(1) not in config["channels"]:
            return f"#{match.group(1)}{end}"
        return f"<#{config['channels'][match.group(1)]}>{end}"

    string = re.sub(r"#(\S*)(\s|\>\>)", replace2, string)

    def replace3(match):
        end = "" if match.group(2) == ">>" else " "
        if match.group(1) not in tags.data.keys():
            return f"!!{match.group(1)}{end}"
        if match.group(1) == thisis:
            return f"[...recursive]{end}"
        return format_string(tags[match.group(1)] + end, thisis=match.group(1))

    string = re.sub(r"!!(\S+?)(\s|\>\>)", replace3, string)
    return string


@tasks.loop(seconds=30)
async def update_presence():
    random_presence = random.choice(config["profile.activities"])
    if random_presence["type"] == "playing":
        await bot.change_presence(
            activity=nextcord.Game(
                name=random_presence.get(
                    "name", "mit jemandem, der die Konfiguration zerschossen hat"
                )
            )
        )
    elif random_presence["type"] == "listening":
        await bot.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.listening,
                name=random_presence.get(
                    "name", "wie jemand die Konfiguration zerschossen hat"
                ),
            )
        )
    elif random_presence["type"] == "watching":
        await bot.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name=random_presence.get(
                    "name", "jemandem, der die Konfiguration zerschossen hat"
                ),
            )
        )
    elif random_presence["type"] == "streaming":
        await bot.change_presence(
            activity=nextcord.Streaming(
                name=random_presence.get(
                    "name", "wie jemand die Konfiguration zerschossen hat"
                ),
                url=random_presence.get("url", "https://twitch.tv/JoJoJux16"),
            )
        )
    else:
        await bot.change_presence(
            activity=nextcord.Activity(
                type=nextcord.ActivityType.watching,
                name="den Typen an, der die Konfiguration zerschossen hat",
            )
        )
    random_name = random.choice(config["profile.names"])
    await bot.user.edit(username=random_name)
    random_nick = random.choice(config["profile.nicks"])
    await bot.get_guild(config["guild"]).me.edit(nick=random_nick)


@bot.event
async def on_ready():
    update_presence.start()
    print(lang["messages.system.bot-ready"].format(bot.user))


@bot.slash_command(
    description=lang["commands.announce.description"], guild_ids=[config["guild"]]
)
async def announce(
    interaction: nextcord.Interaction,
    channel: str = nextcord.SlashOption(
        "channel",
        lang["commands.announce.arguments.channel"],
        required=True,
        choices=config["commands.announce"].keys(),
    ),
    message: str = nextcord.SlashOption(
        "message", lang["commands.announce.arguments.message"], required=True
    ),
    title: str = nextcord.SlashOption(
        "title",
        lang["commands.announce.arguments.title"],
        required=False,
        default=lang["messages.announcements.default-title"],
    ),
    image: nextcord.Attachment = nextcord.SlashOption(
        "image", lang["commands.announce.arguments.image"], required=False
    ),
    thumbnail: nextcord.Attachment = nextcord.SlashOption(
        "thumbnail", lang["commands.announce.arguments.thumbnail"], required=False
    ),
    attachment1: nextcord.Attachment = nextcord.SlashOption(
        "attachment1", lang["commands.announce.arguments.attachment"], required=False
    ),
    attachment2: nextcord.Attachment = nextcord.SlashOption(
        "attachment2", lang["commands.announce.arguments.attachment"], required=False
    ),
    attachment3: nextcord.Attachment = nextcord.SlashOption(
        "attachment3", lang["commands.announce.arguments.attachment"], required=False
    ),
    attachment4: nextcord.Attachment = nextcord.SlashOption(
        "attachment4", lang["commands.announce.arguments.attachment"], required=False
    ),
):
    # Only allow if has role Admin or Updater
    if not any(
        role.id
        in (
            config["roles.admin"],
            *(
                config["roles"][roleid]
                for roleid in config["commands.announce"][channel]["allowed-senders"]
            ),
        )
        for role in interaction.user.roles
    ):
        return await interaction.response.send_message(
            lang["messages.no-permission.to-run-command"], ephemeral=True
        )
    dc_channel = bot.get_channel(
        config["channels"][config["commands.announce"][channel]["channel"]]
    )

    embed = nextcord.Embed()
    embed.title = title
    embed.description = format_string(message, sender=interaction.user.mention)
    if image:
        embed.set_image(url=image.url)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail.url)
    # embed.set_author(
    #     name=interaction.user, icon_url=interaction.user.display_avatar.url
    # )
    # embed.set_author(
    #     name=lang["messages.announcements.note-manually"],
    # )
    embed.set_footer(
        text=lang["messages.announcements.author"].format(interaction.user),
        icon_url=interaction.user.display_avatar.url,
    )
    embed.colour = nextcord.Colour.blurple()
    embed.timestamp = interaction.created_at

    await dc_channel.send(
        content=f"<@&{config['roles'][config['commands.announce'][channel]['ping-role']]}>",
        embed=embed,
        files=[
            await attachment.to_file()
            for attachment in [attachment1, attachment2, attachment3, attachment4]
            if attachment
        ],
    )

    attachemnts_count = sum(
        bool(attachment)
        for attachment in [attachment1, attachment2, attachment3, attachment4]
    )
    await interaction.response.send_message(
        lang["messages.announcements.published"].format(attachemnts_count),
        ephemeral=True,
        embed=embed,
    )


@bot.slash_command(
    description=lang["commands.editannounce.description"], guild_ids=[config["guild"]]
)
async def editannounce(
    interaction: nextcord.Interaction,
    msglink: str = nextcord.SlashOption(
        "msglink",
        lang["commands.editannounce.arguments.msglink"],
        required=True,
    ),
    message: str = nextcord.SlashOption(
        "message", lang["commands.editannounce.arguments.message"], required=False
    ),
    title: str = nextcord.SlashOption(
        "title",
        lang["commands.announce.arguments.title"],
        required=False,
    ),
):

    data = msglink.split("/")
    msgid = int(data[-1])
    channelid = int(data[-2])
    try:
        initial_message = await bot.get_channel(channelid).fetch_message(msgid)
    except nextcord.errors.ApplicationInvokeError as e:
        return await interaction.response.send_message(
            lang["messages.announcements.error"].format(e), ephemeral=True
        )

    # Only allow if has role Admin or Updater
    channel = next(
        key
        for key, value in config["commands.announce"].items()
        if config["channels"].get(value["channel"]) == channelid
    )
    if not any(
        role.id
        in (
            config["roles.admin"],
            *(
                config["roles"][roleid]
                for roleid in config["commands.announce"][channel]["allowed-senders"]
            ),
        )
        for role in interaction.user.roles
    ):
        return await interaction.response.send_message(
            lang["messages.no-permission.to-run-command"], ephemeral=True
        )

    embed = initial_message.embeds[0]
    if title:
        embed.title = title
    if message:
        embed.description = format_string(message, sender=interaction.user.mention)
    embed.set_footer(
        text=lang["messages.announcements.author_edited"].format(
            interaction.user, interaction.created_at
        ),
        icon_url=interaction.user.display_avatar.url,
    )
    embed.colour = nextcord.Colour.blurple()

    await initial_message.edit(
        content=f"<@&{config['roles'][config['commands.announce'][channel]['ping-role']]}>",
        embed=embed,
        files=initial_message.attachments,
    )

    await interaction.response.send_message(
        lang["messages.announcements.edited"].format(len(initial_message.attachments)),
        ephemeral=True,
        embed=embed,
    )


@bot.slash_command(
    description=lang["commands.reloadconfig.description"],
    guild_ids=[config["guild"]],
    name="reloadconfig",
)
async def reload_config(interaction: nextcord.Interaction):
    # Only allow if has role Admin
    if not any(role.id == config["roles.admin"] for role in interaction.user.roles):
        return await interaction.response.send_message(
            lang["messages.no-permission.to-run-command"], ephemeral=True
        )

    message = await interaction.response.send_message(
        lang["messages.reload.trying"], ephemeral=True
    )

    _config = config.data
    _lang = lang.data
    _tags = tags.data
    try:
        config.data = {}
        lang.data = {}
        tags.data = {}

        config.load("config.yaml")
        lang.load("language.yaml")
        tags.load("tags.yaml")

        if not update_presence.is_running():
            update_presence.start()

        if config["features.react-roles.message"] is None:
            rmessage = await bot.get_channel(
                config["features.react-roles.channel"]
            ).send(
                lang["messages.react-roles.default-message"]
                + "\n"
                + "\n".join(
                    f"{entry['emoji']}: {entry['description']} (<@&{entry['role']}>)"
                    for entry in config["features.react-roles.roles"]
                )
            )
            for entry in config["features.react-roles.roles"]:
                await rmessage.add_reaction(entry["emoji"])
            config["features.react-roles.message"] = rmessage.id
            config.save()
        else:
            rmessage = await bot.get_channel(
                config["features.react-roles.channel"]
            ).fetch_message(config["features.react-roles.message"])
            await rmessage.edit(
                content=lang["messages.react-roles.default-message"]
                + "\n"
                + "\n".join(
                    f"{entry['emoji']}: {entry['description']} (<@&{entry['role']}>)"
                    for entry in config["features.react-roles.roles"]
                )
            )
            for reaction in rmessage.reactions:
                if not any(
                    entry["emoji"] == reaction.emoji
                    for entry in config["features.react-roles.roles"]
                ):
                    await rmessage.clear_reaction(reaction.emoji)
            for entry in config["features.react-roles.roles"]:
                if not any(
                    reaction.emoji == entry["emoji"] for reaction in rmessage.reactions
                ):
                    await rmessage.add_reaction(entry["emoji"])
    except Exception as e:
        config.data = _config
        lang.data = _lang
        tags.data = _tags
        await message.edit(content=lang["messages.reload.failed"].format(e))
        raise e

    await message.edit(content=lang["messages.reload.success"])


async def get_tag_autocomplete(interaction: nextcord.Interaction, input_: str):
    return (tag for tag in tags.data.keys() if tag.startswith(input_))


@bot.slash_command(
    description=lang["commands.tag.description"], guild_ids=[config["guild"]]
)
async def tag(
    interaction: nextcord.Interaction,
    tag_: str = nextcord.SlashOption(
        "tag",
        lang["commands.tag.arguments.tag"],
        required=True,
        autocomplete=True,
        autocomplete_callback=get_tag_autocomplete,
    ),
):
    tag_content = tags[tag_]

    if tag_content is None:
        return await interaction.response.send_message(
            lang["messages.tag.not-found"].format(tag_), ephemeral=True
        )

    if isinstance(tag_content, dict):
        embed = nextcord.Embed()
        embed.title = tag_content.get("title")
        if tag_content.get("content"):
            print(format_string(tag_content.get("content")))
        embed.description = (
            format_string(t) if (t := tag_content.get("content")) is not None else None
        )
        embed.set_footer(
            text=lang["messages.tag.author"].format(interaction.user),
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at
        embed.colour = nextcord.Colour.blurple()
        embed.set_image(url=tag_content.get("image"))
        embed.set_thumbnail(url=tag_content.get("thumbnail"))
        embed.set_author(
            name=tag_content.get("author"), icon_url=tag_content.get("author-icon")
        )

        return await interaction.response.send_message(
            (
                format_string(t)
                if (t := tag_content.get("message")) is not None
                else None
            ),
            embed=embed,
        )

    tag_content = format_string(tag_content, sender=interaction.user.mention)

    await interaction.response.send_message(tag_content)


@bot.slash_command(
    description=lang["commands.form.description"], guild_ids=[config["guild"]]
)
async def form(
    interaction: nextcord.Interaction,
    text: str = nextcord.SlashOption(
        "text",
        lang["commands.form.arguments.text"],
        required=True,
    ),
):
    text = format_string(text, sender=interaction.user.mention)
    await interaction.response.send_message(text)


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith("!f "):
        await message.reply(
            format_string(
                lang["messages.ex-f.used"].format(message.content[3:]),
                sender=message.author.mention,
            )
        )


@bot.event
async def on_join(member):
    await member.send(lang["messages.general.welcome"].format(member.mention))
    await member.guild.get_channel(config["channels.off-topic"]).send(
        lang["messages.general.join"].format(member.mention)
    )


@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.message_id == config["features.react-roles.message"]:
        message = await bot.get_channel(
            config["features.react-roles.channel"]
        ).fetch_message(config["features.react-roles.message"])
        if reaction.emoji.name not in (
            entry["emoji"] for entry in config["features.react-roles.roles"]
        ):
            return await message.remove_reaction(reaction.emoji, reaction.member)
        role = next(
            entry["role"]
            for entry in config["features.react-roles.roles"]
            if entry["emoji"] == reaction.emoji.name
        )
        dc_role = message.guild.get_role(role)
        if not any(role == roleid for roleid in reaction.member.roles):
            await reaction.member.add_roles(dc_role)


@bot.event
async def on_raw_reaction_remove(reaction):
    if reaction.message_id == config["features.react-roles.message"]:
        if reaction.emoji.name not in (
            entry["emoji"] for entry in config["features.react-roles.roles"]
        ):
            return
        role = next(
            entry["role"]
            for entry in config["features.react-roles.roles"]
            if entry["emoji"] == reaction.emoji.name
        )
        dc_role = bot.get_guild(config["guild"]).get_role(role)
        member = bot.get_guild(config["guild"]).get_member(reaction.user_id)
        await member.remove_roles(dc_role)


bot.run(BOT_TOKEN)
