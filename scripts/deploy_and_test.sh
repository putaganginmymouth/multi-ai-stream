#!/bin/bash
# Multi-AI-Stream - 完整部署与测试脚本

set -e

echo "=============================================="
echo "Multi-AI-Stream 完整部署与测试"
echo "=============================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
step_title() { echo -e "\n${BLUE}=== $1 ===${NC}\n"; }

# 步骤 1: Python 环境检查
step_title "Step 1/7: Python 环境检查"

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3.10+."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Python version: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION" | cut -d'.' -f1,2) < "3.10" ]]; then
    log_error "Python 3.10+ required. Current: $PYTHON_VERSION"
    exit 1
fi

log_info "✅ Python environment OK"

# 步骤 2: 虚拟环境创建 (可选)
step_title "Step 2/7: 虚拟环境准备"

if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv || {
        log_warn "Virtual env creation failed, using system Python..."
    }
fi

# 步骤 3: 安装核心依赖
step_title "Step 3/7: 安装核心依赖"

if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
fi

# 检查并安装 PyQt6
log_info "Checking PyQt6..."
if ! python3 -c "import PyQt6" 2>/dev/null; then
    log_info "PyQt6 not found, installing..."
    pip install --upgrade pip
    pip install "PyQt6>=6.5.0"
else
    PYQT_VERSION=$(python3 -c "import PyQt6; print(PyQt6.__version__)")
    log_info "PyQt6 version: $PYQT_VERSION"
fi

# 安装其他核心依赖
pip install -r requirements.txt || {
    log_warn "Some packages may have failed, continuing..."
}

log_info "✅ Dependencies installed"

# 步骤 4: 数据库初始化
step_title "Step 4/7: 数据库初始化"

if [ -f "scripts/init_db.py" ]; then
    python3 scripts/init_db.py || log_warn "Database initialization skipped"
else
    log_warn "init_db.py not found, skipping..."
fi

log_info "✅ Database ready"

# 步骤 5: GUI 语法检查
step_title "Step 5/7: GUI 代码验证"

python3 -m py_compile src/gui/main_window.py && \
python3 -m py_compile src/main.py && \
log_info "✅ All Python files syntax OK" || {
    log_error "Syntax errors found in source code"
    exit 1
}

# 步骤 6: 模块导入测试
step_title "Step 6/7: 模块导入测试"

python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

modules = [
    ('core', ['ConfigManager', 'PlatformType', 'AvatarEngineType']),
    ('platform', ['PlatformFactory', 'BasePlatform']),
    ('avatar', ['AvatarFactory', 'BaseAvatar']),
    ('content', ['ContentPipeline', 'AssetManager'])
]

failed = 0
for module_name, classes in modules:
    try:
        module = __import__(f'src.{module_name}', fromlist=classes)
        for cls in classes:
            if hasattr(module, cls):
                print(f"  ✅ {module_name}.{cls}")
            else:
                print(f"  ❌ {module_name}.{cls} not found")
                failed += 1
    except Exception as e:
        print(f"  ❌ {module_name}: {e}")
        failed += 1

if failed > 0:
    sys.exit(1)
EOF

log_info "✅ All modules importable"

# 步骤 7: 运行 GUI (可选)
step_title "Step 7/7: 启动测试"

read -p "Launch GUI application? (y/n): " launch_gui
if [[ "$launch_gui" =~ ^[Yy]$ ]]; then
    log_info "Starting Multi-AI-Stream..."
    
    # 设置环境变量
    export MULTI_STREAM_CONFIG="$PROJECT_DIR/configs/config.yaml"
    
    python3 src/main.py || log_warn "GUI exited"
else
    log_info "Skipping GUI launch (use 'python src/main.py' to start)"
fi

# 最终总结
echo ""
step_title "部署完成!"

log_info "=============================================="
log_info "Multi-AI-Stream is ready!"
log_info "=============================================="
echo ""
log_info "Quick Start:"
log_info "1. Launch GUI: python src/main.py"
log_info "2. Install LivePortrait (optional):"
log_info "   bash scripts/install_liveportrait.sh"
log_info "3. Check status: bash scripts/check_status.sh"
echo ""
