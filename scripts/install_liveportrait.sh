#!/bin/bash
# Multi-AI-Stream - LivePortrait 快速部署脚本
# 一键安装和配置 LivePortrait 数字人引擎

set -e

echo "=============================================="
echo "Multi-AI-Stream LivePortrait 自动部署"
echo "=============================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LP_DIR="$PROJECT_DIR/LivePortrait"
MODELS_DIR="$PROJECT_DIR/assets/avatars/liveportrait"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 步骤 1: 克隆 LivePortrait 项目
install_liveportrait() {
    log_info "Step 1/4: Cloning LivePortrait repository..."
    
    if [ -d "$LP_DIR" ]; then
        log_warn "LivePortrait already exists, skipping clone."
        return 0
    fi
    
    git clone https://github.com/KwaiVGI/LivePortrait.git "$LP_DIR" || {
        log_error "Failed to clone LivePortrait repository."
        exit 1
    }
    
    log_info "LivePortrait cloned successfully!"
}

# 步骤 2: 安装 Python 依赖
install_dependencies() {
    log_info "Step 2/4: Installing Python dependencies..."
    
    cd "$LP_DIR"
    
    # 检测系统环境
    if [[ "$(uname)" == "Darwin" ]]; then
        log_info "Detected macOS, installing CPU/MPS version of PyTorch..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    elif [[ "$(uname)" == "Linux" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        log_info "Installing GPU-accelerated PyTorch (CUDA 11.8)..."
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    fi
    
    # 安装其他依赖
    pip install -r requirements.txt || {
        log_warn "Some dependencies may have failed, continuing anyway..."
    }
    
    cd "$PROJECT_DIR"
    log_info "Dependencies installed!"
}

# 步骤 3: 下载模型文件
download_models() {
    log_info "Step 3/4: Downloading model files..."
    
    mkdir -p "$MODELS_DIR"
    
    # 检查是否已有模型
    if [ -f "$LP_DIR/models/warping_module.pth" ]; then
        log_warn "Models already downloaded, skipping."
        return 0
    fi
    
    # 方法 1: 使用官方下载脚本 (优先)
    if [ -f "$LP_DIR/download_models.sh" ]; then
        cd "$LP_DIR"
        chmod +x download_models.sh
        ./download_models.sh || {
            log_warn "Official download script failed, trying manual download..."
        }
        cd "$PROJECT_DIR"
    fi
    
    # 方法 2: 手动下载 (备用方案)
    if [ ! -d "$LP_DIR/models" ] || [ -z "$(ls -A $LP_DIR/models 2>/dev/null)" ]; then
        log_info "Downloading models from HuggingFace..."
        
        mkdir -p "$LP_DIR/models"
        
        # 下载驱动提取器模型
        wget -q https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/driving_extractor.pth \
            -O "$LP_DIR/models/driving_extractor.pth" || {
            log_error "Failed to download driving_extractor.pth"
        }
        
        # 下载运动提取器模型  
        wget -q https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/motion_extractor.pth \
            -O "$LP_DIR/models/motion_extractor.pth" || {
            log_error "Failed to download motion_extractor.pth"
        }
        
        # 下载形变模块模型
        wget -q https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/warping_module.pth \
            -O "$LP_DIR/models/warping_module.pth" || {
            log_error "Failed to download warping_module.pth"
        }
        
        # 下载生成器模型
        wget -q https://huggingface.co/KwaiVGI/LivePortrait/resolve/main/spade_generator.pth \
            -O "$LP_DIR/models/spade_generator.pth" || {
            log_error "Failed to download spade_generator.pth"
        }
    fi
    
    # 创建符号链接到项目 assets
    ln -sf "$LP_DIR/models" "$MODELS_DIR" 2>/dev/null || true
    
    log_info "Models downloaded and linked!"
}

# 步骤 4: 配置项目
configure_project() {
    log_info "Step 4/4: Configuring Multi-AI-Stream..."
    
    # 更新配置文件
    CONFIG_FILE="$PROJECT_DIR/configs/config.yaml"
    
    if [ -f "$CONFIG_FILE" ]; then
        # 确保 LivePortrait 配置存在
        if ! grep -q "live_portrait:" "$CONFIG_FILE"; then
            log_info "Adding LivePortrait configuration..."
            
            cat >> "$CONFIG_FILE" << 'EOF'

# LivePortrait 特定配置
live_portrait:
    inference_dir: "../LivePortrait"
    batch_size: 1
    resize: true
    
# Wav2Lip 特定配置  
wav2lip:
    height: 512
    width: 512
    fps: 25

EOF
        fi
        
        log_info "Configuration updated!"
    else
        log_warn "Config file not found, skipping configuration."
    fi
    
    # 创建必要的目录结构
    mkdir -p "$PROJECT_DIR/assets/avatars"
    mkdir -p "$PROJECT_DIR/output"
    
    log_info "Directories created!"
}

# 验证安装
verify_installation() {
    log_info "Verifying installation..."
    
    local errors=0
    
    # 检查 LivePortrait 目录
    if [ ! -d "$LP_DIR" ]; then
        log_error "LivePortrait directory not found: $LP_DIR"
        ((errors++))
    else
        log_info "✅ LivePortrait directory exists"
    fi
    
    # 检查模型文件
    if [ -f "$LP_DIR/models/driving_extractor.pth" ] && \
       [ -f "$LP_DIR/models/motion_extractor.pth" ] && \
       [ -f "$LP_DIR/models/warping_module.pth" ] && \
       [ -f "$LP_DIR/models/spade_generator.pth" ]; then
        log_info "✅ All model files present"
    else
        log_error "❌ Some model files are missing"
        ((errors++))
    fi
    
    # 检查 Python 依赖
    if python -c "import torch; import cv2" 2>/dev/null; then
        log_info "✅ Required Python packages available"
        
        # GPU 状态
        python -c "
import torch
cuda = 'CUDA' if torch.cuda.is_available() else 'CPU'
mps = 'MPS' if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available() else ''
print(f'   Acceleration: {cuda} {mps}' | xargs)
" 2>/dev/null || true
    else
        log_error "❌ Python dependencies missing"
        ((errors++))
    fi
    
    if [ $errors -eq 0 ]; then
        echo ""
        log_info "=============================================="
        log_info "LivePortrait installation completed successfully!"
        log_info "=============================================="
        echo ""
        log_info "Next steps:"
        log_info "1. Run: python scripts/init_db.py"
        log_info "2. Install PyQt6 if not already installed:"
        log_info "   pip install PyQt6>=6.5.0"
        log_info "3. Launch application:"
        log_info "   cd multi-ai-stream && python src/main.py"
    else
        echo ""
        log_error "Installation completed with $errors error(s). Please review above."
        exit 1
    fi
}

# 主流程
main() {
    cd "$PROJECT_DIR" || exit 1
    
    echo ""
    log_info "Project directory: $PROJECT_DIR"
    echo ""
    
    # 执行所有步骤
    install_liveportrait
    install_dependencies
    download_models
    configure_project
    
    # 验证安装
    verify_installation
}

# 解析命令行参数
case "${1:-}" in
    --skip-clone)
        install_dependencies
        download_models
        configure_project
        ;;
    --skip-models)
        install_liveportrait
        install_dependencies
        configure_project
        ;;
    --verify-only)
        verify_installation
        ;;
    *)
        main
        ;;
esac
