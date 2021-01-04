# -*- mode: python -*-
import os
import sys
import pyupdater


def collect_submodules(name):
    result = [name]
    path = os.path.join(*name.split("."))
    for sub_dir in os.listdir(path):
        if os.path.exists(os.path.join(path, sub_dir, "__init__.py")):
            sub_name = name + "." + sub_dir
            result += collect_submodules(sub_name)
        elif sub_dir[-3:] == ".py" and sub_dir != "__init__.py":
            result.append(name + "." + sub_dir[:-3])
    return result


def exclude_init_files(path):
    result = []
    has_file = False
    for sub_dir in os.listdir(path):
        if sub_dir in ["__init__.py", "__pycache__"]:
            continue

        sub_path = os.path.join(path, sub_dir)
        if os.path.isdir(sub_path):
            result += exclude_init_files(sub_path)
        elif not has_file and os.path.isfile(sub_path):
            result.append((sub_path, path))
            has_file = True

    return result


block_cipher = None

a = Analysis([os.path.join(os.getcwd(), "main_gui.py")],
             pathex=[os.getcwd()],
             binaries=[],
             datas=[
                 ("templates", "templates"),
                 ("version.txt", "."),
                 *exclude_init_files("sites"),
                 (os.path.join("gui", "assets"), os.path.join("gui", "assets")),
                 (os.path.join("core", "assets"), os.path.join("core", "assets")),
             ],
             hiddenimports=["encodings.idna"] + collect_submodules("sites"),
             hookspath=[os.path.join(pyupdater.__path__[0], "hooks")],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)

exe = EXE(pyz,
      a.scripts,
      [],
      exclude_binaries=True,
      name='mac',
      debug=False,
      bootloader_ignore_signals=False,
      strip=False,
      upx=True,
      console=False )
coll = COLLECT(exe,
           a.binaries,
           a.zipfiles,
           a.datas,
           strip=False,
           upx=True,
           upx_exclude=[],
           name='mac')
app = BUNDLE(coll,
         name='mac.app',
         icon=os.path.join("gui", "assets", "logo", "logo.icns"),
         bundle_identifier=None,
         info_plist={
                 'NSHighResolutionCapable': 'True'
             })
