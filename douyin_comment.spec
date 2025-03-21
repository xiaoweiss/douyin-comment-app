# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['douyin_comment_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'playwright._impl._generated',
        'playwright.async_api',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 添加Playwright浏览器文件
import os
import sys
import glob

browser_base = os.path.expandvars(r"%LOCALAPPDATA%\ms-playwright")
chromium_dirs = glob.glob(os.path.join(browser_base, "chromium-*"))

if chromium_dirs:
    latest_dir = max(chromium_dirs, key=os.path.getmtime)
    browser_dir = os.path.join(latest_dir, "chrome-win")
else:
    browser_dir = ""

if os.path.exists(browser_dir):
    # 文件格式：(dest, source, 'DATA')
    browser_files = [
        ('chrome.exe', os.path.join(browser_dir, 'chrome.exe'), 'DATA'),
        ('chrome_100_percent.pak', os.path.join(browser_dir, 'chrome_100_percent.pak'), 'DATA'),
        ('chrome_200_percent.pak', os.path.join(browser_dir, 'chrome_200_percent.pak'), 'DATA'),
        ('resources.pak', os.path.join(browser_dir, 'resources.pak'), 'DATA'),
        ('v8_context_snapshot.bin', os.path.join(browser_dir, 'v8_context_snapshot.bin'), 'DATA'),
    ]
    
    a.datas.extend(browser_files)
else:
    print(f"警告：Chromium路径不存在 {browser_dir}")

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 添加条件判断
if sys.platform == 'win32':
    icon = 'icon.ico'
else:
    icon = 'icon.icns'

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='抖音评论助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    info_plist='Info.plist',
) 