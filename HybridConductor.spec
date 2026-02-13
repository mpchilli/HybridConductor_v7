# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['start_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('backend/static', 'backend/static'), ('backend/dashboard/templates', 'backend/dashboard/templates')],
    hiddenimports=['backend', 'backend.dashboard', 'backend.dashboard.app'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HybridConductor',
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
)
