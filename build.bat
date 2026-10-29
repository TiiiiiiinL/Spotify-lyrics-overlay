@echo off
REM Builds a standalone .exe. Double-click this file in Windows,
REM or run it in cmd:  build.bat
cd /d "%~dp0"

echo === Installing build tools (PyInstaller) ===
pip install -r requirements.txt

echo === Creating app icon ===
python make_icon.py

echo === Building .exe ===
if exist app.ico (
    pyinstaller --noconfirm --windowed --onefile --name "SpotifyLyricsOverlay" --icon app.ico main.py
) else (
    pyinstaller --noconfirm --windowed --onefile --name "SpotifyLyricsOverlay" main.py
)

echo.
echo === Done! Your app is here: ===
echo    dist\SpotifyLyricsOverlay.exe
echo.
pause
