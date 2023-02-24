import os
from pathlib import Path
import re
import logging
from typing import Optional
from pixivpy3 import *

api = AppPixivAPI()
refresh_token = os.environ["PIXIV_REFRESH_TOKEN"]
access_token = os.environ["PIXIV_ACCESS_TOKEN"]
api.set_auth(access_token, refresh_token)

PIXIV_PATTERN = re.compile(r"^https://www.pixiv.net/artworks/(\d+)")


def get_pixiv_id(url: str) -> Optional[str]:
    result = PIXIV_PATTERN.match(url)
    if result is None:
        return None
    return result.group(1)


def get_url(urls: dict) -> str:
    url = urls.get("original")
    if url is not None:
        return url
    url = urls.get("large")
    if url is not None:
        return url
    return urls["medium"]


def pixiv_get(download_path: Path, pixiv_id: str):
    json_result = api.illust_detail(pixiv_id)
    illust = json_result.get("illust", None)
    if illust is None:
        raise RuntimeError(f"Failed to fetch Pixiv post: {json_result}")
    print(illust.get("meta_pages", []))
    for image in illust.get("meta_pages", []):
        url = get_url(image["image_urls"])
        logging.info(f"Downloading {url}")
        api.download(url, path=str(download_path))
    else:
        url = get_url(illust["image_urls"])
        logging.info(f"Downloading {url}")
        api.download(url, path=str(download_path))
