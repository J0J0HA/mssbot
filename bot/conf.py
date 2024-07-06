import os
import dotenv
from pathlib import Path

from utils.config import ConfigFile
from utils.general import format_string


dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


config_folder = Path("config")
config_file = ConfigFile(config_folder / "config.yaml")
lang_file = ConfigFile(config_folder / "language.yaml", default_to="id")
tags_file = ConfigFile(config_folder / "tags.yaml", default_to="none")

def reload_config():
    config_file.update()
    lang_file.update()
    tags_file.update()
    format_string.bind(config=config_file.config, tags=tags_file.config)

config = config_file.config
lang = lang_file.config
tags = tags_file.config
format_string.bind(config=config, tags=tags)
