import streamlit as st
import pandas as pd

st.set_page_config(layout="wide", page_title="Análise de Inventário")
st.title("Análise Financeira")

st.markdown("""
Esta ferramenta permite analisar o valor total do seu rancho e o impacto financeiro das trocas de itens.
Carregue suas tabelas (em formato CSV) para gerar o relatório.
""")

# ---- Carregamento de Arquivos ----
st.header("1. Carregue as tabelas aqui")

rancho_file = st.file_uploader("📦 Carregar Tabela do Rancho (CSV)", type="csv")
trocas_file = st.file_uploader("🔁 Carregar Tabela de Trocas (CSV)", type="csv")

# ---- Verificação e Processamento dos Dados ----
if rancho_file and trocas_file:
    try:
        df_rancho = pd.read_csv(rancho_file)
        df_trocas = pd.read_csv(trocas_file)

        # Validar as colunas
        rancho_cols_expected = ["Item", "Quantidade", "Valor Unitario"]
        trocas_cols_expected = ["Item Trocado", "Quantidade Trocada", "Item Recebido", "Quantidade Recebida", "Valor do Acerto"]

        if not all(col in df_rancho.columns for col in rancho_cols_expected):
            st.error(f"A Tabela do Rancho deve ter as colunas: {rancho_cols_expected}")
        elif not all(col in df_trocas.columns for col in trocas_cols_expected):
            st.error(f"A Tabela de Trocas deve ter as colunas: {trocas_cols_expected}")
        else:
            st.success("Tabelas carregadas com sucesso! Processando dados...")

            # --- Processamento de Dados ---
            df_rancho["Valor Total"] = df_rancho["Quantidade"] * df_rancho["Valor Unitario"]
            valor_original_rancho = df_rancho["Valor Total"].sum()

            df_trocas_completa = df_trocas.merge(
                df_rancho[["Item", "Valor Unitario"]],
                left_on="Item Trocado",
                right_on="Item",
                how="left"
            ).rename(columns={"Valor Unitario": "Valor Unitario_trocado"}).drop(columns="Item")

            df_trocas_completa = df_trocas_completa.merge(
                df_rancho[["Item", "Valor Unitario"]],
                left_on="Item Recebido",
                right_on="Item",
                how="left"
            ).rename(columns={"Valor Unitario": "Valor Unitario_recebido"}).drop(columns="Item")

            df_trocas_completa.fillna(0, inplace=True)

            df_trocas_completa["Valor Trocado"] = df_trocas_completa["Quantidade Trocada"] * df_trocas_completa["Valor Unitario_trocado"]
            df_trocas_completa["Valor Recebido"] = df_trocas_completa["Quantidade Recebida"] * df_trocas_completa["Valor Unitario_recebido"]
            df_trocas_completa["Ganho/Perda"] = df_trocas_completa["Valor Recebido"] - df_trocas_completa["Valor Trocado"] + df_trocas_completa["Valor do Acerto"]

            ganho_total = df_trocas_completa[df_trocas_completa["Ganho/Perda"] > 0]["Ganho/Perda"].sum()
            perda_total = abs(df_trocas_completa[df_trocas_completa["Ganho/Perda"] < 0]["Ganho/Perda"].sum())
            balanco_final = valor_original_rancho + ganho_total - perda_total
            media_ganho_perda = df_trocas_completa["Ganho/Perda"].mean()

            # Contar os itens mais trocados
            itens_trocados = pd.concat([df_trocas_completa["Item Trocado"], df_trocas_completa["Item Recebido"]])
            contagem_trocas = itens_trocados.value_counts().reset_index()
            contagem_trocas.columns = ["Item", "Número de Trocas"]

            # Contar itens de maior ganho e perda
            itens_mais_ganhos = df_trocas_completa[df_trocas_completa['Ganho/Perda'] > 0]['Item Recebido'].value_counts().nlargest(5)
            itens_mais_perdidos = df_trocas_completa[df_trocas_completa['Ganho/Perda'] < 0]['Item Trocado'].value_counts().nlargest(5)


            # ---- Exibição dos Relatórios ----
            st.header("2. Relatório de Análise")

            st.markdown("### Resumo Financeiro")
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("💰 Valor Original do Rancho", f"R$ {valor_original_rancho:,.2f}")
            with col2:
                st.metric("📈 Ganho Total com Trocas", f"R$ {ganho_total:,.2f}")
            with col3:
                st.metric("📉 Perda Total com Trocas", f"R$ {perda_total:,.2f}")
            with col4:
                st.metric("💵 Valor Final do Rancho", f"R$ {balanco_final:,.2f}")
            with col5:
                st.metric("📊 Balanço Médio por Troca", f"R$ {media_ganho_perda:,.2f}")

            st.markdown("---")

            st.subheader("Gráficos de Desempenho")
            
            # Gráfico dos Itens Mais Trocados
            st.markdown("#### Itens Mais Trocados")
            df_plot_trocas = contagem_trocas.set_index("Item")
            st.bar_chart(df_plot_trocas)

            # Gráfico de Ganhos e Perdas por Troca
            st.markdown("#### Ganho/Perda por Troca")
            df_plot_ganho_perda = df_trocas_completa.reset_index().rename(columns={'index': 'ID da Troca'})
            df_plot_ganho_perda['ID da Troca'] = df_plot_ganho_perda['ID da Troca'] + 1
            st.bar_chart(df_plot_ganho_perda[['ID da Troca', 'Ganho/Perda']].set_index('ID da Troca'))

            st.markdown("---")

            st.subheader("Detalhes e Relatórios de Itens")
            col_left, col_right = st.columns(2)
            with col_left:
                st.markdown("#### Top 5 Itens Mais Ganhos")
                st.dataframe(itens_mais_ganhos, use_container_width=True)
            with col_right:
                st.markdown("#### Top 5 Itens Mais Perdidos")
                st.dataframe(itens_mais_perdidos, use_container_width=True)

            st.markdown("---")
            st.subheader("Tabelas Detalhadas")

            with st.expander("Tabela Detalhada do Rancho"):
                st.dataframe(df_rancho, use_container_width=True)
            
            with st.expander("Tabela Detalhada de Trocas"):
                st.dataframe(df_trocas_completa[["Item Trocado", "Quantidade Trocada", "Item Recebido", "Quantidade Recebida", "Valor Trocado", "Valor Recebido", "Valor do Acerto", "Ganho/Perda"]], use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar os arquivos. Verifique se as colunas do csv estão corretas. Erro: {e}")

else:
    st.info("Por favor, carregue os dois arquivos CSV para gerar o relatório.")