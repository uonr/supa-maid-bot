#!/usr/bin/env python3
import tweepy
import os

from dotenv import load_dotenv

load_dotenv()

# https://docs.tweepy.org/en/stable/authentication.html

consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]

auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, callback="oob")
print(auth.get_authorization_url())
verifier = input("Input PIN: ")
access_token, access_token_secret = auth.get_access_token(verifier)
print(f"Access Token: {access_token}")
print(f"Access Token Secret: {access_token_secret}")
