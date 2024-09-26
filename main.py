import khl
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个机器人实例
bot = khl.Bot(token='1/MzI2NzM=/cyvZltzOh/GLLotmCqnVKw==')

# 指定文本频道 ID，用于发送消息
TEXT_CHANNEL_ID = '9348748149902262'

# 监听所有事件
@bot.on_event('*')
async def on_any_event(event: khl.Event):
    logging.info(f'Received event: {event}')  # 打印完整的事件对象

# 监听语音频道加入事件
@bot.on_event('VOICE_CHANNEL_MEMBER_ADD')
async def on_voice_channel_join(event: khl.Event):
    user_id = str(event.body['user_id'])
    user = await bot.fetch_user(user_id) # 获取用户信息，以便获取昵称
    channel = await bot.fetch_public_channel(TEXT_CHANNEL_ID) # 获取文本频道对象

    logging.info(f'User {user_id} joined voice channel.')
    await channel.send(f'{user.nickname} 进入了语音频道。')

# 监听语音频道离开事件
@bot.on_event('VOICE_CHANNEL_MEMBER_REMOVE')
async def on_voice_channel_leave(event: khl.Event):
    user_id = str(event.body['user_id'])
    user = await bot.fetch_user(user_id)
    channel = await bot.fetch_public_channel(TEXT_CHANNEL_ID)

    logging.info(f'User {user_id} left voice channel.')
    await channel.send(f'{user.nickname} 退出了语音频道。')

# 启动机器人
bot.run()