# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect everything streamlit needs (static files, templates, etc.)
st_datas, st_binaries, st_hiddenimports = collect_all("streamlit")
px_datas, px_binaries, px_hiddenimports = collect_all("plotly")

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=st_binaries + px_binaries,
    datas=[
        ("ganjoor_app.py", "."),   # app script bundled alongside launcher
        ("ganjoor.db",    "."),    # SQLite database
        ("fonts",              "fonts"),        # local Vazirmatn fonts
        (".streamlit/config.toml", ".streamlit"), # disable telemetry
        *st_datas,
        *px_datas,
    ],
    hiddenimports=[
        *st_hiddenimports,
        *px_hiddenimports,
        "streamlit.web.cli",
        "streamlit.runtime.scriptrunner",
        "sqlite3",
        "pandas",
        "plotly",
        "plotly.express",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pymysql", "langchain", "matplotlib", "streamlit.external.langchain", "plotly.matplotlylib"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="گنجور",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # no terminal window on launch
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="گنجور",
)
