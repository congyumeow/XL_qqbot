from pathlib import Path
from typing import Any, Dict, List, Set, Union

import httpx
import nonebot
from aiocache import cached
from nonebot import logger
from pydantic import BaseModel, Extra

try:
    import ujson as json
except ModuleNotFoundError:
    import json


class PluginConfig(BaseModel, extra=Extra.ignore):
    '''
        Path of tarot images resource
    '''
    tarot_path: Path = Path(__file__).parent / "resource"
    chain_reply: bool = True
    tarot_auto_update: bool = False
    nickname: Set[str] = {"Bot"}

    '''
        DO NOT CHANGE THIS VALUE IN ANY .ENV FILES
    '''
    tarot_official_themes: List[str] = ["BilibiliTarot", "TouhouTarot"]


driver = nonebot.get_driver()
tarot_config: PluginConfig = PluginConfig.parse_obj(
    driver.config.dict(exclude_unset=True))


class ResourceError(Exception):

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self):
        return self.msg

    __repr__ = __str__


async def download_url(name: str, is_json: bool = False) -> Union[Dict[str, Any], bytes, None]:
    url: str = "https://raw.fgit.ml/MinatoAquaCrews/nonebot_plugin_tarot/master/nonebot_plugin_tarot/" + name

    async with httpx.AsyncClient() as client:
        for i in range(3):
            try:
                response: httpx.Response = await client.get(url)
                if response.status_code != 200:
                    continue

                return response.json() if is_json else response.content

            except Exception:
                logger.warning(
                    f"Error occurred when downloading {url}, {i+1}/3")

    logger.warning("Abort downloading")
    return None


@cached(ttl=180)
async def get_tarot(_theme: str, _type: str, _name: str) -> Union[bytes, None]:
    '''
        Downloads tarot image and stores cache temporarily
        if downloading failed, return None
    '''
    logger.info(
        f"Downloading tarot image {_theme}/{_type}/{_name} from repo")

    resource: str = "resource/" + f"{_theme}/{_type}/{_name}"
    data = await download_url(resource)

    if data is None:
        logger.warning(
            f"Downloading tarot image {_theme}/{_type}/{_name} failed!")

    return data