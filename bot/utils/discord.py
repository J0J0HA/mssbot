from functools import wraps

import nextcord
from conf import config, lang
from utils.config import KEY


def require_role(role: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: nextcord.Interaction, *args, **kwargs):
            if interaction.user is None:
                return await interaction.response.send_message(
                    lang.gstr(KEY.messages.no_permission.to_run_command()),
                    ephemeral=True,
                )
            if role not in [role.id for role in interaction.user.roles]:
                return await interaction.response.send_message(
                    lang.gstr(KEY.messages.no_permission.to_run_command()),
                    ephemeral=True,
                )
            return await func(interaction, *args, **kwargs)

        return wrapper

    return decorator


def require_any_role_of(*roles):
    def decorator(func):
        @wraps(func)
        async def wrapper(interaction: nextcord.Interaction, *args, **kwargs):
            if interaction.user is None:
                return await interaction.response.send_message(
                    lang.gstr(KEY.messages.no_permission.to_run_command()),
                    ephemeral=True,
                )
            if not any(role.id in roles for role in interaction.user.roles):
                return await interaction.response.send_message(
                    lang.gstr(KEY.messages.no_permission.to_run_command()),
                    ephemeral=True,
                )
            return await func(interaction, *args, **kwargs)

        return wrapper

    return decorator


def cmddef(*names):
    name = names[-1]
    return {
        "name": name,
        "description": lang.gstr(KEY.commands["-".join(names)].description()),
    }


def gcmddef(*names):
    return {"guild_ids": [config["guild"]], **cmddef(*names)}


def argdef(cmdname, name):
    return {
        "name": name,
        "description": lang.gstr(KEY.commands[cmdname].args[name].description()),
    }


async def can_dm_user(user: nextcord.User) -> bool:
    try:
        await user.send()
    except nextcord.Forbidden:
        return False
    except nextcord.HTTPException:
        return True
    raise ValueError("Unexpected success occurred while checking if user can be DMed.")
