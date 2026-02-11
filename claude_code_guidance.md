1. 项目初始化时：

- 在根目录新建 CLAUDE.md -> 写入不可变的项目规则（命令、规范）。

- 在根目录新建 CLAUDE.local.md -> 写入你个人的长期偏好（API Key、本地路径）。

- 跨项目的全局偏好或记忆，则需要通过prompt对话来激活，让claude code保存至/root/.claude/CLAUDE.md文件中，这样就不用一直去海量的history.jsonl中查找了

2. 日常开发中：

- 启动时：永远使用 claude -c 进入，保持上下文连贯。

- 更新记忆时：

    - 直接对 Claude 说："Save this logic to our memory"（它会自动更新 Auto Memory）。

    - 或者直接说："Add this rule to CLAUDE.md"（它会帮你编辑文件）。

3. 定期维护：

- 每隔一段时间，检查 ```~/.claude/projects/<项目>/memory/MEMORY.md```，手动修剪过时的信息，确保前 200 行是最精华的“长期记忆”。