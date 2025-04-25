import base64
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont # pillow==9.5.0
import platform

operating = platform.system()
resourceDir: Path = Path(__file__).parent / "resource"
fontPath = Path(resourceDir) / "font.ttf"


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
    if line.is_integer():
        line = int(line)
    else:
        line = len(info) // 7 + 1
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


def draw_icons_title(draw, tatal_height, title, tatal, avg, count, is_chara_or_wea: int = 1):
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
    if is_chara_or_wea == 11:
        tw, th = font(18).getsize("每UP角色")
        draw.text((365 - tw / 2, tatal_height + 50 + 5), "每UP角色", font=font(18), fill="#EEEEEE")
    elif is_chara_or_wea == 12:
        tw, th = font(18).getsize("每UP光锥")
        draw.text((365 - tw / 2, tatal_height + 50 + 5), "每UP光锥", font=font(18), fill="#EEEEEE")
    else:
        tw, th = font(18).getsize("每金花费")
        draw.text((365 - tw / 2, tatal_height + 50 + 5), "每金花费", font=font(18), fill="#EEEEEE")

    if is_chara_or_wea == 1:
        tw, th = font(30).getsize(f"{count}")
        draw.text((495 - tw / 2, tatal_height + 20), f"{count}", font=font(30), fill="#FFCC65")
        tw, th = font(18).getsize("五星数")
        draw.text((495 - tw / 2, tatal_height + 50 + 5), "五星数", font=font(18), fill="#EEEEEE")
    else:
        tw, th = font(30).getsize(f"{count}%")
        draw.text((495 - tw / 2, tatal_height + 20), f"{count}%", font=font(30), fill="#FFCC65")
        tw, th = font(18).getsize("不歪概率")
        draw.text((495 - tw / 2, tatal_height + 50 + 5), "不歪概率", font=font(18), fill="#EEEEEE")

    return tatal_height + 100


def draw_icon(chara_name):
    img = Image.new("RGBA", (376, 512))
    icon = Image.open(resourceDir / "imgs" / f'{chara_name}.png')
    fg = Image.open(resourceDir / "imgs" / 'fivestart.png')
    fg = fg.resize((376, int(fg.height * (376 / fg.width))))

    img.paste(icon, (0, 0))
    img.paste(fg, (0, -94), fg)

    return img


def draw_icons(gachaImg, draw, info, tatal_height):
    if info[0]["cost"] == 0:
        info.pop(0)
    now_width = 40
    for i in range(0, len(info)):
        if (i / 7).is_integer() and i != 0:
            now_width = 40
            tatal_height += 115
        icon = draw_icon(info[i]["name"])
        icon = icon.resize((70, int(icon.height * (70 / icon.width))))
        bg = jianbian(icon.width, icon.height, icon, 7)
        gachaImg.paste(bg, (now_width, tatal_height + 10), bg)
        draw.rectangle((now_width, tatal_height + bg.height - 20,
                        now_width + 69, tatal_height + bg.height + 10), fill="#FFFFFF")
        tw, th = font(18).getsize(f"{info[i]['cost']}")
        draw.text((now_width + icon.width // 2 - tw // 2, tatal_height + bg.height - 15), f"{info[i]['cost']}",
                  font=font(18), fill="#444444")
        now_width += 75

    tatal_height = tatal_height + 125

    return tatal_height


def change_size(gachaImg, tatal_height):
    img = Image.new("RGBA", (gachaImg.width, tatal_height + 30), "#6CF")
    img.paste(gachaImg, (0, 0), gachaImg)
    return img


def draw(data):
    gachaImg = Image.new("RGBA", (600, 3000), "#6CF")
    draw = ImageDraw.Draw(gachaImg)

    draw.rounded_rectangle((20, 20, 580, 460), 10, "#00000088")
    tatal_height = 460

    draw.text((40, 40), "特征码：", font=font(30), fill="#FFFFFF")
    draw.text((146, 40), data["uid"], font=font(30), fill="#FFCC65")
    draw.text((40, 95), "经分析，你的抽卡欧皇程度为：", font=font(24), fill="#EEEEEE")
    draw.text((40, 160), data["level"], font=font(50), fill="#FFCC65")

    if data["xsc_chara"] != "":
        icon = draw_icon(data["xsc_chara"])
        icon = icon.resize((135, int(icon.height * (135 / icon.width))))
        bg = jianbian(icon.width, icon.height, icon, 15)
        gachaImg.paste(bg, (420, 110), bg)
        tw, th = font(18).getsize(f"新手池{data['xsc_avg']}出")
        draw.text((420 + icon.width // 2 - tw // 2, 110 + icon.height + 5), f"新手池{data['xsc_avg']}出", font=font(18), fill="#EEEEEE")

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
    tw, th = font(22).getsize("每UP光锥需")
    draw.text((495 - tw / 2, 410), "每UP光锥需", font=font(22), fill="#EEEEEE")

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
                         data["chara_count"], data["chara_avg"], data["xbd"], 11)
        tatal_height = draw_icons(gachaImg, draw, data["chara_info"], tatal_height)

    if data["weapon_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["weapon_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "光锥池",
                         data["weapon_count"], data["weapon_avg"], data["weapon_bw"], 12)
        tatal_height = draw_icons(gachaImg, draw, data["weapon_info"], tatal_height)

    if data["cz_display"] == "block":
        tatal_height = draw_icons_bg(draw, tatal_height, data["cz_info"])
        tatal_height = draw_icons_title(draw, tatal_height, "常驻池",
                         data["cz_count"], data["cz_avg"], data["cz_wx"])
        tatal_height = draw_icons(gachaImg, draw, data["cz_info"], tatal_height)

    gachaImg = change_size(gachaImg, tatal_height)

    screenshot_path = resourceDir / "out.png"
    gachaImg.save(screenshot_path)

    return screenshot_path

# if __name__ == "__main__":
#     with open("gachalogs/cache-104082843.json", "r", encoding="utf-8") as f:
#         gachalogs = json.load(f)
#     draw(gachalogs)