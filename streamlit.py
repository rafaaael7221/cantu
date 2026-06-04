import streamlit as st
import pandas as pd
import io
# Importa a função do arquivo main.py
from main import processar_validacao_cnpj

# Configuração da página web
st.set_page_config(page_title="Validador CNPJ - Essential", layout="centered")
st.title("Validador de CNPJ - Apenas Revenda")
st.markdown("Arraste sua planilha do Hybris abaixo para analisar os CNAEs e puxar os endereços da Receita.")

# Componente de Drag and Drop
arquivo_enviado = st.file_uploader("Selecione a planilha Excel (.xlsx)", type=["xlsx"])

if arquivo_enviado is not None:
    try:
        df_origem = pd.read_excel(arquivo_enviado)
        st.success(f"Planilha carregada! {len(df_origem)} registros encontrados.")
        
        if st.button("Iniciar Validação"):
            # Containers para exibição dinâmica
            status_texto = st.empty()
            log_container = st.container()
            
            # Função interna para lidar com os logs na tela enquanto o loop roda no main.py
            def mostrar_log_na_tela(pedido, cnpj, tipo_status, detalhe, endereco=None):
                status_texto.text(f"Processando Pedido: {pedido} | CNPJ: {cnpj}")
                
                with log_container:
                    if tipo_status == "erro_cnpj":
                        st.warning(f"⚠️ Pedido {pedido}: Linha sem CNPJ preenchido. Pulando...")
                    elif tipo_status == "erro_api":
                        st.error(f"❌ Pedido {pedido}: Erro na BrasilAPI (Status {detalhe})")
                    elif tipo_status == "erro_geral":
                        st.error(f"❌ Erro crítico no pedido {pedido}: {detalhe}")
                    else:
                        st.markdown(f"### 📦 Pedido: {pedido} | CNPJ: {cnpj}")
                        if tipo_status == "revenda":
                            st.error(f"🚨 CLASSIFICAÇÃO: CNPJ REVENDA ({detalhe})")
                        elif tipo_status == "regular":
                            st.success("📋 CLASSIFICAÇÃO: CNPJ Comum (Não é revenda)")
                        
                        # Mostra o endereço da receita coletado
                        if endereco:
                            st.text(f"• Logradouro:  '{endereco['logradouro']}'")
                            st.text(f"• Número:      '{endereco['numero']}'" + (f" | Complemento: '{endereco['complemento']}'" if endereco['complemento'] else ""))
                            st.text(f"• Cidade/UF:   '{endereco['cidade_uf']}'")
                            st.text(f"• CEP:         '{endereco['cep']}'")
                        st.markdown("---")

            # Executa a lógica de negócio do main.py passando a função de log
            dados_validados = processar_validacao_cnpj(df_origem, mostrar_log_na_tela)
            
            status_texto.success("✅ Processamento da Versão Essential Concluído!")
            
            # Geração do arquivo para download
            if dados_validados:
                df_resultado = pd.DataFrame(dados_validados)
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_resultado.to_excel(writer, index=False, sheet_name='Resultado')
                
                st.markdown("### Seu resultado está pronto!")
                st.download_button(
                    label="📥 Baixar Planilha de Resultados - Essential",
                    data=buffer.getvalue(),
                    file_name="resultado_essential.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
    except Exception as e:
        st.error(f"Erro ao ler ou processar arquivo: {e}")
