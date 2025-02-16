import requests
from nonebot import on_command
from nonebot.adapters.qq import Bot, Event, Message
from nonebot.params import CommandArg
from nonebot.plugin import PluginMetadata
from nonebot.log import logger
from pypinyin import pinyin, Style  # 用于将中文转换为拼音

__plugin_meta__ = PluginMetadata(
    name="weather_query",
    description="查询指定城市的实时天气信息",
    usage="指令：天气 <城市名称>",
    extra={
        "author": "congyumeow <l72221112@gmail.com>",
        "version": "v1.0.0"
    }
)

# 天气查询指令
weather = on_command("天气", priority=5, block=True)

# OpenWeatherMap API 配置
API_KEY = "API Key"  # 替换为你的API Key
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

def chinese_to_pinyin(city_name: str) -> str:
    """
    将中文城市名转换为拼音（无空格）
    """
    pinyin_list = pinyin(city_name, style=Style.NORMAL)
    return "".join([item[0] for item in pinyin_list])

@weather.handle()
async def handle_weather_query(bot: Bot, event: Event, args: Message = CommandArg()):
    city_input = args.extract_plain_text().strip()  # 用户输入的城市名
    if not city_input:
        await weather.finish("请输入城市名称，例如：天气 北京")

    # 判断是否为中文城市名
    is_chinese = any('\u4e00' <= char <= '\u9fff' for char in city_input)
    if is_chinese:
        city_api = chinese_to_pinyin(city_input)  # 转换为拼音用于API查询
    else:
        city_api = city_input  # 非中文直接使用

    # 调用天气API
    try:
        params = {
            "q": city_api,
            "appid": API_KEY,
            "units": "metric",  # 使用公制单位（摄氏度）
            "lang": "zh_cn"     # 返回中文描述
        }
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        # 检查API返回状态
        if data["cod"] != 200:
            await weather.finish(f"无法获取{city_input}的天气信息，请检查城市名称是否正确。")

        # 解析天气数据
        weather_info = data["weather"][0]["description"]  # 天气描述
        temperature = data["main"]["temp"]               # 温度
        humidity = data["main"]["humidity"]              # 湿度
        wind_speed = data["wind"]["speed"]               # 风速

        # 格式化返回消息
        message = (
            f"{city_input}的当前天气：\n"  # 使用用户输入的中文城市名
            f"天气状况：{weather_info}\n"
            f"温度：{temperature}°C\n"
            f"湿度：{humidity}%\n"
            f"风速：{wind_speed} m/s"
        )
        await bot.send(
            event=event,
            message=message,
            at_sender=False
        )

    except Exception as e:
        logger.error(f"天气查询失败：{e}")
        await weather.finish("天气查询失败，请稍后重试。")