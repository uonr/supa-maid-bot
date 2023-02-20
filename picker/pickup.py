import logging
import os
from typing import List
import pathlib
import httpx
import uuid
import json
import shutil
from .you_get import you_get
from .twitter import get_status_id, twitter_get
from .pixiv import get_pixiv_id, pixiv_get
from .utils import is2XX

booru_token = os.environ["BOORU_TOKEN"]
booru_api_url = os.environ.get("BOORU_API_URL", "https://moe.yuru.me/api")

tmp = pathlib.Path(os.environ.get("TMP_PATH", "/tmp/supa-maid"))


async def upload_to_booru(download_path: str, source: str):
    headers = {
        "Authorization": f"Token {booru_token}",
        "Accept": "application/json",
    }

    async with httpx.AsyncClient() as client:
        metadata = {
            "tags": [],
            "safety": "safe",
            "source": source,
        }
        for file in download_path.glob("*"):
            metadata_byte = json.dumps(metadata).encode("utf-8")
            response = await client.post(
                f"{booru_api_url}/posts",
                headers=headers,
                files={
                    "metadata": metadata_byte,
                    "content": open(file, "rb"),
                },
            )
            if is2XX(response.status_code):
                logging.info(f"Upload {source} successfully")
            else:
                raise RuntimeError(
                    f"Failed to upload to booru. [{response.status_code}] {response.content}"
                )


async def pickup(url: str):
    url = url.replace("fxtwitter.", "twitter.").replace("vxtwitter.", "twitter.")
    download_path = tmp.joinpath(str(uuid.uuid4()))
    download_path.mkdir(parents=True, exist_ok=True)
    try:
        tweet_id = get_status_id(url)
        pixiv_id = get_pixiv_id(url)
        if tweet_id is not None:
            await twitter_get(download_path, tweet_id)
        elif pixiv_id is not None:
            pixiv_get(download_path, pixiv_id)
        else:
            await you_get(download_path, url)
        await upload_to_booru(download_path, url)
    finally:
        shutil.rmtree(download_path)
