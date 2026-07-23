@echo off
REM Bygger en fristaende .exe. Dubbelklicka denna fil i Windows,
REM eller kor den i cmd:  build.bat
cd /d "%~dp0"

echo === Installerar byggverktyg (PyInstaller) ===
pip install -r requirements.txt

echo === Skapar app-ikon ===
python make_icon.py

echo === Bygger .exe ===
if exist app.ico (
    pyinstaller --noconfirm --windowed --onefile --name "SpotifyLyricsOverlay" --icon app.ico main.py
) else (
    pyinstaller --noconfirm --windowed --onefile --name "SpotifyLyricsOverlay" main.py
)

echo.
echo === Klart! Din app finns har: ===
echo    dist\SpotifyLyricsOverlay.exe
echo.
pause
