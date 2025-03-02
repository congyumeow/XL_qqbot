# 扫雷游戏插件 minesweeper.py
import random
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont
from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message, MessageSegment
from nonebot.params import CommandArg

# 游戏配置
MAP_SIZE = (9, 9)  # 横向A-I，纵向1-9
MINE_COUNT = 15
CELL_SIZE = 30
FONT_PATH = "arial.ttf"

# 颜色定义
COLORS = {
    "bg": (189, 189, 189),
    "grid": (105, 105, 105),
    "hidden": (192, 192, 192),
    "revealed": (255, 255, 255),
    "mine": (255, 0, 0),
    "flag": (0, 128, 0),
    "text": (0, 0, 0)
}

# 游戏状态存储
games = {}

# 命令注册
minesweeper = on_command("扫雷", priority=5)
dig = on_command("挖开", priority=5)
flag = on_command("标记", priority=5)
helper = on_command("帮助", priority=5)


class MineGame:
    def __init__(self):
        self.width, self.height = MAP_SIZE
        self.mines = set()
        self.revealed = set()
        self.flags = set()
        self.game_over = False
        self._generate_map()

    def _generate_map(self):
        # 生成地雷位置
        while len(self.mines) < MINE_COUNT:
            x = random.randint(0, self.width - 1)
            y = random.randint(0, self.height - 1)
            self.mines.add((x, y))

        # 生成数字提示
        self.hints = {}
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.mines:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            count += (nx, ny) in self.mines
                self.hints[(x, y)] = count

    def get_cell_state(self, x, y):
        if (x, y) in self.revealed:
            if (x, y) in self.mines:
                return "mine"
            return str(self.hints[(x, y)]) if self.hints[(x, y)] > 0 else "empty"
        if (x, y) in self.flags:
            return "flag"
        return "hidden"

    def check_win(self):
        return len(self.revealed) + len(self.mines) == self.width * self.height


def generate_map_image(game):
    img = Image.new("RGB",
                    (CELL_SIZE * (game.width + 1), CELL_SIZE * (game.height + 1)),
                    COLORS["bg"])
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 16)

    # 绘制坐标轴
    for i in range(game.width):
        text = chr(65 + i)
        x = CELL_SIZE * (i + 1) + CELL_SIZE // 2
        draw.text((x, 5), text, fill=COLORS["text"], font=font)

    for j in range(game.height):
        text = str(j + 1)
        y = CELL_SIZE * (j + 1) + CELL_SIZE // 2
        draw.text((5, y), text, fill=COLORS["text"], font=font)

    # 绘制网格
    for i in range(game.width + 1):
        x = CELL_SIZE * i
        draw.line([(x, CELL_SIZE), (x, CELL_SIZE * (game.height + 1))],
                  fill=COLORS["grid"], width=2)

    for j in range(game.height + 1):
        y = CELL_SIZE * j
        draw.line([(CELL_SIZE, y), (CELL_SIZE * (game.width + 1), y)],
                  fill=COLORS["grid"], width=2)

    # 绘制单元格
    for y in range(game.height):
        for x in range(game.width):
            state = game.get_cell_state(x, y)
            cell_x = CELL_SIZE * (x + 1) + 2
            cell_y = CELL_SIZE * (y + 1) + 2
            cell_size = CELL_SIZE - 4

            if state == "hidden":
                draw.rectangle([cell_x, cell_y, cell_x + cell_size, cell_y + cell_size],
                               fill=COLORS["hidden"])
            elif state == "flag":
                draw.rectangle([cell_x, cell_y, cell_x + cell_size, cell_y + cell_size],
                               fill=COLORS["flag"])
            elif state == "mine":
                draw.rectangle([cell_x, cell_y, cell_x + cell_size, cell_y + cell_size],
                               fill=COLORS["mine"])
            else:
                draw.rectangle([cell_x, cell_y, cell_x + cell_size, cell_y + cell_size],
                               fill=COLORS["revealed"])
                if state != "empty":
                    text = state
                    text_x = cell_x + cell_size // 2 - 5
                    text_y = cell_y + cell_size // 2 - 8
                    draw.text((text_x, text_y), text, fill=COLORS["text"], font=font)

    return img


async def send_game_image(game):
    """生成并返回图片消息"""
    img = generate_map_image(game)
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    return MessageSegment.file_image(img_bytes)


@minesweeper.handle()
async def start_game(bot: Bot, event: Event):
    user_id = event.get_user_id()
    games[user_id] = MineGame()
    image_msg = await send_game_image(games[user_id])
    await bot.send(event, "扫雷游戏开始！" + image_msg)


@dig.handle()
async def dig_cell(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    game = games.get(user_id)
    if not game:
        await bot.send(event, "请先使用【扫雷】开始游戏")
        return

    raw_coords = args.extract_plain_text().upper().split()
    errors = []
    success = 0
    exploded = False

    for coord in raw_coords:
        # 坐标格式验证
        if len(coord) < 2 or not coord[0].isalpha() or not coord[1:].isdigit():
            errors.append(f"坐标 {coord} 格式错误")
            continue

        # 坐标转换
        x = ord(coord[0]) - 65
        y = int(coord[1:]) - 1

        # 范围检查
        if not (0 <= x < game.width and 0 <= y < game.height):
            errors.append(f"坐标 {coord} 超出范围")
            continue

        # 状态检查
        if (x, y) in game.revealed:
            errors.append(f"坐标 {coord} 已经挖开")
            continue

        # 地雷检查
        if (x, y) in game.mines:
            game.game_over = True
            game.revealed.add((x, y))
            exploded = True
            break

        # 展开区域
        to_reveal = [(x, y)]
        while to_reveal:
            cx, cy = to_reveal.pop()
            if (cx, cy) in game.revealed:
                continue
            game.revealed.add((cx, cy))
            if game.hints[(cx, cy)] == 0:
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < game.width and 0 <= ny < game.height:
                            if (nx, ny) not in game.mines and (nx, ny) not in game.revealed:
                                to_reveal.append((nx, ny))
        success += 1

    # 处理结果
    if exploded:
        image_msg = await send_game_image(game)
        await bot.send(event, f"💥 在 {coord} 踩到地雷！游戏结束" + image_msg)
        del games[user_id]
        return

    if game.check_win():
        image_msg = await send_game_image(game)
        await bot.send(event, "🎉 恭喜你扫雷成功！" + image_msg)
        del games[user_id]
        return

    # 构建结果消息
    result = []
    if success > 0:
        result.append(f"成功挖开 {success} 个区域")
    if errors:
        result.append("以下坐标存在问题：\n" + "\n".join(errors))

    image_msg = await send_game_image(game)
    await bot.send(event, "\n".join(result) + image_msg)


@flag.handle()
async def flag_cell(bot: Bot, event: Event, args: Message = CommandArg()):
    user_id = event.get_user_id()
    game = games.get(user_id)
    if not game:
        await bot.send(event, "请先使用【扫雷】开始游戏")
        return

    raw_coords = args.extract_plain_text().upper().split()
    errors = []
    flagged = 0
    unflagged = 0

    for coord in raw_coords:
        # 坐标验证
        if len(coord) < 2 or not coord[0].isalpha() or not coord[1:].isdigit():
            errors.append(f"坐标 {coord} 格式错误")
            continue

        x = ord(coord[0]) - 65
        y = int(coord[1:]) - 1

        if not (0 <= x < game.width and 0 <= y < game.height):
            errors.append(f"坐标 {coord} 超出范围")
            continue

        if (x, y) in game.revealed:
            errors.append(f"坐标 {coord} 已挖开不能标记")
            continue

        # 切换标记状态
        if (x, y) in game.flags:
            game.flags.remove((x, y))
            unflagged += 1
        else:
            game.flags.add((x, y))
            flagged += 1

    # 构建结果消息
    result = []
    if flagged > 0 or unflagged > 0:
        result.append(f"新增标记 {flagged} 个，取消标记 {unflagged} 个")
    if errors:
        result.append("以下坐标存在问题：\n" + "\n".join(errors))

    image_msg = await send_game_image(game)
    await bot.send(event, "\n".join(result) + image_msg)


# 帮助信息
@helper.handle()
async def show_help(bot: Bot, event: Event):
    help_msg = """扫雷游戏指令：
🟩 扫雷 - 开始新游戏
🟦 挖开 A5 - 挖开指定坐标
🚩 标记 B3 - 标记/取消标记地雷
⚪ 地图说明：
- 灰色：未挖开
- 白色：安全区域
- 数字：周围地雷数
- 红色：地雷
- 绿色：标记"""
    await bot.send(event, help_msg)