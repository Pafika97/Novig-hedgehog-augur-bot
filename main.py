
import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv
import pandas as pd

from utils.excel import to_excel
from connectors.augur import fetch_augur_markets
from connectors.hedgehog import fetch_hedgehog_markets
from connectors.novig import fetch_novig_markets

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise SystemExit("Please set BOT_TOKEN in .env")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

async def _send_df_as_excel(chat_id: int, df: pd.DataFrame, platform: str):
    path = to_excel(df, platform)
    await bot.send_document(chat_id, document=open(path, "rb"))

@dp.message(Command("start"))
async def cmd_start(m: Message):
    await m.answer("Готов! Используйте /fetch augur|hedgehog|novig|all")

@dp.message(Command("fetch"))
async def cmd_fetch(m: Message):
    args = (m.text or "").split()
    target = args[1].lower() if len(args) > 1 else "all"

    results = []

    if target in ("augur", "all"):
        try:
            df_augur = fetch_augur_markets(limit=300)
        except Exception as e:
            await m.answer(f"Augur: ошибка — {e}")
            df_augur = pd.DataFrame([])
        results.append(("augur", df_augur))

    if target in ("hedgehog", "all"):
        try:
            df_hh = fetch_hedgehog_markets(limit=300)
        except Exception as e:
            await m.answer(f"Hedgehog: ошибка — {e}")
            df_hh = pd.DataFrame([])
        results.append(("hedgehog", df_hh))

    if target in ("novig", "all"):
        try:
            df_nv = fetch_novig_markets(limit=300)
        except Exception as e:
            await m.answer(f"Novig: ошибка — {e}")
            df_nv = pd.DataFrame([])
        results.append(("novig", df_nv))

    # отправляем файлы
    for platform, df in results:
        await _send_df_as_excel(m.chat.id, df, platform)

def main():
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()
