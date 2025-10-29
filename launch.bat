@echo off
echo ========================================
echo    Chiller Picker Application
echo ========================================
echo.
echo Starting the web interface...
echo.
echo The application will open in your browser at:
echo    http://localhost:8501
echo.
echo If it doesn't open automatically, copy the URL above
echo and paste it into your browser.
echo.
echo Press Ctrl+C to stop the application when done.
echo.
echo ========================================
echo.

REM Try to run streamlit directly first
streamlit run app.py 2>nul
if %errorlevel% neq 0 (
    echo Streamlit not found in PATH, trying with python -m streamlit...
    python -m streamlit run app.py
)

pause
