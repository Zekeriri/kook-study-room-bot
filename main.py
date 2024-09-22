import khl
from datetime import datetime

# 创建一个机器人实例
bot = khl.Bot(token='1/MzI2NzM=/cyvZltzOh/GLLotmCqnVKw==')

# 用于存储用户的每日计划，格式为：{'用户ID': {'日期': '计划'}}
daily_plans = {}

# ping 命令
@bot.command()
async def ping(ctx: khl.Message):
    print("Ping command received")  # 打印调试信息
    await ctx.reply('Pong!')

# 添加每日计划的命令
@bot.command(name='add_plan')  # 确保命令的名称被正确注册
async def add_plan(ctx: khl.Message, *args):  # 使用 *args 来捕获所有参数
    plan = ' '.join(args)  # 将所有传入参数组合为一个字符串
    print(f"Received add_plan command with plan: {plan}")  # 打印调试信息
    if not plan:  # 检查是否输入了计划内容
        await ctx.reply("请提供计划内容！正确的命令格式为：!add_plan [你的计划内容]")
        return

    user_id = str(ctx.author.id)  # 获取用户 ID
    date = datetime.now().strftime('%Y-%m-%d')  # 获取当前日期

    # 检查用户是否已经有当天的计划
    if user_id not in daily_plans:
        daily_plans[user_id] = {}

    # 保存计划
    daily_plans[user_id][date] = plan
    await ctx.reply(f"你的计划已经添加：{plan}（日期：{date}）")

# 查看当天计划的命令
@bot.command(name='show_plan')
async def show_plan(ctx: khl.Message):
    user_id = str(ctx.author.id)
    date = datetime.now().strftime('%Y-%m-%d')

    # 检查是否有当天的计划
    if user_id in daily_plans and date in daily_plans[user_id]:
        plan = daily_plans[user_id][date]
        await ctx.reply(f"你今天的计划是：{plan}")
    else:
        await ctx.reply("你今天还没有添加计划！")

# 启动机器人
bot.run()
