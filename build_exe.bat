@echo off
REM Builds a standalone offline executable (no Python installation required
REM to run it afterward) on Windows.
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --name docx-formatter cli.py --distpath dist --workpath build --specpath .
echo.
echo Build complete: dist\docx-formatter.exe
echo Test it with: dist\docx-formatter.exe samples\sample_unformatted.docx output.docx
pause
