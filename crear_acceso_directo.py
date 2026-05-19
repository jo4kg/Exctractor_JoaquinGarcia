"""
Crea un acceso directo en el Escritorio con el ícono del logo.
Correr una sola vez después de instalar.
"""

import os
import sys
from pathlib import Path

def convertir_png_a_ico(png_path, ico_path):
    try:
        from PIL import Image
        img = Image.open(png_path)
        img = img.resize((256, 256), Image.LANCZOS)
        img.save(ico_path, format="ICO", sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])
        return True
    except Exception as e:
        print(f"No se pudo convertir el logo: {e}")
        return False

def crear_acceso_directo():
    try:
        import winshell
        from win32com.client import Dispatch
    except ImportError:
        # Instalar winshell si no está
        os.system(f"{sys.executable} -m pip install winshell pywin32 --quiet")
        try:
            import winshell
            from win32com.client import Dispatch
        except Exception as e:
            print(f"Error instalando dependencias: {e}")
            return False

    app_dir     = Path(os.path.dirname(os.path.abspath(__file__)))
    bat_path    = app_dir / "Iniciar.vbs"
    logo_png    = app_dir / "logo.png"
    logo_ico    = app_dir / "logo.ico"
    lnk_path    = app_dir / "Extractor Trades.lnk"

    # Convertir logo.png a .ico
    if logo_png.exists() and not logo_ico.exists():
        convertir_png_a_ico(str(logo_png), str(logo_ico))

    # Crear acceso directo
    shell   = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(lnk_path))
    shortcut.Targetpath      = str(bat_path)
    shortcut.WorkingDirectory = str(app_dir)
    shortcut.Description     = "Extractor de Trades - PMP"
    if logo_ico.exists():
        shortcut.IconLocation = str(logo_ico)
    shortcut.save()

    print(f"✅ Acceso directo creado en: {lnk_path}")
    return True

if __name__ == "__main__":
    crear_acceso_directo()
    input("\nPresioná Enter para cerrar...")