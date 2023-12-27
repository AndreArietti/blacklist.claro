@echo off

rem Atualizar as bibliotecas Python
echo Atualizando as bibliotecas Python...
python -m pip install --upgrade pip
pip install --upgrade selenium
pip install --upgrade selenium-wire
pip install --upgrade pyautogui
pip install --upgrade psutil
echo Bibliotecas Python atualizadas com sucesso.

rem Verificar a versão do Google Chrome
echo Verificando a versão do Google Chrome...
python - << EOF
import re
import subprocess
import psutil

def get_chrome_version():
    processes = [proc for proc in psutil.process_iter(['name', 'exe']) if 'chrome' in proc.info['name'].lower()]
    for proc in processes:
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', proc.info['exe'])
        if match:
            return match.group(1)
    return None

chrome_version = get_chrome_version()
if chrome_version:
    print("Versão atual do Google Chrome:", chrome_version)
else:
    print("Google Chrome não encontrado.")
EOF

rem Converter a versão do navegador para o formato do ChromeDriver
set "major_version=%chrome_version:~0,2%"
echo Versão principal do Chrome: %major_version%

rem Fazer o download do ChromeDriver correspondente
echo Fazendo o download do ChromeDriver correspondente à versão %chrome_version%...
curl -o chromedriver.zip https://chromedriver.storage.googleapis.com/%major_version%/chromedriver_win32.zip
echo ChromeDriver baixado com sucesso.

rem Descompactar o arquivo ZIP do ChromeDriver
echo Descompactando o ChromeDriver...
tar -xf chromedriver.zip
echo ChromeDriver descompactado com sucesso.

rem Substituir o ChromeDriver antigo pelo novo
echo Substituindo o ChromeDriver antigo pelo novo...
move chromedriver.exe .\blacklist_claro
echo ChromeDriver atualizado com sucesso.

rem Excluir o arquivo ZIP
echo Excluindo o arquivo ZIP...
del chromedriver.zip
echo Arquivo ZIP excluído com sucesso.

echo Script concluído.
pause
