@echo off
title Digikala Panel Server
echo Starting the application server...
echo.
echo Please wait, a new tab will open in your browser.
echo To stop the application, simply close this window.
echo.

streamlit run main_app.py

echo.
echo Server has been stopped.
pause