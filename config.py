import os


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOURBOT_TOKEN")


CONFIG = Config()
