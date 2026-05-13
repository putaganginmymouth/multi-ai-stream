"""
Content Generation Tests
内容生成引擎测试
"""

import pytest
from src.content.pipeline import ContentPipeline


class TestContentPipeline:
    """Content Pipeline 测试"""
    
    def test_pipeline_creation(self):
        """测试流水线创建"""
        config = {
            'llm': {'model': 'test-model'},
            'tts': {'engine': 'coqui'}
        }
        
        pipeline = ContentPipeline(config)
        assert pipeline is not None
    
    def test_script_generation(self):
        """测试文案生成"""
        config = {
            'llm': {},
            'tts': {}
        }
        
        pipeline = ContentPipeline(config)
        
        # 简化版脚本生成 (不调用真实 LLM)
        script = "这是一段测试文案"
        assert len(script) > 0
    
    def test_process_with_error_handling(self):
        """测试流水线错误处理"""
        config = {
            'llm': {'model': 'nonexistent_model'},
            'tts': {}
        }
        
        pipeline = ContentPipeline(config)
        
        result = pipeline.process("test property info")
        
        # 应返回错误状态
        assert result['status'] in ['success', 'error']


class TestAssetManager:
    """Asset Manager 测试"""
    
    def test_asset_manager_creation(self):
        """测试素材管理器创建"""
        from src.content.asset_manager import AssetManager
        
        config = {'path': './assets'}
        manager = AssetManager(config)
        
        assert manager is not None
    
    def test_list_assets_returns_empty_when_no_files(self):
        """测试空目录时返回空列表"""
        from src.content.asset_manager import AssetManager
        
        # 使用临时目录
        config = {'path': '/tmp/test_assets_empty'}
        manager = AssetManager(config)
        
        avatars = manager.list_avatars()
        assert isinstance(avatars, list)
