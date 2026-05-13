"""
Comment Responder Tests - 评论回复引擎测试
"""

import pytest
from unittest.mock import Mock, patch
from src.comment.responder import Responder, TemplateResponder, SimpleResponder


class TestResponder:
    """Responder 基类测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {
            'min_delay_seconds': 5,
            'enabled': True
        }
    
    def test_init_default_delay(self, sample_config):
        """测试默认最小回复间隔"""
        responder = Responder(sample_config)
        
        assert responder.min_delay == 5
    
    def test_should_reply_frequency_control(self, sample_config):
        """测试频率控制"""
        responder = Responder(sample_config)
        
        # 首次调用应该可以回复
        assert responder.should_reply() is True
        
        # 模拟刚刚回复过
        import time
        responder.last_reply_time = time.time()
        
        # 短时间内不应再次回复
        assert responder.should_reply() is False
    
    def test_on_comment_frequency_blocked(self, sample_config):
        """测试频率控制下 on_comment 返回 None"""
        responder = Responder(sample_config)
        
        # 模拟刚刚回复过
        import time
        responder.last_reply_time = time.time()
        
        mock_comment = Mock()
        result = responder.on_comment(mock_comment)
        
        assert result is None


class TestTemplateResponder:
    """TemplateResponder 模板匹配测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {
            'min_delay_seconds': 2,
            'enabled': True
        }
    
    def test_init_templates_loaded(self, sample_config):
        """测试初始化时加载话术模板"""
        responder = TemplateResponder(sample_config)
        
        assert 'welcome' in responder.templates
        assert 'price_inquiry' in responder.templates
        assert len(responder.templates) == 8
    
    @pytest.fixture
    def mock_comment(self):
        comment = Mock()
        comment.content = "这个房子多少钱？"
        comment.username = "用户 123"
        return comment
    
    def test_price_inquiry_match(self, sample_config, mock_comment):
        """测试价格询问匹配"""
        responder = TemplateResponder(sample_config)
        
        response = responder._generate_response(mock_comment)
        
        assert response is not None
        assert len(response) > 0
    
    def test_location_inquiry_match(self, sample_config):
        """测试位置询问匹配"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "房子在哪里？"
        comment.username = "张三"
        
        response = responder._generate_response(comment)
        
        assert response is not None
    
    def test_area_inquiry_match(self, sample_config):
        """测试面积询问匹配"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "多大面积的？"
        comment.username = "李四"
        
        response = responder._generate_response(comment)
        
        assert response is not None
    
    def test_decoration_inquiry_match(self, sample_config):
        """测试装修询问匹配"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "是精装还是毛坯？"
        comment.username = "王五"
        
        response = responder._generate_response(comment)
        
        assert response is not None
    
    def test_loan_inquiry_match(self, sample_config):
        """测试贷款询问匹配"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "支持公积金贷款吗？"
        comment.username = "赵六"
        
        response = responder._generate_response(comment)
        
        assert response is not None
    
    def test_welcome_match(self, sample_config):
        """测试欢迎语匹配"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "大家好，新来的！"
        comment.username = "新用户"
        
        response = responder._generate_response(comment)
        
        assert response is not None
        # 验证 nickname 被替换
        assert "新用户" in response or "用户" in response
    
    def test_no_match_returns_none(self, sample_config):
        """测试无匹配时返回 None"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "随机无关内容 xyz123"
        comment.username = "测试"
        
        response = responder._generate_response(comment)
        
        assert response is None


class TestSimpleResponder:
    """SimpleResponder 简化版测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {'min_delay_seconds': 2}
    
    def test_fixed_response(self, sample_config):
        """测试固定回复模式"""
        responder = SimpleResponder(sample_config)
        
        comment = Mock()
        comment.content = "任意内容"
        comment.username = "用户"
        
        response = responder._generate_response(comment)
        
        assert response == responder.default_response


class TestResponderFrequencyControl:
    """Responder 频率控制专项测试"""
    
    @pytest.fixture
    def sample_config(self):
        return {'min_delay_seconds': 1}
    
    def test_consecutive_calls_respect_delay(self, sample_config):
        """测试连续调用遵守延迟间隔"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "价格多少？"
        comment.username = "用户"
        
        # 第一次回复应该成功
        response1 = responder.on_comment(comment)
        assert response1 is not None
        
        # 短时间内第二次调用应被频率控制阻止
        import time
        time.sleep(0.5)  # 小于 min_delay_seconds
        
        response2 = responder.on_comment(comment)
        assert response2 is None
    
    def test_second_call_after_delay(self, sample_config):
        """测试延迟后再次可以回复"""
        responder = TemplateResponder(sample_config)
        
        comment = Mock()
        comment.content = "价格多少？"
        comment.username = "用户"
        
        # 第一次回复
        response1 = responder.on_comment(comment)
        assert response1 is not None
        
        # 等待超过 min_delay_seconds
        import time
        time.sleep(1.5)
        
        # 第二次调用应该成功
        response2 = responder.on_comment(comment)
        assert response2 is not None
