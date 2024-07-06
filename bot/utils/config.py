import copy
import os
from pathlib import Path
import shutil
from typing_extensions import deprecated
import yaml
from typing import Optional, Union


class UNSET: ...


class Config:
    def __init__(self, default_to: Optional[str] = UNSET) -> None:
        self.default_to: Optional[str] = default_to
        self.data: dict = {}
        self.load()

    def update(self, data: dict) -> None:
        self.data.update(data)

    def load(self, path: str | Path = "config.yaml") -> None:
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            return
        self.update(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    def save(self, path: str | Path = "config.yaml") -> None:
        if not isinstance(path, Path):
            path = Path(path)
        path.write_bytes(yaml.dump(self.data, encoding="utf-8"))

    def gobj(self, key: str, default: Optional[dict] = UNSET) -> dict:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not UNSET else {}

    def glist(self, key: str, default: Optional[list] = None) -> list:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not UNSET else []

    def gstr(self, key: str, default: Optional[str] = UNSET) -> str:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        return default if default is not UNSET else key

    def gint(self, key: str, default: Optional[int] = UNSET) -> int:
        parts = key.rsplit(".", 1)
        child = parts[-1]
        if len(parts) == 1:
            data = self.data
        else:
            data = self.gobj(parts[0])
        if child in data:
            return data[child]
        if default is not UNSET:
            return default
        raise KeyError(key)

    def set(self, key: str, value) -> None:
        print("Setting", key, value)
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


class ConfigFile:
    def __init__(self, path: str | Path, **options) -> None:
        if not isinstance(path, Path):
            path = Path(path)
        self.path = path
        self.config = Config(**options)
        self.config.load(self.path)
        self.start_raw_hash = hash(self.path.read_text(encoding="utf-8"))
        self.start_hash = hash(yaml.dump(self.config.data))

    def save(self) -> None:
        if hash(yaml.dump(self.config.data)) == self.start_hash:
            return
        if self.path.exists() and hash(self.path.read_text(encoding="utf-8")) != self.start_raw_hash:
            self.path.with_suffix(f"{self.path.suffix}.{len(list(self.path.parent.glob(str(self.path.with_suffix('')) + '*.bak')))}.bak")
            shutil.move(self.path, self.path)
            print("Config file merge conflict, backing up to", self.path.with_suffix(f"{self.path.suffix}.bak"))
        self.config.save(self.path)

    def update(self) -> None:
        self.save()
        self.config.load(self.path)

    def get_backup(self) -> dict:
        return copy.deepcopy(self.config.data)

    def restore_backup(self, backup: dict) -> None:
        self.config.data = backup

    def __del__(self) -> None:
        self.save()

    def try_to_change(self) -> "TryChangeConfig":
        return TryChangeConfig(self)


class TryChangeConfig:
    backup: Optional[dict] = None

    def __init__(self, config_file: ConfigFile) -> None:
        self.config_file = config_file

    def __enter__(self) -> Config:
        self.backup = self.config_file.get_backup()

    def __exit__(self, exc_type, exc_value, exc_traceback) -> None:
        if exc_type:
            self.config_file.restore_backup(self.backup)


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
