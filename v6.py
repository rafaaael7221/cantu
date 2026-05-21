import time
import pandas as pd
import requests
import streamlit as st
import io

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

# --- CONFIGURAÇÃO DA TELA DO STREAMLIT ---
st.set_page_config(page_title="Validador CNPJ", layout="centered")
st.title("Validador de CNPJ - Revenda")
st.markdown("Envie a sua planilha de pedidos abaixo para verificar quais CNPJs são revenda.")

# Componente para fazer o upload do arquivo
arquivo_enviado = st.file_uploader("Arraste seu arquivo Excel aqui (.xlsx)", type=["xlsx"])

if arquivo_enviado is not None:
    try:
        df_origem = pd.read_excel(arquivo_enviado)
        st.success(f"Planilha carregada! {len(df_origem)} registros encontrados.")
        
        # Botão para disparar o processo
        if st.button("Iniciar Validação"):
            novas_linhas = []
            
            # Containers para mostrar o progresso na tela
            progresso = st.progress(0)
            status_texto = st.empty()
            log_container = st.container()
            
            for index, linha in df_origem.iterrows():
                # Atualiza barra de progresso
                progresso.progress((index + 1) / len(df_origem))
                
                pedido = linha.get('Pedido', 'N/A')
                cnpj_planilha = limpar_numeros(linha.get('CNPJ', ''))
                
                status_texto.text(f"Processando Pedido: {pedido} | CNPJ: {cnpj_planilha}")
                
                if not cnpj_planilha:
                    continue
                    
                url_api = f"https://brasilapi.com.br/api/cnpj/v1/{cnpj_planilha}"
                
                try:
                    resposta = requests.get(url_api)
                    time.sleep(1) # Respeita o limite da API
                    
                    if resposta.status_code != 200:
                        continue
                        
                    dados_receita = resposta.json()
                    
                    # Validação de Revenda
                    cnae_principal = limpar_numeros(dados_receita.get('cnae_fiscal', ''))
                    cnaes_empresa = [cnae_principal]
                    for cnae_sec in dados_receita.get('cnaes_secundarios', []):
                        cnaes_empresa.append(limpar_numeros(cnae_sec.get('codigo', '')))
                    
                    cnae_revenda_identificado = next((c for c in cnaes_empresa if c in CNAES_REVENDA), None)
                    
                    acao_back, pendencia, resolucao = "", "", ""
                    
                    if cnae_revenda_identificado:
                        acao_back = "Cancelar Pedido - CNPJ revenda"
                        pendencia = "CNPJ Revenda"
                        resolucao = "Abrir ticket em massa"
                        with log_container:
                            st.error(f"🚨 Pedido {pedido}: CNPJ REVENDA ({cnae_revenda_identificado})")
                    else:
                        with log_container:
                            st.success(f"📋 Pedido {pedido}: CNPJ Comum")
                            
                    novas_linhas.append({
                        "Pedido": pedido, 
                        "CNPJ": cnpj_planilha, 
                        "Ação Back": acao_back,
                        "Pendência": pendencia, 
                        "Resolução": resolucao
                    })
                    
                except Exception:
                    pass
            
            status_texto.text("✅ Processamento concluído!")
            
            # --- GERAR O BOTÃO DE DOWNLOAD ---
            if novas_linhas:
                df_resultado = pd.DataFrame(novas_linhas)
                
                # Cria o arquivo Excel na memória RAM do servidor
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Resultado')
                
                st.markdown("### Seu resultado está pronto!")
                st.download_button(
                    label="📥 Baixar Planilha de Resultados",
                    data=buffer.getvalue(),
                    file_name="resultado_backoffice.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
    except Exception as e:
        st.error(f"Erro ao ler arquivo: {e}")