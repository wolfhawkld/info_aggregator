#!/bin/bash
# RSS聚合助手启动脚本
# 用途: crontab 定时任务调用

set -e

# 项目根目录（脚本所在目录）
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

# 日志目录
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# 日志文件（按日期）
LOG_FILE="$LOG_DIR/daily_$(date +%Y%m%d).log"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 每日任务启动" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误: 未找到虚拟环境" >> "$LOG_FILE"
    exit 1
fi

# 运行每日任务
python main.py --daily >> "$LOG_FILE" 2>&1

# 记录结束时间
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 每日任务完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"