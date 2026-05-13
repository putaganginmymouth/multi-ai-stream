"""
Custom Exceptions for Multi-AI-Stream
自定义异常体系
"""


class MultiStreamError(Exception):
    """
    基础异常类
    所有其他异常的父类
    """
    
    def __init__(self, message: str, code: str = "MS_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


class PlatformError(MultiStreamError):
    """
    平台相关异常
    """
    pass


class PlatformConnectionError(PlatformError):
    """平台连接失败"""
    
    def __init__(self, platform_name: str, reason: str):
        message = f"无法连接到 {platform_name}: {reason}"
        super().__init__(message, "PLATFORM_CONN_ERROR")


class PlatformAuthError(PlatformError):
    """平台认证失败"""
    
    def __init__(self, platform_name: str, error_msg: str):
        message = f"{platform_name} 认证失败：{error_msg}"
        super().__init__(message, "PLATFORM_AUTH_ERROR")


class PlatformStreamError(PlatformError):
    """平台推流错误"""
    
    def __init__(self, platform_name: str, error_code: int, error_desc: str):
        message = f"{platform_name} 推流错误 ({error_code}): {error_desc}"
        super().__init__(message, "PLATFORM_STREAM_ERROR")


class AvatarError(MultiStreamError):
    """
    数字人生成相关异常
    """
    pass


class AvatarEngineNotFoundError(AvatarError):
    """数字人引擎未找到"""
    
    def __init__(self, engine_type: str):
        message = f"未找到数字人引擎：{engine_type}"
        super().__init__(message, "AVATAR_ENGINE_NOT_FOUND")


class AvatarGenerationError(AvatarError):
    """数字人生成失败"""
    
    def __init__(self, reason: str, details: str = ""):
        message = f"数字人生成失败：{reason}"
        if details:
            message += f"\n详情：{details}"
        super().__init__(message, "AVATAR_GEN_ERROR")


class ModelNotFoundError(AvatarError):
    """模型文件未找到"""
    
    def __init__(self, model_path: str):
        message = f"模型文件不存在：{model_path}"
        super().__init__(message, "MODEL_NOT_FOUND")


class LipSyncError(AvatarError):
    """口型同步错误"""
    
    def __init__(self, reason: str):
        message = f"口型同步失败：{reason}"
        super().__init__(message, "LIP_SYNC_ERROR")


class ContentError(MultiStreamError):
    """
    内容生成相关异常
    """
    pass


class ScriptGenerationError(ContentError):
    """文案生成失败"""
    
    def __init__(self, reason: str):
        message = f"LLM 文案生成失败：{reason}"
        super().__init__(message, "SCRIPT_GEN_ERROR")


class TTSError(ContentError):
    """TTS 合成错误"""
    
    def __init__(self, engine_name: str, error_msg: str):
        message = f"{engine_name} TTS 合成失败：{error_msg}"
        super().__init__(message, "TTS_ERROR")


class AssetNotFoundError(ContentError):
    """素材未找到"""
    
    def __init__(self, asset_type: str, asset_name: str):
        message = f"未找到 {asset_type} 素材：{asset_name}"
        super().__init__(message, "ASSET_NOT_FOUND")


class ConfigError(MultiStreamError):
    """
    配置相关异常
    """
    
    def __init__(self, config_key: str, error_msg: str):
        message = f"配置错误 [{config_key}]: {error_msg}"
        super().__init__(message, "CONFIG_ERROR")


class ValidationError(MultiStreamError):
    """
    数据验证异常
    """
    
    def __init__(self, field_name: str, error_msg: str):
        message = f"字段验证失败 [{field_name}]: {error_msg}"
        super().__init__(message, "VALIDATION_ERROR")


class DependencyError(MultiStreamError):
    """
    依赖缺失异常
    """
    
    def __init__(self, dependency_name: str, install_cmd: str = ""):
        message = f"缺少依赖：{dependency_name}"
        if install_cmd:
            message += f"\n请运行：{install_cmd}"
        super().__init__(message, "DEPENDENCY_ERROR")
