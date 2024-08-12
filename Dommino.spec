# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('lib/Phidget22.dll','lib')],
    datas=[('graphic/images/green-led-on.png','images'),\
    ('graphic/images/red-led-on.png','images'),\
    ('graphic/images/pause_icon.png','images'),\
    ('graphic/images/play_icon.png','images'),\
    ('config/app_default_settings.ini','config'),\
    ('config/CALlog.txt','config'),\
    ('config/device_id.ini','config'),\
    ('config/latest_cal.ini','config'),\
    ('lib/oceandirect/lib/OceanDirect.dll','lib/oceandirect/lib')],
    hiddenimports=[],
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
    [],
    exclude_binaries=False,
    name='Dommino',
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
    name='Dommino',
)
