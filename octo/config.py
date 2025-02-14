import json
from jellyfin import JellyfinAccount
from pathlib import Path

class Config:
    JF_ACCOUNTS:list[JellyfinAccount] = []
    CACHE_DIR:Path = Path()

    def __init__(self):
        pass

