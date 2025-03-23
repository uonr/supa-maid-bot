import logging
import os
import asyncio
from typing import List
import urllib.parse
import pathlib
import httpx
import uuid
import json
import shutil
import tempfile
import base64
from telegram import Message

booru_username = os.environ["BOORU_USERNAME"]
booru_token = os.environ["BOORU_TOKEN"]
lanraragi_url = os.environ["LANRARAGI_API_URL"]
lanraragi_token = os.environ["LANRARAGI_TOKEN"]
booru_api_url = os.environ.get("BOORU_API_URL", "https://moe.yuru.me/api")
pixiv_refresh_token = os.environ.get("PIXIV_REFRESH_TOKEN", None)


class PickupError(Exception):
    def __init__(self, message, detail=None):
        super().__init__(message)
        self.detail = detail


tmp = pathlib.Path(tempfile.mkdtemp())


async def upload_to_booru(download_path: pathlib.Path, source: str, reply: Message):
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
            if response.is_success:
                logging.info(f"Upload {source} successfully")
            else:
                target = reply.reply_to_message or reply
                error = response.json()
                if error.get("name", "") == "PostAlreadyUploadedError":
                    return
                await target.reply_text(
                    f"上传到 booru 失败了喵\n\n```\n{error}\n```",
                    parse_mode="Markdown",
                )
                raise PickupError(
                    f"Failed to upload to booru. [{response.status_code}]",
                    response.content,
                )


async def gallery_get(download_path: str, url: str, reply: Message):
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
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        logging.info(stdout.decode())
    if stderr:
        target = reply.reply_to_message or reply
        await target.reply_text(
            "Failed to download from gallery-dl\n\n```\n" + stderr.decode() + "\n```",
            parse_mode="markdown",
        )
        raise PickupError("Failed to download from gallery-dl")


async def lanraragi(reply: Message, url: str):
    api_url = f"{lanraragi_url}/download_url?url=" + urllib.parse.quote(url, safe="")
    encoded_token = base64.b64encode(lanraragi_token.encode()).decode()
    headers = {
        "Authorization": f"Bearer {encoded_token}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=headers)
        if response.status_code != 200:
            target = reply.reply_to_message or reply
            await target.reply_text(
                f"Failed to download from lanraragi. [{response.status_code}]",
            )
            raise PickupError(
                f"Failed to download from lanraragi. [{response.status_code}]",
                response.content,
            )
        response_data = response.json()
        assert type(response_data) == dict
        job_id = response_data.get("job")
        assert type(job_id) == int
        prev_text = ""
        while True:
            response = await client.get(
                f"{lanraragi_url}/minion/{job_id}/detail", headers=headers
            )
            response_data = response.json()
            logging.info(response_data)
            text = f"Downloading... {url} `{job_id}`"
            try:
                if text != prev_text:
                    await reply.edit_text(text, parse_mode="Markdown")
                prev_text = text
            except Exception as e:
                pass
            assert type(response_data) == dict
            state = response_data.get("state")
            if state == "finished":
                result = response_data.get("result", {})
                success = result.get("success", 0)
                message = result.get("message", "")
                if message == "URL already downloaded!":
                    return
                elif success == 1:
                    return
            elif state == "active":
                await asyncio.sleep(5)
                continue
            target = reply.reply_to_message or reply
            await target.reply_text(f"下载失败了喵 {url}\n\n```\n{result}\n```")
            raise PickupError(f"Failed to download to lanraragi", response.content)

async def pickup(reply: Message, url: str):
    url = (
        url.replace("fxtwitter.", "twitter.")
        .replace("vxtwitter.", "twitter.")
        .replace("fixupx.", "x.")
    )
    if url.find("e-hentai") != -1 or url.find("exhentai") != -1:
        await lanraragi(reply, url)
        return

    download_path = tmp.joinpath(str(uuid.uuid4()))
    download_path.mkdir(parents=True, exist_ok=True)
    try:
        await gallery_get(str(download_path), url, reply)
        await upload_to_booru(download_path, url, reply)
    finally:
        shutil.rmtree(download_path)
