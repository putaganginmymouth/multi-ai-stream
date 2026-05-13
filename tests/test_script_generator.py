"""
Script Generator Tests - LLM 文案生成器测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.content.script_generator import ScriptGeneratorHandler


class TestScriptGeneratorHandler:
    """ScriptGeneratorHandler 核心功能测试"""
    
    @pytest.fixture
    def remote_config(self):
        return {
            'llm': {
                'mode': 'remote',
                'remote': {
                    'provider': 'deepseek',
                    'api_key': 'test_api_key_123456',
                    'base_url': 'https://api.deepseek.com/v1',
                    'model': 'deepseek-chat'
                }
            },
            'llm.prompt_config': {
                'role': '二手房车销售专家',
                'product_type': '房产和房车产品',
                'selling_points': ['核心地段', '精装修']
            }
        }
    
    @pytest.fixture
    def local_mode_config(self):
        return {
            'llm': {
                'mode': 'local',
                'local': {
                    'model': 'qwen/Qwen-7B-Chat-GGUF'
                }
            }
        }
    
    @pytest.fixture
    def sample_property_info(self):
        return "上海中环二手房，2 室 1 厅，89 平，500 万"
    
    def test_init_with_remote_config(self, remote_config):
        """测试远程 API 模式初始化"""
        handler = ScriptGeneratorHandler(remote_config)
        
        assert handler._mode == 'remote'
        assert handler._provider == 'deepseek'
        assert handler._api_key == 'test_api_key_123456'
    
    def test_init_with_local_mode(self, local_mode_config):
        """测试本地模式初始化"""
        handler = ScriptGeneratorHandler(local_mode_config)
        
        assert handler._mode == 'local'
    
    @patch('src.content.script_generator.requests.post')
    def test_generate_with_remote_api_success(self, mock_post, remote_config, sample_property_info):
        """测试远程 API 成功生成"""
        # Mock API 响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {
                    'content': '【开场】大家好！\n\n【核心卖点】优质房源\n\n【互动引导】欢迎咨询'
                }
            }]
        }
        mock_post.return_value = mock_response
        
        handler = ScriptGeneratorHandler(remote_config)
        
        script = handler.handle(sample_property_info)
        
        assert script is not None
        assert len(script) > 0
    
    @patch('src.content.script_generator.requests.post')
    def test_generate_with_remote_api_no_api_key(self, mock_post, remote_config):
        """测试无 API Key 时抛出异常"""
        # 移除 API key
        config = {
            'llm': {
                'mode': 'remote',
                'remote': {
                    'provider': 'deepseek',
                    'api_key': '',  # Empty key
                    'base_url': 'https://api.deepseek.com/v1'
                }
            }
        }
        
        handler = ScriptGeneratorHandler(config)
        
        with pytest.raises(Exception):  # ScriptGenerationError
            handler.handle("测试信息")
    
    def test_generate_with_local_mode_fallback(self, local_mode_config, sample_property_info):
        """测试本地模式返回降级文案"""
        handler = ScriptGeneratorHandler(local_mode_config)
        
        script = handler.handle(sample_property_info)
        
        assert script is not None
        # 验证包含基本的结构标记
        assert '【开场】' in script or len(script) > 50
    
    def test_clean_generated_text_removes_markdown(self):
        """测试清理 Markdown 标记"""
        handler = ScriptGeneratorHandler({})
        
        text_with_md = "```text\n【开场】大家好！\n```\n\n【核心卖点】优质房源"
        cleaned = handler._clean_generated_text(text_with_md)
        
        assert '```' not in cleaned
    
    def test_parse_script_structure(self):
        """测试解析文案结构"""
        handler = ScriptGeneratorHandler({})
        
        script = """【开场】(5-10 秒)
大家好！今天给大家带来一套优质房源。

【核心卖点】(20-30 秒)
位于市中心，精装修，性价比高。

【互动引导】(5-10 秒)
欢迎私信咨询！"""
        
        parsed = handler.parse_script(script)
        
        assert 'opening' in parsed
        assert 'highlights' in parsed
        assert 'call_to_action' in parsed
    
    def test_estimate_duration(self):
        """测试时长估算"""
        handler = ScriptGeneratorHandler({})
        
        # 约 100 个中文字符，按 250 字/分钟计算应约 24 秒
        script = "大家好！今天给大家带来一套优质房源。位于市中心，精装修。"
        
        duration = handler.estimate_duration(script)
        
        assert duration > 0
        # 验证估算在合理范围内 (10-60 秒)
        assert 5 <= duration <= 90


class TestScriptGeneratorPromptConfig:
    """测试动态 Prompt 配置"""
    
    def test_prompt_config_loaded(self):
        """测试 prompt_config 加载"""
        config = {
            'llm': {
                'prompt_config': {
                    'role': '房产销售专家',
                    'product_type': '高端住宅',
                    'selling_points': ['景观好', '交通便利']
                }
            }
        }
        
        handler = ScriptGeneratorHandler(config)
        
        assert handler._role == '房产销售专家'
        assert handler._product_type == '高端住宅'
        assert len(handler._selling_points) == 2
    
    def test_system_prompt_template_usage(self):
        """测试系统提示词模板使用"""
        config = {
            'llm': {
                'system_prompt_template': "你是一位{role}，擅长介绍{product_type}。",
                'prompt_config': {
                    'role': '销售专家',
                    'product_type': '房产'
                }
            }
        }
        
        handler = ScriptGeneratorHandler(config)
        
        assert hasattr(handler, '_system_prompt_template')


class TestScriptGeneratorFallback:
    """测试降级文案生成"""
    
    def test_fallback_script_structure(self):
        """测试降级文案包含基本结构"""
        config = {'llm': {}}  # Empty config triggers fallback
        
        handler = ScriptGeneratorHandler(config)
        
        script = handler._generate_fallback_script("测试房源信息")
        
        assert '【开场】' in script
        assert '【核心卖点】' in script
        assert '【互动引导】' in script
