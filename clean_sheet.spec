# -*- mode: python ; coding: utf-8 -*-
"""
Clean Sheet - PyInstaller Specification File
Builds a standalone Windows executable with all dependencies
"""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

block_cipher = None

# Collect all hidden imports
hiddenimports = [
    # Database
    'pymongo',
    'pymongo.collection',
    'pymongo.database',
    'pymongo.mongo_client',
    'bson',
    'bson.objectid',
    'dns',
    'dns.resolver',

    # AI Assistant
    'anthropic',
    'anthropic.resources',
    'anthropic.types',

    # UI Components
    'tksheet',
    'tkinter',
    'tkinter.ttk',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.scrolledtext',

    # Security
    'bcrypt',
    'email_validator',

    # Configuration
    'dotenv',
    'configparser',

    # Data Processing
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.cell',
    'openpyxl.workbook',
    'openpyxl.worksheet',
    'pandas',
    'pandas._libs',
    'pandas._libs.tslibs',

    # Auto-update
    'requests',
    'packaging',
    'packaging.version',

    # Standard library
    'threading',
    'hashlib',
    'datetime',
    'json',
    'logging',
    'pathlib',
    'subprocess',
]

# Collect data files
datas = [
    ('presets/system', 'presets/system'),  # System presets
    ('clean_sheet_icon.ico', '.'),  # Application icon (will be created by create_icon.py)
]

# Try to collect pymongo certificates (may not exist, that's ok)
try:
    datas += collect_data_files('pymongo')
except:
    pass

# Try to collect certifi certificates for HTTPS
try:
    datas += collect_data_files('certifi')
except:
    pass

a = Analysis(
    ['main_gui_v2_office365.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'scipy',
        'numpy.tests',
        'pytest',
        'unittest',
        'test',
        'tests',
        'setuptools',
        '_pytest',
        'py',
        'pluggy',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CleanSheet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX (reduces file size)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI application)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='clean_sheet_icon.ico',  # Application icon
)
