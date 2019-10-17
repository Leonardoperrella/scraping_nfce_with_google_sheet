from __future__ import print_function
import os.path
import pickle
import re
from pprint import pprint
from bs4 import BeautifulSoup
from decouple import config
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

SCOPES = [config('SCOPES')]
SPREADSHEET_ID = config('SPREADSHEET_ID')
HEADER_ROW = 'Sheet1!A2:L'
BODY_ROW = 'Sheet1!A2:A'
COLUMNS = 'COLUMNS'
UF = config('UF')


def le_chaves():
    with open('chaves.txt', 'r+') as f:
        dic = {}
        list_chaves = f.read().split()
        for chave in list_chaves:
            key = re.findall(r'p=(\w{44})', chave)
            if key:
                dic[key[0]] = chave
            else:    
                dic[chave] = 'http://www4.fazenda.'+UF+f'.gov.br/consultaNFCe/QRCode?p={chave}|1|1|1|1'

        f.truncate(0)
        return dic


def filtra_chave_nao_lidas(dic_chaves):
    
    novo_dic_chaves = {}

    sheet = google_connect()

    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        majorDimension=COLUMNS,
        range=BODY_ROW).execute()
    
    chaves_lidas = result.get('values', [])

    if not chaves_lidas:
        return dic_chaves

    chaves_lidas = list(dict.fromkeys(chaves_lidas[0]))

    for chv in dic_chaves:
        if chv not in chaves_lidas:
            novo_dic_chaves[chv] = dic_chaves[chv]

    return novo_dic_chaves
           

def carrega_dados(soup):
    l = []
    list_ = []
    total_descontos = 0
    
    table = soup.find(name='table')

    cnpj = soup.select('div.text')[0].text
    cnpj = re.sub('CNPJ:|\s+|\.+|-|\/', '', cnpj)

    nome_estabelecimento = soup.find(name='div', attrs={'id':'u20'}).text

    if soup.find_all(name='div', attrs={'id':'linhaTotal'})[2].label.text == 'Descontos R$:':
        total_descontos = soup.find_all(name='div', attrs={'id':'linhaTotal'})[2].span.text

    found_cpf = False
    list_li = soup.find_all('li')
    for content in list_li:
        s = content.text
        s = re.sub('\s', '', s)
        if re.match(r'CPF:\d{3}\.\d{3}\.\d{3}\-\d{2}', s):
            cpf = re.sub('CPF:|\s|\.+|-', '', s)
            found_cpf = True
            break

    if not found_cpf:
        cpf = 'Consumidor não identificado'

    chave = soup.find(name='span', attrs={'class':'chave'}).text
    chave = chave.replace(' ', '')

    data_emissao = soup.find(name='div', attrs={'id':'infos'}).text
    data_emissao = re.sub('\s+', '', data_emissao)
    data_emissao = re.search(r'\d{2}(\/)\d{2}(\/)\d{4}', data_emissao)[0]
    
    for n in range(0, len(table.select('tr'))):

        #codigo do produto
        s = table.select('tr td span.RCod')[n].text
        s = re.sub('\s+', '', s)
        cod_prod = ''.join(re.findall(r'\d+', s))

        # nome_tem
        nomeItem = table.select('tr td span.txtTit')[n].text

        #val_unit
        s = table.select('tr td span.RvlUnit')[n].text
        s = re.sub('\s+', '', s)
        valUnit = ''.join(re.findall(r'\d*,?\d+', s))

        #quantidade
        s = table.select('tr td span.Rqtd')[n].text
        quantidade = ''.join(re.findall(r'\d*,?\d+', s))

        #unidade
        s = table.select('tr td span.RUN')[n].text
        unidade = s[-2:]

        #total_item
        totalItem = table.select('tr td span.valor')[n].text

        l = [
            chave,
            cnpj,
            nome_estabelecimento,
            data_emissao,
            cod_prod,
            nomeItem,
            valUnit,
            quantidade,
            unidade,
            totalItem,
            total_descontos,
            cpf,
        ]

        list_.append(l)

    return list_    


def exporta_sheet(list_):

    sheet = google_connect()

    value_input_option = 'USER_ENTERED'
    insert_data_option = 'OVERWRITE'

    value_range_body = {
        "values": list_
    }

    req = sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range=HEADER_ROW, 
        valueInputOption=value_input_option, 
        insertDataOption=insert_data_option, 
        body=value_range_body)

    resp = req.execute()

    return(resp)


def google_connect(creds=None):
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
    
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)

    return service.spreadsheets()


def main():
    
    keys = filtra_chave_nao_lidas(le_chaves())

    if not keys:
        print('todas as chaves ja foram exportadas.')
        return None
    
    for key in keys:
        
        print('buscando dados...')

        # options = webdriver.ChromeOptions();
        # options.add_argument('headless');
        # driver = webdriver.Firefox(options=options)

        options = Options()
        options.headless = True
        driver = webdriver.Firefox(options=options)
        url = keys[key]
        driver.get(url)
        timeout = 5
        trying = 5
        lwhile = True
        while lwhile:
            try:
                element_present = EC.presence_of_element_located((By.ID, 'tabResult'))
                WebDriverWait(driver, timeout).until(element_present)
                print('Pagina carregada com sucesso')
                break
            except TimeoutException:
                print("Timed out, tentando novamente")
                trying -= 1
                if trying == 0:
                    print("Numero de tentativas esgotado")
                    print(f"Dados da chave: {key} não exportados")
                    lwhile = False

        if not lwhile:
            driver.quit()
            return None

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        resp = exporta_sheet(carrega_dados(soup))

        if 'updatedCells' not in resp['updates']:
            print(f"Dados não exportados, chave {key}")
            pprint(resp)
            return None

        pprint(resp)
        print(f"Dados exportados com sucesso! {key} \o/")

    print(f'https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit')


if __name__ == '__main__':
    main()
