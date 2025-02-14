import nonebot
from nonebot.adapters.qq import Adapter as QQAdapter

nonebot.init()

driver = nonebot.get_driver()
driver.register_adapter(QQAdapter)


nonebot.load_from_toml("pyproject.toml")

icon = """\033[0;35m─────────────────────────────────────────
   ▉▉▉▉▉▉╗  ▉▉╗ ▉▉▉▉▉▉╗  ▉▉╗ ▉▉▉╗   ▉▉╗
  ▉▉╔════╝  ▉▉║ ▉▉╝ ╔▉▉╗ ▉▉║ ▉▉▉▉╗  ▉▉║
  ╚▉▉▉▉▉▉╗  ▉▉║ ▉▉▉▉▉▉╔╝ ▉▉║ ▉▉╔▉▉╗ ▉▉║
   ╚════▉▉╗ ▉▉║ ▉▉╔═▉▉╚╗ ▉▉║ ▉▉║╚▉▉╗▉▉║
   ▉▉▉▉▉▉╔╝ ▉▉║ ▉▉║ ╚▉▉║ ▉▉║ ▉▉║ ╚▉▉▉▉║
   ╚═════╝  ╚═╝ ╚═╝  ╚═╝ ╚═╝ ╚═╝  ╚═══╝
─────────────────────────────────────────\033[0m"""

if __name__ == "__main__":
    print(icon)
    nonebot.run()
