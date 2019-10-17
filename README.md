# scraping_nfce_with_google_sheet

1 - Activate your virtualenv.

2 - run: pip install -r requirements.txt

3 - Create a new google sheet.

4 - Go to File -> SpreedSheet Settings and change to country Brazil.

In the first row (A1:L1), complete de head with. (You can change de names if you want.)
chave,	cnpj,	nome_estab,	data_emissao,	cod_prod,	nome_item,	val_unit,	quantidade,	unidade,	total_item,	total_desconto,	cpf

5 - With the python-decouple installed, create a file setting.ini with the follws comands below.

```
[settings]
SCOPES=<google sheets http>
SPREADSHEET_ID=<sheet_Id>
UF=<state acronym>
```

5- copy the qrcode and/or keys in chaves.txt, one below each other.

6- run: scraping_google_sheet_nfce.py

