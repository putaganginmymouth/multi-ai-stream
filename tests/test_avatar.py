"""
Avatar Engine Tests
数字人生成引擎测试
"""

import pytest
from src.avatar.factory import AvatarFactory


class TestAvatarFactory:
    """Avatar Factory 测试"""
    
    def test_create_live_portrait_engine(self, sample_avatar_config):
        """测试创建 LivePortrait 引擎实例"""
        engine = AvatarFactory.create("live_portrait", sample_avatar_config)
        
        assert engine is not None
        assert str(engine.get_model_info()['name']) == "LivePortraitEngine"
    
    def test_create_wav2lip_engine(self):
        """测试创建 Wav2Lip 引擎实例"""
        config = {
            'type': 'wav2lip',
            'models_path': './assets/avatars'
        }
        
        engine = AvatarFactory.create("wav2lip", config)
        assert engine is not None
    
    def test_create_invalid_engine(self):
        """测试创建不存在引擎类型应抛出异常"""
        with pytest.raises(Exception):  # AvatarEngineNotFoundError
            AvatarFactory.create("invalid_engine", {})


class TestBaseAvatar:
    """Base Avatar 抽象类测试"""
    
    def test_model_loading_fails_gracefully(self, sample_avatar_config):
        """测试模型加载时不应崩溃"""
        engine = AvatarFactory.create("live_portrait", sample_avatar_config)
        
        # load_model() 应安全返回（成功或失败），但绝不应抛出未处理异常
        result = engine.load_model()
        assert isinstance(result, bool), "load_model() 应返回布尔值"
