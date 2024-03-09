import nextcord
import re


def renamed_class(cls, name):
    class Wrapper(cls):
        ...

    Wrapper.__name__ = name
    return Wrapper


def renamed_function(func, name):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.__name__ = name
    return wrapper


class BindableFunction:
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def bound(self, *args, **kwargs):
        new_bindable = self.__class__(self.func)
        new_bindable.args = args
        new_bindable.kwargs = kwargs
        return new_bindable

    def bind(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        return self
    
    def unbind(self):
        self.args = ()
        self.kwargs = {}
        return self
    
    def __repr__(self):
        return f"<BindableFunction {self.__name__} bound={self.is_bound}>"
    
    def __str__(self):
        return f"<BindableFunction {self.__name__} bound={self.is_bound}>"
    
    @property
    def is_bound(self):
        return bool(self.args or self.kwargs)
    
    @property
    def __name__(self):
        return self.func.__name__

    def __call__(self, *args, **kwargs):
        return self.func(*self.args, *args, **self.kwargs, **kwargs)


def bindable(func):
    return BindableFunction(func)


async def can_dm_user(user: nextcord.User) -> bool:
    try:
        await user.send()
    except nextcord.Forbidden:
        return False
    except nextcord.HTTPException:
        return True
    raise ValueError("Unexpected success occurred while checking if user can be DMed.")


@bindable
def format_string(string, sender=None, thisis=None, config=None, tags=None):
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
