import khl
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个机器人实例
bot = khl.Bot(token='1/MzI2NzM=/cyvZltzOh/GLLotmCqnVKw==')

# 指定文本频道 ID，用于发送消息
TEXT_CHANNEL_ID = '9348748149902262'

# 监听所有事件（用于调试）
@bot.on_event('*')
async def on_any_event(event: khl.Event):
    logging.info(f'Received event: {event}')

# 监听语音频道加入事件
@bot.on_event('VOICE_CHANNEL_MEMBER_ADD')
async def on_voice_channel_join(event: khl.Event):
    user_id = str(event.body['user_id'])
    logging.info(f'User {user_id} joined voice channel. Event details: {event.body}')

    try:
        user = await bot.fetch_user(user_id)
        if user is None:
            logging.error(f'Failed to fetch user with ID {user_id}')
        else:
            logging.info(f'Fetched user: {user}')

        channel = await bot.fetch_public_channel(TEXT_CHANNEL_ID)
        if channel is None:
            logging.error(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')
        else:
            logging.info(f'Fetched channel: {channel}')

        if user and channel:
            # 尝试使用 bot.send 发送消息
            await bot.send(channel_id=TEXT_CHANNEL_ID, content=f'{user.nickname} 进入了语音频道。')
            logging.info('Sent join message successfully.')

    except Exception as e:
        logging.error(f'Error occurred in on_voice_channel_join: {e}')

# 监听语音频道离开事件
@bot.on_event('VOICE_CHANNEL_MEMBER_REMOVE')
async def on_voice_channel_leave(event: khl.Event):
    user_id = str(event.body['user_id'])
    logging.info(f'User {user_id} left voice channel. Event details: {event.body}')

    try:
        user = await bot.fetch_user(user_id)
        if user is None:
            logging.error(f'Failed to fetch user with ID {user_id}')
        else:
            logging.info(f'Fetched user: {user}')

        channel = await bot.fetch_public_channel(TEXT_CHANNEL_ID)
        if channel is None:
            logging.error(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')
        else:
            logging.info(f'Fetched channel: {channel}')

        if user and channel:
            # 尝试使用 bot.send 发送消息
            await bot.send(channel_id=TEXT_CHANNEL_ID, content=f'{user.nickname} 退出了语音频道。')
            logging.info('Sent leave message successfully.')

    except Exception as e:
        logging.error(f'Error occurred in on_voice_channel_leave: {e}')

# 启动机器人
bot.run()