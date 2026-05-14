"""
Seed Data Script — 录入初始产品数据 (v4.0)
用于在首次部署时快速录入测试产品

用法:
    cd multi-ai-stream
    python scripts/seed_data.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data.repository import ProductAssetRepository, PublicQARepository
from pathlib import Path


def seed_products(db_path: str = None):
    """录入初始产品数据"""
    if db_path is None:
        db_path = str(Path(__file__).parent.parent / 'data' / 'multistream.db')

    repo = ProductAssetRepository(db_path)
    qa_repo = PublicQARepository(db_path)

    products = [
        {
            'name': '1号房车 - 豪华越野版',
            'product_alias': '1号,一号,1号房车,豪华版,越野版,1号车',
            'video_path': 'assets/videos/product_1.mp4',
            'product_detail': '品牌:远方房车\n型号:豪华越野版\n尺寸:5.9×2.4×3.0米\n价格:88万\n配置:太阳能供电、四驱底盘、独立卫生间、双人床\n适合:越野爱好者、长途旅行',
            'duration': 120,
            'script_text': '欢迎来到直播间！今天给大家带来的是这款豪华越野房车。它全长5.9米，蓝牌C照就能开！搭载四驱底盘，什么路都能走。顶部配备800W太阳能板，野外也能自给自足。内部非常宽敞，双人床、独立卫生间、厨房一应俱全。现在只要88万，首付20%就能开回家！',
            'script_segments': [
                {"start": 0, "end": 15, "text": "欢迎语+整体外观", "visual": "wide"},
                {"start": 15, "end": 45, "text": "尺寸和驾驶资格", "visual": "closeup"},
                {"start": 45, "end": 70, "text": "太阳能+配置亮点", "visual": "wide"},
                {"start": 70, "end": 95, "text": "内部空间展示", "visual": "closeup"},
                {"start": 95, "end": 120, "text": "价格+购买引导", "visual": "wide"},
            ],
            'qa_pairs': [
                {
                    "question": "多少钱",
                    "answer": "这款豪华越野版房车售价88万，首付20%只要17.6万。",
                    "keywords": ["价格", "多少钱", "报价", "贵不贵"]
                },
                {
                    "question": "油耗多少",
                    "answer": "柴油2.8T发动机，百公里油耗约12升，高速更低。",
                    "keywords": ["油耗", "费油", "油钱"]
                },
                {
                    "question": "能睡几个人",
                    "answer": "标准配置双人床+卡座变床，最多可睡4人。",
                    "keywords": ["睡觉", "床位", "住人", "休息"]
                },
            ],
            'avatar_image_path': 'assets/avatars/avatar.jpg',
        },
        {
            'name': '2号房车 - 经济舒适版',
            'product_alias': '2号,二号,2号房车,经济版,舒适版,2号车',
            'video_path': 'assets/videos/product_2.mp4',
            'product_detail': '品牌:远方房车\n型号:经济舒适版\n尺寸:4.8×2.2×2.6米\n价格:38万\n配置:基础水电系统、双人床、简易厨房\n适合:城市周边游、小家庭出行',
            'duration': 90,
            'script_text': '接下来看这款经济舒适版房车！4.8米车长，停车超方便。现在只要38万就能拥有一辆属于自己的房车。基础水电、双人床、厨房都配齐了，周末带上家人来一场说走就走的旅行！',
            'script_segments': [
                {"start": 0, "end": 10, "text": "开场介绍", "visual": "wide"},
                {"start": 10, "end": 50, "text": "外观尺寸+停车优势", "visual": "closeup"},
                {"start": 50, "end": 90, "text": "内部配置+价格引导", "visual": "wide"},
            ],
            'qa_pairs': [
                {
                    "question": "多少钱",
                    "answer": "经济舒适版38万，性价比非常高。",
                    "keywords": ["价格", "多少钱", "报价"]
                },
            ],
            'avatar_image_path': 'assets/avatars/avatar.jpg',
        },
    ]

    # 录入产品
    for p in products:
        pid = repo.save(p)
        print(f"  ✅ 产品 {pid}: {p['name']}")

    # 录入公共 Q&A
    public_qas = [
        {
            'question': '保修多久',
            'answer': '全系房车提供3年或6万公里质保，底盘5年质保。',
            'keywords': ['保修', '售后', '质保', '维修'],
            'priority': 90,
            'linked_product_id': 1,
        },
        {
            'question': '可以贷款吗',
            'answer': '支持银行按揭，首付最低20%，最长5年分期。也支持厂家金融0利率方案。',
            'keywords': ['贷款', '按揭', '分期', '首付'],
            'priority': 85,
            'linked_product_id': None,
        },
        {
            'question': '在哪里看车',
            'answer': '我们在北京、上海、广州、成都都有展厅，也可以预约上门试驾。',
            'keywords': ['看车', '试驾', '展厅', '地址', '哪里'],
            'priority': 80,
            'linked_product_id': None,
        },
    ]

    for qa in public_qas:
        qid = qa_repo.save(qa)
        print(f"  ✅ 公共QA {qid}: {qa['question']}")

    print(f"\n{'='*50}")
    print(f"数据录入完成！")
    print(f"  产品: {len(products)} 个")
    print(f"  公共QA: {len(public_qas)} 条")
    print(f"  运行 python src/main.py 启动 GUI")
    print(f"{'='*50}")


if __name__ == '__main__':
    seed_products()
