"""
Asset Manager - 素材库管理模块
负责管理数字人图片、背景场景等静态资源
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import shutil
from ..core.base import Base
from ..core.enums import PropertyCategory
from ..core.exceptions import AssetNotFoundError

logger = logging.getLogger(__name__)


class AssetManager(Base):
    """
    素材库管理器
    
    功能:
    - 管理数字人头像图片
    - 管理直播背景场景
    - 管理文案模板
    - 支持素材分类和标签
    
    目录结构:
        assets/
        ├── avatars/          # 数字人图片
        │   ├── default.jpg
        │   └── custom/
        ├── backgrounds/      # 背景场景
        │   ├── living_room/
        │   ├── office/
        │   └── outdoor/
        └── templates/        # 文案模板
            └── property_template.txt
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__()
        
        self.config = config
        
        # 素材库根目录
        self._root_path = Path(config.get('path', './assets'))
        self._avatars_path = self._root_path / 'avatars'
        self._backgrounds_path = self._root_path / 'backgrounds'
        self._templates_path = self._root_path / 'templates'
        
        # 创建目录结构
        self._init_directories()
    
    def _init_directories(self):
        """初始化素材库目录"""
        for path in [self._avatars_path, self._backgrounds_path, self._templates_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    # ========== 数字人头像管理 ==========
    
    def list_avatars(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        列出所有数字人头像
        
        Args:
            category: 分类 (可选)
            
        Returns:
            list: [{'name': str, 'path': Path, 'category': str}, ...]
        """
        avatars = []
        
        for img_path in self._avatars_path.rglob('*.jpg'):
            avatars.append({
                'name': img_path.stem,
                'path': img_path,
                'category': category or 'default'
            })
        
        for img_path in self._avatars_path.rglob('*.png'):
            avatars.append({
                'name': img_path.stem,
                'path': img_path,
                'category': category or 'default'
            })
        
        return avatars
    
    def get_avatar(self, name: str) -> Path:
        """
        获取指定数字人头像路径
        
        Args:
            name: 头像名称 (不含扩展名)
            
        Returns:
            Path: 图片文件路径
            
        Raises:
            AssetNotFoundError: 如果未找到
        """
        for ext in ['jpg', 'png', 'jpeg']:
            avatar_path = self._avatars_path / f"{name}.{ext}"
            if avatar_path.exists():
                return avatar_path
        
        raise AssetNotFoundError('avatar', name)
    
    def upload_avatar(self, image_path: Path, name: Optional[str] = None,
                      category: str = 'custom') -> Path:
        """
        上传数字人头像
        
        Args:
            image_path: 源图片路径
            name: 保存名称 (可选，默认使用原文件名)
            category: 分类
            
        Returns:
            Path: 保存后的路径
        """
        save_name = name or image_path.stem
        
        # 创建分类目录
        if category != 'default':
            category_dir = self._avatars_path / category
            category_dir.mkdir(parents=True, exist_ok=True)
            
            dest_path = category_dir / f"{save_name}.jpg"
        else:
            dest_path = self._avatars_path / f"{save_name}.jpg"
        
        # 复制文件
        shutil.copy2(image_path, dest_path)
        
        logger.info(f"上传头像：{image_path} -> {dest_path}")
        return dest_path
    
    def delete_avatar(self, name: str):
        """删除数字人头像"""
        avatar_path = self.get_avatar(name)
        avatar_path.unlink()
        logger.info(f"删除头像：{name}")
    
    # ========== 背景场景管理 ==========
    
    def list_backgrounds(self) -> List[Dict[str, Any]]:
        """列出所有背景场景"""
        backgrounds = []
        
        for category_dir in self._backgrounds_path.iterdir():
            if category_dir.is_dir():
                for img_path in category_dir.glob('*.jpg'):
                    backgrounds.append({
                        'name': img_path.stem,
                        'path': img_path,
                        'category': category_dir.name
                    })
        
        return backgrounds
    
    def get_background(self, name: str) -> Path:
        """获取背景场景路径"""
        for ext in ['jpg', 'png']:
            # 尝试所有分类目录
            for cat_dir in self._backgrounds_path.iterdir():
                if cat_dir.is_dir():
                    bg_path = cat_dir / f"{name}.{ext}"
                    if bg_path.exists():
                        return bg_path
        
        raise AssetNotFoundError('background', name)
    
    # ========== 文案模板管理 ==========
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """列出所有文案模板"""
        templates = []
        
        for template_file in self._templates_path.iterdir():
            if template_file.is_file():
                templates.append({
                    'name': template_file.stem,
                    'path': template_file
                })
        
        return templates
    
    def get_template(self, name: str) -> str:
        """获取模板内容"""
        template_path = self._templates_path / f"{name}.txt"
        
        if not template_path.exists():
            raise AssetNotFoundError('template', name)
        
        return template_path.read_text(encoding='utf-8')
    
    def save_template(self, name: str, content: str):
        """保存模板内容"""
        template_path = self._templates_path / f"{name}.txt"
        template_path.write_text(content, encoding='utf-8')
        logger.info(f"保存模板：{name}")
    
    # ========== 场景匹配 ==========
    
    def match_background(self, property_type: PropertyCategory, 
                         style: str = 'modern') -> Optional[Path]:
        """
        根据房产类型和风格匹配背景场景
        
        Args:
            property_type: 房产分类
            style: 风格 (modern/classic/outdoor)
            
        Returns:
            Path: 匹配的背景图片路径，未找到返回 None
        """
        # 简单的映射规则
        mapping = {
            PropertyCategory.RVS: ['rv', 'motorhome', 'camping'],
            PropertyCategory.HOUSE: ['house', 'residential', 'living_room'],
            PropertyCategory.APARTMENT: ['apartment', 'condo', 'interior'],
            PropertyCategory.COMMERCIAL: ['office', 'commercial', 'building']
        }
        
        keywords = mapping.get(property_type, [])
        
        for bg in self.list_backgrounds():
            bg_name = bg['name'].lower()
            if any(kw in bg_name for kw in keywords):
                return bg['path']
        
        # 返回默认背景
        default_bg = self._backgrounds_path / 'default.jpg'
        if default_bg.exists():
            return default_bg
        
        return None
    
    def get_asset_stats(self) -> Dict[str, int]:
        """获取素材库统计信息"""
        return {
            'avatars': len(self.list_avatars()),
            'backgrounds': len(self.list_backgrounds()),
            'templates': len(self.list_templates())
        }
