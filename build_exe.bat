@echo off
echo Instalando PyInstaller...
pip install pyinstaller

echo.
echo Construyendo el ejecutable...
pyinstaller --onefile --windowed --name "ExtractorTrades" extractor_ui.py

echo.
echo Listo! El .exe está en la carpeta dist\
pause
