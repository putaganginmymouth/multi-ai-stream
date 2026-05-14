"""
OBS Controller - Scene/Media Source Management
OBS 场景与媒体源切换控制器 (v4.0)

职责:
- 管理产品→OBS 场景的映射
- 切换 OBS 场景（SetCurrentProgramScene）
- 控制媒体源播放/暂停

设计模式：外观模式 (Facade)，封装 OBS WebSocket 调用
"""

import logging
import time
from typing import Dict, Any, Optional
from ..core.base import Configurable

logger = logging.getLogger(__name__)

# OBS WebSocket 可选依赖
try:
    from obswebsocket import obsws, requests as obs_requests
    HAS_OBS = True
except ImportError:
    HAS_OBS = False
    logger.warning("obs-websocket-py 未安装，OBS 控制功能不可用: pip install obs-websocket-py")


class ObsController(Configurable):
    """
    OBS 场景/媒体源切换控制器

    使用示例:
        ctrl = ObsController(config)
        ctrl.connect()
        ctrl.register_scene(product_id=1, scene_name="product_1_camper")
        ctrl.switch_to_product(1)
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        obs_cfg = config.get('obs', {})
        self._host = obs_cfg.get('host', 'localhost')
        self._port = obs_cfg.get('port', 4455)
        self._password = obs_cfg.get('password', '')
        self._max_retries = obs_cfg.get('max_retries', 3)
        self._retry_delay = obs_cfg.get('retry_delay', 2)

        self._ws: Optional[Any] = None

        # 场景映射: {product_id: scene_name}
        self._scene_map: Dict[int, str] = {}

        # 媒体源映射: {product_id: source_name}
        self._media_source_map: Dict[int, str] = {}

        # 场景命名模板
        self._scene_template = config.get('playback', {}).get(
            'obs_scene_template', 'product_{id}_{name}'
        )

    def _validate_config(self) -> bool:
        return bool(self._host and self._port)

    def connect(self) -> bool:
        """连接 OBS WebSocket（支持指数退避重试）"""
        if not HAS_OBS:
            logger.error("obs-websocket-py 未安装")
            return False

        for attempt in range(self._max_retries):
            try:
                self._ws = obsws(self._host, self._port, self._password)
                self._ws.connect()

                # 验证连接
                version = self._ws.call(obs_requests.GetVersion())
                logger.info(
                    f"OBS 连接成功: {self._host}:{self._port}, "
                    f"OBS v{version.getObsVersion()}"
                )
                return True

            except Exception as e:
                wait = self._retry_delay * (2 ** attempt)
                logger.warning(
                    f"OBS 连接失败 (第{attempt+1}/{self._max_retries}次): {e}. "
                    f"{wait}s 后重试..."
                )
                time.sleep(wait)

        logger.error(f"OBS 连接失败，已重试 {self._max_retries} 次")
        return False

    def disconnect(self):
        """断开 OBS 连接"""
        if self._ws:
            try:
                self._ws.disconnect()
            except Exception as e:
                logger.warning(f"断开 OBS 连接时出错: {e}")
            self._ws = None

    def register_scene(self, product_id: int, scene_name: str = None,
                       product_name: str = None):
        """
        注册产品→场景映射

        如果未指定 scene_name，自动使用模板生成:
        product_{id}_{name} 如 product_1_camper
        """
        if not scene_name:
            scene_name = self._scene_template.format(
                id=product_id, name=(product_name or str(product_id))
            )
        self._scene_map[product_id] = scene_name
        logger.debug(f"注册场景映射: product_id={product_id} → scene={scene_name}")

    def register_all_from_products(self, products: list):
        """从产品列表批量注册场景映射"""
        for product in products:
            self.register_scene(
                product_id=product.get('id'),
                product_name=product.get('name', '')
            )

    def switch_to_product(self, product_id: int) -> bool:
        """
        切换到指定产品的 OBS 场景

        Returns:
            bool: 切换是否成功
        """
        if product_id not in self._scene_map:
            logger.error(f"未注册产品场景映射: product_id={product_id}")
            return False

        if not self._ws or not self._is_connected():
            logger.error("OBS 未连接")
            return False

        scene_name = self._scene_map[product_id]

        try:
            self._ws.call(obs_requests.SetCurrentProgramScene(
                sceneName=scene_name
            ))
            logger.info(f"OBS 场景已切换: {scene_name}")
            return True

        except Exception as e:
            logger.error(f"OBS 场景切换失败: {e}")
            return False

    def get_current_scene(self) -> Optional[str]:
        """获取当前 OBS 场景名"""
        if not self._ws or not self._is_connected():
            return None

        try:
            response = self._ws.call(obs_requests.GetCurrentProgramScene())
            return response.getCurrentProgramSceneName()
        except Exception as e:
            logger.error(f"获取当前场景失败: {e}")
            return None

    def list_scenes(self) -> list:
        """获取所有可用场景列表"""
        if not self._ws or not self._is_connected():
            return []

        try:
            response = self._ws.call(obs_requests.GetSceneList())
            return [s['sceneName'] for s in response.getScenes()]
        except Exception as e:
            logger.error(f"获取场景列表失败: {e}")
            return []

    def set_media_source(self, product_id: int, source_name: str):
        """注册产品的媒体源（用于控制视频播放）"""
        self._media_source_map[product_id] = source_name

    def play_media(self, product_id: int) -> bool:
        """播放指定产品的媒体源"""
        if product_id not in self._media_source_map:
            return False

        source_name = self._media_source_map[product_id]
        try:
            self._ws.call(obs_requests.TriggerMediaInputAction(
                inputName=source_name,
                mediaAction='OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART'
            ))
            return True
        except Exception as e:
            logger.error(f"播放媒体源失败: {e}")
            return False

    def is_available(self) -> bool:
        """检查 OBS 是否可用"""
        return HAS_OBS and self._is_connected() if self._ws else HAS_OBS

    def _is_connected(self) -> bool:
        """检查 WebSocket 是否已连接"""
        if not self._ws:
            return False
        try:
            self._ws.call(obs_requests.GetVersion())
            return True
        except Exception:
            return False

    def get_scene_for_product(self, product_id: int) -> Optional[str]:
        """获取产品对应的场景名"""
        return self._scene_map.get(product_id)

    def clear_mappings(self):
        """清除所有场景和媒体源映射"""
        self._scene_map.clear()
        self._media_source_map.clear()
