import khl
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import configparser

from khl import EventTypes

# 配置日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取本地配置文件
config = configparser.ConfigParser()
config.read('config.ini')  # 假设配置文件名为 config.ini

# 从配置文件中获取 token 和 TEXT_CHANNEL_ID
bot = khl.Bot(token=config.get('kook', 'token'))
TEXT_CHANNEL_ID = config.get('kook', 'text_channel_id')

# 数据存储文件路径
DATA_FILE_PATH = 'kook_study_data.json'

# 一天的开始时间（凌晨 5 点）
DAY_START_HOUR = 5

# 限制一天内添加的任务数量
MAX_TASKS_PER_DAY = 10

# 用于存储用户加入频道的时间
join_times = {}

# 加载数据或初始化
def load_or_init_data():
    data_file = Path(DATA_FILE_PATH)
    if data_file.is_file():
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        return {
            'tasks': {},  # {user_id: [{'content': ..., 'completed': ...}, ...]}
            'study_times': {},  # {user_id: [{'start_time': ..., 'end_time': ..., 'duration': ...}, ...]}
            'daily_study_time': {},  # {user_id: float()}  # 秒数
            'weekly_study_time': {},  # {user_id: float()}
            'monthly_study_time': {},  # {user_id: float()}
            'yearly_study_time': {},  # {user_id: float()}
            'total_study_time': {}  # {user_id: float()}
        }

# 保存数据
def save_data(data):
    with open(DATA_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 获取当前日期（从凌晨 5 点开始）
def get_current_date():
    now = datetime.now()
    if now.hour < DAY_START_HOUR:
        now -= timedelta(days=1)
    return now.strftime('%Y-%m-%d')

# 获取当前周的第一天（周一）
def get_current_week_start():
    now = datetime.now()
    if now.hour < DAY_START_HOUR:
        now -= timedelta(days=1)
    week_start = now - timedelta(days=now.weekday())
    return week_start.strftime('%Y-%m-%d')

# 获取当前月的第一天
def get_current_month_start():
    now = datetime.now()
    if now.hour < DAY_START_HOUR:
        now -= timedelta(days=1)
    month_start = now.replace(day=1)
    return month_start.strftime('%Y-%m-%d')

# 获取当前年的第一天
def get_current_year_start():
    now = datetime.now()
    if now.hour < DAY_START_HOUR:
        now -= timedelta(days=1)
    year_start = now.replace(month=1, day=1)
    return year_start.strftime('%Y-%m-%d')

# 格式化时间差，去掉微秒部分
def format_timedelta(td):
    total_seconds = int(td.total_seconds())
    return str(timedelta(seconds=total_seconds))

# 加载数据
data = load_or_init_data()

# 监听所有事件（用于调试）
@bot.on_event('*')
async def on_any_event(event: khl.Event):
    print(f'Received event: {event}')

# ping 命令
@bot.command()
async def ping(ctx: khl.Message):
    print("Ping command received")  # 打印调试信息
    await ctx.reply('Pong!')

# 帮助指令
@bot.command(name='帮助')
async def help_command(ctx: khl.Message):
    message = (
        "**可用指令：**\n\n"
        "**任务管理**\n"
        "- `/添加任务 [任务内容]`：添加一个新任务。\n"
        "- `/删除任务 [任务编号]`：删除指定编号的任务。\n"
        "- `/完成任务 [任务编号]`：将指定编号的任务标记为已完成。\n"
        "- `/查看任务`：查看今天的任务列表。\n\n"
        "**学习时长查询**\n"
        "- `/今日学习时长`：查询今天的学习时长。\n"
        "- `/本周学习时长`：查询本周的学习时长。\n"
        "- `/本月学习时长`：查询本月的学习时长。\n"
        "- `/本年学习时长`：查询本年的学习时长。\n"
        "- `/生涯学习时长`：查询生涯总学习时长。\n"
    )
    await ctx.reply(message)

# 独立的显示任务函数
async def display_tasks(ctx: khl.Message):
    message = "**今日任务：**\n"
    has_tasks = False
    for user_id, tasks in data['tasks'].items():
        user = await bot.client.fetch_user(user_id)
        if user and tasks:
            has_tasks = True
            # 使用 `` 包裹用户名，并加粗
            message += f"**`{user.nickname}`：**\n"
            for i, task in enumerate(tasks):
                if task['completed']:
                    # 已完成任务使用删除线，并在末尾加上 "(已完成)"，并使用灰色表示
                    message += f"{i + 1}. ~~{task['content']}~~ (已完成)\n"
                else:
                    # 未完成任务正常显示，并使用加粗表示
                    message += f"{i + 1}. **{task['content']}**\n"
    if not has_tasks:
        message = "还没有人添加任务。"
    await ctx.reply(message)

# 独立的显示时间函数
async def get_study_time_message(ctx, title, study_time_data, time_filter=None):
    message = f"**{title}：**\n"
    for user_id, study_time in study_time_data.items():
        user = await bot.client.fetch_user(user_id)
        if user:
            if time_filter is None:  # 处理生涯学习时长的情况
                filtered_study_time = study_time
            else:
                study_times = data['study_times'][user_id]
                filtered_study_time = sum(
                    record['duration']
                    for record in study_times
                    if time_filter(datetime.strptime(record['start_time'], "%Y-%m-%d %H:%M:%S"))
                )
            formatted_study_time = format_timedelta(timedelta(seconds=filtered_study_time))
            message += f"**`{user.nickname}`:** {formatted_study_time}\n"
    if message == f"**{title}：**\n":
        if time_filter is None:
            message = "暂无学习记录。"
        else:
            message = f"{title}暂无学习记录。"
    return message


# 添加任务
@bot.command(name='添加任务')
async def add_task(ctx: khl.Message, task_content: str = None):
    if not task_content:
        await ctx.reply("请提供任务内容。正确用法：`/添加任务 [任务内容]`")
        return

    user_id = str(ctx.author_id)
    current_date = get_current_date()

    # 初始化用户任务列表
    if user_id not in data['tasks']:
        data['tasks'][user_id] = []

    # 检查是否超过每日任务限制
    if len(data['tasks'][user_id]) >= MAX_TASKS_PER_DAY:
        await ctx.reply(f"每天最多只能添加 {MAX_TASKS_PER_DAY} 个任务。")
        return

    # 添加任务
    data['tasks'][user_id].append({'content': task_content, 'completed': False})
    save_data(data)
    await ctx.reply(f"任务 '{task_content}' 添加成功！")
    await display_tasks(ctx)  # 自动触发查看任务

# 删除任务
@bot.command(name='删除任务')
async def delete_task(ctx: khl.Message, task_index: int = None):
    if task_index is None:
        await ctx.reply("请提供要删除的任务编号。正确用法：`/删除任务 [任务编号]`")
        return

    user_id = str(ctx.author_id)
    current_date = get_current_date()

    # 检查任务列表是否存在
    if user_id not in data['tasks'] or not data['tasks'][user_id]:
        await ctx.reply("您还没有添加任何任务。")
        return

    # 检查任务编号是否有效
    if task_index < 1 or task_index > len(data['tasks'][user_id]):
        await ctx.reply("任务编号无效，请检查后重试。")
        return

    # 删除任务
    del data['tasks'][user_id][task_index - 1]
    save_data(data)
    await ctx.reply("任务删除成功！")
    await display_tasks(ctx)  # 自动触发查看任务

# 完成任务
@bot.command(name='完成任务')
async def complete_task(ctx: khl.Message, task_index: int = None):
    if task_index is None:
        await ctx.reply("请提供要完成的任务编号。正确用法：`/完成任务 [任务编号]`")
        return

    user_id = str(ctx.author_id)
    current_date = get_current_date()

    # 检查任务列表是否存在
    if user_id not in data['tasks'] or not data['tasks'][user_id]:
        await ctx.reply("您还没有添加任何任务。")
        return

    # 检查任务编号是否有效
    if task_index < 1 or task_index > len(data['tasks'][user_id]):
        await ctx.reply("任务编号无效，请检查后重试。")
        return

    # 完成任务
    data['tasks'][user_id][task_index - 1]['completed'] = True
    save_data(data)
    await ctx.reply("任务完成！")
    await display_tasks(ctx)  # 自动触发查看任务

# 查看任务
@bot.command(name='查看任务')
async def view_tasks(ctx: khl.Message):
    await display_tasks(ctx)

# 用户加入语音频道
@bot.on_event(EventTypes.JOINED_CHANNEL)
async def on_join_event(bot: khl.Bot, event: khl.Event):
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        user_id = str(event.body['user_id'])
        user = await bot.client.fetch_user(user_id)  # 获取用户信息
        if user:
            join_time = datetime.now()  # 获取当前时间
            join_times[user_id] = join_time

            # 初始化用户的学习时长记录
            if user_id not in data['study_times']:
                data['study_times'][user_id] = []

            await bot.client.send(target=channel, content=f'{user.nickname} 在 {join_time.strftime("%Y-%m-%d %H:%M:%S")} 开始了学习。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 用户退出语音频道
@bot.on_event(EventTypes.EXITED_CHANNEL)
async def on_exit_event(bot: khl.Bot, event: khl.Event):
    channel = await bot.client.fetch_public_channel(TEXT_CHANNEL_ID)
    if channel:  # 检查是否成功获取到频道对象
        user_id = str(event.body['user_id'])
        user = await bot.client.fetch_user(user_id)  # 获取用户信息
        if user:
            if user_id in join_times:
                join_time = join_times[user_id]
                leave_time = datetime.now()
                study_duration = leave_time - join_time

                # 记录学习时长
                data['study_times'][user_id].append({
                    'start_time': join_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'end_time': leave_time.strftime("%Y-%m-%d %H:%M:%S"),
                    'duration': study_duration.total_seconds()
                })

                # 更新每日、每周、每月、每年的学习时长
                update_study_time(user_id, study_duration, 'daily')
                update_study_time(user_id, study_duration, 'weekly')
                update_study_time(user_id, study_duration, 'monthly')
                update_study_time(user_id, study_duration, 'yearly')

                # 更新总学习时长
                data['total_study_time'][user_id] = data['total_study_time'].get(user_id, 0) + study_duration.total_seconds()

                del join_times[user_id]
                save_data(data)

                # 格式化 study_duration
                formatted_study_duration = format_timedelta(study_duration)

                await bot.client.send(
                    target=channel,
                    content=f'{user.nickname} 在 {leave_time.strftime("%Y-%m-%d %H:%M:%S")} 结束了学习，本次学习时长为 {formatted_study_duration}。'
                )

                # 每天凌晨 5 点清空任务列表和每日学习时长
                if leave_time.hour == DAY_START_HOUR and leave_time.minute == 0:
                    reset_daily_data()
            else:
                await bot.client.send(target=channel, content=f'{user.nickname} 离开了频道。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 更新学习时长（每日、每周、每月、每年）
def update_study_time(user_id, study_duration, period):
    if period == 'daily':
        data['daily_study_time'][user_id] = data['daily_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'weekly':
        current_week_start = get_current_week_start()
        data['weekly_study_time'][user_id] = data['weekly_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'monthly':
        current_month_start = get_current_month_start()
        data['monthly_study_time'][user_id] = data['monthly_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'yearly':
        current_year_start = get_current_year_start()
        data['yearly_study_time'][user_id] = data['yearly_study_time'].get(user_id, 0) + study_duration.total_seconds()

# 今日学习时长
@bot.command(name='今日学习时长')
async def today_study_time(ctx: khl.Message):
    message = await get_study_time_message(ctx, '今日学习时长', data['daily_study_time'])
    await ctx.reply(message)

# 本周学习时长
@bot.command(name='本周学习时长')
async def weekly_study_time(ctx: khl.Message):
    current_week_start = get_current_week_start()
    message = await get_study_time_message(
        ctx,
        '本周学习时长',
        data['weekly_study_time'],
        lambda start_time: start_time.strftime('%Y-%m-%d') >= current_week_start
    )
    await ctx.reply(message)

# 本月学习时长
@bot.command(name='本月学习时长')
async def monthly_study_time(ctx: khl.Message):
    current_month_start = get_current_month_start()
    message = await get_study_time_message(
        ctx,
        '本月学习时长',
        data['monthly_study_time'],
        lambda start_time: start_time.strftime('%Y-%m-%d') >= current_month_start
    )
    await ctx.reply(message)

# 本年学习时长
@bot.command(name='本年学习时长')
async def yearly_study_time(ctx: khl.Message):
    current_year_start = get_current_year_start()
    message = await get_study_time_message(
        ctx,
        '本年学习时长',
        data['yearly_study_time'],
        lambda start_time: start_time.strftime('%Y-%m-%d') >= current_year_start
    )
    await ctx.reply(message)

# 生涯学习时长
@bot.command(name='生涯学习时长')
async def total_study_time(ctx: khl.Message):
    message = await get_study_time_message(ctx, '生涯学习时长', data['total_study_time'])
    await ctx.reply(message)

# 每天凌晨 5 点清空任务列表和每日学习时长
def reset_daily_data():
    data['tasks'] = {}
    data['daily_study_time'] = {}
    save_data(data)
    logging.info("已重置每日任务和学习时长。")

# 启动机器人
bot.run()
