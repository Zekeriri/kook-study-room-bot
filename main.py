from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import configparser

from khl import EventTypes, Bot, Message, Event

# # 配置日志
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# 读取本地配置文件
config = configparser.ConfigParser()
config.read('config.ini')  # 假设配置文件名为 config.ini

# 从配置文件中获取 token 和 TEXT_CHANNEL_ID
bot = Bot(token=config.get('kook', 'token'))
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
            data = json.load(f)
        # 确保 'reading_records' 字段存在
        if 'reading_records' not in data:
            data['reading_records'] = {}
        return data
    else:
        return {
            'tasks': {},  # {user_id: [{'content': ..., 'completed': ...}, ...]}
            'study_times': {},  # {user_id: [{'start_time': ..., 'end_time': ..., 'duration': ...}, ...]}
            'daily_study_time': {},  # {user_id: float()}  # 秒数
            'weekly_study_time': {},  # {user_id: float()}
            'monthly_study_time': {},  # {user_id: float()}
            'yearly_study_time': {},  # {user_id: float()}
            'total_study_time': {},  # {user_id: float()}
            'last_reset': {  # 记录最后重置时间
                'daily': None,
                'weekly': None,
                'monthly': None,
                'yearly': None
            },
            'reading_records': {}  # {user_id: [{'total_words': int, 'reading_times': [float], 'timestamp': str}, ...]}
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

# 检查并重置数据
def check_and_reset(data, period):
    now = datetime.now()
    if period == 'daily':
        current_period_start = get_current_date()
    elif period == 'weekly':
        current_period_start = get_current_week_start()
    elif period == 'monthly':
        current_period_start = get_current_month_start()
    elif period == 'yearly':
        current_period_start = get_current_year_start()
    else:
        return  # 无效的周期

    last_reset = data['last_reset'].get(period)

    if last_reset != current_period_start:
        if period == 'daily':
            data['daily_study_time'] = {}
            data['tasks'] = {}
        elif period == 'weekly':
            data['weekly_study_time'] = {}
        elif period == 'monthly':
            data['monthly_study_time'] = {}
        elif period == 'yearly':
            data['yearly_study_time'] = {}
        # 更新最后重置时间
        data['last_reset'][period] = current_period_start
        save_data(data)
        logging.info(f"已重置 {period} 数据。")

# 加载数据
data = load_or_init_data()

# ping 命令
@bot.command()
async def ping(ctx: Message):
    print("Ping command received")  # 打印调试信息
    await ctx.reply('Pong!')

# 帮助指令
@bot.command(name='帮助')
async def help_command(ctx: Message):
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
        "- `/生涯学习时长`：查询生涯总学习时长。\n\n"
        "**阅读速度记录**\n"
        "- `/添加阅读记录 [总词数] [阅读时间1(第一遍)] [阅读时间2(第二遍)] ...`：\n  记录本次的阅读速度记录本次的阅读速度。\n  一篇文章可能需要多次阅读才能完全理解，因此可以输入多个阅读时间。\n  速度表示看懂文章的平均速度。\n"
        "- `/查看阅读记录`：查看已记录的阅读速度，显示最近10条。\n"
        "- `/删除阅读记录 [记录编号]`：删除指定编号的阅读记录。\n"
        "- `/查看阅读数据`：查看阅读数据分析。\n"
    )
    await ctx.reply(message)

# 独立的显示任务函数
async def display_tasks(ctx: Message):
    message = "**今日任务：**\n"
    has_tasks = False
    for user_id, tasks in data['tasks'].items():
        user = await bot.client.fetch_user(user_id)
        if user and tasks:
            has_tasks = True
            # 使用 `` 包裹用户名，并加粗
            nickname = user.nickname if user.nickname else user.username
            message += f"**`{nickname}`：**\n"
            for i, task in enumerate(tasks):
                if task['completed']:
                    # 已完成任务使用删除线，并在末尾加上 "(已完成)"
                    message += f"{i + 1}. ~~{task['content']}~~ (已完成)\n"
                else:
                    # 未完成任务正常显示，并使用加粗表示
                    message += f"{i + 1}. **{task['content']}**\n"
    if not has_tasks:
        message = "还没有人添加任务。"
    await ctx.reply(message)

# 独立的显示时间函数
async def get_study_time_message(ctx, title, study_time_data, period=None):
    if period:
        check_and_reset(data, period)

    message = f"**{title}：**\n"
    for user_id, study_time in study_time_data.items():
        user = await bot.client.fetch_user(user_id)
        if user:
            if period is None:  # 处理生涯学习时长的情况
                filtered_study_time = study_time
            else:
                study_times = data['study_times'].get(user_id, [])
                if period == 'daily':
                    current_period_start = get_current_date()
                elif period == 'weekly':
                    current_period_start = get_current_week_start()
                elif period == 'monthly':
                    current_period_start = get_current_month_start()
                elif period == 'yearly':
                    current_period_start = get_current_year_start()
                else:
                    current_period_start = None

                if current_period_start:
                    if period in ['daily', 'weekly', 'monthly', 'yearly']:
                        start_datetime = datetime.strptime(current_period_start, "%Y-%m-%d")
                    else:
                        start_datetime = None

                    if start_datetime:
                        filtered_study_time = sum(
                            record['duration']
                            for record in study_times
                            if datetime.strptime(record['start_time'], "%Y-%m-%d %H:%M:%S") >= start_datetime
                        )
                    else:
                        filtered_study_time = 0
                else:
                    filtered_study_time = 0

            formatted_study_time = format_timedelta(timedelta(seconds=filtered_study_time))
            nickname = user.nickname if user.nickname else user.username
            message += f"**`{nickname}`:** {formatted_study_time}\n"
    if message == f"**{title}：**\n":
        if period is None:
            message = "暂无学习记录。"
        else:
            message = f"{title} 暂无学习记录。"
    return message

# 添加任务
@bot.command(name='添加任务')
async def add_task(ctx: Message, task_content: str = None):
    check_and_reset(data, 'daily')  # 在添加任务时调用 check_and_reset 函数
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
async def delete_task(ctx: Message, task_index: int = None):
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
async def complete_task(ctx: Message, task_index: int = None):
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
async def view_tasks(ctx: Message):
    check_and_reset(data, 'daily')  # 在查看任务时调用 check_and_reset 函数
    await display_tasks(ctx)

# 用户加入语音频道
@bot.on_event(EventTypes.JOINED_CHANNEL)
async def on_join_event(bot: Bot, event: Event):
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

            nickname = user.nickname if user.nickname else user.username
            await bot.client.send(target=channel,
                                  content=f'{nickname} 开始了学习。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 用户退出语音频道
@bot.on_event(EventTypes.EXITED_CHANNEL)
async def on_exit_event(bot: Bot, event: Event):
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

                nickname = user.nickname if user.nickname else user.username
                await bot.client.send(
                    target=channel,
                    content=f'{nickname} 结束了学习，本次学习时长为 {formatted_study_duration}。'
                )
            else:
                nickname = user.nickname if user.nickname else user.username
                await bot.client.send(target=channel, content=f'{nickname} 离开了频道。')
        else:
            print(f"Failed to fetch user with ID {user_id}")
    else:
        print(f'Failed to fetch channel with ID {TEXT_CHANNEL_ID}')

# 更新学习时长（每日、每周、每月、每年）
def update_study_time(user_id, study_duration, period):
    if period == 'daily':
        check_and_reset(data, 'daily')
        data['daily_study_time'][user_id] = data['daily_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'weekly':
        check_and_reset(data, 'weekly')
        data['weekly_study_time'][user_id] = data['weekly_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'monthly':
        check_and_reset(data, 'monthly')
        data['monthly_study_time'][user_id] = data['monthly_study_time'].get(user_id, 0) + study_duration.total_seconds()
    elif period == 'yearly':
        check_and_reset(data, 'yearly')
        data['yearly_study_time'][user_id] = data['yearly_study_time'].get(user_id, 0) + study_duration.total_seconds()

# 今日学习时长
@bot.command(name='今日学习时长')
async def today_study_time(ctx: Message):
    message = await get_study_time_message(ctx, '今日学习时长', data['daily_study_time'], period='daily')
    await ctx.reply(message)

# 本周学习时长
@bot.command(name='本周学习时长')
async def weekly_study_time(ctx: Message):
    message = await get_study_time_message(ctx, '本周学习时长', data['weekly_study_time'], period='weekly')
    await ctx.reply(message)

# 本月学习时长
@bot.command(name='本月学习时长')
async def monthly_study_time(ctx: Message):
    message = await get_study_time_message(ctx, '本月学习时长', data['monthly_study_time'], period='monthly')
    await ctx.reply(message)

# 本年学习时长
@bot.command(name='本年学习时长')
async def yearly_study_time(ctx: Message):
    message = await get_study_time_message(ctx, '本年学习时长', data['yearly_study_time'], period='yearly')
    await ctx.reply(message)

# 生涯学习时长
@bot.command(name='生涯学习时长')
async def total_study_time(ctx: Message):
    message = await get_study_time_message(ctx, '生涯学习时长', data['total_study_time'])
    await ctx.reply(message)

# 新增部分：阅读速度记录功能

# 辅助函数：生成阅读数据分析消息
async def generate_reading_data_message(user_id):
    records = data['reading_records'].get(user_id, [])

    if not records:
        return "还没有阅读记录。"

    # 获取最近50次记录
    recent_50_records = records[-50:]

    if not recent_50_records:
        return "还没有阅读记录。"

    # 计算平均阅读速度
    total_words = sum(record['total_words'] for record in recent_50_records)
    total_time = sum(sum(record['reading_times']) for record in recent_50_records)

    if total_time > 0:
        average_speed = total_words / total_time
    else:
        average_speed = 0

    # 计算趋势
    num_records = len(recent_50_records)
    half = num_records // 2
    first_half = recent_50_records[:half]
    second_half = recent_50_records[half:]

    def calculate_average_speed(records_subset):
        tw = sum(record['total_words'] for record in records_subset)
        tt = sum(sum(record['reading_times']) for record in records_subset)
        return tw / tt if tt > 0 else 0

    if half > 0:
        first_half_avg = calculate_average_speed(first_half)
        second_half_avg = calculate_average_speed(second_half)
        if second_half_avg > first_half_avg:
            trend = "较前半部分记录有所增加"
        elif second_half_avg < first_half_avg:
            trend = "较前半部分记录有所减少"
        else:
            trend = "与前半部分记录持平"
    else:
        trend = "记录不足以分析趋势"

    message = "**阅读数据分析：**\n\n"
    message += f"- 最近50次阅读记录：{len(recent_50_records)} 次\n"
    message += f"- 平均阅读速度：{average_speed:.2f} 词/分钟\n"
    message += f"- 阅读速度趋势：{trend}\n"

    return message

# 记录阅读速度
@bot.command(name='添加阅读记录')
async def record_reading_speed(ctx: Message, total_words: int = None, *reading_times: float):
    if total_words is None or not reading_times:
        await ctx.reply("参数无效。正确用法：`/添加阅读记录 [总词数] [阅读时间1] [阅读时间2] ...`")
        return

    # 输入验证
    if not isinstance(total_words, int) or total_words <= 0:
        await ctx.reply("总词数必须是一个正整数。")
        return

    try:
        reading_times = [float(time) for time in reading_times]
    except ValueError:
        await ctx.reply("阅读时间必须是一个或多个正数（单位：分钟）。")
        return

    if any(time <= 0 for time in reading_times):
        await ctx.reply("阅读时间必须是一个或多个正数（单位：分钟）。")
        return

    user_id = str(ctx.author_id)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 初始化用户的阅读记录
    if user_id not in data['reading_records']:
        data['reading_records'][user_id] = []

    # 创建新的阅读记录
    new_record = {
        'total_words': total_words,
        'reading_times': reading_times,
        'timestamp': timestamp
    }

    # 添加记录
    data['reading_records'][user_id].append(new_record)
    save_data(data)

    # 计算本次阅读速度
    total_time = sum(reading_times)
    if total_time > 0:
        reading_speed = total_words / total_time
    else:
        reading_speed = 0

    # 格式化阅读时间
    reading_time_formatted = ""
    for idx, time in enumerate(reading_times, start=1):
        reading_time_formatted += f"  - 第{idx}遍：{time} 分钟\n"

    await ctx.reply(
        f"阅读记录已成功添加！\n"
        f"总词数：{total_words}\n"
        f"阅读时间：\n{reading_time_formatted}"
        f"本次阅读速度：{reading_speed:.2f} 词/分钟"
    )

    # 自动调用查看阅读数据
    reading_data_message = await generate_reading_data_message(user_id)
    await ctx.reply(reading_data_message)

# 查看阅读记录
@bot.command(name='查看阅读记录')
async def view_reading_records(ctx: Message):
    user_id = str(ctx.author_id)
    records = data['reading_records'].get(user_id, [])

    if not records:
        await ctx.reply("还没有阅读记录。")
        # 自动调用查看阅读数据
        reading_data_message = await generate_reading_data_message(user_id)
        await ctx.reply(reading_data_message)
        return

    # 获取最近10条记录
    recent_records = records[-10:]
    recent_records = reversed(recent_records)  # 从最新开始

    message = "**最近10条阅读记录：**\n\n"
    for idx, record in enumerate(recent_records, start=1):
        reading_time_formatted = ""
        for r_idx, time in enumerate(record['reading_times'], start=1):
            reading_time_formatted += f"  - 第{r_idx}遍：{time} 分钟\n"
        message += (
            f"{idx}. 总词数：{record['total_words']}\n"
            f"   阅读时间：\n{reading_time_formatted}"
        )

    await ctx.reply(message)

    # 自动调用查看阅读数据
    reading_data_message = await generate_reading_data_message(user_id)
    await ctx.reply(reading_data_message)

# 删除阅读记录
@bot.command(name='删除阅读记录')
async def delete_reading_record(ctx: Message, record_index: int = None):
    if record_index is None:
        await ctx.reply("请提供要删除的记录编号。正确用法：`/删除阅读记录 [记录编号]`")
        return

    user_id = str(ctx.author_id)
    records = data['reading_records'].get(user_id, [])

    if not records:
        await ctx.reply("还没有阅读记录。")
        # 自动调用查看阅读数据
        reading_data_message = await generate_reading_data_message(user_id)
        await ctx.reply(reading_data_message)
        return

    # 记录编号从1开始
    if record_index < 1 or record_index > len(records):
        await ctx.reply("记录编号无效，请检查后重试。正确用法：`/删除阅读记录 [记录编号]`")
        return

    # 删除指定记录
    del records[record_index - 1]
    save_data(data)

    await ctx.reply(f"阅读记录 #{record_index} 已删除。")

    if not records:
        await ctx.reply("当前没有任何阅读记录。")
    else:
        # 获取最近10条记录
        recent_records = records[-10:]
        recent_records = reversed(recent_records)  # 从最新开始

        message = "**当前阅读记录：**\n\n"
        for idx, record in enumerate(recent_records, start=1):
            reading_time_formatted = ""
            for r_idx, time in enumerate(record['reading_times'], start=1):
                reading_time_formatted += f"  - 第{r_idx}遍：{time} 分钟\n"
            message += (
                f"{idx}. 总词数：{record['total_words']}\n"
                f"   阅读时间：\n{reading_time_formatted}"
            )

        await ctx.reply(message)

    # 自动调用查看阅读数据
    reading_data_message = await generate_reading_data_message(user_id)
    await ctx.reply(reading_data_message)

# 查看阅读数据分析
@bot.command(name='查看阅读数据')
async def view_reading_data(ctx: Message):
    user_id = str(ctx.author_id)
    reading_data_message = await generate_reading_data_message(user_id)
    await ctx.reply(reading_data_message)

# 启动机器人
bot.run()
