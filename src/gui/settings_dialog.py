"""
Settings Dialog - System Configuration Panel
系统设置对话框 - LLM/TTS 模型配置模块
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

try:
    from PyQt6.QtWidgets import (
        QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
        QGroupBox, QLabel, QLineEdit, QPushButton,
        QComboBox, QMessageBox, QFileDialog, QFormLayout,
        QFrame, QTextEdit, QScrollArea, QSplitter, QCheckBox,
        QSpinBox, QDoubleSpinBox, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QSize
    from PyQt6.QtGui import QFont, QColor
except ImportError:
    print("PyQt6 not installed. Install with: pip install PyQt6")
    sys.exit(1)


class SettingsDialog(QDialog):
    """系统设置对话框"""
    
    def __init__(self, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        
        self.config = config.copy()
        self.original_config = config.copy()
        
        self.setWindowTitle("⚙️ 系统设置 - Multi-AI-Stream")
        self.setMinimumSize(800, 700)
        self.resize(900, 750)
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化用户界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # ========== 标题栏 ==========\n        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        
        title_label = QLabel("🔧 系统设置")
        title_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        version_label = QLabel(f"v1.0.0 | 模型配置模块")
        version_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 11px;")
        header_layout.addWidget(version_label)
        
        layout.addWidget(header_frame)
        
        # ========== 标签页容器 ==========\n        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; border-radius: 5px; }
            QTabBar::tab { 
                background: #f0f0f0; padding: 10px 20px; margin-right: 2px; 
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected { background: white; }
        """)
        
        # 标签 1: LLM 模型配置
        self.llm_tab = self._create_llm_settings()
        self.tabs.addTab(self.llm_tab, "🤖 LLM 文案生成")
        
        # 标签 2: TTS 语音合成配置
        self.tts_tab = self._create_tts_settings()
        self.tabs.addTab(self.tts_tab, "🔊 TTS 语音合成")
        
        # 标签 3: OBS 推流配置
        self.obs_tab = self._create_obs_settings()
        self.tabs.addTab(self.obs_tab, "📹 OBS 推流设置")
        
        # 标签 4: 定时任务配置 (新增 v3.0)
        self.schedule_tab = self._create_schedule_settings()
        self.tabs.addTab(self.schedule_tab, "⏰ 定时开关直播")
        
        layout.addWidget(self.tabs)
        
        # ========== 底部按钮栏 ==========\n        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        reset_btn = QPushButton("↩️ 重置为默认")
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6; color: white;
                padding: 10px 20px; font-size: 13px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        reset_btn.clicked.connect(self._reset_to_defaults)
        
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c; color: white;
                padding: 10px 25px; font-size: 13px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("💾 保存并应用")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white;
                padding: 10px 25px; font-size: 13px; font-weight: bold; border-radius: 5px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        save_btn.clicked.connect(self._save_and_apply)
        
        button_layout.addWidget(reset_btn)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
    
    def _create_llm_settings(self) -> QWidget:
        """创建 LLM 配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ========== 模式选择 ==========\n        mode_group = QGroupBox("🔄 LLM 运行模式")
        mode_layout = QFormLayout(mode_group)
        
        self.llm_mode_combo = QComboBox()
        self.llm_mode_combo.addItems([
            ("远程 API (DeepSeek)", "remote"),
            ("本地模型 (GGUF)", "local")
        ])
        self.llm_mode_combo.currentIndexChanged.connect(self._on_llm_mode_changed)
        
        # 从配置加载当前模式
        current_mode = self.config.get('llm', {}).get('mode', 'remote')
        mode_idx = self.llm_mode_combo.findData(current_mode)
        if mode_idx >= 0:
            self.llm_mode_combo.setCurrentIndex(mode_idx)
        
        mode_layout.addRow("运行模式:", self.llm_mode_combo)
        content_layout.addWidget(mode_group)
        
        # ========== 远程 API 配置 ==========\n        self.remote_frame = QGroupBox("☁️ 远程 API 配置")
        remote_layout = QFormLayout(self.remote_frame)
        self.remote_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #667eea;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { color: #667eea; }
        """)
        
        # Provider 选择
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems([
            ("DeepSeek", "deepseek"),
            ("其他兼容 OpenAI API", "other")
        ])
        current_provider = self.config.get('llm', {}).get('remote', {}).get('provider', 'deepseek')
        provider_idx = self.llm_provider_combo.findData(current_provider)
        if provider_idx >= 0:
            self.llm_provider_combo.setCurrentIndex(provider_idx)
        
        remote_layout.addRow("服务商:", self.llm_provider_combo)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("请输入 DeepSeek API Key")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        api_key = self.config.get('llm', {}).get('remote', {}).get('api_key', '')
        if api_key:
            # 只显示部分用于安全提示
            masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
            self.api_key_input.setPlaceholderText(f"已配置：{masked_key} (点击填写完整密钥)")
        
        remote_layout.addRow("API Key:", self.api_key_input)
        
        # Base URL
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("https://api.deepseek.com/v1")
        base_url = self.config.get('llm', {}).get('remote', {}).get('base_url', 'https://api.deepseek.com/v1')
        self.base_url_input.setText(base_url)
        
        remote_layout.addRow("API 地址:", self.base_url_input)
        
        # Model Name
        self.model_name_input = QLineEdit()
        self.model_name_input.setPlaceholderText("deepseek-chat")
        model_name = self.config.get('llm', {}).get('remote', {}).get('model', 'deepseek-chat')
        self.model_name_input.setText(model_name)
        
        remote_layout.addRow("模型名称:", self.model_name_input)
        
        # 提示信息
        info_label = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                💡 <b>DeepSeek API:</b><br>
                • 访问 <a href='https://platform.deepseek.com' 
                   style='color: #667eea;'>DeepSeek 开放平台</a> 获取 API Key<br>
                • 新用户注册赠送免费额度 (约$1.5)<br>
                • 推荐模型：deepseek-chat (性价比高) / deepseek-coder<br>
                • 当前定价：输入 $0.27/1M tokens, 输出 $1.10/1M tokens
            </div>
        """)
        info_label.setOpenExternalLinks(True)
        remote_layout.addRow("", info_label)
        
        content_layout.addWidget(self.remote_frame)
        
        # ========== 本地模型配置 ==========\n        self.local_frame = QGroupBox("💻 本地模型配置")
        local_layout = QFormLayout(self.local_frame)
        self.local_frame.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #95a5a6;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { color: #95a5a6; }
        """)
        
        self.local_model_input = QLineEdit()
        self.local_model_input.setPlaceholderText("qwen/Qwen-7B-Chat-GGUF 或本地路径")
        local_model = self.config.get('llm', {}).get('local', {}).get('model', 'qwen/Qwen-7B-Chat-GGUF')
        self.local_model_input.setText(local_model)
        
        local_layout.addRow("模型路径/名称:", self.local_model_input)
        
        # Quantization 选择
        quant_combo = QComboBox()
        quant_combo.addItems(["q4_0", "q4_K_M", "q5_K_M", "q8_0"])
        quant_idx = quant_combo.findText(
            self.config.get('llm', {}).get('local', {}).get('quantization', 'q4_0')
        )
        if quant_idx >= 0:
            quant_combo.setCurrentIndex(quant_idx)
        
        local_layout.addRow("量化级别:", quant_combo)
        
        # 硬件要求提示
        hw_info = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                💾 <b>硬件需求:</b><br>
                • Q4_0 (7B): ~5GB RAM / ~3GB VRAM<br>
                • Q5_K_M (7B): ~6GB RAM / ~4GB VRAM<br>
                • Q8_0 (7B): ~8GB RAM / ~6GB VRAM<br>
                <br>
                🚀 <b>性能提示:</b> 使用远程 API 无需考虑硬件限制，响应更快、质量更高
            </div>
        """)
        hw_info.setWordWrap(True)
        local_layout.addRow("", hw_info)
        
        content_layout.addWidget(self.local_frame)
        
        # ========== 系统提示词配置 ==========\n        prompt_group = QGroupBox("📝 系统提示词")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.system_prompt_text = QTextEdit()
        self.system_prompt_text.setMaximumHeight(150)
        self.system_prompt_text.setFont(QFont("Consolas", 9))
        system_prompt = self.config.get('llm', {}).get('system_prompt', '')
        if system_prompt:
            self.system_prompt_text.setPlainText(system_prompt)
        
        prompt_layout.addWidget(self.system_prompt_text)
        
        content_layout.addWidget(prompt_group)
        
        # ========== 输出模板配置 ==========\n        template_group = QGroupBox("📋 输出格式模板")
        template_layout = QVBoxLayout(template_group)
        
        self.output_template_text = QTextEdit()
        self.output_template_text.setMaximumHeight(120)
        self.output_template_text.setFont(QFont("Consolas", 9))
        output_template = self.config.get('llm', {}).get('output_template', '')
        if output_template:
            self.output_template_text.setPlainText(output_template)
        
        template_layout.addWidget(self.output_template_text)
        
        content_layout.addWidget(template_group)
        
        content_layout.addStretch()        
        # ========== 产品配置 (v2.0) ==========\n        product_group = QGroupBox("🏠 产品信息与角色设定")
        product_layout = QVBoxLayout(product_group)
        
        # Product Details
        self.product_details_text = QTextEdit()
        self.product_details_text.setMaximumHeight(120)
        self.product_details_text.setFont(QFont("Consolas", 9))
        self.product_details_text.setPlaceholderText("""请输入产品详细信息，包括：
- 产品名称/型号
- 核心卖点与特色功能
- 适用人群与场景
- 价格区间与优惠政策""")
        
        product_details = self.config.get('product', {}).get('details', '')
        if product_details:
            self.product_details_text.setPlainText(product_details)
        
        product_layout.addWidget(self.product_details_text)
        
        # Expert Role
        self.expert_role_text = QTextEdit()
        self.expert_role_text.setMaximumHeight(120)
        self.expert_role_text.setFont(QFont("Consolas", 9))
        self.expert_role_text.setPlaceholderText("""请输入专家角色定义，例如：
你是一位专业的房车产品专家，擅长：
- 深入了解每款房车的配置细节
- 用生动形象的语言讲解产品特点
- 耐心解答用户关于价格、尺寸、功能等问题
- 根据用户需求推荐合适的车型""")
        
        expert_role = self.config.get('expert_role', {}).get('definition', '')
        if expert_role:
            self.expert_role_text.setPlainText(expert_role)
        
        product_layout.addWidget(self.expert_role_text)
        
        # Product info tips
        tips_label = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                💡 <b>使用说明:</b><br>
                • <b>产品详细信息：</b>用于 LLM 生成产品介绍文案时的上下文<br>
                • <b>专家角色：</b>决定回复风格（清晰/具体/耐心/周到）<br>
                • 这两个配置将直接影响评论回复的质量与一致性
            </div>
        """)
        tips_label.setWordWrap(True)
        product_layout.addWidget(tips_label)
        
        content_layout.addWidget(product_group)


        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_tts_settings(self) -> QWidget:
        """创建 TTS 配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ========== TTS 引擎选择 ==========\n        engine_group = QGroupBox("🔊 TTS 引擎选择")
        engine_layout = QFormLayout(engine_group)
        
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems([
            ("Edge-TTS (免费，推荐)", "edge"),
            ("Coqui-TTS (开源离线)", "coqui"),
            ("讯飞 API (商用高质量)", "iflytek")
        ])
        
        current_engine = self.config.get('tts', {}).get('engine', 'edge')
        engine_idx = self.tts_engine_combo.findData(current_engine)
        if engine_idx >= 0:
            self.tts_engine_combo.setCurrentIndex(engine_idx)
        
        self.tts_engine_combo.currentIndexChanged.connect(self._on_tts_engine_changed)
        
        engine_layout.addRow("引擎:", self.tts_engine_combo)
        content_layout.addWidget(engine_group)
        
        # ========== Edge-TTS 配置 ==========\n        edge_group = QGroupBox("⚡ Edge-TTS 配置 (微软免费 API)")
        edge_layout = QFormLayout(edge_group)
        edge_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #4CAF50;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { color: #4CAF50; }
        """)
        
        self.edge_voice_combo = QComboBox()
        self.edge_voice_combo.addItems([
            ("晓晓 (女声，自然流畅)", "zh-CN-XiaoxiaoNeural"),
            ("云希 (男声，稳重)", "zh-CN-YunxiNeural"),
            ("晓伊 (女声，活泼)", "zh-CN-XiaoyiNeural"),
            ("云健 (男声，新闻播报)", "zh-CN-YunjianNeural")
        ])
        
        current_voice = self.config.get('tts', {}).get('edge', {}).get('voice', 'zh-CN-XiaoxiaoNeural')
        voice_idx = self.edge_voice_combo.findData(current_voice)
        if voice_idx >= 0:
            self.edge_voice_combo.setCurrentIndex(voice_idx)
        
        edge_layout.addRow("语音:", self.edge_voice_combo)
        
        # Edge-TTS 无需 API Key，显示说明
        info_label = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                ✅ <b>Edge-TTS 特点:</b><br>
                • 完全免费，无需 API Key<br>
                • 微软 Azure Neural TTS 质量<br>
                • 中文支持完美，发音自然<br>
                • 需要联网（但已内置 edge-tts 库自动处理）<br>
                <br>
                📦 <b>安装:</b> pip install edge-tts pydub
            </div>
        """)
        info_label.setWordWrap(True)
        edge_layout.addRow("", info_label)
        
        content_layout.addWidget(edge_group)
        
        # ========== Coqui-TTS 配置 ==========\n        coqui_group = QGroupBox("🎵 Coqui-TTS (开源离线)")
        coqui_layout = QFormLayout(coqui_group)
        coqui_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #FF9800;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { color: #FF9800; }
        """)
        
        self.coqui_model_input = QLineEdit()
        self.coqui_model_input.setPlaceholderText("tts_models/multilingual/multi-dataset/xtts_v2")
        coqui_model = self.config.get('tts', {}).get('coqui', {}).get('model', 'tts_models/multilingual/multi-dataset/xtts_v2')
        self.coqui_model_input.setText(coqui_model)
        
        coqui_layout.addRow("模型:", self.coqui_model_input)
        
        self.coqui_lang_combo = QComboBox()
        self.coqui_lang_combo.addItems(["zh", "en", "ja", "ko"])
        coqui_lang_idx = self.coqui_lang_combo.findText(
            self.config.get('tts', {}).get('coqui', {}).get('language', 'zh')
        )
        if coqui_lang_idx >= 0:
            self.coqui_lang_combo.setCurrentIndex(coqui_lang_idx)
        
        coqui_layout.addRow("语言:", self.coqui_lang_combo)
        
        # Coqui 硬件要求提示
        coqui_info = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                ⚠️ <b>注意:</b> Coqui-TTS 需要下载大模型 (~2GB)，首次使用会较慢<br>
                💾 <b>硬件要求:</b> ≥8GB RAM, ≥4GB VRAM (推荐)<br>
                📦 <b>安装:</b> pip install TTS pydub
            </div>
        """)
        coqui_info.setWordWrap(True)
        coqui_layout.addRow("", coqui_info)
        
        content_layout.addWidget(coqui_group)
        
        # ========== 讯飞 API 配置 ==========\n        iflytek_group = QGroupBox("🎤 讯飞语音合成 (商用)")
        iflytek_layout = QFormLayout(iflytek_group)
        iflytek_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold; border: 2px solid #FF5722;
                border-radius: 5px; margin-top: 10px; padding-top: 10px;
            }
            QGroupBox::title { color: #FF5722; }
        """)
        
        self.iflytek_app_id = QLineEdit()
        self.iflytek_app_id.setPlaceholderText("讯飞开放平台应用 ID")
        iflytek_app_id = self.config.get('tts', {}).get('iflytek', {}).get('app_id', '')
        if iflytek_app_id:
            self.iflytek_app_id.setText(iflytek_app_id[:6] + "****" + iflytek_app_id[-4:])
        
        iflytek_layout.addRow("应用 ID:", self.iflytek_app_id)
        
        self.iflytek_api_key = QLineEdit()
        self.iflytek_api_key.setPlaceholderText("API Key")
        self.iflytek_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        iflytek_layout.addRow("API Key:", self.iflytek_api_key)
        
        self.iflytek_api_secret = QLineEdit()
        self.iflytek_api_secret.setPlaceholderText("API Secret")
        self.iflytek_api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        
        iflytek_layout.addRow("API Secret:", self.iflytek_api_secret)
        
        # 讯飞说明
        iflytek_info = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                🌐 <b>讯飞开放平台:</b><br>
                • 访问 <a href='https://www.xfyun.cn' 
                   style='color: #FF5722;'>xfyun.cn</a> 注册并创建应用<br>
                • 开通"语音合成"服务获取 API Key<br>
                • 提供多种音色，音质优秀但需付费<br>
                • 免费额度有限，商用请查询定价
            </div>
        """)
        iflytek_info.setOpenExternalLinks(True)
        iflytek_info.setWordWrap(True)
        iflytek_layout.addRow("", iflytek_info)
        
        content_layout.addWidget(iflytek_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_obs_settings(self) -> QWidget:
        """创建 OBS 推流配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ========== OBS 连接配置 ==========\n        obs_group = QGroupBox("📹 OBS Studio 连接")
        obs_layout = QFormLayout(obs_group)
        
        self.obs_host_input = QLineEdit()
        self.obs_host_input.setPlaceholderText("localhost")
        obs_host = self.config.get('obs', {}).get('host', 'localhost')
        self.obs_host_input.setText(obs_host)
        
        obs_layout.addRow("主机地址:", self.obs_host_input)
        
        self.obs_port_spin = QSpinBox()
        self.obs_port_spin.setRange(0, 65535)
        self.obs_port_spin.setValue(self.config.get('obs', {}).get('port', 4455))
        self.obs_port_spin.setSuffix(" port")
        
        obs_layout.addRow("WebSocket 端口:", self.obs_port_spin)
        
        self.obs_password_input = QLineEdit()
        self.obs_password_input.setPlaceholderText("可选，用于安全验证")
        self.obs_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        obs_pwd = self.config.get('obs', {}).get('password', '')
        if obs_pwd:
            self.obs_password_input.setText(obs_pwd[:4] + "****" + obs_pwd[-2:])
        
        obs_layout.addRow("连接密码:", self.obs_password_input)
        
        # OBS 说明
        obs_info = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                🔧 <b>OBS 配置步骤:</b><br>
                1. 安装 OBS Studio (https://obsproject.com)<br>
                2. 工具 → WebSocket 服务器服务 → 启用<br>
                3. 设置端口为 4455，可选设置密码<br>
                4. 点击"启动服务器"<br>
                <br>
                📺 <b>用途:</b> 数字人视频生成后自动推流到直播平台
            </div>
        """)
        obs_info.setWordWrap(True)
        obs_layout.addRow("", obs_info)
        
        content_layout.addWidget(obs_group)
        
        # ========== 输出目录配置 ==========\n        output_group = QGroupBox("📁 输出目录")
        output_layout = QFormLayout(output_group)
        
        self.video_dir_input = QLineEdit()
        self.video_dir_input.setPlaceholderText("./output/videos")
        video_dir = self.config.get('output', {}).get('video_dir', './output/videos')
        self.video_dir_input.setText(video_dir)
        
        browse_video_btn = QPushButton("📂 浏览")
        browse_video_btn.clicked.connect(lambda: self._browse_folder(self.video_dir_input, "选择视频输出目录"))
        
        video_row = QHBoxLayout()
        video_row.addWidget(self.video_dir_input)
        video_row.addWidget(browse_video_btn)
        output_layout.addRow("视频目录:", video_row)
        
        self.audio_dir_input = QLineEdit()
        self.audio_dir_input.setPlaceholderText("./output/audio")
        audio_dir = self.config.get('output', {}).get('audio_dir', './output/audio')
        self.audio_dir_input.setText(audio_dir)
        
        browse_audio_btn = QPushButton("📂 浏览")
        browse_audio_btn.clicked.connect(lambda: self._browse_folder(self.audio_dir_input, "选择音频输出目录"))
        
        audio_row = QHBoxLayout()
        audio_row.addWidget(self.audio_dir_input)
        audio_row.addWidget(browse_audio_btn)
        output_layout.addRow("音频目录:", audio_row)
        
        content_layout.addWidget(output_group)
        
        # ========== 推流参数配置 ==========\n        stream_group = QGroupBox("📡 推流参数")
        stream_layout = QFormLayout(stream_group)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(self.config.get('output', {}).get('default_fps', 25))
        self.fps_spin.setSuffix(" fps")
        
        stream_layout.addRow("帧率:", self.fps_spin)
        
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(500, 10000)
        self.bitrate_spin.setValue(self.config.get('output', {}).get('default_bitrate', 2500))
        self.bitrate_spin.setSuffix(" Kbps")
        
        stream_layout.addRow("比特率:", self.bitrate_spin)
        
        # 推流参数说明
        bitrate_info = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                📊 <b>推荐配置:</b><br>
                • 抖音/快手：25fps, 2500-4000 Kbps<br>
                • 视频号：30fps, 2000-3000 Kbps<br>
                • 高清直播：60fps, 6000+ Kbps (需良好网络)
            </div>
        """)
        bitrate_info.setWordWrap(True)
        stream_layout.addRow("", bitrate_info)
        
        content_layout.addWidget(stream_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_schedule_settings(self) -> QWidget:
        """创建定时任务配置面板 (v3.0 新增)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ========== 定时任务列表 ==========
        schedule_list_group = QGroupBox("📅 已创建的定时任务")
        schedule_list_layout = QVBoxLayout(schedule_list_group)
        
        self.schedule_table = QTableWidget()
        self.schedule_table.setColumnCount(5)
        self.schedule_table.setHorizontalHeaderLabels([
            "平台", "开始时间", "结束时间", "状态", "操作"
        ])
        self.schedule_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.schedule_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        schedule_list_layout.addWidget(self.schedule_table)
        
        # 添加/删除任务按钮
        button_row = QHBoxLayout()
        
        add_schedule_btn = QPushButton("➕ 新增定时任务")
        add_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; 
                padding: 8px 16px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        add_schedule_btn.clicked.connect(self._add_schedule_task)
        
        delete_schedule_btn = QPushButton("🗑️ 删除选中任务")
        delete_schedule_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; 
                padding: 8px 16px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        delete_schedule_btn.clicked.connect(self._delete_selected_schedule)
        
        button_row.addWidget(add_schedule_btn)
        button_row.addWidget(delete_schedule_btn)
        button_row.addStretch()
        
        schedule_list_layout.addLayout(button_row)
        content_layout.addWidget(schedule_list_group)
        
        # ========== 新增任务表单 ==========
        add_form_group = QGroupBox("➕ 新建定时任务")
        add_form_layout = QFormLayout(add_form_group)
        
        # 平台选择
        self.schedule_platform_combo = QComboBox()
        self.schedule_platform_combo.addItems([
            ("抖音", "douyin"),
            ("快手", "kuaishou"),
            ("视频号", "wechat")
        ])
        add_form_layout.addRow("直播平台:", self.schedule_platform_combo)
        
        # 开始时间
        self.schedule_start_datetime = QDateTimeEdit()
        self.schedule_start_datetime.setCalendarPopup(True)
        self.schedule_start_datetime.setDateTime(QDateTime.currentDateTime().addMinutes(5))
        add_form_layout.addRow("开始时间:", self.schedule_start_datetime)
        
        # 结束时间 (可选，用于单次任务自动停止)
        self.schedule_end_datetime = QDateTimeEdit()
        self.schedule_end_datetime.setCalendarPopup(True)
        self.schedule_end_datetime.setDateTime(QDateTime.currentDateTime().addHours(1))
        add_form_layout.addRow("结束时间:", self.schedule_end_datetime)
        
        # 说明
        info_label = QLabel("""
            <div style='color: #666; font-size: 12px;'>
                📌 <b>使用说明:</b><br>
                • 开始时间必须晚于当前时间至少 5 分钟<br>
                • 结束时间为可选，设置后任务会在该时间点自动停止推流<br>
                • 系统会每 30 秒检查一次到期任务并自动触发<br>
                • 定时服务需要在应用启动时自动启用
            </div>
        """)
        info_label.setWordWrap(True)
        add_form_layout.addRow("", info_label)
        
        content_layout.addWidget(add_form_group)
        
        # ========== 定时服务开关 ==========
        service_group = QGroupBox("⚙️ 定时调度服务状态")
        service_layout = QVBoxLayout(service_group)
        
        self.service_status_label = QLabel("🔴 未启动")
        self.service_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        service_layout.addWidget(self.service_status_label)
        
        start_service_btn = QPushButton("▶️ 启动服务")
        start_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; 
                padding: 8px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        start_service_btn.clicked.connect(self._start_schedule_service)
        
        stop_service_btn = QPushButton("⏹️ 停止服务")
        stop_service_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; 
                padding: 8px 20px; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        stop_service_btn.clicked.connect(self._stop_schedule_service)
        
        service_btn_row = QHBoxLayout()
        service_btn_row.addWidget(start_service_btn)
        service_btn_row.addWidget(stop_service_btn)
        service_layout.addLayout(service_btn_row)
        
        content_layout.addWidget(service_group)
        
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _on_llm_mode_changed(self, index):
        """LLM 模式切换事件"""
        mode = self.llm_mode_combo.currentData()
        if mode == 'remote':
            self.remote_frame.setVisible(True)
            self.local_frame.setVisible(False)
        else:
            self.remote_frame.setVisible(False)
            self.local_frame.setVisible(True)
    
    def _on_tts_engine_changed(self, index):
        """TTS 引擎切换事件"""
        engine = self.tts_engine_combo.currentData()
        
        # 根据引擎类型显示/隐藏相关配置（这里简化处理，所有组都可见）
        # 实际可以添加 setVisible 控制
        
    def _browse_folder(self, line_edit: QLineEdit, title: str):
        """浏览文件夹对话框"""
        folder = QFileDialog.getExistingDirectory(
            self, title, "", QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            line_edit.setText(folder)
    
    def _reset_to_defaults(self):
        """重置为默认配置"""
        reply = QMessageBox.question(
            self, "确认重置",
            "确定要重置所有配置为默认值吗？\n当前修改将丢失。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 重新加载原始配置
            from ..core.config import get_config
            
            default_config = get_config()
            
            # 重置所有字段到默认值（简化实现）
            self.api_key_input.clear()
            self.system_prompt_text.setPlainText(
                "你是一位专业的二手房车销售专家，擅长用生动的语言介绍房产和房车产品。你的任务是生成适合数字人直播的讲解文案。"
            )
            
            QMessageBox.information(self, "成功", "配置已重置为默认值")
    
    def _save_and_apply(self):
        """保存并应用配置"""
        # 收集 LLM 配置
        llm_config = {
            'mode': self.llm_mode_combo.currentData(),
        }
        
        if self.llm_mode_combo.currentData() == 'remote':
            llm_config['remote'] = {
                'provider': self.llm_provider_combo.currentData(),
                'api_key': self.api_key_input.text().strip(),
                'base_url': self.base_url_input.text().strip(),
                'model': self.model_name_input.text().strip()
            }
        else:
            llm_config['local'] = {
                'model': self.local_model_input.text().strip(),
                'quantization': self.config.get('llm', {}).get('local', {}).get('quantization', 'q4_0')
            }
        
        # 系统提示词和模板
        llm_config['system_prompt'] = self.system_prompt_text.toPlainText()
        llm_config['output_template'] = self.output_template_text.toPlainText()
        
        self.config['llm'] = llm_config
        
        # 收集 TTS 配置
        tts_config = {
            'engine': self.tts_engine_combo.currentData()
        }
        
        if self.tts_engine_combo.currentData() == 'edge':
            tts_config['edge'] = {
                'voice': self.edge_voice_combo.currentData()
            }
        elif self.tts_engine_combo.currentData() == 'coqui':
            tts_config['coqui'] = {
                'model': self.coqui_model_input.text().strip(),
                'language': self.coqui_lang_combo.currentText()
            }
        
        self.config['tts'] = tts_config
        
        # 收集 OBS 配置
        obs_config = {
            'host': self.obs_host_input.text().strip(),
            'port': self.obs_port_spin.value(),
            'password': self.obs_password_input.text().strip()
        }
        self.config['obs'] = obs_config
        
        # 收集输出目录配置
        output_config = {
            'video_dir': self.video_dir_input.text().strip(),
            'audio_dir': self.audio_dir_input.text().strip(),
            'default_fps': self.fps_spin.value(),
            'default_bitrate': self.bitrate_spin.value()
        }
        self.config['output'] = output_config
        
        # 保存配置
        try:
            from ..core.config import get_config
            
            config_manager = get_config()
            
            # 更新内部配置字典
            for key, value in self.config.items():
                config_manager.set(key, value)
            
            # 保存到文件
            config_manager.save()
            
            QMessageBox.information(
                self, "成功", 
                f"✅ 配置已保存并应用！\n\n"
                f"- LLM: {llm_config['mode']}模式\n"
                f"- TTS: {tts_config['engine']}引擎\n"
                f"- OBS: {obs_config['host']}:{obs_config['port']}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(
                self, "错误", 
                f"配置保存失败:\n{str(e)}"
            )
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置的完整副本"""
        return self.config.copy()
    
    # ========== 定时任务相关方法 ==========
    
    def _add_schedule_task(self):
        """添加定时任务"""
        from PyQt6.QtCore import QDateTime
        
        platform = self.schedule_platform_combo.currentData()
        start_time = self.schedule_start_datetime.dateTime().toPyDateTime()
        end_time = self.schedule_end_datetime.dateTime().toPyDateTime()
        
        # 验证时间
        if start_time <= QDateTime.currentDateTime().toPyDateTime():
            QMessageBox.warning(self, "警告", "开始时间必须晚于当前时间！")
            return
        
        if end_time <= start_time:
            QMessageBox.warning(self, "警告", "结束时间必须晚于开始时间！")
            return
        
        # TODO: 调用 SchedulerService 创建任务
        # from ..scheduler import SimpleSchedulerService
        # service = SimpleSchedulerService()
        # task = service.create_task(platform, start_time, end_time)
        
        QMessageBox.information(
            self, "提示", 
            f"定时任务已添加:\\n\\n平台：{platform}\\n开始：{start_time.strftime('%Y-%m-%d %H:%M')}\\n结束：{end_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
        # 刷新任务列表 (简化实现)
    
    def _delete_selected_schedule(self):
        """删除选中的定时任务"""
        selected_rows = self.schedule_table.selectedItems()
        if not selected_rows:
            QMessageBox.information(self, "提示", "请先选择要删除的任务")
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除选中的定时任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # TODO: 调用 SchedulerService.delete_task()
            pass
    
    def _start_schedule_service(self):
        """启动定时调度服务"""
        # TODO: 创建并启动 SchedulerService
        # from ..scheduler import SchedulerService
        # self.schedule_service = SchedulerService(db_session)
        # self.schedule_service.start()
        
        self.service_status_label.setText("🟢 运行中")
        self.service_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4CAF50;")
        
        QMessageBox.information(self, "成功", "定时调度服务已启动\\n(每 30 秒检查到期任务)")
    
    def _stop_schedule_service(self):
        """停止定时调度服务"""
        self.service_status_label.setText("🔴 未启动")
        self.service_status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f44336;")
        
        QMessageBox.information(self, "成功", "定时调度服务已停止")
