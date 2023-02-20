import asyncio
import logging


async def you_get(download_path: str, url: str):
    cmd = " ".join(["you-get", "--no-caption", "--output-dir", str(download_path), url])
    print(cmd)
    proc = await asyncio.create_subprocess_shell(
        cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if stdout:
        logging.info(stdout.decode())
    if stderr:
        raise RuntimeError(stderr.decode())
