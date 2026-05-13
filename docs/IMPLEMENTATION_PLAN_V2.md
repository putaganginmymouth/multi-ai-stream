# Multi-AI-Stream v2.0 实施文档 - 房车产品数字人直播系统

**版本**: v2.0  
**创建日期**: 2026-05-13  
**作者**: duanxiaobo  

---

## 📋 目录

1. [项目概述](#1-项目概述)
2. [核心功能设计](#2-核心功能设计)
3. [数据库模型](#3-数据库模型)
4. [服务层实现](#4-服务层实现)
5. [GUI 界面设计](#5-gui 界面设计)
6. [实施路线图](#6-实施路线图)
7. [技术难点与解决方案](#7-技术难点与解决方案)

---

## 1. 项目概述

### 1.1 项目定位

Multi-AI-Stream v2.0 是一个基于 AI 数字人的多平台房车产品直播系统，通过 LLM 智能生成产品介绍文案和评论回复，支持视频 - 文案对齐播放、公共/私有 Q&A 双层降级机制、随机/顺序循环模式以及评论点播功能。

### 1.2 核心特性

| 功能模块 | 说明 |
|---------|------|
| **素材库管理** | 上传房车产品视频，标注产品详细信息，自动生成介绍文案 |
| **专家角色提示词** | 配置统一的数字人专家人设，LLM 生成产品介绍和回复评论 |
| **Q&A 双层降级系统** | LLM→公共 Q&A→私有 Q&A→默认回复，四级保障 |
| **循环播放模式** | 顺序循环 / 随机循环，支持直播自动轮播 |
| **评论点播功能** | NLP 识别"介绍 X 号房车"→等待当前内容完成后切换 |
| **视频 - 文案对齐** | LLM 生成带时间戳的分段文案，触发对应视频片段播放 |

---

## 2. 核心功能设计

### 🎯 多平台直播评论接收架构 (新增)

#### 2.0 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              Multi-AI-Stream Core                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────┐           │
│  │        CommentAggregator (评论聚合器)       │           │
│  ├─────────────────────────────────────────────┤           │
│  │                                             │           │
│  │  • 统一接口：on_new_comment(comment)        │           │
│  │  • 去重过滤：同一用户短时间内合并            │           │
│  │  • 优先级排序：高权重平台优先处理           │           │
│  │  • 并发控制：线程池限制最大同时处理数       │           │
│  └───────────────┬─────────────────────────────┘           │
│                  ↓                                           │
│  ┌─────────────────────────────────────────────┐           │
│  │         CommentHandler (回复生成器)         │           │
│  ├─────────────────────────────────────────────┤           │
│  │  • ReplyGenerator.generate_reply(comment)   │           │
│  │  • LLM→公共 Q&A→私有 Q&A→默认 (四级降级)    │           │
│  └───────────────┬─────────────────────────────┘           │
│                  ↓                                           │
│  ┌─────────────────────────────────────────────┐           │
│  │          PlatformReplySender                │           │
│  ├─────────────────────────────────────────────┤           │
│  │  • 抖音：蝉妈妈 API / WebSocket              │           │
│  │  • 快手：蝉妈妈 API / WebSocket              │           │
│  │  • 视频号：企业微信 Webhook                  │           │
│  └─────────────────────────────────────────────┘           │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│                    Platform Adapters                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐     │
│  │ DouyinWS    │  │ KuaishouWS  │  │ WeComWebhook    │   │
│  │ (蝉妈妈 API) │  │ (蝉妈妈 API) │  │ (企业微信免费)   │   │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘     │
│         ↓                ↓                  ↓               │
│    蝉妈妈平台       蝉妈妈平台        企业微信群机器人      │
└─────────┴────────────────┴──────────────────┴─────────────┘
```

#### 2.0.1 评论接收方式对比

| 平台 | 官方 API | 第三方采集 | 免费快速方案 | 推荐度 |
|------|---------|-----------|-------------|--------|
| **抖音** | ⚠️ 需企业认证 (3-7 天) | ✅ 蝉妈妈 ¥799/月 | ⭐ 开源 WebSocket | ⭐⭐⭐⭐ |
| **快手** | ⚠️ 需企业认证 (3-5 天) | ✅ 蝉妈妈 ¥799/月 | ⭐ 开源项目 | ⭐⭐⭐⭐ |
| **视频号** | ❌ 无公开 API | ✅ 小鹅通 ¥299/月 | 🆓 企业微信 Webhook | ⭐⭐⭐⭐⭐ |

#### 2.0.2 推荐接入方案

**Phase M0 (MVP)**: 
- 视频号：企业微信 Webhook (免费 +5 分钟配置)
- 抖音/快手：OBS 插件显示评论，手动确认回复

**Phase M1 (正式)**:
- 蝉妈妈专业版 ¥799/月 → 获取抖音 + 快手 WebSocket API
- 全平台自动回复集成

---

### 2.1 Q&A 双层匹配系统

#### 2.1.1 架构说明

```
┌─────────────────────────────────────────────┐
│           用户评论                          │
└──────────────┬──────────────────────────────┘
               ↓
       ┌────────────────┐
       │  LLM 生成      │ ← 优先尝试 (超时/失败则降级)
       └────────┬───────┘
                ↓ (失败)
    ┌───────────────────────┐
    │   Q&A 匹配            │
    ├───────────────────────┤
    │ 1. 公共 Q&A (全局)   │ ← 优先级高，先匹配
    │ 2. 私有 Q&A (产品级) │ ← 次优先，当前产品介绍相关
    └───────────┬───────────┘
                ↓ (无匹配)
       ┌────────────────┐
       │  默认回复      │ ← "稍后专家解答"
       └────────────────┘
```

#### 2.1.2 Q&A 数据结构

**公共 Q&A (`public_qa`表)**:
- `question`: 问题文本，如"价格多少？"
- `answer`: 回答文本，如"这款房车售价 88 万，性价比很高。"
- `keywords`: 关键字列表，如["价格", "多少钱", "报价"]
- `priority`: 优先级 (1-100)，越高优先匹配

**私有 Q&A (`product_assets.qa_pairs`字段)**:
```json
[
  {
    "question": "这款房车的最大亮点是什么？",
    "answer": "最大的亮点是越野性能和空间布局...",
    "keywords": ["亮点", "优点", "特色"],
    "auto_reply_weight": 0.8
  }
]
```

#### 2.1.3 Q&A 匹配算法

```python
def _calculate_match_score(comment: str, qa_pair: Dict) -> float:
    """计算评论与 Q&A 的匹配分数 (0-1)"""
    
    # 1. 关键字匹配 (权重高，1.0)
    matched_keywords = [kw for kw in keywords if kw in comment]
    keyword_score = len(matched_keywords) / max(len(keywords), 1)
    
    # 2. 问题文本相似度 (字符重合度，权重 0.5)
    common_chars = set(comment) & set(question)
    semantic_score = len(common_chars) / max(len(set(question)), 1)
    
    return min(keyword_score * 1.0 + semantic_score * 0.5, 1.0)
```

---

### 2.2 直播间循环管理

#### 2.2.1 循环模式

| 模式 | 说明 | 实现方式 |
|------|------|---------|
| **顺序循环** | 按产品 ID 从小到大依次播放 | 维护 `current_play_index`，每次 +1 取模 |
| **随机循环** | 每次从剩余产品中随机选择 | Fisher-Yates 洗牌算法 |

#### 2.2.2 状态管理

```python
class LiveRoomManager:
    """直播间管理器"""
    
    def get_next_product_id(self, all_product_ids: List[int]) -> Optional[int]:
        """获取下一个要介绍的产品 ID"""
        
        if self.loop_mode == 'sequential':
            # 顺序模式：索引 +1 取模
            self.current_play_index = (self.current_play_index + 1) % len(all_product_ids)
            return all_product_ids[self.current_play_index]
        
        elif self.loop_mode == 'random':
            # 随机模式：洗牌后返回第一个
            shuffled = all_product_ids.copy()
            random.shuffle(shuffled)
            return shuffled[0]
```

---

### 2.3 评论点播功能

#### 2.3.1 触发时机：**完成当前内容后切换** (方案 B)

**流程说明**:
1. 识别到"介绍 X 号房车"→记录目标产品 ID
2. **继续播放当前产品的全部文案和视频片段**
3. 当前产品介绍结束后，自动切换到目标产品
4. 如果期间又收到新的点播请求，更新目标为最新请求

#### 2.3.2 NLP 识别逻辑

```python
def request_product_order(self, comment_text: str) -> Optional[int]:
    """从评论文本中提取产品编号"""
    
    # Step 1: 数字提取 (支持多种表达)
    pattern = r'[第号\s]*?(\d+)[\s号房车产品]'
    match = re.search(pattern, comment_text, re.IGNORECASE)
    
    if not match:
        return None
    
    product_number = int(match.group(1))
    
    # Step 2: 模糊匹配产品名称 (支持"3 号"、"三号"、"产品 3")
    for product in products:
        if str(product_number) in product.name or \
           f"{product_number}号" in product.name:
            return product.id
    
    # Step 3: 尝试精确 ID 匹配
    product = session.query(ProductAsset).filter_by(id=product_number).first()
    if product:
        return product.id
    
    return None
```

**支持的表达示例**:
- "介绍下 3 号房车吧" → 提取"3"
- "看一下二号房车" → 提取"2"  
- "产品 5 的详细信息" → 提取"5"
- "第 10 号房车价格多少" → 提取"10"

---

### 2.4 数字人联动 (方案 A: OBS 场景切换)

#### 2.4.1 架构设计

```
┌───────────────────────────────────────────────┐
│              OBS Studio                       │
├───────────────────────────────────────────────┤
│                                               │
│  ┌─────────────┐   ┌─────────────────────┐   │
│  │Scene: RV-01 │   │ Scene: RV-02        │   │
│  ├─────────────┤   ├─────────────────────┤   │
│  │Video Source │   │ Video Source        │   │
│  │ (rv_001.mp4)│   │ (rv_002.mp4)        │   │
│  ├─────────────┤   ├─────────────────────┤   │
│  │Image Source │   │ Image Source        │   │
│  │ (avatar.jpg)│   │ (avatar.jpg)        │   │
│  ├─────────────┤   ├─────────────────────┤   │
│  │Filter: LipSync ←──────────────────→ LivePortrait API │
│  └─────────────┘   └─────────────────────┘   │
│                                               │
└───────────────────────────────────────────────┘
```

#### 2.4.2 工作流程

1. **准备阶段**: 
   - 为每个产品创建 OBS 场景，包含视频源和数字人图像
   - LivePortrait 实时驱动数字人口型同步

2. **播放阶段**:
   ```python
   def play_aligned_content(self, product_asset: ProductAsset):
       """按时间轴顺序播放"""
       
       for seg in segments:
           # Step 1: OBS 切换到产品视频场景
           obs.set_current_scene(f"Scene_{product_asset.id}")
           
           # Step 2: FFmpeg 播放视频片段 (同时)
           subprocess.run(['ffplay', '-ss', seg['start'], '-t', duration, video_path])
           
           # Step 3: TTS 生成音频 + LivePortrait 驱动口型
           audio = tts_synthesize(seg['text'])
           live_portrait.sync_lip(audio)
   ```

3. **切换阶段**:
   - OBS `SetCurrentScene()` 无缝切换场景
   - LivePortrait 自动适配新视频帧

---

## 3. 数据库模型

### 3.1 ProductAsset (产品资产表)

```python
class ProductAsset(Base):
    """房车产品资产表"""
    
    __tablename__ = 'product_assets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)           # 产品名称，如"1 号房车 - 豪华越野版"
    video_path = Column(String(500), nullable=False)     # 视频文件路径
    product_detail = Column(Text, nullable=False)        # 📝 产品详细信息
    
    # 元数据 (FFmpeg 提取)
    duration = Column(Float)                              # 视频时长 (秒)
    width = Column(Integer)                               # 分辨率宽
    height = Column(Integer)                              # 分辨率高
    
    # 文案对齐信息
    script_text = Column(Text)                            # 📄 生成的介绍文案
    script_segments = Column(JSON)                        # 🔗 分段标注 [{"start": 0, "end": 15, "text": "..."}]
    
    # Q&A 配置 (私有 Q&A)
    qa_pairs = Column(JSON, default=list)                 # [
                                                            #   {
                                                            #     "question": "价格多少？",
                                                            #     "answer": "...",
                                                            #     "keywords": ["价格", "多少钱"],
                                                            #     "auto_reply_weight": 0.8
                                                            #   }
                                                            # ]
    
    is_active = Column(Boolean, default=False)            # 是否正在介绍中
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
```

### 3.2 PublicQA (公共 Q&A 表)

```python
class PublicQA(Base):
    """公共 Q&A 表 (全局共享)"""
    
    __tablename__ = 'public_qa'
    
    id = Column(Integer, primary_key=True)
    question = Column(String(500), nullable=False)        # 问题
    answer = Column(Text, nullable=False)                 # 回答
    
    keywords = Column(JSON, default=list)                 # 关键字列表
    enabled = Column(Boolean, default=True)               # 是否启用
    priority = Column(Integer, default=50)                # 优先级 (1-100)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
```

### 3.3 CurrentProductState (当前产品介绍状态表)

```python
class CurrentProductState(Base):
    """当前产品介绍状态表"""
    
    __tablename__ = 'current_product_state'
    
    id = Column(Integer, primary_key=True, default=1)     # 固定为 1 行
    
    product_id = Column(Integer, ForeignKey('product_assets.id'))
    product_name = Column(String(200))
    product_detail = Column(Text)
    
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    is_live = Column(Boolean, default=False)
```

### 3.4 LiveRoomConfig (直播间配置表)

```python
class LiveRoomConfig(Base):
    """直播间配置"""
    
    __tablename__ = 'live_room_config'
    
    id = Column(Integer, primary_key=True, default=1)
    
    loop_mode = Column(String(20), default='sequential')  # sequential | random
    enable_comment_order = Column(Boolean, default=True)  # 是否启用评论点播
    use_public_qa = Column(Boolean, default=True)         # 是否使用公共 Q&A
    qa_match_min_confidence = Column(Float, default=0.6)  # 最低置信度
    
    current_play_index = Column(Integer, default=-1)      # -1 表示未开始 (顺序模式追踪)
    
    updated_at = Column(DateTime, onupdate=datetime.now)
```

---

## 4. 服务层实现

### 4.1 PublicQAService (公共 Q&A 管理)

**核心方法**:
- `add_public_qa(question, answer, keywords, priority)` - 添加单条
- `delete_public_qa(qa_ids)` - 批量删除
- `import_from_json(json_data)` - JSON 批量导入
- `export_to_json()` - 导出为 JSON

**JSON Schema**:
```json
[
  {
    "question": "价格多少？",
    "answer": "这款房车售价 88 万，性价比很高。",
    "keywords": ["价格", "多少钱", "报价"],
    "priority": 80
  }
]
```

### 4.2 ReplyGeneratorHandler (评论回复生成器)

**四级降级流程**:
1. **LLM 生成优先** - 调用 DeepSeek API，超时 10s 则降级
2. **公共 Q&A 匹配** - 全局共享的问答对
3. **私有 Q&A 匹配** - 当前产品介绍相关的问答对
4. **默认回复** - "感谢您的关注！这个问题比较具体..."

**配置参数**:
```yaml
llm_timeout_seconds: 10           # LLM 超时时间 (秒)
qa_match_min_confidence: 0.6      # Q&A 最低匹配置信度 (0-1)
```

### 4.3 LiveRoomManager (直播间管理器)

**核心方法**:
- `set_loop_mode(mode)` - 设置循环模式 (sequential/random)
- `get_next_product_id(all_product_ids)` - 获取下一个产品 ID
- `request_product_order(comment_text)` - 从评论提取点播请求
- `end_showcase()` - 结束当前介绍

---

## 5. GUI 界面设计

### 5.1 AssetLibraryDialog (素材库管理)

**功能模块**:
```
┌─────────────────────────────────────────────┐
│  [📤上传视频]   [➕添加 Q&A]  [📥JSON 导入]  │
├─────────────────────────────────────────────┤
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 🏠 产品列表 (表格)                     │ │
│  ├───────────────────────────────────────┤ │
│  │ 名称    │ 时长 │ Q&A 数 │ 状态         │ │
│  │ 1 号房车 │60s   │ 5 条   │ ✓已配置      │ │
│  └───────────────────────────────────────┘ │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │ 💬 Q&A 配置                            │ │
│  ├───────────────────────────────────────┤ │
│  │ 📑公共 Q&A (全局) / 🏠私有 Q&A (产品级)│ │
│  └───────────────────────────────────────┘ │
│                                             │
│          [▶️开始介绍]   [❌取消]            │
└─────────────────────────────────────────────┘
```

**交互细节**:
- **添加 Q&A**: 点击"➕"弹出表单对话框 (问题/回答/关键字)
- **JSON 导入**: 选择 JSON 文件 → 解析验证 → 批量插入公共 Q&A
- **批量删除**: 勾选多行 → 点击"🗑️批量删除"→确认后删除
- **双击编辑**: 双击产品行 → 弹出编辑对话框修改产品信息/Q&A

### 5.2 MainWindow (主窗口)

**新增控件**:
```python
# 循环模式选择区域
┌───────────────────────────────────────┐
│ 🔁 循环播放模式                       │
│ [模式:] [顺序循环 ▼]  ☑启用评论点播   │
└───────────────────────────────────────┘

# 直播日志区 (显示评论和回复)
┌───────────────────────────────────────┐
│ 📝 直播日志                           │
│ ───────────────────────────────────── │
│ 👤 User123: 这款房车价格多少？         │
│ 🤖 回复：这款房车售价 88 万，性价比很... │
│ 👤 User456: 介绍下 3 号房车吧            │
│ 📢 检测到点播请求：切换到产品 3          │
└───────────────────────────────────────┘
```

---

## 6. 实施路线图

### 🎯 多平台评论接入方案 (新增章节)

#### **Phase M0: MVP 验证 (第 1-2 天)** - 成本 ¥0~¥200

| 任务 | 说明 | 费用 |
|------|------|------|
| 视频号 Webhook 配置 | 企业微信群机器人，5 分钟完成 | 免费 |
| OBS 插件安装 | "直播评论助手" 插件显示评论 | ¥199/年 |
| MVP 测试流程 | 手动点击按钮发送回复 | - |

**交付成果**: 
- ✅ 视频号评论接收 + 显示可用
- ⚠️ 抖音/快手评论仅显示，需人工确认发送

---

#### **Phase M1: 正式接入 (第 3-7 天)** - 成本 ¥2,400/季

| 任务 | 说明 | 费用 |
|------|------|------|
| 蝉妈妈专业版订阅 | 获取抖音 + 快手 WebSocket API | ¥799/月 ×3 = ¥2,397 |
| CommentAdapter 集成 | 实现第三方 API 适配器层 | - |
| 全平台自动回复测试 | 验证 LLM→Q&A 降级流程 | - |

**交付成果**: 
- ✅ 三平台评论接收 + 自动回复全部可用
- ✅ 去重/限流机制生效

---

### Phase P0: Q&A 系统基础 (3-4 天)

| 任务 | 文件 | 预计工时 |
|------|------|---------|
| 数据库模型扩展 (`PublicQA`, `LiveRoomConfig`) | `src/data/models.py` | 2h |
| PublicQAService CRUD + JSON 导入导出 | `src/data/services.py` | 4h |
| ReplyGeneratorHandler(LLM+Q&A 降级) | `src/content/reply_generator.py` | 6h |
| AssetLibraryDialog(Q&A 批量编辑/JSON) | `src/gui/asset_dialog.py` | 8h |

**交付成果**:
- ✅ Q&A 双层匹配系统可用
- ✅ JSON 导入导出功能完成
- ✅ LLM 超时自动降级到 Q&A

---

### Phase P1: 循环模式 + 评论点播 (3-4 天)

| 任务 | 文件 | 预计工时 |
|------|------|---------|
| LiveRoomManager(循环逻辑 + 点播识别) | `src/core/live_room_manager.py` | 6h |
| MainWindow 集成 (循环模式 UI+ 评论处理) | `src/gui/main_window.py` | 4h |
| CurrentProductState 状态管理 | `src/data/services.py` | 3h |

**交付成果**:
- ✅ 顺序/随机循环播放可用
- ✅ 评论点播功能识别并触发切换
- ✅ 当前产品介绍状态持久化

---

### Phase P2: 数字人联动 + 视频对齐 (3-4 天)

| 任务 | 文件 | 预计工时 |
|------|------|---------|
| SyncEngine(时间戳文案生成+视频片段触发) | `src/asset/sync_engine.py` | 8h |
| OBS 场景切换集成 (`python-obs-studio`) | - | 4h |
| LivePortrait 实时口型同步驱动 | `src/avatar/live_portrait.py` | 6h |

**交付成果**:
- ✅ 视频 - 文案时间轴对齐播放
- ✅ OBS 多场景自动切换
- ✅ 数字人语音与口型同步

---

### Phase P3: 端到端测试优化 (2 天)

| 任务 | 说明 |
|------|------|
| 完整流程测试：上传视频→配置 Q&A→开始直播 | 验证各模块协作 |
| 性能优化：LLM 响应速度、Q&A 匹配效率 | 降低延迟 |
| UI 交互打磨：错误提示、状态反馈 | 提升用户体验 |

---

## 7. 技术难点与解决方案

### 7.1 Q&A 匹配准确率不高

**问题**: 用户评论表达多样，关键字难以完全覆盖。

**解决方案**:
- ✅ **混合评分算法**: 关键字 (60%) + 文本相似度 (40%)
- ✅ **模糊匹配扩展**: 支持同义词映射 ("价格"≈"多少钱"≈"报价")
- ✅ **学习优化**: 记录高频未匹配评论，人工补充 Q&A

---

### 7.2 LLM 响应超时不稳定

**问题**: 网络波动导致 API 调用延迟 >10s。

**解决方案**:
- ✅ **线程超时控制**: `thread.join(timeout=10)` + daemon 线程
- ✅ **四级降级保障**: LLM→公共 Q&A→私有 Q&A→默认回复
- ✅ **预缓存热门产品 Q&A**: 减少实时 API 调用

---

### 7.3 视频 - 文案时间轴对齐精度

**问题**: LLM 生成的分段时间点与实际视频不完全匹配。

**解决方案**:
- ✅ **人工微调接口**: UI 提供可视化编辑器，可拖动调整分段点
- ✅ **FFmpeg 验证**: 提取实际视频时长，自动校验并提示偏差
- ✅ **缓冲策略**: 每段预留±2s 缓冲时间，避免衔接生硬

---

### 7.4 OBS 场景切换卡顿

**问题**: 多个视频源同时加载导致内存占用高、切换延迟。

**解决方案**:
- ✅ **按需加载**: 仅当前播放的产品视频加载到 OBS
- ✅ **预加载下一产品**: 后台准备下一个场景，减少等待时间
- ✅ **LivePortrait 复用**: 数字人实例全局单例，避免重复初始化

---

## A. 附录：配置文件示例

### config.yaml (完整配置)

```yaml
app:
  name: "Multi-AI-Stream"
  version: "2.0.0"

# LLM 配置
llm:
  mode: "remote"              # remote / local
  timeout_seconds: 10         # 超时时间 (秒)
  
  remote:
    provider: "deepseek"
    api_key: "sk-xxx"
    base_url: "https://api.deepseek.com/v1"
    model: "deepseek-chat"
  
  expert_role:
    definition: |
      你是一位资深房车产品专家，拥有 10 年以上 RV 行业经验。你的特点是：
      - 清晰专业：用简洁语言解释技术参数
      - 具体详实：提供真实数据和场景化描述
      - 耐心周到：主动解答用户可能关心的所有问题
      - 热情亲和：像朋友一样推荐产品，避免过度营销感
      
      回答风格要求:
      1. 每条回复不超过 80 字 (20 秒语音)
      2. 先肯定用户关注点，再补充关键信息
      3. 必要时提供对比建议或购买指导
      4. 结尾引导互动："感兴趣可以留言了解更多"

# Q&A 匹配配置
qa:
  min_confidence: 0.6         # 最低匹配置信度 (0-1)
  use_public_qa: true         # 是否启用公共 Q&A

# 输出目录
output_dir: "./output"

# TTS 配置
tts:
  engine: "edge"              # edge / coqui / iflytek
```

---

## B. 附录：JSON Schema 验证规则

### PublicQA Import Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "required": ["question", "answer"],
    "properties": {
      "question": {
        "type": "string",
        "minLength": 1,
        "description": "问题文本"
      },
      "answer": {
        "type": "string",
        "minLength": 1,
        "description": "回答文本"
      },
      "keywords": {
        "type": "array",
        "items": {"type": "string"},
        "default": []
      },
      "priority": {
        "type": "integer",
        "minimum": 1,
        "maximum": 100,
        "default": 50
      }
    }
  }
}
```

---

## C. 附录：NLP 识别正则表达式库

| 表达示例 | 正则模式 | 提取结果 |
|---------|---------|---------|
| "介绍下 3 号房车" | `(\d+)` | 3 |
| "看一下二号房车" | `(二 | 两 |2)` | 2 |
| "产品 5 的详细信息" | `product\s*(\d+)` | 5 |
| "第 10 号房车" | `第 (\d+) 号` | 10 |

---

**文档版本历史**:
- v1.0 (2026-05-13): 初始版本，Q&A 系统 + 循环模式 + 评论点播设计
- v1.1 (2026-05-13): 补充数字人联动方案 A(OBS 场景切换)

**下一步**: 等待用户进一步补充需求后开始实施。
