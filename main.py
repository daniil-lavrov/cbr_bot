import asyncio
import datetime
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from redis import Redis
from datetime import datetime
import xml.etree.ElementTree as ET
import pytz

from config import CONFIG
from handlers import router

bot = Bot(token=CONFIG.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def load_info():
    url = 'https://cbr.ru/scripts/XML_daily.asp'
    redis = Redis(host="redis", port=6379)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                xml_data = await response.text()
                root = ET.fromstring(xml_data)
                for item in root.findall('Valute'):
                    currency_code = item.find('CharCode').text
                    rub_per_unit = float(item.find('VunitRate').text.replace(',', '.'))
                    redis.set(currency_code, rub_per_unit)
                redis.set('RUB', 1)
                redis.set('last_checked_date', (datetime.now(pytz.timezone('Europe/Moscow'))).strftime('%d-%m-%Y'))

async def main():

    scheduler = AsyncIOScheduler()
    scheduler.add_job(load_info, trigger=CronTrigger(hour=10, timezone=pytz.timezone('Europe/Moscow')))

    redis = Redis(host="redis", port=6379)
    key = 'last_checked_date'
    last_checked_date = redis.get(key)

    if last_checked_date:
        last_checked_date = last_checked_date.decode('utf-8')
        if last_checked_date != (datetime.now(pytz.timezone('Europe/Moscow'))).strftime('%d-%m-%Y'):
            await load_info()
    else:
        await load_info()

    dp = Dispatcher()
    dp.include_router(router)

    scheduler.start()

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
