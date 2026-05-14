"""
Main Window - PyQt6 GUI Multi-Platform Version
主窗口界面 - 多平台并发推流控制版
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, 
        QHBoxLayout, QPushButton, QLabel, QTextEdit,
        QTabWidget, QGroupBox, QLineEdit, QCheckBox,
        QMessageBox, QSplitter, QScrollArea, QListWidget,
        QFileDialog, QDoubleSpinBox, QComboBox, QProgressBar,
        QTableWidget, QTableWidgetItem, QHeaderView, QFormLayout,
        QFrame, QSizePolicy, QStatusBar, QMenuBar, QAction,
        QToolBar, QStackedWidget, QInputDialog, QSpinBox, QGridLayout
    )
    from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
    from PyQt6.QtGui import QFont, QIcon, QColor, QTextCursor, QKeySequence
except ImportError:
    print("PyQt6 not installed. Install with: pip install PyQt6")
    sys.exit(1)


class MainWindow(QMainWindow):
    """主窗口类 - 多平台并发控制版"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config.copy()
        self.setWindowTitle("Multi-AI-Stream v3.0 - 数字人直播系统")
        self.setGeometry(100, 100, 1500, 950)
        
        # 状态变量
        self.is_streaming = False
        
        # StreamManager (多平台并发控制器)
        from ..stream.stream_manager import StreamManager
        self.stream_manager = StreamManager(config, use_obs=False)  # 默认使用模拟模式测试
        
        # 连接信号槽
        self.stream_manager.platform_started.connect(self._on_platform_started)
        self.stream_manager.platform_stopped.connect(self._on_platform_stopped)
        self.stream_manager.status_changed.connect(self._on_status_changed)
        self.stream_manager.log_message.connect(self._log)
        
        # 初始化界面
        self._init_ui()
        self._create_menu_bar()
        
        # 状态定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)
    
    def _init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # ========== 顶部标题栏 ==========
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        title_label = QLabel("🎬 Multi-AI-Stream - 数字人直播系统 v3.0")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: white;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 版本信息
        version_label = QLabel("v3.0 | Build 2026-05-13 | 多平台并发版")
        version_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12px;")
        header_layout.addWidget(version_label)
        
        main_layout.addWidget(header_frame)
        
        # ========== 主内容区 (标签页) ==========
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #ddd; border-radius: 5px; }
            QTabBar::tab { 
                background: #f0f0f0; padding: 10px 20px; margin-right: 2px; 
                border-radius: 5px 5px 0 0;
            }
            QTabBar::tab:selected { background: white; }
        """)
        
        # 标签 1: 直播控制台 (主面板) - 改造为多平台控制
        self.live_tab = self._create_live_panel()
        self.tabs.addTab(self.live_tab, "📺 直播控制")
        
        # 标签 2: 数字人配置
        self.avatar_tab = self._create_avatar_settings()
        self.tabs.addTab(self.avatar_tab, "👤 数字人配置")
        
        # 标签 3: 素材管理
        self.asset_tab = self._create_asset_manager()
        self.tabs.addTab(self.asset_tab, "📁 素材管理")
        
        # 标签 4: 房源信息管理
        self.property_tab = self._create_property_manager()
        self.tabs.addTab(self.property_tab, "🏠 房源管理")
        
        main_layout.addWidget(self.tabs)
        
        # ========== 底部状态栏 ==========
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("✓ 就绪 - 系统正常", 5000)
    
    def _create_live_panel(self) -> QWidget:
        """创建直播控制面板 - 多平台并发版本"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)
        
        # ========== 平台选择 (Checkbox List) ==========
        platform_group = QGroupBox("🌐 直播平台选择")
        p_layout = QVBoxLayout(platform_group)
        
        # 平台复选框列表
        self.platform_checkboxes = {}
        platforms_info = {
            'douyin': {'name': '抖音', 'rtmp_placeholder': 'rtmp://live-push.douyin.com/live/', 'key_placeholder': '抖音推流密钥'},
            'kuaishou': {'name': '快手', 'rtmp_placeholder': 'rtmp://xx.kuaishou.com/live/', 'key_placeholder': '快手推流密钥'},
            'wechat': {'name': '视频号', 'rtmp_placeholder': 'rtmp://live.weixin.qq.com/', 'key_placeholder': '微信推流密钥'},
        }
        
        for platform, info in platforms_info.items():
            # 平台行 (复选框 + RTMP URL + Stream Key)
            row_layout = QHBoxLayout()
            
            checkbox = QCheckBox(info['name'])
            checkbox.setChecked(False)  # 默认不勾选
            checkbox.setToolTip(f"{info['name']} 推流开关")
            self.platform_checkboxes[platform] = {
                'checkbox': checkbox,
                'rtmp_input': QLineEdit(),
                'key_input': QLineEdit()
            }
            
            # RTMP URL 输入框
            rtmp_input = self.platform_checkboxes[platform]['rtmp_input']
            rtmp_input.setPlaceholderText(info['rtmp_placeholder'])
            rtmp_input.setToolTip("从直播平台创作者中心获取 RTMP 地址")
            
            # Stream Key 输入框
            key_input = self.platform_checkboxes[platform]['key_input']
            key_input.setPlaceholderText(info['key_placeholder'])
            key_input.setEchoMode(QLineEdit.EchoMode.Password)
            
            row_layout.addWidget(checkbox, 1)
            row_layout.addWidget(rtmp_input, 2)
            row_layout.addWidget(key_input, 2)
            
            p_layout.addLayout(row_layout)
        
        layout.addWidget(platform_group)
        
        # ========== 批量控制按钮 ==========
        control_frame = QFrame()
        c_layout = QHBoxLayout(control_frame)
        c_layout.setSpacing(15)
        c_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.start_all_btn = QPushButton("▶️ 启动选中的平台")
        self.start_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; 
                padding: 12px 30px; font-size: 16px; font-weight: bold; 
                border-radius: 8px; min-width: 180px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.start_all_btn.clicked.connect(self._on_start_selected_platforms)
        
        self.stop_all_btn = QPushButton("⏹️ 停止所有平台")
        self.stop_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; color: white; 
                padding: 12px 30px; font-size: 16px; font-weight: bold; 
                border-radius: 8px; min-width: 180px;
            }
            QPushButton:hover { background-color: #da190b; }
            QPushButton:pressed { background-color: #c62828; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.stop_all_btn.clicked.connect(self._on_stop_all_platforms)
        self.stop_all_btn.setEnabled(False)
        
        c_layout.addWidget(self.start_all_btn)
        c_layout.addWidget(self.stop_all_btn)
        
        layout.addWidget(control_frame)
        
        # ========== 平台状态列表 ==========
        status_group = QGroupBox("📊 平台运行状态")
        s_layout = QVBoxLayout(status_group)
        
        self.platform_status_list = QListWidget()
        self.platform_status_list.setStyleSheet("""
            QListWidget { 
                border: 1px solid #ddd; border-radius: 5px; padding: 8px; 
                background-color: white;
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #eee; }
            QListWidget::item:selected { background-color: #e3f2fd; }
        """)
        
        s_layout.addWidget(self.platform_status_list)
        layout.addWidget(status_group)
        
        # ========== 推流统计 ==========
        stats_group = QGroupBox("📈 推流统计 (三路并发)")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_table = QTableWidget()
        self.stats_table.setColumnCount(5)
        self.stats_table.setHorizontalHeaderLabels([
            "平台", "状态", "总流量 (MB)", "FPS", "码率 (Kbps)"
        ])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stats_table.setStyleSheet("""
            QTableWidget { border: 1px solid #ddd; border-radius: 5px; }
            QTableWidget::item { padding: 6px; }
        """)
        
        stats_layout.addWidget(self.stats_table)
        layout.addWidget(stats_group)
        
        # ========== 日志输出区 ==========
        log_group = QGroupBox("📝 直播日志")
        log_layout = QVBoxLayout(log_group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        self.log_text.setMaximumHeight(250)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e; color: #d4d4d4;
                border: 1px solid #333; border-radius: 5px;
                padding: 8px;
            }
        """)
        
        log_layout.addWidget(self.log_text)
        layout.addWidget(log_group)
        
        return widget
    
    def _create_avatar_settings(self) -> QWidget:
        """创建数字人配置面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # ========== 引擎选择 ==========
        engine_group = QGroupBox("🎭 数字人生成引擎")
        e_layout = QFormLayout(engine_group)
        
        self.engine_combo = QComboBox()
        self.engine_combo.addItems([
            ("LivePortrait (实时驱动，30fps+)", "live_portrait"),
            ("Wav2Lip (离线生成，高质量)", "wav2lip")
        ])
        e_layout.addRow("引擎:", self.engine_combo)
        
        content_layout.addWidget(engine_group)
        
        # ========== LivePortrait 配置 ==========
        lp_group = QGroupBox("🎬 LivePortrait 参数")
        lp_layout = QFormLayout(lp_group)
        
        self.lip_sync_spin = QDoubleSpinBox()
        self.lip_sync_spin.setRange(0.5, 2.0)
        self.lip_sync_spin.setValue(1.0)
        self.lip_sync_spin.setSuffix("x")
        lp_layout.addRow("口型强度:", self.lip_sync_spin)
        
        self.fps_spin = QSpinBox()
        self.fps_spin.setRange(15, 60)
        self.fps_spin.setValue(25)
        self.fps_spin.setSuffix(" fps")
        lp_layout.addRow("帧率:", self.fps_spin)
        
        content_layout.addWidget(lp_group)
        
        # ========== TTS 配置 ==========
        tts_group = QGroupBox("🔊 TTS 语音合成")
        tts_layout = QFormLayout(tts_group)
        
        self.tts_engine_combo = QComboBox()
        self.tts_engine_combo.addItems([
            ("Coqui-TTS (开源)", "coqui"),
            ("Edge-TTS (免费)", "edge"),
            ("讯飞 API (商用)", "iflytek")
        ])
        tts_layout.addRow("引擎:", self.tts_engine_combo)
        
        content_layout.addWidget(tts_group)
        
        # ========== 保存按钮 ==========
        save_btn = QPushButton("💾 保存配置")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; color: white; 
                padding: 10px; font-size: 14px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        save_btn.clicked.connect(self._save_avatar_config)
        
        content_layout.addStretch()
        content_layout.addWidget(save_btn)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        return widget
    
    def _create_asset_manager(self) -> QWidget:
        """创建素材管理面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # 数字人头像列表
        avatar_group = QGroupBox("👤 数字人头像")
        avatar_layout = QHBoxLayout(avatar_group)
        
        self.avatar_list = QListWidget()
        self.avatar_list.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }
        """)
        
        upload_avatar_btn = QPushButton("📤 上传")
        upload_avatar_btn.clicked.connect(self._on_upload_avatar)
        
        delete_avatar_btn = QPushButton("🗑️ 删除")
        delete_avatar_btn.clicked.connect(self._delete_selected_avatar)
        
        avatar_layout.addWidget(self.avatar_list, 1)
        avatar_layout.addWidget(upload_avatar_btn)
        avatar_layout.addWidget(delete_avatar_btn)
        
        layout.addWidget(avatar_group)
        
        # 背景场景列表
        bg_group = QGroupBox("🖼️ 直播背景")
        bg_layout = QHBoxLayout(bg_group)
        
        self.bg_list = QListWidget()
        self.bg_list.setStyleSheet("""
            QListWidget { border: 1px solid #ddd; border-radius: 5px; padding: 5px; }
        """)
        
        layout.addWidget(bg_group)
        
        # 填充示例数据
        self._load_sample_assets()
        
        return widget
    
    def _create_property_manager(self) -> QWidget:
        """创建房源管理面板"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(10)
        
        # 房源列表表格
        table_group = QGroupBox("🏠 房源信息")
        table_layout = QVBoxLayout(table_group)
        
        self.property_table = QTableWidget()
        self.property_table.setColumnCount(6)
        self.property_table.setHorizontalHeaderLabels([
            "名称", "价格 (万)", "面积", "位置", "状态", "操作"
        ])
        self.property_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.property_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table_layout.addWidget(self.property_table)
        
        # 添加房源按钮
        add_btn = QPushButton("➕ 添加房源")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; color: white; 
                padding: 8px 16px; border-radius: 5px; font-weight: bold;
            }
        """)
        add_btn.clicked.connect(self._add_property)
        
        layout.addWidget(add_btn)
        layout.addWidget(table_group)
        
        # 填充示例数据
        self._load_sample_properties()
        
        return widget
    
    def _create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu("📁 文件")
        
        save_config_action = QAction("💾 保存配置", self)
        save_config_action.setShortcut("Ctrl+S")
        save_config_action.triggered.connect(self._save_config)
        file_menu.addAction(save_config_action)
        
        exit_action = QAction("❌ 退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 🔧 工具菜单
        tools_menu = menubar.addMenu("🔧 工具")
        
        clear_log_action = QAction("🗑️ 清空日志", self)
        clear_log_action.setShortcut("Ctrl+L")
        clear_log_action.triggered.connect(lambda: self.log_text.clear())
        tools_menu.addAction(clear_log_action)
        
        refresh_status_action = QAction("🔄 刷新状态", self)
        refresh_status_action.triggered.connect(self._refresh_platform_stats)
        tools_menu.addAction(refresh_status_action)
        
        # ⚙️ 系统设置菜单
        settings_menu = menubar.addMenu("⚙️ 系统设置")
        
        llm_settings_action = QAction("🤖 LLM 模型配置", self)
        llm_settings_action.setShortcut("Ctrl+L")
        llm_settings_action.triggered.connect(self._open_llm_settings)
        settings_menu.addAction(llm_settings_action)
        
        tts_settings_action = QAction("🔊 TTS 语音配置", self)
        tts_settings_action.setShortcut("Ctrl+T")
        tts_settings_action.triggered.connect(self._open_tts_settings)
        settings_menu.addAction(tts_settings_action)
        
        full_settings_action = QAction("⚙️ 系统设置 (全部)", self)
        full_settings_action.setShortcut("Ctrl+,")
        full_settings_action.triggered.connect(self._open_full_settings)
        settings_menu.addAction(full_settings_action)
    
    # ========== 平台控制方法 ==========
    
    def _on_start_selected_platforms(self):
        """启动选中的平台"""
        selected_platforms = []
        
        for platform, checkbox_info in self.platform_checkboxes.items():
            if checkbox_info['checkbox'].isChecked():
                rtmp_url = checkbox_info['rtmp_input'].text().strip()
                stream_key = checkbox_info['key_input'].text().strip()
                
                if not rtmp_url or not stream_key:
                    QMessageBox.warning(
                        self, "警告",
                        f"{checkbox_info['checkbox'].text()} 的 RTMP URL 和推流密钥不能为空！"
                    )
                    return
                
                selected_platforms.append(platform)
        
        if not selected_platforms:
            QMessageBox.information(self, "提示", "请至少勾选一个平台")
            return
        
        # 确认对话框
        platforms_str = ", ".join([self.platform_checkboxes[p]['checkbox'].text() for p in selected_platforms])
        reply = QMessageBox.question(
            self, "确认启动",
            f"确定要启动以下平台的推流吗？\n\n{platforms_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 启动所有选中的平台
        self._log(f"🚀 开始启动 {len(selected_platforms)} 个平台的推流...")
        
        for platform in selected_platforms:
            rtmp_url = self.platform_checkboxes[platform]['rtmp_input'].text().strip()
            stream_key = self.platform_checkboxes[platform]['key_input'].text().strip()
            
            # 更新配置
            if 'platforms' not in self.config:
                self.config['platforms'] = {}
            if platform not in self.config['platforms']:
                self.config['platforms'][platform] = {}
            
            self.config['platforms'][platform]['rtmp_url'] = rtmp_url
            self.config['platforms'][platform]['stream_key'] = stream_key
            
            # 启动推流 (通过 StreamManager)
            self.stream_manager.start_platform(platform)
        
        # 更新按钮状态
        self.start_all_btn.setEnabled(False)
        self.stop_all_btn.setEnabled(True)
    
    def _on_stop_all_platforms(self):
        """停止所有平台的推流"""
        reply = QMessageBox.question(
            self, "确认停止",
            "确定要停止所有正在运行的平台吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self._log("⏹️ 开始停止所有平台的推流...")
            self.stream_manager.stop_all_platforms()
    
    def _on_platform_started(self, platform: str):
        """平台启动事件"""
        checkbox_info = self.platform_checkboxes.get(platform)
        if checkbox_info:
            checkbox_info['checkbox'].setChecked(True)
        
        # 更新状态列表
        item = QListWidgetWidgetItem(f"✅ {platform} 已启动")
        item.setForeground(QColor("#4CAF50"))
        self.platform_status_list.addItem(item)
        
        # 刷新统计表格
        self._refresh_platform_stats()
    
    def _on_platform_stopped(self, platform: str):
        """平台停止事件"""
        checkbox_info = self.platform_checkboxes.get(platform)
        if checkbox_info:
            checkbox_info['checkbox'].setChecked(False)
        
        # 更新状态列表
        item = QListWidgetItem(f"❌ {platform} 已停止")
        item.setForeground(QColor("#f44336"))
        self.platform_status_list.addItem(item)
        
        # 刷新统计表格
        self._refresh_platform_stats()
    
    def _on_status_changed(self, platform: str, status: str):
        """状态变更事件"""
        self._log(f"{platform}: {status}")
        self._refresh_platform_stats()
    
    def _refresh_platform_stats(self):
        """刷新平台统计表格"""
        summary = self.stream_manager.get_status_summary()
        
        self.stats_table.setRowCount(len(summary))
        
        for row, (platform, stats) in enumerate(summary.items()):
            # 平台名称
            platform_name = self.platform_checkboxes[platform]['checkbox'].text()
            self.stats_table.setItem(row, 0, QTableWidgetItem(platform_name))
            
            # 状态
            status_item = QTableWidgetItem(stats['status'])
            if stats['is_running']:
                status_item.setForeground(QColor("#4CAF50"))
            else:
                status_item.setForeground(QColor("#999"))
            self.stats_table.setItem(row, 1, status_item)
            
            # 总流量 (MB)
            total_mb = stats.get('stats', {}).get('total_bytes_sent', 0) / (1024 * 1024)
            self.stats_table.setItem(row, 2, QTableWidgetItem(f"{total_mb:.2f}"))
            
            # FPS
            fps = stats.get('stats', {}).get('fps', 0)
            self.stats_table.setItem(row, 3, QTableWidgetItem(str(fps)))
            
            # 码率 (Kbps)
            bitrate = stats.get('stats', {}).get('bitrate', 0) / 1000
            self.stats_table.setItem(row, 4, QTableWidgetItem(str(int(bitrate))))
    
    def _save_avatar_config(self):
        """保存数字人配置"""
        config = {
            'engine': self.engine_combo.currentData(),
            'lip_sync_strength': self.lip_sync_spin.value(),
            'fps': self.fps_spin.value()
        }
        
        QMessageBox.information(
            self, "成功", 
            f"数字人配置已保存:\n引擎：{config['engine']}\n口型强度：{config['lip_sync_strength']}x\n帧率：{config['fps']}"
        )
        self._log("数字人配置已保存")
    
    def _save_config(self):
        """保存配置"""
        from PyQt6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存配置", "config_backup.yaml", "YAML Files (*.yaml)"
        )
        
        if file_path:
            QMessageBox.information(self, "成功", f"配置已保存到:\n{file_path}")
            self._log(f"配置已保存：{file_path}")
    
    def _open_llm_settings(self):
        """打开 LLM 设置对话框"""
        from .settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.config, self)
        
        if 'llm' not in self.config:
            self.config['llm'] = {'mode': 'remote'}
        
        if self.config['llm'].get('mode') != 'remote':
            self.config['llm']['mode'] = 'remote'
            dialog.llm_mode_combo.setCurrentIndex(0)  # remote
        
        dialog.exec()
    
    def _open_tts_settings(self):
        """打开 TTS 设置对话框"""
        from .settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.config, self)
        
        if 'tts' not in self.config:
            self.config['tts'] = {'engine': 'edge'}
        
        dialog.tts_engine_combo.setCurrentIndex(1)  # edge
        
        dialog.exec()
    
    def _open_full_settings(self):
        """打开完整系统设置对话框"""
        from .settings_dialog import SettingsDialog
        
        dialog = SettingsDialog(self.config, self)
        
        if 'llm' not in self.config:
            self.config['llm'] = {'mode': 'remote'}
        elif self.config['llm'].get('mode') != 'remote':
            self.config['llm']['mode'] = 'remote'
            dialog.llm_mode_combo.setCurrentIndex(0)
        
        if 'tts' not in self.config:
            self.config['tts'] = {'engine': 'edge'}
        else:
            engine_idx = dialog.tts_engine_combo.findData(self.config['tts'].get('engine', 'edge'))
            if engine_idx >= 0:
                dialog.tts_engine_combo.setCurrentIndex(engine_idx)
        
        dialog.exec()
    
    def _update_status(self):
        """更新状态栏"""
        running_platforms = self.stream_manager.get_active_platforms()
        
        if running_platforms:
            uptime = datetime.now().strftime("%H:%M:%S")
            self.status_bar.showMessage(
                f"🔴 直播中 | {len(running_platforms)}路并发 ({', '.join(running_platforms)}) | {uptime}", 
                0
            )
        else:
            self.status_bar.showMessage("✓ 就绪 - 系统正常", 0)
    
    def _log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if "✅" in message or "成功" in message:
            color = "#4CAF50"
        elif "❌" in message or "错误" in message:
            color = "#f44336"
        else:
            color = "#2196F3"
        
        log_html = f'<span style="color: {color};">[{timestamp}]</span> {message}<br>'
        
        self.log_text.append(log_html)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)
    
    def _browse_folder(self, line_edit: QLineEdit):
        """浏览文件夹"""
        folder = QFileDialog.getExistingDirectory(
            self, "选择目录", "", QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            line_edit.setText(folder)
    
    def _on_upload_avatar(self):
        """上传头像"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择数字人图片", "", "Images (*.jpg *.png)"
        )
        
        if file_path:
            avatar_name = Path(file_path).stem
            self.avatar_list.addItem(avatar_name)
            self._log(f"已上传头像：{avatar_name}")
    
    def _delete_selected_avatar(self):
        """删除选中的头像"""
        current_item = self.avatar_list.currentItem()
        if current_item:
            row = self.avatar_list.row(current_item)
            self.avatar_list.takeItem(row)
            self._log(f"已删除头像：{current_item.text()}")
    
    def _load_sample_assets(self):
        """加载示例素材"""
        self.avatar_list.addItems(["default_avatar", "avatar_01"])
        self.bg_list.addItems(["living_room", "office", "outdoor"])
    
    def _add_property(self):
        """添加房源"""
        name, ok = QInputDialog.getText(self, "添加房源", "房源名称:")
        
        if ok and name:
            row = self.property_table.rowCount()
            self.property_table.insertRow(row)
            
            self.property_table.setItem(row, 0, QTableWidgetItem(name))
            self.property_table.setItem(row, 1, QTableWidgetItem("500"))
            self.property_table.setItem(row, 2, QTableWidgetItem("89㎡"))
            self.property_table.setItem(row, 3, QTableWidgetItem("市中心"))
            
            status_item = QTableWidgetItem("待直播")
            status_item.setForeground(QColor("#4CAF50"))
            self.property_table.setItem(row, 4, status_item)
            
            edit_btn = QPushButton("编辑")
            self.property_table.setCellWidget(row, 5, edit_btn)
            
            self._log(f"已添加房源：{name}")
    
    def _load_sample_properties(self):
        """加载示例房源"""
        properties = [
            ("中环二手房 A", "500", "89㎡", "市中心"),
            ("房车样板间 B", "380", "45㎡", "郊区营地"),
        ]
        
        for name, price, area, location in properties:
            row = self.property_table.rowCount()
            self.property_table.insertRow(row)
            
            self.property_table.setItem(row, 0, QTableWidgetItem(name))
            self.property_table.setItem(row, 1, QTableWidgetItem(price))
            self.property_table.setItem(row, 2, QTableWidgetItem(area))
            self.property_table.setItem(row, 3, QTableWidgetItem(location))
    
    def closeEvent(self, event):
        """关闭事件"""
        # 停止所有推流
        if not self.stream_manager.get_active_platforms():
            reply = QMessageBox.question(
                self, "确认退出",
                "确定要退出 Multi-AI-Stream 吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        
        # 停止所有推流并清理资源
        self.stream_manager.cleanup()
        
        event.accept()
