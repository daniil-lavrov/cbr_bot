from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from redis import Redis

router = Router()

@router.message(Command("exchange"))
async def exchange(msg: Message):

    args = msg.text.split()
    redis = Redis(host="redis", port=6379)

    if len(args) != 4:
        await msg.reply("Использование: /exchange <валюта_1> <валюта_2> <количество>")
        return

    currency_from = args[1].upper()
    currency_to = args[2].upper()
    amount = args[3]

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await msg.reply("Количество должно быть положительным числом.")
        return

    rate_from = redis.get(currency_from)
    rate_to = redis.get(currency_to)

    if rate_from is None:
        await msg.reply(f"Не найден курс для {currency_from}.")
        return

    if rate_to is None:
        await msg.reply(f"Не найден курс для {currency_to}.")
        return

    rub_per_unit_from = float(rate_from.decode('utf-8'))
    rub_per_unit_to = float(rate_to.decode('utf-8'))

    amount_in_rub = amount * rub_per_unit_from
    converted_amount = amount_in_rub / rub_per_unit_to

    response = f"{amount} {currency_from} = {converted_amount:.2f} {currency_to}"
    await msg.reply(response)

@router.message(Command("rates"))
async def exchange(msg: Message):
    redis = Redis(host="redis", port=6379)

    all_keys = []

    cursor = '0'
    while cursor != 0:
        cursor, keys = redis.scan(cursor=cursor)
        all_keys.extend([key.decode('utf-8') for key in keys if len(key.decode('utf-8')) == 3])
        if cursor == 0:
            break

    for key in all_keys:
        await msg.answer(key + ': ' + redis.get(key).decode('utf-8'))