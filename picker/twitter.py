#!/usr/bin/env python3
from pathlib import Path
from typing import Optional
from os import path
import tweepy
import httpx
import re
import os

# https://docs.tweepy.org/en/stable/authentication.html
consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]
access_token = os.environ["TWITTER_ACCESS_TOKEN"]
access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]

auth = tweepy.OAuth1UserHandler(
    consumer_key, consumer_secret, access_token, access_token_secret
)

api = tweepy.API(auth)


TWEET_PATTERN = re.compile(r"^https://twitter.com/[\w\d\-_]+/status/(\d+)")


def get_status_id(tweet_url: str) -> Optional[str]:
    result = TWEET_PATTERN.match(tweet_url)
    if result is None:
        return None
    return result.group(1)


def content_type_is_video(variant):
    return variant.get("content_type", "").startswith("video/")


async def twitter_get(download_path: Path, status_id: str):
    # https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/tweet
    tweet = api.get_status(status_id)
    async with httpx.AsyncClient() as client:
        if not hasattr(tweet, "extended_entities"):
            print(tweet)
            raise RuntimeError('No "extended_entities" in tweet')

        def is_video(media):
            media_type = media.get("type", None)
            return media_type == "video" or media_type == "animated_gif"

        url_list = []
        for media in filter(is_video, tweet.extended_entities.get("media", [])):
            variants = media.get("video_info", {}).get("variants", [])
            assert isinstance(variants, list)
            if len(variants) == 0:
                raise RuntimeError("Failed retrieving video")
            variants = list(filter(content_type_is_video, variants))
            variants.sort(key=lambda x: x.get("bitrate", 0))
            url = variants[-1].get("url", None)
            if url is None:
                print(variants)
                raise RuntimeError('No "url" in variants')
            url_list.append(url)

        if len(url_list) == 0:
            for media in tweet.extended_entities.get("media", []):
                url = media.get("media_url_https", None)
                if url is None:
                    continue
                url_list.append(url)

        for url in url_list:
            response = await client.get(url)
            filename = url.split("/")[-1]
            with open(path.join(download_path, filename), "wb") as f:
                f.write(response.content)
