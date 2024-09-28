import khl
from datetime import datetime
import logging

from khl import EventTypes

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个机器人实例
bot = khl.Bot(token='1/MzI2NzM=/cyvZltzOh/GLLotmCqnVKw==')

# 指定文本频道 ID，用于发送消息
TEXT_CHANNEL_ID = '9348748149902262'

# 监听所有事件（用于调试）
@bot.on_event('*')
async def on_any_event(event: khl.Event):
    print(f'Received event: {event}')

# ping 命令
@bot.command()
async def ping(ctx: khl.Message):
    print("Ping command received")  # 打印调试信息
    await ctx.reply('Pong!')

@bot.on_event(EventTypes.JOINED_CHANNEL)
async def on_join_event(bot: khl.Bot, event: khl.Event):
    # print('111')
    # 获取频道对象
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        # await bot.client.send(target=channel, content='111')  # 将频道对象作为 target
        user_id = str(event.body['user_id'])
        user = await bot.fetch_user(user_id)  # 获取用户信息
        if user:
            await bot.client.send(target=channel, content=f'{user.nickname} 加入了频道。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

@bot.on_event(EventTypes.EXITED_CHANNEL)
async def on_exit_event(bot: khl.Bot, event: khl.Event):
    # print('111')
    # 获取频道对象
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        # await bot.client.send(target=channel, content='111')  # 将频道对象作为 target
        user_id = str(event.body['user_id'])
        user = await bot.fetch_user(user_id)  # 获取用户信息
        if user:
            await bot.client.send(target=channel, content=f'{user.nickname} 离开了频道。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 启动机器人
bot.run()