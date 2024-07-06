import random
import nextcord
from nextcord.ext import commands
from nextcord.ext import tasks
from utils.config import KEY
from utils.discord import cmddef, argdef, gcmddef, require_role, can_dm_user
from conf import BOT_TOKEN, config, lang, tags, format_string

intents = nextcord.Intents.default()
intents.presences = True
intents.message_content = True
intents.members = True
bot = commands.Bot(intents=intents)


@tasks.loop(seconds=30)
async def update_presence():
    random_presence = random.choice(config.glist(KEY.profile.activities()))
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
    random_name = random.choice(config.glist(KEY.profile.names()))
    await bot.user.edit(username=random_name)
    random_nick = random.choice(config.glist(KEY.profile.nicks()))
    await bot.get_guild(config.gint(KEY.guild())).me.edit(nick=random_nick)


@bot.event
async def on_ready():
    print(lang.gstr(KEY.messages.system.bot_ready()).format(bot.user))
    update_presence.start()


def get_parent_cmd(name, on=bot):
    @on.slash_command(guild_ids=[config.gint(KEY.guild())], name=name)
    async def announcement(interaction: nextcord.Interaction):
        await interaction.send("That is impossible.", ephemeral=True)

    return announcement


slash_group_general = get_parent_cmd("mssbot")
slash_group_announcement = get_parent_cmd("announcement")


@slash_group_announcement.subcommand(
    **cmddef("announcement", "create"),
)
async def announce(
    interaction: nextcord.Interaction,
    channel: str = nextcord.SlashOption(
        "channel",
        lang.gstr(KEY.commands.announce.arguments.channel()),
        required=True,
        choices=config.gobj(KEY.commands.announce()).keys(),
    ),
    message: str = nextcord.SlashOption(
        "message", lang.gstr(KEY.commands.announce.arguments.message()), required=True
    ),
    title: str = nextcord.SlashOption(
        "title",
        lang.gstr(KEY.commands.announce.arguments.title()),
        required=False,
        default=lang.gstr(KEY.messages.announcements.default_title()),
    ),
    image: nextcord.Attachment = nextcord.SlashOption(
        "image", lang.gstr(KEY.commands.announce.arguments.image()), required=False
    ),
    thumbnail: nextcord.Attachment = nextcord.SlashOption(
        "thumbnail", lang.gstr(KEY.commands.announce.arguments.thumbnail()), required=False
    ),
    attachment1: nextcord.Attachment = nextcord.SlashOption(
        "attachment1", lang.gstr(KEY.commands.announce.arguments.attachment()), required=False
    ),
    attachment2: nextcord.Attachment = nextcord.SlashOption(
        "attachment2", lang.gstr(KEY.commands.announce.arguments.attachment()), required=False
    ),
    attachment3: nextcord.Attachment = nextcord.SlashOption(
        "attachment3", lang.gstr(KEY.commands.announce.arguments.attachment()), required=False
    ),
    attachment4: nextcord.Attachment = nextcord.SlashOption(
        "attachment4", lang.gstr(KEY.commands.announce.arguments.attachment()), required=False
    ),
):
    # Only allow if has role Admin or Updater
    if not any(
        role.id
        in (
            config.gint(KEY.roles.admin()),
            *(
                config.gobj(KEY.roles())[roleid]
                for roleid in config.glist(KEY.commands.announce[channel].allowed_senders())
            ),
        )
        for role in interaction.user.roles
    ):
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.no_permission.to_run_command()), ephemeral=True
        )
    dc_channel = bot.get_channel(
        config.gint(KEY.channels[config.gobj(KEY.commands.announce())[channel].channel]())
    )

    embed = nextcord.Embed()
    embed.title = title
    embed.description = format_string(message, sender=interaction.user.mention if interaction.user else None)
    if image:
        embed.set_image(url=image.url)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail.url)
    # embed.set_author(
    #     name=interaction.user, icon_url=interaction.user.display_avatar.url
    # )
    # embed.set_author(
    #     name=lang.gstr(KEY.messages.announcements.note_manually()),
    # )
    embed.set_footer(
        text=lang.gstr(KEY.messages.announcements.author()).format(interaction.user),
        icon_url=interaction.user.display_avatar.url if interaction.user else None,
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
        lang.gstr(KEY.messages.announcements.published()).format(attachemnts_count),
        ephemeral=True,
        embed=embed,
    )


@slash_group_announcement.subcommand(
    **cmddef("announcement", "edit"),
)
async def editannounce(
    interaction: nextcord.Interaction,
    msglink: str = nextcord.SlashOption(
        "msglink",
        lang.gstr(KEY.commands.editannounce.arguments.msglink()),
        required=True,
    ),
    message: str = nextcord.SlashOption(
        "message", lang.gstr(KEY.commands.editannounce.arguments.message()), required=False
    ),
    title: str = nextcord.SlashOption(
        "title",
        lang.gstr(KEY.commands.announce.arguments.title()),
        required=False,
    ),
):

    data = msglink.split("/")
    msgid = int(data[-1])
    channelid = int(data[-2])
    try:
        channel = await bot.fetch_channel(channelid)
        initial_message = await channel.fetch_message(msgid)
    except nextcord.errors.ApplicationInvokeError as e:
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.announcements.error()).format(e), ephemeral=True
        )

    # Only allow if has role Admin or Updater
    channel = next(
        key
        for key, value in config.gobj(KEY.commands.announce()).items()
        if config.gobj(KEY.channels()).get(value["channel"]) == channelid
    )
    if not any(
        role.id
        in (
            config.gint(KEY.roles.admin()),
            *(
                config.gobj(KEY.roles())[roleid]
                for roleid in config.gobj(KEY.commands.announce())[channel]["allowed-senders"]
            ),
        )
        for role in interaction.user.roles
    ):
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.no_permission.to_run_command()), ephemeral=True
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
        lang.gstr(KEY.messages.announcements.edited()).format(len(initial_message.attachments)),
        ephemeral=True,
        embed=embed,
    )


@slash_group_general.subcommand(
    **cmddef("mssbot", "reload"),
)
async def reload_config(interaction: nextcord.Interaction):
    # Only allow if has role Admin
    if not any(role.id == config.gint(KEY.roles.admin()) for role in interaction.user.roles):
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.no_permission.to_run_command()), ephemeral=True
        )

    message = await interaction.response.send_message(
        lang.gstr(KEY.messages.reload.trying()), ephemeral=True
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

        if config.gint(KEY.features.react_roles.message(), None) is None:
            rmessage = await bot.get_channel(
                config.gint(KEY.features.react_roles.channel())
            ).send(
                lang.gstr(KEY.messages.react_roles.default_message())
                + "\n"
                + "\n".join(
                    f"{entry['emoji']}: {entry['description']} (<@&{entry['role']}>)"
                    for entry in config.glist(KEY.features.react_roles.roles())
                )
            )
            for entry in config.glist(KEY.features.react_roles.roles()):
                await rmessage.add_reaction(entry["emoji"])
            config.set(KEY.features.react_roles.message(), rmessage.id)
            config.save()
        else:
            rmessage = await bot.get_channel(
                config.gint(KEY.features.react_roles.channel())
            ).fetch_message(config.gint(KEY.features.react_roles.message()))
            await rmessage.edit(
                content=lang.gstr(KEY.messages.react_roles.default_message())
                + "\n"
                + "\n".join(
                    f"{entry['emoji']}: {entry['description']} (<@&{entry['role']}>)"
                    for entry in config.glist(KEY.features.react_roles.roles())
                )
            )
            for reaction in rmessage.reactions:
                if not any(
                    entry["emoji"] == reaction.emoji
                    for entry in config.glist(KEY.features.react_roles.roles())
                ):
                    await rmessage.clear_reaction(reaction.emoji)
            for entry in config.glist(KEY.features.react_roles.roles()):
                if not any(
                    reaction.emoji == entry["emoji"] for reaction in rmessage.reactions
                ):
                    await rmessage.add_reaction(entry["emoji"])
    except Exception as e:
        config.data = _config
        lang.data = _lang
        tags.data = _tags
        await message.edit(content=lang.gstr(KEY.messages.reload.failed()).format(e))
        raise e

    await message.edit(content=lang.gstr(KEY.messages.reload.success()))


async def get_tag_autocomplete(interaction: nextcord.Interaction, input_: str):
    return (tag for tag in tags.data.keys() if tag.startswith(input_))


@bot.slash_command(
    **gcmddef("tag"),
)
async def tag(
    interaction: nextcord.Interaction,
    tag_: str = nextcord.SlashOption(
        **argdef("tag", "tag"),
        required=True,
        autocomplete=True,
        autocomplete_callback=get_tag_autocomplete,
    ),
):
    tag_content = tags.gstr(tag_)

    if tag_content is None:
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.tag.not_found()).format(tag_), ephemeral=True
        )

    if isinstance(tag_content, dict):
        embed = nextcord.Embed()
        embed.title = tag_content.get("title")
        embed.description = (
            format_string(t) if (t := tag_content.get("content")) is not None else None
        )
        embed.set_footer(
            text=lang.gstr(KEY.messages.tag.author()).format(interaction.user),
            icon_url=interaction.user.display_avatar.url,
        )
        embed.timestamp = interaction.created_at
        embed.colour = nextcord.Colour.blurple()
        embed.set_image(url=tag_content.get("image"))
        embed.set_thumbnail(url=tag_content.get("thumbnail"))
        if "author" in tag_content:
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


@slash_group_general.subcommand(
    **cmddef("mssbot", "formatmsg"),
)
async def form(
    interaction: nextcord.Interaction,
    text: str = nextcord.SlashOption(
        "text",
        lang.gstr(KEY.commands.form.arguments.text()),
        required=True,
    ),
):
    text = format_string(text, sender=interaction.user.mention)
    await interaction.response.send_message(text)


@bot.slash_command(
    **gcmddef("trust"),
)
@require_role(config.gint(KEY.roles.admin()))
async def trust(
    interaction: nextcord.Interaction,
    member: nextcord.Member = nextcord.SlashOption(
        "user",
        lang.gstr(KEY.commands.trust.arguments.member()),
        required=True,
    ),
):
    trusted_role = member.guild.get_role(config.gint(KEY.roles.trusted()))
    if trusted_role in member.roles:
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.trust.already_trusted()).format(member.mention), ephemeral=True
        )
    await member.add_roles(trusted_role)
    await interaction.response.send_message(
        lang.gstr(KEY.messages.trust.success()).format(member.mention)
    )


@bot.slash_command(
    **gcmddef("untrust"),
)
@require_role(config.gint(KEY.roles.admin()))
async def untrust(
    interaction: nextcord.Interaction,
    member: nextcord.Member = nextcord.SlashOption(
        "user",
        lang.gstr(KEY.commands.untrust.arguments.member()),
        required=True,
    ),
):
    trusted_role = member.guild.get_role(config.gint(KEY.roles.trusted()))
    if trusted_role not in member.roles:
        return await interaction.response.send_message(
            lang.gstr(KEY.messages.untrust.not_trusted()).format(member.mention), ephemeral=True
        )
    await member.remove_roles(trusted_role)
    await interaction.response.send_message(
        lang.gstr(KEY.messages.untrust.success()).format(member.mention)
    )
    
@slash_group_general.subcommand(
    **cmddef("mssbot", "stop"),
)
@require_role(config.gint(KEY.roles.admin()))
async def stop(
    interaction: nextcord.Interaction,
):
    await interaction.response.send_message(lang.gstr(KEY.messages.system.bot_stop_response()), ephemeral=True)
    await bot.close()

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.content.startswith("!f "):
        await message.reply(
            format_string(
                lang.gstr(KEY.messages.ex_f.used()).format(message.content[3:]),
                sender=message.author.mention,
            )
        )
    if message.content.startswith("!!"):
        if message.content[2:] not in tags:
            await message.reply(
                lang.gstr(KEY.messages.tag.not_found()).format(message.content[2:])
            )
            return
        if isinstance(tags[message.content[2:]], dict):
            await message.reply(
                lang.gstr(KEY.messages.tag.use_slash_command()).format(message.content[2:])
            )
            return
        await message.reply(
            tags[message.content[2:]].format(sender=message.author.mention)
        )


@bot.event
async def on_join(member):
    if can_dm_user(member):
        await member.send(lang.gstr(KEY.messages.general.welcome()).format(member.mention))
        await member.guild.get_channel(config.gint(KEY.channels.off_topic())).send(
            lang.gstr(KEY.messages.general.join()).format(member.mention)
        )
    else:
        await member.guild.get_channel(config.gint(KEY.channels.off_topic())).send(
            lang.gstr(KEY.messages.general.join_no_dm()).format(member.mention)
        )
    await member.add_roles(member.guild.get_role(config.gint(KEY.roles.new_member())))


@bot.event
async def on_raw_reaction_add(reaction):
    if reaction.message_id == config.gint(KEY.features.react_roles.message()):
        message = await bot.get_channel(
            config.gint(KEY.features.react_roles.channel())
        ).fetch_message(config.gint(KEY.features.react_roles.message()))
        if reaction.emoji.name not in (
            entry["emoji"] for entry in config.glist(KEY.features.react_roles.roles())
        ):
            return await message.remove_reaction(reaction.emoji, reaction.member)
        role = next(
            entry["role"]
            for entry in config.glist(KEY.features.react_roles.roles())
            if entry["emoji"] == reaction.emoji.name
        )
        dc_role = message.guild.get_role(role)
        if not any(role == roleid for roleid in reaction.member.roles):
            await reaction.member.add_roles(dc_role)


@bot.event
async def on_raw_reaction_remove(reaction):
    if reaction.message_id == config.gint(KEY.features.react_roles.message()):
        if reaction.emoji.name not in (
            entry["emoji"] for entry in config.glist(KEY.features.react_roles.roles())
        ):
            return
        role = next(
            entry["role"]
            for entry in config.glist(KEY.features.react_roles.roles())
            if entry["emoji"] == reaction.emoji.name
        )
        dc_role = bot.get_guild(config.glint(KEY.guild())).get_role(role)
        member = bot.get_guild(config.glint(KEY.guild())).get_member(reaction.user_id)
        await member.remove_roles(dc_role)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
