from typing_extensions import deprecated
import yaml
from typing import Optional, Union


class Config:
    def __init__(self, default_to: Optional[str] = None) -> None:
        self.default_to: Optional[str] = default_to
        self.data: dict = {}
        self.load()

    def update(self, data: dict) -> None:
        self.data.update(data)

    def load(self, path: str = "config.yaml") -> None:
        with open(path, "r", encoding="utf-8") as file:
            self.update(yaml.safe_load(file) or {})

    def save(self, path: str = "config.yaml") -> None:
        with open(path, "w", encoding="utf-8") as file:
            yaml.dump(self.data, file)

    def gobj(self, key: str, default: Optional[dict] = None) -> dict:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not None else {}

    def glist(self, key: str, default: Optional[list] = None) -> list:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not None else []

    def gstr(self, key: str, default: Optional[str] = None) -> str:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not None else key
    
    def gint(self, key: str, default: Optional[int] = None) -> int:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        if default is not None:
            return default
        raise KeyError(key)
    
    def set(self, key: str, value) -> None:
        parts = key.split(".")
        data = self.data
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value

    @deprecated("Use .g*-methods instead")
    def __getitem__(self, key: str) -> Union[None, dict, list, str, int, float, bool]:
        parts = key.split(".")
        data = self.data
        for part in parts:
            if part not in data:
                if self.default_to == "id":
                    return key
                elif self.default_to == "none":
                    return None
                else:
                    raise KeyError(key)
            data = data[part]
        return data

    def __setitem__(self, key, value) -> None:
        parts = key.split(".")
        data = self.data
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value

    def __delitem__(self, key) -> None:
        parts = key.split(".")
        data = self.data
        for part in parts[:-1]:
            data = data[part]
        del data[parts[-1]]

    def __contains__(self, key) -> bool:
        parts = key.split(".")
        data = self.data
        for part in parts:
            if part not in data:
                return False
            data = data[part]
        return True

    def __repr__(self) -> str:
        return f"<Config data={self.data}>"

    def __str__(self) -> str:
        return str(self.data)

    def __iter__(self) -> iter:
        return iter(self.data)

    def __len__(self) -> int:
        return len(self.data)


class Key:
    def __init__(self, key: Optional[list] = None) -> None:
        self.key = key or []

    def __getattr__(self, key: str) -> "Key":
        key = key.replace("_", "-")
        if self.key:
            return Key(self.key + [key])
        return Key([key])
    
    def __getitem__(self, key: str) -> "Key":
        return self.__getattr__(key)

    def __str__(self) -> str:
        return ".".join(self.key)
    
    def __repr__(self) -> str:
        return f"KEY.{self.key}"
    
    def __call__(self) -> str:
        return str(self)
        
KEY = Key()
