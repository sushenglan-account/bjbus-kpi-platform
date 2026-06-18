#!/bin/bash
# 北京公交KPI看板启动脚本

echo "=================================="
echo "  北京公交KPI看板 - 智能问数平台  "
echo "=================================="
echo ""

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python版本: $python_version"

# 检查是否安装了依赖
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "检测到缺少依赖，正在安装..."
    pip3 install -r requirements.txt
fi

echo ""
echo "正在启动应用..."
echo "访问地址: http://localhost:8501"
echo ""
echo "按 Ctrl+C 停止应用"
echo ""

# 启动Streamlit应用
streamlit run app.py --server.port 8501 --server.address localhost
