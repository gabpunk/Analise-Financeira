import streamlit as st
import pandas as pd

# ---- Título e Introdução da Aplicação ----
st.set_page_config(layout="wide", page_title="Análise de Inventário Simples")
st.title("💰 Análise de Inventário e Balanço de Trocas")

st.markdown("""
Esta ferramenta funciona com base no **balanço de estoque**. 
1. Carregue a tabela com o estado **inicial** do seu rancho.
2. Edite a coluna **Quantidade** para refletir o estado **final** (após as trocas).
3. O relatório será gerado com base na variação do valor do seu inventário.
""")

# ---- Carregamento de Arquivos ----
st.header("1. Carregar Tabela do Rancho")

rancho_file = st.file_uploader("📦 Carregar Tabela do Rancho (CSV) - Estado Inicial", type="csv")

if rancho_file:
    try:
        df_rancho_original = pd.read_csv(rancho_file)

        # Validar as colunas
        rancho_cols_expected = ["Item", "Quantidade", "Valor Unitario"]
        if not all(col in df_rancho_original.columns for col in rancho_cols_expected):
            st.error(f"A Tabela deve ter as colunas: {rancho_cols_expected}")
            st.stop()
        
        # Garantir que as colunas numéricas sejam números na Tabela Original
        df_rancho_original["Quantidade"] = pd.to_numeric(df_rancho_original["Quantidade"], errors='coerce').fillna(0)
        df_rancho_original["Valor Unitario"] = pd.to_numeric(df_rancho_original["Valor Unitario"], errors='coerce').fillna(0)

        # --- 1.1. Edição Manual ---
        st.header("1.1. Edição e Simulação de Trocas")
        st.warning("🚨 **ATENÇÃO:** Altere a **'Quantidade'** na tabela abaixo para simular as trocas. Para **adicionar** um item, use o botão '+' no final da tabela.")

        df_rancho_final = st.data_editor(
            df_rancho_original.copy(), 
            use_container_width=True, 
            num_rows="dynamic", 
            key="editor_rancho",
            hide_index=True
        )
        
        # Garantir que as colunas numéricas são de fato números após a edição
        df_rancho_final["Quantidade"] = pd.to_numeric(df_rancho_final["Quantidade"], errors='coerce').fillna(0)
        df_rancho_final["Valor Unitario"] = pd.to_numeric(df_rancho_final["Valor Unitario"], errors='coerce').fillna(0)
        

        # --- 2. Processamento de Dados Baseado na Diferença ---
        
        # 1. Calcular o valor original total (apenas com base no CSV inicial)
        df_rancho_original["Valor Total Original"] = df_rancho_original["Quantidade"] * df_rancho_original["Valor Unitario"]
        valor_original_rancho = df_rancho_original["Valor Total Original"].sum()
        
        # 2. Preparar DataFrames para Merge
        df_inicial = df_rancho_original[["Item", "Quantidade", "Valor Unitario"]].rename(columns={"Quantidade": "Qtd_Inicial", "Valor Unitario": "Valor_Unitario_Original"})
        df_final = df_rancho_final[["Item", "Quantidade", "Valor Unitario"]].rename(columns={"Quantidade": "Qtd_Final", "Valor Unitario": "Valor_Unitario_Final"})

        # USANDO OUTER MERGE para capturar TODAS as linhas (adicionadas ou removidas)
        df_comparacao = df_inicial.merge(
            df_final,
            on="Item",
            how="outer" 
        )

        # 3. Limpeza e Consistência dos Dados
        # Valor Unitario: Prioriza o valor editado, senão usa o original, senão 0.
        df_comparacao['Valor Unitario'] = df_comparacao['Valor_Unitario_Final'].fillna(df_comparacao['Valor_Unitario_Original']).fillna(0)
        
        # Quantidades: Zera as quantidades se o item não estava presente na tabela (resultado do outer merge)
        df_comparacao["Qtd_Inicial"] = df_comparacao["Qtd_Inicial"].fillna(0)
        df_comparacao["Qtd_Final"] = df_comparacao["Qtd_Final"].fillna(0)
        
        # 4. Calcular a diferença e o impacto financeiro
        df_comparacao["Qtd_Diferenca"] = df_comparacao["Qtd_Final"] - df_comparacao["Qtd_Inicial"]
        df_comparacao["Valor_Diferenca"] = df_comparacao["Qtd_Diferenca"] * df_comparacao["Valor Unitario"]
        
        
        # 5. Calcular Ganhos e Perdas
        ganho_total = df_comparacao[df_comparacao["Valor_Diferenca"] > 0]["Valor_Diferenca"].sum()
        perda_total = abs(df_comparacao[df_comparacao["Valor_Diferenca"] < 0]["Valor_Diferenca"].sum())
        balanco_total_trocas = ganho_total - perda_total
        balanco_final = valor_original_rancho + balanco_total_trocas
        
        # 6. Métricas de Trocas
        itens_trocados = df_comparacao[df_comparacao["Qtd_Diferenca"] != 0].copy()
        itens_trocados["Tipo"] = itens_trocados["Qtd_Diferenca"].apply(lambda x: "Recebido (Ganho)" if x > 0 else "Trocado (Perda)")
        
        contagem_trocas = itens_trocados["Item"].value_counts().reset_index()
        contagem_trocas.columns = ["Item", "Número de Trocas/Variações"]


        # ---- Exibição dos Relatórios ----
        st.header("2. Relatório de Análise (Balanço de Inventário)")

        st.markdown("### Resumo Financeiro")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric(
                "💰 Valor Original do Rancho", 
                f"R$ {valor_original_rancho:,.2f}",
                help="O valor total do rancho antes de qualquer troca, baseado no arquivo CSV inicial."
            )
        with col2:
            st.metric(
                "📈 Valor Ganhado em Itens", 
                f"R$ {ganho_total:,.2f}",
                help="Valor financeiro total dos itens que foram ADICIONADOS ao rancho (Quantidade Final > Inicial)."
            )
        with col3:
            st.metric(
                "📉 Valor Perdido em Itens", 
                f"R$ {perda_total:,.2f}",
                help="Valor financeiro total dos itens que foram REMOVIDOS do rancho (Quantidade Final < Inicial)."
            )
        with col4:
            st.metric(
                "⚖️ Balanço Total das Trocas", 
                f"R$ {balanco_total_trocas:,.2f}",
                help="Ganho Total menos Perda Total. Indica o lucro ou prejuízo líquido da movimentação de estoque."
            )
        with col5:
            st.metric(
                "💵 Valor Final do Rancho", 
                f"R$ {balanco_final:,.2f}",
                help="Valor Original do Rancho ajustado pelo Balanço Total das Trocas. O valor atualizado do seu rancho."
            )

        st.markdown("---")

        st.subheader("Gráficos de Variação")
        
        # Gráfico dos Itens Mais Trocados
        st.markdown("#### Itens com Maior Variação de Estoque")
        df_plot_trocas = contagem_trocas.set_index("Item")
        st.bar_chart(df_plot_trocas)

        # Gráfico de Ganhos e Perdas por Item (o balanço)
        st.markdown("#### Balanço Financeiro por Item")
        # Filtra itens que tiveram alguma variação
        df_plot_balanco = df_comparacao[df_comparacao["Valor_Diferenca"] != 0][["Item", "Valor_Diferenca"]].set_index("Item")
        st.bar_chart(df_plot_balanco)


        st.markdown("---")
        st.subheader("Tabelas Detalhadas")

        with st.expander("Variação Detalhada por Item (Trocas/Balanço)"):
            df_detalhe = itens_trocados[["Item", "Qtd_Inicial", "Qtd_Final", "Qtd_Diferenca", "Valor Unitario", "Valor_Diferenca", "Tipo"]].copy()
            df_detalhe.columns = ["Item", "Qtd Inicial", "Qtd Final", "Diferença Qtd", "Valor Unit.", "Balanço Financeiro", "Tipo de Variação"]
            st.dataframe(df_detalhe, use_container_width=True)
            
        with st.expander("Tabela Final do Rancho (Após Edição)"):
            st.dataframe(df_rancho_final, use_container_width=True)

    except Exception as e:
        st.error(f"Ocorreu um erro ao processar o arquivo. Verifique o formato e as colunas. Erro: {e}")

else:
    st.info("Por favor, carregue o arquivo CSV da Tabela de Rancho para começar.")