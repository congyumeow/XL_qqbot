<!-- markdownlint-disable MD033 MD041 -->
<div align=center>

<img width="285" height="285" src="./icon.jpg" alt="jibril_bot"/>

</div>

<div align=center>

<a href="https://www.python.org">
    <img src="https://img.shields.io/badge/Python-3.10%20%7c%203.11-blue" alt="python" />
</a>
<a  href="https://nonebot.dev/">
    <img src="https://img.shields.io/badge/nontbot-v2.3.2-EA5252" alt="nonebot" />
</a>
<a href="https://bot.q.qq.com/wiki/">
  <img src="https://img.shields.io/badge/QQ-Bot-lightgrey?style=social&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMTIuODIgMTMwLjg5Ij48ZyBkYXRhLW5hbWU9IuWbvuWxgiAyIj48ZyBkYXRhLW5hbWU9IuWbvuWxgiAxIj48cGF0aCBkPSJNNTUuNjMgMTMwLjhjLTcgMC0xMy45LjA4LTIwLjg2IDAtMTkuMTUtLjI1LTMxLjcxLTExLjQtMzQuMjItMzAuMy00LjA3LTMwLjY2IDE0LjkzLTU5LjIgNDQuODMtNjYuNjQgMi0uNTEgNS4yMS0uMzEgNS4yMS0xLjYzIDAtMi4xMy4xNC0yLjEzLjE0LTUuNTcgMC0uODktMS4zLTEuNDYtMi4yMi0yLjMxLTYuNzMtNi4yMy03LjY3LTEzLjQxLTEtMjAuMTggNS40LTUuNTIgMTEuODctNS40IDE3LjgtLjU5IDYuNDkgNS4yNiA2LjMxIDEzLjA4LS44NiAyMS0uNjguNzQtMS43OCAxLjYtMS43OCAyLjY3djQuMjFjMCAxLjM1IDIuMiAxLjYyIDQuNzkgMi4zNSAzMS4wOSA4LjY1IDQ4LjE3IDM0LjEzIDQ1IDY2LjM3LTEuNzYgMTguMTUtMTQuNTYgMzAuMjMtMzIuNyAzMC42My04LjAyLjE5LTE2LjA3LS4wMS0yNC4xMy0uMDF6IiBmaWxsPSIjMDI5OWZlIi8+PHBhdGggZD0iTTMxLjQ2IDExOC4zOGMtMTAuNS0uNjktMTYuOC02Ljg2LTE4LjM4LTE3LjI3LTMtMTkuNDIgMi43OC0zNS44NiAxOC40Ni00Ny44MyAxNC4xNi0xMC44IDI5Ljg3LTEyIDQ1LjM4LTMuMTkgMTcuMjUgOS44NCAyNC41OSAyNS44MSAyNCA0NS4yOS0uNDkgMTUuOS04LjQyIDIzLjE0LTI0LjM4IDIzLjUtNi41OS4xNC0xMy4xOSAwLTE5Ljc5IDAiIGZpbGw9IiNmZWZlZmUiLz48cGF0aCBkPSJNNDYuMDUgNzkuNThjLjA5IDUgLjIzIDkuODItNyA5Ljc3LTcuODItLjA2LTYuMS01LjY5LTYuMjQtMTAuMTktLjE1LTQuODItLjczLTEwIDYuNzMtOS44NHM2LjM3IDUuNTUgNi41MSAxMC4yNnoiIGZpbGw9IiMxMDlmZmUiLz48cGF0aCBkPSJNODAuMjcgNzkuMjdjLS41MyAzLjkxIDEuNzUgOS42NC01Ljg4IDEwLTcuNDcuMzctNi44MS00LjgyLTYuNjEtOS41LjItNC4zMi0xLjgzLTEwIDUuNzgtMTAuNDJzNi41OSA0Ljg5IDYuNzEgOS45MnoiIGZpbGw9IiMwODljZmUiLz48L2c+PC9nPjwvc3ZnPg==" alt="QQ">
</a>

</div>

<div align=center>

## 吉普莉尔 Bot

</div>

## 简介

本机器人通过[adapter-qq](https://github.com/nonebot/adapter-qq)进行连接与测试

## 部署

```bash
# 获取代码
git clone https://github.com/congyumeow/XL_qqbot.git

# 进入目录
cd xl_qqbot

# 安装依赖
pip install nonebot-adapter-qq nonebot-plugin-apscheduler PyMySQL tinydb openai pillow==9.5.0
```
修改机器人配置文件[.env.dev](.env.dev)中`QQ_BOTS`的`id`、`token`、`secret`属性，获取方式查看机器人[开发管理](https://q.qq.com/qqbot/#/developer/developer-setting)页面,具体详情参考[adapter-qq](https://github.com/nonebot/adapter-qq)
```bash
# 启动
python bot.py
```

## 功能列表

### 对话
机器人接入deepseek-r1模型,需在[config.py](./src/plugins/nonebot_plugin_ds/config.py)中配置[deepseek](https://platform.deepseek.com)密钥
- at机器人+想要说的话

### 今日运势
- 今日运势

### 天气
需在天气插件[__init__.py](./src/plugins/nonebot_plugin_weather/__init__.py)文件中配置[openapi](https://openweathermap.org/api)密钥
- 天气 [城市名]
- 国内城市名用中文，其余城市名用英文

### 鸣潮、崩铁抽卡记录分析
- 绑定鸣潮/崩铁角色
- 鸣潮/崩铁抽卡记录
- 补充鸣潮/崩铁抽卡记录
鸣潮需提供UID、record_id,获取方式通过指令“鸣潮抽卡记录帮助”查看
崩铁需提供UID、抽卡链接

### RPG小游戏
- 游戏菜单查看游戏相关指令

