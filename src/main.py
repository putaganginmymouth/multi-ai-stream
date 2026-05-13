"""
Multi-AI-Stream - Main Entry Point
主程序入口点
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from core.config import ConfigManager
from core.enums import LogLevel


def setup_logging(config):
    """设置日志系统"""
    log_level = getattr(logging, config.get('logging.level', 'INFO'))
    log_file = config.get('logging.file', './logs/app.log')
    
    # 确保日志目录存在
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def create_gui(config):
    """创建 GUI 界面"""
    try:
        from PyQt6.QtWidgets import QApplication
        
        from gui.main_window import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow(config)
        window.show()
        
        sys.exit(app.exec())
        
    except ImportError as e:
        logging.error(f"GUI 模块导入失败：{e}")
        logging.info("运行命令行模式...")
        run_cli_mode(config)


def create_cli(config):
    """创建命令行界面"""
    from core.config import get_config
    
    cfg = get_config()
    
    print("=" * 60)
    print("Multi-AI-Stream - Digital Human Live Streaming System")
    print("=" * 60)
    print(f"Version: {cfg.get('app.version', '1.0.0')}")
    print(f"Avatar Engine: {cfg.get('avatar.default_engine', 'live_portrait')}")
    print(f"TTS Engine: {cfg.get('tts.engine', 'coqui')}")
    print("=" * 60)
    
    # TODO: 实现命令行交互界面
    print("\n命令行模式暂未实现，请使用 GUI 版本。")


def main():
    """主函数"""
    try:
        # 加载配置
        config = ConfigManager.get_instance()
        
        # 设置日志
        setup_logging(config.to_dict())
        
        logging.info("Multi-AI-Stream 启动中...")
        
        # 检查 GUI 依赖
        gui_available = False
        try:
            import PyQt6
            gui_available = True
        except ImportError:
            pass
        
        if gui_available:
            create_gui(config)
        else:
            logging.warning("PyQt6 未安装，运行 CLI 模式")
            create_cli(config)
            
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        logging.exception(f"程序异常：{e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
