import base64
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import platform

operating = platform.system()
resourceDir: Path = Path(__file__).parent / "resource"
fontPath = Path(resourceDir) / "font.ttf"
itemhtml = """
    <div class="item">
        <img src="./{{itemtype}}/{{itemname}}">
        <div>{{item_count}}</div>
    </div>
"""


def font(size: int):
    fstr = str(fontPath)
    return ImageFont.truetype(fstr, size=size)


def jianbian(width, height, img, rad):
    gradient = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(gradient)

    start_color = (148, 89, 122)
    end_color = (204, 159, 111)

    for y in range(height):
        r = start_color[0] + (end_color[0] - start_color[0]) * y // height
        g = start_color[1] + (end_color[1] - start_color[1]) * y // height
        b = start_color[2] + (end_color[2] - start_color[2]) * y // height
        draw.line([(0, y), (width - 1, y)], fill=(r, g, b))

    gradient.paste(img, (0, 0), img)

    mask = Image.new("L", gradient.size, 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, width, height), radius=rad, fill=255)

    image = Image.new("RGBA", gradient.size, (0, 0, 0, 0),)
    image.paste(gradient, mask=mask)

    return image


def draw_icons_bg(draw, tatal_height, info: list):
    tatal_height += 20
    line = len(info) / 7
    if line < 1:
        line = 1
    else:
        line = len(info) // 7
    draw.pieslice(((20, tatal_height), (40, tatal_height + 20)), 180, 270, fill=(0, 0, 0, 192))
    draw.pieslice(((560, tatal_height), (580, tatal_height + 20)), 270, 360, fill=(0, 0, 0, 192))
    for y in range(tatal_height, tatal_height + 11):
        draw.line([(30, y), (570, y)], fill=(0, 0, 0, 192))
    for y in range(tatal_height + 10, tatal_height + 101):
        draw.line([(20, y), (580, y)], fill=(0, 0, 0, 192))
    for y in range(tatal_height + 101, (tatal_height + 101 + line * 115)):
        draw.line([(20, y), (580, y)], fill=(0, 0, 0, 128))
    ls_hight = tatal_height + 100 + line * 115
    draw.pieslice(((20, ls_hight - 10), (40, ls_hight + 10)), 90, 180, fill=(0, 0, 0, 128))
    draw.pieslice(((560, ls_hight - 10), (580, ls_hight + 10)), 0, 90, fill=(0, 0, 0, 128))
    for y in range(ls_hight, ls_hight + 11):
        draw.line([(30, y), (570, y)], fill=(0, 0, 0, 128))

    return tatal_height


def draw_icons_title(draw, tatal_height, title, tatal, avg, count, is_chara: bool = False):
    draw.rounded_rectangle((40, tatal_height + 20, 170, tatal_height + 80), 5, "#1095A5")
    tw, th = font(24).getsize(title)
    draw.text((105 - tw / 2, tatal_height + 50 - th / 2), title, font=font(22), fill="#EEEEEE")

    tw, th = font(30).getsize(f"{tatal}")
    draw.text((235 - tw / 2, tatal_height + 20), f"{tatal}", font=font(30), fill="#FFCC65")
    tw, th = font(18).getsize("总抽卡")
    draw.text((235 - tw / 2, tatal_height + 50 + 5), "总抽卡", font=font(18), fill="#EEEEEE")

    tw, th = font(30).getsize(f"{avg}")
    tw1, th1 = font(18).getsize("抽")
    draw.text((365 - (tw + tw1) / 2, tatal_height + 20), f"{avg}", font=font(30), fill="#FFCC65")
    draw.text((365 + (tw + tw1) / 2 - tw1, tatal_height + 20 + th - th1), "抽", font=font(18), fill="#FFCC65")
    if is_chara:
        tw, th = font(18).getsize("每UP角色")
        draw.text((365 - tw / 2, tatal_height + 50 + 5), "每UP角色", font=font(18), fill="#EEEEEE")
    else:
        tw, th = font(18).getsize("每金花费")
        draw.text((365 - tw / 2, tatal_height + 50 + 5), "每金花费", font=font(18), fill="#EEEEEE")

    if is_chara:
        tw, th = font(30).getsize(f"{count}%")
        draw.text((495 - tw / 2, tatal_height + 20), f"{count}%", font=font(30), fill="#FFCC65")
        tw, th = font(18).getsize("不歪概率")
        draw.text((495 - tw / 2, tatal_height + 50 + 5), "不歪概率", font=font(18), fill="#EEEEEE")
    else:
        tw, th = font(30).getsize(f"{count}")
        draw.text((495 - tw / 2, tatal_height + 20), f"{count}", font=font(30), fill="#FFCC65")
        tw, th = font(18).getsize("五星数")
        draw.text((495 - tw / 2, tatal_height + 50 + 5), "五星数", font=font(18), fill="#EEEEEE")

    return tatal_height + 100


def draw_icons(gachaImg, draw, info, jsons, tatal_height):
    if "今汐" in jsons.keys():
        type = "character"
    else:
        type = "weapon"
    if info[0]["cost"] == 0:
        info.pop(0)
    now_width = 40
    for i in range(0, len(info)):
        ic = jsons[info[i]["name"]]
        icon = Image.open(resourceDir / f"{type}" / f"{ic}.png")
        icon = icon.resize((70, int(icon.height * (70 / icon.width))))
        bg = jianbian(icon.width, icon.height, icon, 7)
        gachaImg.paste(bg, (now_width, tatal_height + 10), bg)
        draw.rectangle((now_width, tatal_height + bg.height - 20,
                        now_width + 69, tatal_height + bg.height + 10), fill="#FFFFFF")
        tw, th = font(18).getsize(f"{info[i]['cost']}")
        draw.text((now_width + icon.width // 2 - tw // 2, tatal_height + bg.height - 15), f"{info[i]['cost']}",
                  font=font(18), fill="#444444")
        now_width += 75
        if now_width > 560:
            now_width = 40
            tatal_height += (bg.height + 20)

    line = len(info) / 7
    if line < 1:
        tatal_height = tatal_height + 125
    else:
        line = len(info) // 7
        tatal_height = tatal_height + 125 * line

    return tatal_height


def change_size(gachaImg, tatal_height):
    img = Image.new("RGBA", (gachaImg.width, tatal_height + 30), "#6CF")
    img.paste(gachaImg, (0, 0), gachaImg)
    return img


def draw(data):
    data_file = resourceDir / "data.json"
    with open(data_file, "r", encoding="utf-8") as f:
        data_json = json.load(f)

    characters = data_json["character"]
    weapons = data_json["weapon"]

    gachaImg = Image.new("RGBA", (600, 3000), "#6CF")
    draw = ImageDraw.Draw(gachaImg)

    draw.rounded_rectangle((20, 20, 580, 460), 10, "#00000088")
    tatal_height = 460

    draw.text((40, 40), "特征码：", font=font(30), fill="#FFFFFF")
    draw.text((146, 40), data["uid"], font=font(30), fill="#FFCC65")
    draw.text((40, 95), "经分析，你的抽卡欧皇程度为：", font=font(24), fill="#EEEEEE")
    draw.text((40, 160), data["level"], font=font(50), fill="#FFCC65")

    if data["gechara_display"] == "block":
        icon = Image.open(resourceDir / "character" / data["gechara"])
        icon = icon.resize((135, int(icon.height * (135 / icon.width))))
        bg = jianbian(icon.width, icon.height, icon, 15)
        gachaImg.paste(bg, (420, 110), bg)
        tw, th = font(18).getsize("感恩唤取角色")
        draw.text((420 + icon.width // 2 - tw // 2, 110 + icon.height + 5), "感恩唤取角色", font=font(18), fill="#EEEEEE")

    draw.text((40, 260), "抽卡次数：", font=font(24), fill="#EEEEEE")
    draw.text((160, 254), f'{data["count"]}抽', font=font(30), fill="#FFCC65")
    draw.text((40, 310), "抽卡次数：", font=font(24), fill="#EEEEEE")
    draw.text((160, 304), f'{data["avg"]}抽', font=font(30), fill="#FFCC65")

    tw, th = font(22).getsize("小保底不歪")
    draw.text((105 - tw / 2, 410), "小保底不歪", font=font(22), fill="#EEEEEE")
    tw, th = font(22).getsize("五星数")
    draw.text((235 - tw / 2, 410), "五星数", font=font(22), fill="#EEEEEE")
    tw, th = font(22).getsize("每UP角色需")
    draw.text((365 - tw / 2, 410), "每UP角色需", font=font(22), fill="#EEEEEE")
    tw, th = font(22).getsize("每UP武器需")
    draw.text((495 - tw / 2, 410), "每UP武器需", font=font(22), fill="#EEEEEE")

    tw, th = font(30).getsize(f"{data['xbd']}%")
    draw.text((105 - tw / 2, 370), f"{data['xbd']}%", font=font(30), fill="#FFCC65")
    tw, th = font(30).getsize(f"{data['wx']}金")
    draw.text((235 - tw / 2, 370), f"{data['wx']}金", font=font(30), fill="#FFCC65")
    tw, th = font(30).getsize(f"{data['jspj']}抽")
    draw.text((365 - tw / 2, 370), f"{data['jspj']}抽", font=font(30), fill="#FFCC65")
    tw, th = font(30).getsize(f"{data['wqpj']}抽")
    draw.text((495 - tw / 2, 370), f"{data['wqpj']}抽", font=font(30), fill="#FFCC65")

    if data["chara_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["chara_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "角色池",
                         data["chara_count"], data["chara_avg"], data["xbd"], True)
        tatal_height = draw_icons(gachaImg, draw, data["chara_info"], characters, tatal_height)

    if data["weapon_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["weapon_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "武器池",
                         data["weapon_count"], data["weapon_avg"], data["weapon_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["weapon_info"], weapons, tatal_height)

    if data["czjs_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["czjs_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "常驻角色",
                         data["czjs_count"], data["czjs_avg"], data["czjs_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["czjs_info"], characters, tatal_height)

    if data["czwq_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["czwq_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "常驻武器",
                         data["czwq_count"], data["czwq_avg"], data["czwq_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["czwq_info"], weapons, tatal_height)

    if data["xsc_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["xsc_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "新手池",
                         data["xsc_count"], data["xsc_avg"], data["xsc_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["xsc_info"], characters, tatal_height)

    if data["zxc_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["xsc_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "新手自选",
                         data["zxc_count"], data["zxc_avg"], data["zxc_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["zxc_info"], weapons, tatal_height)

    gachaImg = change_size(gachaImg, tatal_height)

    screenshot_path = resourceDir / "out.png"
    gachaImg.save(screenshot_path)

    return screenshot_path

# if __name__ == "__main__":
#     with open("./gachalogs/cache-113107089.json", "r", encoding="utf-8") as f:
#         data = json.load(f)
#     draw(data)

