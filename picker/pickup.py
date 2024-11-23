import logging
import os
import asyncio
from typing import List
import pathlib
import httpx
import uuid
import json
import shutil
import tempfile
import base64
from .utils import is2XX

booru_username = os.environ["BOORU_USERNAME"]
booru_token = os.environ["BOORU_TOKEN"]
booru_api_url = os.environ.get("BOORU_API_URL", "https://moe.yuru.me/api")
pixiv_refresh_token = os.environ.get("PIXIV_REFRESH_TOKEN", None)

tmp = pathlib.Path(tempfile.mkdtemp())


async def upload_to_booru(download_path: pathlib.Path, source: str):
    token = f"{booru_username}:{booru_token}"
    headers = {
        "Authorization": f"Token {base64.b64encode(token.encode()).decode()}",
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


async def gallery_get(download_path: str, url: str):
    cmd = " ".join(
        [
            "gallery-dl",
            "--quiet",
            "--cookies-from-browser",
            "firefox",
            "--directory",
            download_path,
            url,
        ]
    )
    print(cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        logging.info(stdout.decode())
    if stderr:
        raise RuntimeError(stderr.decode())


async def pickup(url: str):
    url = (
        url.replace("fxtwitter.", "twitter.")
        .replace("vxtwitter.", "twitter.")
        .replace("fixupx.", "x.")
    )
    download_path = tmp.joinpath(str(uuid.uuid4()))
    download_path.mkdir(parents=True, exist_ok=True)
    try:
        await gallery_get(str(download_path), url)
        await upload_to_booru(download_path, url)
    finally:
        shutil.rmtree(download_path)
