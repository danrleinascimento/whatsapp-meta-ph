from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

ROOT = Path.cwd()


a = Analysis(
    ['app/cli.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[
        (str(ROOT / 'sql'), 'sql'),
        (str(ROOT / 'web' / 'dist'), 'web/dist'),
    ],
    hiddenimports=[
        *collect_submodules('app'),
        'uvicorn.logging',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.lifespan.on',
        'psycopg2',
        'psycopg2.extras',
        'servicemanager',
        'win32event',
        'win32service',
        'win32serviceutil',
        'win32timezone',
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
    name='whatsph',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=str(ROOT / 'ph.ico'),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
