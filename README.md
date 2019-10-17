# scraping_nfce_with_google_sheet

1 - Create a new google sheet.
In the first row complete de head with. (You can change de names if you want.)
chave,	cnpj,	nome_estab,	data_emissao,	cod_prod,	nome_item,	val_unit,	quantidade,	unidade,	total_item,	total_desconto,	cpf


2 - With the python-decouple installed, create a file setting.ini with the follws comands below.

[settings]
SCOPES=<'google sheets http'>
SPREADSHEET_ID=<'sheet_Id'>
UF=<'state acronym'>

3- Activate your virtualenv.

4- run: pip install -r requirements.txt

5- copy the qrcode or keys in chaves.txt, one below each other.

6- run: scraping_google_sheet_nfce.py

