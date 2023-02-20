#!/usr/bin/env python3
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


TWEET_PATTERN = re.compile("^https://twitter.com/[\w\d\-_]+/status/(\d+)")


def get_status_id(tweet_url: str) -> Optional[str]:
    result = TWEET_PATTERN.match(tweet_url)
    if result is None:
        return None
    return result.group(1)


async def twitter_get(download_path: str, status_id: str):
    # https://developer.twitter.com/en/docs/twitter-api/v1/data-dictionary/object-model/tweet
    tweet = api.get_status(status_id)
    async with httpx.AsyncClient() as client:
        for media in tweet.extended_entities.get("media", []):
            url = media.get("media_url_https", None)
            if url is None:
                continue
            response = await client.get(url)
            filename = url.split("/")[-1]
            with open(path.join(download_path, filename), "wb") as f:
                f.write(response.content)
