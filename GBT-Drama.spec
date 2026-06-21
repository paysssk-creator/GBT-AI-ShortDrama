# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\ADMIN\\GBT-AI-ShortDrama\\desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\ADMIN\\GBT-AI-ShortDrama\\config\\characters.json', 'config')],
    hiddenimports=['gradio', 'edge_tts', 'pipeline'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'matplotlib'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GBT-Drama',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GBT-Drama',
)
