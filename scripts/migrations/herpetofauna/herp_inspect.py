import pandas as pd

p = r"G:\Meu Drive\Opyta\Clientes\Clientes\Clientes\Itatiaia\Guanhães Energia\Campanhas de campo\28_campanha-Abril_26\Herpetofauna\Planilha\1.ITA-GUA-Dados_brutos-Herpetofauna-Campanha_28_260516_CORRIGIDA_MIGRACAO.xlsx"
spp = pd.read_excel(p, 'Cadastro_Especies')
esf = pd.read_excel(p, 'Metadados_Esforco')
res = pd.read_excel(p, 'Resultados_Herpetofauna')
print('SPP cols:', list(spp.columns))
print('ESF cols:', list(esf.columns))
print('RES cols:', list(res.columns))
print()
print('SPP sample:')
print(spp.head(2).to_string())
print()
print('ESF sample:')
print(esf.head(2).to_string())
print()
print('RES sample:')
print(res.head(2).to_string())
