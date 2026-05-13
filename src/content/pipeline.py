"""
Content Generation Pipeline - Chain of Responsibility Pattern
内容生成流水线，使用责任链模式处理文案生成->TTS 合成->口型同步的流程
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
from ..core.base import Base
from ..core.enums import ScriptStage
from ..core.exceptions import ContentError, ScriptGenerationError, TTSError

logger = logging.getLogger(__name__)


class ContentPipeline(Base):
    """
    内容生成流水线
    
    处理流程:
    房源信息 → [ScriptGenerator] → TTS → [TTSHandler] → Audio → [LipSyncHandler] → Video
    
    设计模式：责任链模式 (Chain of Responsibility)
    
    使用示例:
        pipeline = ContentPipeline(config)
        video_path = pipeline.process(
            property_info="上海中环二手房，2 室 1 厅，89 平，500 万",
            avatar_engine=avatar_instance,
            output_dir="./output"
        )
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        
        # 初始化各个处理节点
        from .script_generator import ScriptGeneratorHandler
        from .tts_service import TTSHandler
        
        self.handlers = {
            ScriptStage.SCRIPT_GENERATION: ScriptGeneratorHandler(config.get('llm', {})),
            ScriptStage.TTS_SYNTHESIS: TTSHandler(config.get('tts', {})),
            # LipSyncHandler 将在需要时动态创建
        }
        
        # 输出目录
        self._output_dir = Path(config.get('output_dir', './output'))
        self._output_dir.mkdir(parents=True, exist_ok=True)
    
    def process(self, property_info: str, avatar_engine=None, 
                output_name: Optional[str] = None) -> Dict[str, Any]:
        """
        处理内容生成流水线
        
        Args:
            property_info: 房源/产品信息
            avatar_engine: 数字人引擎实例 (可选，用于口型同步)
            output_name: 输出文件名前缀
            
        Returns:
            dict: 包含各阶段结果的字典
                {
                    'script': str,           # 生成的文案
                    'audio_path': str,       # TTS 音频路径
                    'video_path': str,       # 最终视频路径 (如果做了口型同步)
                    'status': 'success'/'error',
                    'errors': [...]          # 错误列表
                }
        """
        result = {
            'script': '',
            'audio_path': '',
            'video_path': '',
            'status': 'success',
            'errors': [],
            'stages_completed': []
        }
        
        try:
            # 阶段 1: 文案生成
            script = self._process_script(property_info)
            result['script'] = script
            
            # 阶段 2: TTS 合成
            audio_path = self._process_tts(script, output_name or 'default')
            result['audio_path'] = audio_path
            
            # 阶段 3: 口型同步 (如果提供了 avatar_engine)
            if avatar_engine:
                video_path = self._process_lip_sync(audio_path, avatar_engine, output_name)
                result['video_path'] = video_path
            
            logger.info(f"内容生成完成：{audio_path}")
            
        except ScriptGenerationError as e:
            result['status'] = 'error'
            result['errors'].append({'stage': 'script', 'error': str(e)})
            logger.error(f"文案生成失败：{e}")
            
        except TTSError as e:
            result['status'] = 'error'
            result['errors'].append({'stage': 'tts', 'error': str(e)})
            logger.error(f"TTS 合成失败：{e}")
            
        except Exception as e:
            result['status'] = 'error'
            result['errors'].append({'stage': 'unknown', 'error': str(e)})
            logger.exception(f"内容生成流水线错误：{e}")
        
        return result
    
    def _process_script(self, property_info: str) -> str:
        """处理文案生成阶段"""
        handler = self.handlers[ScriptStage.SCRIPT_GENERATION]
        script = handler.handle(property_info)
        
        # 修复：使用实例变量追踪已完成的阶段
        if not hasattr(self, '_stages_completed'):
            self._stages_completed = []
        if ScriptStage.SCRIPT_GENERATION not in self._stages_completed:
            self._stages_completed.append(ScriptStage.SCRIPT_GENERATION)
        
        return script
    
    def _process_tts(self, script: str, output_name: str) -> str:
        """处理 TTS 合成阶段"""
        handler = self.handlers[ScriptStage.TTS_SYNTHESIS]
        audio_path = handler.handle(script, self._output_dir / f"{output_name}.wav")
        
        # 修复：使用实例变量追踪已完成的阶段
        if not hasattr(self, '_stages_completed'):
            self._stages_completed = []
        if ScriptStage.TTS_SYNTHESIS not in self._stages_completed:
            self._stages_completed.append(ScriptStage.TTS_SYNTHESIS)
        
        return str(audio_path)
    
    def _process_lip_sync(self, audio_path: str, avatar_engine, 
                          output_name: str) -> str:
        """处理口型同步阶段"""
        # TODO: 实现口型同步处理
        
        video_path = self._output_dir / f"{output_name}_synced.mp4"
        
        if not hasattr(self, '_stages_completed'):
            self._stages_completed = []
        if ScriptStage.LIP_SYNC not in self._stages_completed:
            self._stages_completed.append(ScriptStage.LIP_SYNC)
        
        return str(video_path)
    
    def add_handler(self, stage: ScriptStage, handler):
        """添加自定义处理节点"""
        self.handlers[stage] = handler
    
    def get_stage_status(self) -> Dict[str, bool]:
        """获取各阶段状态"""
        return {
            stage.value: stage in getattr(self, '_stages_completed', [])
            for stage in ScriptStage
        }
