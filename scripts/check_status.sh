#!/bin/bash
# Multi-AI-Stream - 项目状态快速检查脚本

echo "=============================================="
echo "Multi-AI-Stream 项目状态检查"
echo "=============================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_item() {
    local name="$1"
    local command="$2"
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "✅ $name"
        return 0
    else
        echo -e "❌ $name"
        return 1
    fi
}

echo ""
echo "[系统环境]"
python3 --version 2>/dev/null && echo "   Python 版本 OK" || echo "   ❌ Python 未安装"
command -v pip3 > /dev/null && echo "✅ pip3 available" || echo "❌ pip3 not found"

echo ""
echo "[项目结构]"
check_item "src directory" "test -d src"
check_item "configs directory" "test -d configs"
check_item "tests directory" "test -d tests"
check_item "assets directory" "test -d assets"

echo ""
echo "[核心文件]"
check_item "config.yaml" "test -f configs/config.yaml"
check_item "requirements.txt" "test -f requirements.txt"
check_item "main.py" "test -f src/main.py"
check_item "README.md" "test -f README.md"

echo ""
echo "[Python 依赖]"
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

packages = ['PyQt6', 'sqlalchemy', 'pyyaml', 'numpy']
for pkg in packages:
    try:
        __import__(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} not installed")
EOF

echo ""
echo "[模块完整性]"
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

modules = {
    'core': ['ConfigManager', 'PlatformType'],
    'platform': ['PlatformFactory', 'DouyinPlatform'],
    'avatar': ['AvatarFactory', 'LivePortraitEngine'],
    'content': ['ContentPipeline', 'AssetManager']
}

for module, classes in modules.items():
    try:
        m = __import__(f'src.{module}', fromlist=classes)
        all_exist = all(hasattr(m, c) for c in classes)
        status = "✅" if all_exist else "❌"
        print(f"{status} src/{module}")
    except Exception as e:
        print(f"❌ src/{module}: {e}")
EOF

echo ""
echo "[LivePortrait 集成]"
if [ -d "LivePortrait" ]; then
    echo "✅ LivePortrait directory exists"
    
    if [ -f "LivePortrait/models/warping_module.pth" ]; then
        echo "✅ Model files present"
    else
        echo "❌ Models not downloaded (run: bash scripts/install_liveportrait.sh)"
    fi
else
    echo "❌ LivePortrait not installed"
fi

echo ""
echo "[数据库]"
if [ -f "data/multi_ai_stream.db" ]; then
    DB_SIZE=$(du -h data/multi_ai_stream.db | cut -f1)
    echo "✅ Database exists ($DB_SIZE)"
else
    echo "⚠️  Database not initialized (run: python scripts/init_db.py)"
fi

echo ""
echo "[测试覆盖]"
if [ -d "tests" ] && ls tests/test_*.py >/dev/null 2>&1; then
    TEST_COUNT=$(ls tests/test_*.py | wc -l)
    echo "✅ $TEST_COUNT test files found"
else
    echo "⚠️  No test files found"
fi

echo ""
echo "[文档]"
DOC_FILES=("README.md" "DESIGN_SPEC.md" "USER_GUIDE.md")
for doc in "${DOC_FILES[@]}"; do
    if [ -f "$doc" ]; then
        SIZE=$(wc -c < "$doc")
        echo "✅ $doc ($SIZE bytes)"
    else
        echo "❌ $doc missing"
    fi
done

echo ""
echo "=============================================="
echo "检查完成!"
echo "=============================================="
echo ""
echo "下一步操作:"
echo "1. 安装 PyQt6: pip install PyQt6>=6.5.0"
echo "2. 初始化数据库：python scripts/init_db.py"
echo "3. 启动 GUI: python src/main.py"
echo ""
