"""
PyInstaller Build Script for Windows EXE
Windows EXE 打包脚本
"""

import sys
import os
from pathlib import Path


def build_exe():
    """构建 Windows EXE"""
    
    # 项目根目录
    project_root = Path(__file__).parent.parent
    
    # PyInstaller 命令参数
    spec_content = f"""
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('configs/config.yaml', 'configs'),
        ('assets/avatars', 'assets/avatars'),
        ('assets/backgrounds', 'assets/backgrounds'),
    ],
    hiddenimports=[
        'PyQt6',
        'sqlalchemy',
        'pyyaml',
        'numpy',
        'cv2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='MultiAIStream',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # UPX 压缩
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""
    
    # 写入 spec 文件
    spec_path = project_root / 'MultiAIStream.spec'
    spec_path.write_text(spec_content)
    
    print(f"创建 spec 文件：{spec_path}")
    
    # 执行 PyInstaller
    import subprocess
    
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        str(spec_path),
    ]
    
    print(f"执行命令：{' '.join(cmd)}")
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode == 0:
        dist_dir = project_root / 'dist'
        exe_file = dist_dir / 'MultiAIStream.exe'
        
        print(f"\n✓ 打包成功!")
        print(f"EXE 文件位置：{exe_file}")
        print(f"文件大小：{exe_file.stat().st_size / 1024 / 1024:.2f} MB")
    else:
        print("\n✗ 打包失败，请检查错误信息")


if __name__ == '__main__':
    build_exe()
