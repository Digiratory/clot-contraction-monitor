# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['./src/clot_contraction_monitor/app/main.py'],
    pathex=[],
    binaries=[],
    datas=[('./src/clot_contraction_monitor/assets/*', './clot_contraction_monitor/assets/')],
    hiddenimports=['matplotlib.backends.backend_pdf', 'matplotlib.backends.backend_pgf', 'matplotlib.backends.backend_ps', 'matplotlib.backends.backend_svg'],
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
    name='clot-contraction-monitor.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=['bn_modeller\\resources\\icon.ico'],
)
