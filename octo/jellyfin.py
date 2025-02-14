import requests
import concurrent.futures
from time import perf_counter_ns
from pathlib import Path
import os
import json
import pickle as pk
import datetime

def convert_nanoseconds_to_seconds(nanoseconds: int) -> float:
    return nanoseconds / 1_000_000_000

def get_headers(token:str=None) -> dict:
    headers = {
    'authorization': f'MediaBrowser Client="Octo", Device="Chrome", DeviceId="TW96aWxsYS81LjAgKFgxMTsgTGludXggeDg2XzY0KSBBcHBsZVdlYktpdC81MzcuMzYgKEtIVE1MLCBsaWtlIEdlY2tvKSBDaHJvbWUvMTMxLjAuMC4wIFNhZmFyaS81MzcuMzZ8MTczODE0NDMzNjc4NQ11", {'Token="'+token+'", ' if token else ''} Version="10.10.3"',
    }
    return headers

class JellyfinAccount:
    def __init__(self, server:str, username:str, password:str, token:str=None):
        self.server = server
        self.username = username
        self.password = password
        self.token = token

        if token is None:
            self.token = self.authenticate()

    def authenticate(self) -> str:
        _authentication_url = f"{self.server}/Users/AuthenticateByName"
        payload = {
            "Username": self.username,
            "Pw": self.password
        }

        response = requests.post(_authentication_url, json=payload, headers=get_headers())
        response.raise_for_status()

        return response.json()["AccessToken"]

def fetch_url(url,headers):
    try:
        response = requests.get(url, headers=headers)
        return response.json()['Items']
    except requests.RequestException as e:
        return str(e)

def fetch_all(urls, headers):
    responses = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = executor.map(lambda url: fetch_url(url, headers), urls)
        responses = list(results)
        _ = []
        for i in responses:
            _.extend(i)
            
    return _

def fetch_recording_store(jellyfin_account:JellyfinAccount, use_cache:bool=False, cache_dir:Path=None) -> list[dict]:

    if use_cache and cache_dir is None:
        raise ValueError("cache_dir must be provided if use_cache is True")

    workers = 2

    # First get number of tracks available in the server
    _first_url = f"{jellyfin_account.server}/Items?IncludeItemTypes=Audio&Recursive=true&StartIndex=0&Limit=1"
    data = requests.get(_first_url, headers=get_headers(jellyfin_account.token))
    data.raise_for_status()

    total_tracks = data.json()['TotalRecordCount']

    if use_cache:
        if os.path.exists(cache_dir / "jellyfin" / "track_store.pk"):
            with open(cache_dir / "jellyfin" / "track_store_metadata.json", "r") as f:
                track_store_metadata = json.load(f)
            
            if track_store_metadata['trackcount'] == total_tracks:
                print("Loading tracks from cache")
                return pk.load(open(cache_dir / "jellyfin" / "track_store.pk", "rb"))

    pool_size = total_tracks // workers

    fetch_urls = []

    _start_index = 0
    for i in range(workers):
        if i != workers-1:
            _limit = pool_size
        else:
            _limit = total_tracks - _start_index

        fetch_urls.append(
            _first_url.replace("StartIndex=0", f"StartIndex={_start_index}") \
                        .replace("Limit=1", f"Limit={_limit}")
        )
        _start_index+=pool_size
    
    responses = fetch_all(fetch_urls, headers=get_headers(jellyfin_account.token))

    if use_cache:
        os.makedirs(cache_dir / "jellyfin", exist_ok=True)
        pk.dump(responses, open(cache_dir / "jellyfin" / "track_store.pk", "wb"))
        json.dump({
            "trackcount": len(responses),
            "date": str(datetime.datetime.now())
        }, open(cache_dir / "jellyfin" / "track_store_metadata.json", "w"))
    return responses

