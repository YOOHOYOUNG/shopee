# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(sys.getrecursionlimit() * 5)

block_cipher = None

a = Analysis(
    ['shopee_calculator_v1_0.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'importlib_metadata',
        'importlib_metadata._compat',
        'streamlit',
        'altair',
        'numpy',
        'pandas',
        'requests',
        'validators',
        'pyarrow',
        'pydeck',
        'toml',
        'blinker',
        'base58',
        'tzlocal',
        'jinja2',
        'watchdog',
        'pygments',
        'protoc',
        'protobuf',
        'pympler',
        'cachetools',
        'click',
        'packaging',
        'toolz',
        'tornado',
        'pillow',
        'dateutil',
        'markdown',
        'urllib3',
        'idna',
        'chardet',
        'certifi',
        'attrs',
        'jsonschema',
        'pyparsing',
        'pyarrow._generated_version',
        'pyarrow._generated_version',
        # 필요한 다른 모듈이 있다면 여기에 추가하세요.
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['sphinx', 'sphinxcontrib'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='shopee_calculator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='shopee_calculator'
)