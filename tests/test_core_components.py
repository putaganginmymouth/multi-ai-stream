"""
Quick Test - Verify Core Components Initialization
快速验证核心组件初始化是否正常
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_database_models():
    """测试数据库模型导入"""
    
    print("=" * 60)
    print("Testing Database Models...")
    print("=" * 60)
    
    from src.data.models import (
        ProductAsset, PublicQA, CurrentProductState, 
        LiveRoomConfig, SystemConfig
    )
    
    print("✅ All models imported successfully:")
    print(f"   - ProductAsset: {ProductAsset.__tablename__}")
    print(f"   - PublicQA: {PublicQA.__tablename__}")
    print(f"   - CurrentProductState: {CurrentProductState.__tablename__}")
    print(f"   - LiveRoomConfig: {LiveRoomConfig.__tablename__}")
    print(f"   - SystemConfig: {SystemConfig.__tablename__}")


def test_repository():
    """测试仓库层"""
    
    print("\n" + "=" * 60)
    print("Testing Repository Layer...")
    print("=" * 60)
    
    from src.data.repository import (
        ProductAssetRepository, PublicQARepository,
        CurrentProductStateRepository, LiveRoomConfigRepository
    )
    
    print("✅ All repositories imported successfully:")
    print(f"   - ProductAssetRepository")
    print(f"   - PublicQARepository")
    print(f"   - CurrentProductStateRepository")
    print(f"   - LiveRoomConfigRepository")


def test_service():
    """测试服务层"""
    
    print("\n" + "=" * 60)
    print("Testing Service Layer...")
    print("=" * 60)
    
    from src.data.services import get_public_qa_service, get_product_state_service
    
    service = get_public_qa_service()
    assert service is not None
    
    state_service = get_product_state_service()
    assert state_service is not None
    
    print("✅ All services imported successfully:")
    print(f"   - PublicQAService (singleton): {service}")
    print(f"   - ProductStateService: {state_service}")


def test_reply_generator():
    """测试评论回复生成器"""
    
    print("\n" + "=" * 60)
    print("Testing Reply Generator...")
    print("=" * 60)
    
    from src.content.reply_generator import ReplyGeneratorHandler
    
    # Create with minimal config
    config = {
        'expert_role': {
            'definition': '你是一位专业的房车产品专家。'
        },
        'llm_timeout_seconds': 10,
        'qa_match_min_confidence': 0.6
    }
    
    handler = ReplyGeneratorHandler(config)
    assert handler is not None
    
    print("✅ ReplyGeneratorHandler created successfully")
    print(f"   - Config: {handler.config}")


def test_wecom_adapter():
    """测试企业微信 Webhook 适配器"""
    
    print("\n" + "=" * 60)
    print("Testing WeCom Webhook Adapter...")
    print("=" * 60)
    
    from src.platform_adapters.adapters.wecom_webhook_adapter import (
        WeComWebhookAdapter, get_wecom_adapter
    )
    
    # Test singleton pattern
    adapter1 = get_wecom_adapter('https://test.url?key=abc')
    adapter2 = get_wecom_adapter('https://test.url?key=abc')
    
    assert adapter1 is adapter2, "WeComWebhookAdapter should be singleton per URL"
    
    print("✅ WeComWebhookAdapter created successfully")
    print(f"   - Adapter: {adapter1}")


def test_qa_import_export():
    """测试 Q&A 导入导出功能"""
    
    print("\n" + "=" * 60)
    print("Testing Q&A Import/Export...")
    print("=" * 60)
    
    from src.data.services import get_public_qa_service
    
    service = get_public_qa_service()
    
    # Test JSON format validation
    test_json = '''[
        {
            "question": "价格多少？",
            "answer": "这款房车售价 88 万，性价比很高。",
            "keywords": ["价格", "多少钱", "报价"],
            "priority": 80
        },
        {
            "question": "尺寸多大？",
            "answer": "长度 5.9 米，宽度 2.4 米，高度 3.0 米。",
            "keywords": ["尺寸", "大小", "长宽高"],
            "priority": 70
        }
    ]'''
    
    try:
        result = service.import_from_json(test_json)
        
        if result['failed'] > 0:
            raise RuntimeError(f"Import failed: {result['errors']}")
        
        print("✅ JSON validation passed")
        print(f"   - Imported {result['success']} Q&A pairs successfully")
        
    except Exception as e:
        print(f"❌ JSON validation failed: {e}")
        raise


if __name__ == '__main__':
    
    print("\n" + "=" * 60)
    print("Multi-AI-Stream v2.0 Core Components Test")
    print("=" * 60 + "\n")
    
    try:
        test_database_models()
        test_repository()
        test_service()
        test_reply_generator()
        test_wecom_adapter()
        test_qa_import_export()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
    except Exception as e:
        print("\n" + "❌ TEST FAILED:", str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
