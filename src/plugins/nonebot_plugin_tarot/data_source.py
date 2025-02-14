import json
import random
from io import BytesIO
from pathlib import Path
from typing import List, Dict, Union, Tuple

from PIL import Image

from .config import tarot_config, ResourceError, get_tarot

tarot_json: Path = Path(__file__).parent / "tarot.json"


def pick_sub_types(theme: str) -> List[str]:
    '''
        Random choose a sub type of the "theme".
        If it is in official themes, all the sub types are available.
    '''
    all_sub_types: List[str] = ["MajorArcana",
                                "Cups", "Pentacles", "Sowrds", "Wands"]

    if theme == "BilibiliTarot":
        return all_sub_types

    if theme == "TouhouTarot":
        return ["MajorArcana"]

    sub_types: List[str] = [f.name for f in (
            tarot_config.tarot_path / theme).iterdir() if f.is_dir() and f.name in all_sub_types]

    return sub_types


def pick_theme() -> str:
    '''
        Random choose a theme from the union of local & official themes
    '''
    sub_themes_dir: List[str] = [
        f.name for f in tarot_config.tarot_path.iterdir() if f.is_dir()]

    if len(sub_themes_dir) > 0:
        return random.choice(list(set(sub_themes_dir).union(tarot_config.tarot_official_themes)))

    return random.choice(tarot_config.tarot_official_themes)


def random_cards(all_cards: Dict[str, Dict[str, Dict[str, Union[str, Dict[str, str]]]]],
                 theme: str,
                 num: int = 1
                 ) -> List[Dict[str, Union[str, Dict[str, str]]]]:
    '''
        Iterate the sub directory, get the subset of cards
    '''
    sub_types: List[str] = pick_sub_types(theme)
    if len(sub_types) < 1:
        raise ResourceError(f"本地塔罗牌主题 {theme} 为空！请检查资源！")
    subset: Dict[str, Dict[str, Union[str, Dict[str, str]]]] = {
        k: v for k, v in all_cards.items() if v.get("type") in sub_types
    }
    # 2. Random sample the cards according to the num
    cards_index: List[str] = random.sample(list(subset), num)
    cards_info: List[Dict[str, Union[str, Dict[str, str]]]] = [
        v for k, v in subset.items() if k in cards_index]
    return cards_info


def get_text_and_image(theme: str,
                        card_info: Dict[str,
                        Union[str, Dict[str, str]]]
                        ):
    '''
        Get a tarot image & text arrcording to the "card_info"
    '''
    _type: str = card_info.get("type")
    _name: str = card_info.get("pic")
    img_name: str = ""
    img_dir: Path = tarot_config.tarot_path / theme / _type
    # Consider the suffix of pictures
    for p in img_dir.glob(_name + ".*"):
        img_name = p.name
    if img_name == "":
        if theme in tarot_config.tarot_official_themes:
            data = get_tarot(theme, _type, _name)
            if data is None:
                return False, "图片下载出错，请重试或将资源部署本地……", None
            img: Image.Image = Image.open(BytesIO(data))
        else:
            # In user's theme, then raise ResourceError
            raise ResourceError(
                f"Tarot image {theme}/{_type}/{_name} doesn't exist! Make sure the type {_type} is complete.")
    else:
        img: Image.Image = Image.open(img_dir / img_name)
    # 3. Choose up or down
    name_cn: str = card_info.get("name_cn")
    if random.random() < 0.5:
        # 正位
        meaning: str = card_info.get("meaning").get("up")
        msg = f"「{name_cn}正位」「{meaning}」"
    else:
        meaning: str = card_info.get("meaning").get("down")
        msg = f"「{name_cn}逆位」「{meaning}」"
        img = img.rotate(180)
    buf = BytesIO()
    img.save(buf, format='png')
    return True, msg, buf


def onetime_divine():
    '''
        One-time divination.
    '''
    # 1. Pick a theme randomly
    theme: str = pick_theme()

    # 2. Get one card ONLY
    with open(tarot_json, 'r', encoding='utf-8') as f:
        content = json.load(f)
        all_cards = content.get("cards")
        card_info_list = random_cards(all_cards, theme)

    # 3. Get the text and image
    flag, msg, img = get_text_and_image(theme, card_info_list[0])

    return ("回应是" + msg, img) if flag else (msg, img)


# def switch_chain_reply(self, new_state: bool) -> None:
#     '''
#         开启/关闭全局群聊转发模式
#     '''
#     self.is_chain_reply = new_state
