import time
import pandas as pd
import requests

CNAES_REVENDA = [
    "4520001", "4520006", "4520007", "4530701", "4530702", 
    "4530703", "4530704", "4530705", "4530706", "4541202", 
    "4541206", "4541207", "4542101"
]

def limpar_texto(texto):
    if pd.isna(texto) or not texto:
        return ""
    return str(texto).strip().upper()

def limpar_numeros(texto):
    if pd.isna(texto) or not texto:
        return ""
    return "".join(filter(str.isdigit, str(texto)))

def processar_validacao_cnpj(df_origem, log_callback):
    """
    Processa a planilha de origem linha por linha.
    O parâmetro log_callback é uma função enviada pela interface para mostrar os resultados na tela.
    """
    novas_linhas = []
    
    for index, linha in df_origem.iterrows():
        pedido = linha.get('Pedido', 'N/A')
        cnpj_planilha = limpar_numeros(linha.get('CNPJ', ''))
        
        if not cnpj_planilha:
            log_callback(pedido, cnpj_planilha, "erro_cnpj", None)
            continue
            
        url_api = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_planilha}"
        
        try:
            resposta = requests.get(url_api)
            time.sleep(3) # Rate limit da BrasilAPI
            
            if resposta.status_code != 200:
                log_callback(pedido, cnpj_planilha, "erro_api", resposta.status_code)
                continue
                
            dados_receita = resposta.json()
            
            # Extração de CNAEs e validação de revenda
            cnae_principal = limpar_numeros(dados_receita.get('cnae_fiscal', ''))
            cnaes_empresa = [cnae_principal]
            for cnae_sec in dados_receita.get('cnaes_secundarios', []):
                cnaes_empresa.append(limpar_numeros(cnae_sec.get('codigo', '')))
            
            cnae_revenda_identificado = next((c for c in cnaes_empresa if c in CNAES_REVENDA), None)
            
            # Captura isolada do endereço apenas para exibição visual
            tipo_via = limpar_texto(dados_receita.get('tipo_logradouro', ''))
            nome_via = limpar_texto(dados_receita.get('logradouro', ''))
            logradouro_rec = f"{tipo_via} {nome_via}".strip() if tipo_via and tipo_via not in nome_via else nome_via
            
            numero_rec = limpar_texto(dados_receita.get('numero', ''))
            complemento_rec = limpar_texto(dados_receita.get('complemento', ''))
            cidade_rec = limpar_texto(dados_receita.get('municipio', ''))
            estado_rec = limpar_texto(dados_receita.get('uf', ''))
            cep_rec = limpar_numeros(dados_receita.get('cep', ''))
            
            endereco_formatado = {
                "logradouro": logradouro_rec,
                "numero": numero_rec,
                "complemento": complemento_rec,
                "cidade_uf": f"{cidade_rec}/{estado_rec}",
                "cep": cep_rec
            }
            
            # Aplicação das Regras de Negócio do Backoffice
            acao_back, pendencia, resolucao = "", "", ""
            
            if cnae_revenda_identificado:
                acao_back = "Cancelar Pedido - CNPJ revenda"
                pendencia = "CNPJ Revenda"
                resolucao = "Abrir ticket em massa"
                log_callback(pedido, cnpj_planilha, "revenda", cnae_revenda_identificado, endereco_formatado)
            else:
                log_callback(pedido, cnpj_planilha, "regular", None, endereco_formatado)

            novas_linhas.append({
                "Pedido": pedido, 
                "CNPJ": cnpj_planilha, 
                "Ação Back": acao_back,
                "Pendência": pendencia, 
                "Resolução": resolucao
            })

        except Exception as e:
            log_callback(pedido, cnpj_planilha, "erro_geral", str(e))

    return novas_linhas
