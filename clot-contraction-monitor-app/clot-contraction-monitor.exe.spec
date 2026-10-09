# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

# Collect onnxruntime data files and dynamic libraries
onnxruntime_datas = collect_data_files('onnxruntime')
onnxruntime_binaries = collect_dynamic_libs('onnxruntime')

a = Analysis(
    ['./src/clot_contraction_monitor/app/main.py'],
    pathex=[],
    binaries=onnxruntime_binaries,
    datas=onnxruntime_datas + [('./src/clot_contraction_monitor/assets/*', './clot_contraction_monitor/assets/')],
    hiddenimports=['matplotlib.backends.backend_pdf',
                    'matplotlib.backends.backend_pgf',
                    'matplotlib.backends.backend_ps',
                    'matplotlib.backends.backend_svg',
                    'onnxruntime',
                    'onnxruntime.capi',
                    'onnxruntime.capi.onnxruntime_pybind11_state',
                    'onnxruntime.capi.onnxruntime_validation',
                    'onnxruntime.capi._ld_preload',
                    ],
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
