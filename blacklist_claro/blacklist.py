import csv
import json
import logging
import gzip
import io
import os
import shutil
from datetime import datetime
import requests
from seleniumwire import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

class Blacklist():
    def __init__(self, entrada_file, saida_file):
        self.entrada = entrada_file
        self.saida = saida_file
        self.numeros = []
        self.cookies = {}
        self.access_token = None
        self.session = requests.Session()

        self.logger = logging.getLogger(__name__)
        logging.basicConfig(filename='error.log', level=logging.ERROR)

        opts = Options()
        opts.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36")
        self.browser = webdriver.Chrome(options=opts)

        if not os.path.exists("Blacklist_Telefones"):
            os.makedirs("Blacklist_Telefones")

        with open(self.saida, 'a', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["numero", "situacao", "data_importacao"])

        with open(self.entrada, 'r', newline='') as csvfile:
            spamreader = csv.DictReader(csvfile, delimiter=';', quotechar='|')
            sub_array = []
            for row in spamreader:
                sub_array.append(row.get('numeros'))
                if len(row.get('numeros')) == 10:
                    numero_com_nono = row.get('numeros')[0:2] + '9' + row.get('numeros')[2:]
                    sub_array.append(numero_com_nono)
                if len(sub_array) == 100:
                    self.numeros.append(",".join(sub_array))
                    sub_array = []
            if len(sub_array) > 0:
                self.numeros.append(",".join(sub_array))

    def iniciar(self):
        try:
            self.browser.get("https://vendas.conexaoclarobrasil.com.br/venda/acompanhamento")
            WebDriverWait(self.browser, 300).until(EC.visibility_of_element_located((By.XPATH, '//*[@id="xdrawer-app-bar"]/div/div/div[2]/button[3]')))
            self.logger.info("Login efetuado com sucesso")

            all_cookies = self.browser.get_cookies()
            for objeto in all_cookies:
                self.cookies[objeto.get('name')] = objeto.get('value')

            self.session.cookies = requests.utils.cookiejar_from_dict(self.cookies)

            for request in self.browser.requests:
                if request.response:
                    if request.url == 'https://autenticacao-api.conexaoclarobrasil.com.br/oauth/token':
                        dados_login = request.response.body
                        gzip_stream = io.BytesIO(dados_login)
                        gzip_file = gzip.GzipFile(fileobj=gzip_stream)
                        dados_login_decoded = gzip_file.read()
                        dados_login_obj = json.loads(dados_login_decoded.decode('utf-8'))
                        self.access_token = dados_login_obj.get('access_token')

            if self.access_token:
                self.logger.info("Token coletado com sucesso: %s", self.access_token)
                self.browser.quit()
                with open(self.saida, 'a', newline='') as f:
                    writer = csv.writer(f, delimiter=';')
                    self.consultar(writer)
            else:
                self.logger.error("Erro ao coletar token de acesso")

        except Exception as e:
            self.logger.exception("Erro ao efetuar login.")
            raise e

    def consultar(self, writer):
        try:
            headers = {
                'Connection': 'keep-alive',
                'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
                'Accept': 'application/json, text/plain, */*',
                'Authorization': 'Bearer ' + self.access_token,
                'X-Usuario-Canal': 'AGENTE_AUTORIZADO',
                'sec-ch-ua-mobile': '?0',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
                'Origin': 'https://app.conexaoclarobrasil.com.br',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'Accept-Language': 'pt-BR,pt;q=0.9',
            }
            for numeros in self.numeros:
                params = (
                    ('page', '0'),
                    ('size', '100'),
                    ('orderBy', 'numero'),
                    ('orderDirection', 'asc'),
                    ('telefones', numeros),
                )
                response = requests.get('https://autenticacao-api.conexaoclarobrasil.com.br/call/api/v2/lei-nao-perturbe',
                                        headers=headers, params=params)
                if response.status_code == 200:
                    self.salvar_resposta(response.text, writer)
                else:
                    self.logger.error("Erro ao fazer a consulta. Status code: %s", response.status_code)
                    response.raise_for_status()

            self.logger.info("Parabéns! A sua importação foi um sucesso. O arquivo foi salvo na pasta 'Blacklist_Telefones'.")

        except Exception as e:
            self.logger.exception("Houve um erro durante a consulta.")
            raise e

    def salvar_resposta(self, resposta, writer):
        try:
            resposta_json = json.loads(resposta)
            numerosResponse = resposta_json.get('numerosResponse')
            for numero in numerosResponse.get("content"):
                situacao = numero.get('situacao')
                if situacao:
                    writer.writerow([numero.get("numero"), situacao.get("codigo"), numero.get("dataImportacao")])

        except Exception as e:
            self.logger.exception("Erro ao salvar dados no arquivo")
            raise e

def main():
    entrada_file = 'entrada.csv'
    saida_file = f'Blacklist_Telefones/saida_{datetime.today().strftime("%d-%m-%Y_%H_%M_%S")}.csv'
    instancia = Blacklist(entrada_file, saida_file)
    try:
        instancia.iniciar()
    except Exception as e:
        print("Houve um erro no script. Consulte o arquivo error.log para mais detalhes.")
        logging.exception("Error occurred during script execution: %s", str(e))

if __name__ == '__main__':
    main()
