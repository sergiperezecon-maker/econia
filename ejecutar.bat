@echo off
echo Instalando dependencias...
pip install -r requirements.txt --quiet
echo.
echo Abriendo EconIA...
python -m streamlit run app.py
pause
