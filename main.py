import khl
from datetime import datetime, timedelta
import logging

from khl import EventTypes

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个机器人实例
bot = khl.Bot(token='1/MzI2NzM=/cyvZltzOh/GLLotmCqnVKw==')

# 指定文本频道 ID，用于发送消息
TEXT_CHANNEL_ID = '9348748149902262'

# 用于存储用户加入频道的时间
join_times = {}
# 用于存储一天的总学习时长
daily_study_time = timedelta()
# 用于存储所有用户的总学习时长
total_study_times = {}

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
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        user_id = str(event.body['user_id'])
        user = await bot.client.fetch_user(user_id)  # 获取用户信息
        if user:
            join_time = datetime.now()  # 获取当前时间
            join_times[user_id] = join_time
            await bot.client.send(target=channel, content=f'{user.nickname} 在 {join_time.strftime("%Y-%m-%d %H:%M:%S")} 开始了学习。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

@bot.on_event(EventTypes.EXITED_CHANNEL)
async def on_exit_event(bot: khl.Bot, event: khl.Event):
    global daily_study_time, total_study_times
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        user_id = str(event.body['user_id'])
        user = await bot.client.fetch_user(user_id)  # 获取用户信息
        if user:
            if user_id in join_times:
                join_time = join_times[user_id]
                leave_time = datetime.now()
                study_duration = leave_time - join_time
                daily_study_time += study_duration
                del join_times[user_id]

                # 更新用户的总学习时长
                total_study_times[user_id] = total_study_times.get(user_id, timedelta()) + study_duration

                # 格式化 study_duration 和 daily_study_time，去掉微秒部分
                formatted_study_duration = str(study_duration).split('.')[0]
                formatted_daily_study_time = str(daily_study_time).split('.')[0]

                await bot.client.send(
                    target=channel,
                    content=f'{user.nickname} 在 {leave_time.strftime("%Y-%m-%d %H:%M:%S")} 结束了学习，本次学习时长为 {formatted_study_duration}。\n'
                            f'今天累计学习时长为 {formatted_daily_study_time}。'
                )

                # 如果过了午夜，重置 daily_study_time
                if leave_time.day != join_time.day:
                    daily_study_time = timedelta()
            else:
                await bot.client.send(target=channel, content=f'{user.nickname} 离开了频道。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 查看所有用户总学习时长的命令
@bot.command(name='学习时长')
async def show_total_study_time(ctx: khl.Message):
    if total_study_times:
        message = "所有用户的总学习时长：\n"
        for user_id, study_time in total_study_times.items():
            user = await bot.client.fetch_user(user_id)
            if user:
                # 格式化 study_time，去掉微秒部分
                formatted_study_time = str(study_time).split('.')[0]
                message += f"{user.nickname}: {formatted_study_time}\n"
        await ctx.reply(message)
    else:
        await ctx.reply("暂无学习记录。")

# 启动机器人
bot.run()