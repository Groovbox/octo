from dataclasses import dataclass
import datetime

@dataclass
class Artist:
    id: str
    title:str
    aliases: list[str]

@dataclass
class Recording:
    id: str
    youtube_video_id: str
    title:str
    aliases: list[str]
    contributors: list[Artist]
    genre: list[str]

@dataclass
class Release:
    id: str
    title:str
    aliases: list[str]
    recordings:list[Recording]
    contributors: list[Artist]
    date: datetime.date
    cover: str
    genre: list[str]
