import os
import dotenv

from config import Config
from util import format_string


dotenv.load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

config = Config()
lang = Config(default_to="id")
tags = Config(default_to="none")

format_string.bind(config=config, tags=tags)

config.data = {}
lang.data = {}
tags.data = {}

config.load("config.yaml")
lang.load("language.yaml")
tags.load("tags.yaml")
