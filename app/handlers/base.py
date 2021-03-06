import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.markdown import hpre, hbold
from loguru import logger

from app import config
from app.config import PLUS_TRIGGERS, MINUS_TRIGGERS, PLUS_EMOJI, MINUS_EMOJI
from app.misc import dp
from app.models.chat import Chat
from app.services.remove_message import delete_message


@dp.message_handler(commands=["start"], commands_prefix='!/')
@dp.throttled(rate=3)
async def cmd_start(message: types.Message):
    logger.info("User {user} start conversation with bot", user=message.from_user.id)
    await message.answer(
        "Я бот для подсчёта рейтинга в группе, просто добавьте меня "
        "в группу и плюсуйте друг другу в рейтинг.\n"
        "<code>!help</code> - справка о командах\n"
        # "<code>!about</code> - информация о боте и его исходники "
    )


@dp.message_handler(commands=["help"], commands_prefix='!/')
@dp.throttled(rate=3)
async def cmd_help(message: types.Message):
    logger.info("User {user} read help in {chat}", user=message.from_user.id, chat=message.chat.id)
    msg = await message.reply(
        (
            'Прибавить рейтинг можно начав сообщение с: "{plus}". \n'
            'Минусануть - написав первой строкой что-то из "{minus}".\n'
            'Чтобы выбрать пользователя - нужно ответить реплаем на сообщение пользователя '
            'или упомянуть его через @ (работает даже если у пользователя нет username).\n'
            'Увеличение и уменьшение идёт всегда ровно на одну единицу за раз\n'
            '<code>!top</code> [chat_id] - лучшие пользователи по рейтингу для текущего чата или для чата с chat_id \n'
            '<code>!about</code> - информация о боте и его исходники\n'
            '<code>!me</code> - посмотреть свою карму (желательно это делать в личных сообщениях с ботом)\n'
            # '<code>!report</code> {{реплаем}} - пожаловаться на сообщение модераторам\n'
            '<code>!idchat</code> - показать Ваш id, id чата и, '
            'если имеется, - id пользователя, которому Вы ответили командой'
        ).format(
            plus='", "'.join([*PLUS_TRIGGERS, *PLUS_EMOJI]),
            minus='", "'.join([*MINUS_TRIGGERS, *MINUS_EMOJI])
        )
    )
    if message.chat.type != "PRIVATE":
        asyncio.create_task(delete_message(msg, config.TIME_TO_REMOVE_TEMP_MESSAGES))
        asyncio.create_task(delete_message(message, config.TIME_TO_REMOVE_TEMP_MESSAGES))


@dp.message_handler(commands=["about"], commands_prefix='!')
@dp.throttled(rate=3)
async def cmd_about(message: types.Message):
    logger.info("User {user} about", user=message.from_user.id)
    msg = await message.reply(
    'Форк карма бота. Исходники по ссылке https://github.com/alekssamos/KarmaBot\n'
    'Считает рейтинг ровно по единице, а не в зависимости от силы.'
    )
    if message.chat.type != "PRIVATE":
        asyncio.create_task(delete_message(msg, config.TIME_TO_REMOVE_TEMP_MESSAGES))
        asyncio.create_task(delete_message(message, config.TIME_TO_REMOVE_TEMP_MESSAGES))


@dp.message_handler(commands='idchat', commands_prefix='!')
@dp.throttled(rate=30)
async def get_idchat(message: types.Message):
    text = (
        f"id этого чата: {hpre(message.chat.id)}\n"
        f"Ваш id: {hpre(message.from_user.id)}"
    )
    if message.reply_to_message:
        text += (
            f"\nid {hbold(message.reply_to_message.from_user.full_name)}: "
            f"{hpre(message.reply_to_message.from_user.id)}"
        )
    msg = await message.reply(text, disable_notification=True)
    if message.chat.type != "PRIVATE":
        asyncio.create_task(delete_message(msg, config.TIME_TO_REMOVE_TEMP_MESSAGES))
        asyncio.create_task(delete_message(message, config.TIME_TO_REMOVE_TEMP_MESSAGES))


@dp.message_handler(state='*', commands='cancel')
@dp.throttled(rate=3)
async def cancel_state(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logger.info(f'Cancelling state {current_state}')
    # Cancel state and inform user about it
    await state.finish()
    # And remove keyboard (just in case)
    await message.reply('Диалог прекращён, данные удалены', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(content_types=types.ContentTypes.MIGRATE_TO_CHAT_ID)
async def chat_migrate(message: types.Message, chat: Chat):
    old_id = message.chat.id
    new_id = message.migrate_to_chat_id
    chat.chat_id = new_id
    await chat.save()
    logger.info(f"Migrate chat from {old_id} to {new_id}")
