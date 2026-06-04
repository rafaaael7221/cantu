# Backoffice: Validador ESSENTIAL 1.0

Utilizada apenas para rastrear CNPJs de revenda.

O que ele faz:
1. Recebe a planilha de pedidos extraída do sistema Hybris.
2. Consulta a base de dados da Receita Federal pela Brasil API.
3. Classifica e escreve na planilha os CNPJs irregulares.
4. Exibe na tela do navegador se o CNPJ é irregular e também o endereço cadastrado na receita.
