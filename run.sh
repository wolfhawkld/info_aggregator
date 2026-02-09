#!/bin/bash
# RSS聚合助手快速启动脚本

cd "$(dirname "$0")"

echo "==================================="
echo "RSS AI聚合助手"
echo "==================================="

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "首次运行，正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装/更新依赖
if [ ! -f "venv/.deps_installed" ]; then
    echo "正在安装依赖..."
    pip install -r requirements.txt
    touch venv/.deps_installed
fi

# 检查配置
if [ ! -f "config/config.yaml" ]; then
    echo "错误: 配置文件不存在"
    echo "请先复制并编辑 config/config.yaml"
    exit 1
fi

# 运行程序
python3 main.py "$@"
