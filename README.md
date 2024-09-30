## kook-study-room-bot

**Kook 机器人需求规范**

开发环境

python3.10 以上

khl.py

参考

[khl.py (khl-py.eu.org)](https://khl-py.eu.org/)

### 0. 共通需求

- **一天的时间定义**：一天从凌晨 5 点开始，到次日凌晨 5 点结束。
- **指令输出**：所有指令的输出结果都应包含所有有数据的人的信息，包括任务和学习时长。

### 1. 任务管理

- 添加任务

  ：

  - 指令：`/添加任务 [任务内容]`
  - 功能：将任务添加到用户的任务列表中。
  - 限制：一天内添加的任务数量不应超过一定限制（例如 10 个）。

- 删除任务

  ：

  - 指令：`/删除任务 [任务编号]`
  - 功能：从用户的任务列表中删除指定编号的任务。
  - 限制：只能删除自己添加的任务。

- 完成任务

  ：

  - 指令：`/完成任务 [任务编号]`
  - 功能：将指定编号的任务标记为已完成。
  - 限制：只能完成自己添加的任务。

- 查看任务

  ：

  - 指令：`/查看任务`
  - 功能：显示用户当天的任务列表，包括未完成任务和已完成任务（已完成任务用删除线标记）。

- 数据存储

  ：

  - 仅记录当天的任务，每天凌晨 5 点清空任务列表。

### 2. 学习时长记录

- 记录方式

  ：

  - 用户进入语音频道时开始记录学习时长。
  - 用户退出语音频道时停止记录时长。

- 查询命令

  ：

  - `/今日学习时长`：查询当天（从凌晨 5 点开始）的学习时长。
  - `/本周学习时长`：查询本周（从周一开始）的学习时长，包括每天的具体时长和总时长。
  - `/本月学习时长`：查询本月（从每月 1 号开始）的学习时长，包括每周的具体时长和总时长。
  - `/本年学习时长`：查询本年（从 1 月 1 日开始）的学习时长，包括每月的具体时长和总时长。
  - `/生涯学习时长`：查询所有记录的学习时长，包括每年的具体时长和总时长。

- 数据存储

  ：

  - 存储每个用户的学习时长记录，包括开始时间、结束时间和时长。
  - 每天凌晨 5 点计算并存储当天的总学习时长。
  - 每周、每月、每年结束时计算并存储相应的总学习时长。

### 3. 帮助指令

- **指令**：`/帮助` 或 `/help`

- 功能

  ：列出所有可用的指令及其使用方法，

  包括：

  - 任务管理指令：
    - `/添加任务 [任务内容]`
    - `/删除任务 [任务编号]`
    - `/完成任务 [任务编号]`
    - `/查看任务`
  - 学习时长查询指令：
    - `/今日学习时长`
    - `/本周学习时长`
    - `/本月学习时长`
    - `/本年学习时长`
    - `/生涯学习时长`

- **输出**：以清晰、易读的方式展示指令列表和使用方法，例如：

```
**可用指令：**

**任务管理**
- `/添加任务 [任务内容]`：添加一个新任务。
- `/删除任务 [任务编号]`：删除指定编号的任务。
- `/完成任务 [任务编号]`：将指定编号的任务标记为已完成。
- `/查看任务`：查看今天的任务列表。

**学习时长查询**
- `/今日学习时长`：查询今天的学习时长。
- `/本周学习时长`：查询本周的学习时长。
- `/本月学习时长`：查询本月的学习时长。
- `/本年学习时长`：查询本年的学习时长。
- `/生涯学习时长`：查询生涯总学习时长。
```

### 4. 错误处理和用户体验

#### 错误处理

- 无效指令或参数

  ：

  - 机器人应明确指出指令或参数无效的原因，

    例如：

    - “无效的指令，请使用 `/帮助` 查看可用指令。”
    - “任务编号无效，请检查后重试。”
    - “任务内容不能为空。”

  - 对于复杂的指令，可以提供更详细的使用说明。

- 意外情况

  ：

  - 机器人应捕获并处理可能出现的异常，例如网络错误、数据存储错误等。

  - 发生错误时，

    机器人应向用户返回友好的错误提示，

    例如：

    - “抱歉，系统出现错误，请稍后重试。”
    - “网络连接不稳定，请检查网络设置。”

  - 同时，机器人应将错误信息记录到日志中，以便后续排查和解决问题。

#### 用户体验

- 及时性

  ：

  - 机器人应尽可能快速地响应用户的指令，避免长时间等待。
  - 对于需要较长时间处理的请求，可以先给用户一个即时反馈，例如“正在处理您的请求，请稍候...”，并在处理完成后再给出最终结果。

- 准确性

  ：

  - 机器人应确保返回的信息准确无误，避免误导用户。
  - 对于需要计算或查询的数据，应进行严格的校验和处理，确保结果的正确性。

- 友好性

  ：

  - 机器人的回复应使用礼貌、友好的语言，避免生硬或冷漠的表达。
  - 可以根据不同的场景和用户的情绪，适当调整回复的语气和风格。

- 易用性

  ：

  - 指令的设计应简单易懂，符合用户的习惯。
  - 可以使用自然语言处理技术，让机器人理解更口语化的指令。
  - 对于复杂的指令，可以提供示例或更详细的说明。