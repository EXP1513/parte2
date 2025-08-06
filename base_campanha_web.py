import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Base Campanha", page_icon=":bar_chart:", layout="centered")
st.image("logo.png", width=260)
st.title("Base Campanha")
st.markdown("Organize e limpe suas bases de campanha automaticamente 🚀")

# Upload dos arquivos
kpi_file = st.file_uploader("Importar KPI", type=["xls", "xlsx", "xlsm", "xlsb", "csv"])
fidelizados_file = st.file_uploader("Importar Fidelizados", type=["xls", "xlsx", "xlsm", "xlsb", "csv"])
painel_file = st.file_uploader("Importar Painel", type=["xls", "xlsx", "xlsm", "xlsb", "csv"])

@st.cache_data
def carregar(arquivo):
    extensao = arquivo.name.split(".")[-1].lower()
    if extensao == "csv":
        return pd.read_csv(arquivo)
    elif extensao == "xls":
        return pd.read_excel(arquivo, engine="xlrd")
    elif extensao in ["xlsx", "xlsm"]:
        return pd.read_excel(arquivo, engine="openpyxl")
    elif extensao == "xlsb":
        return pd.read_excel(arquivo, engine="pyxlsb")
    else:
        return None

def processamento_completo(kpi, fidelizados, painel):
    # --- Limpeza KPI ---
    if kpi is None:
        return None, None
    if "Whatsapp Principal" in kpi.columns:
        kpi["Whatsapp Principal"] = kpi["Whatsapp Principal"].astype(str).str.replace(r"\D", "", regex=True)
    if "Observação" in kpi.columns:
        kpi = kpi[kpi["Observação"].astype(str).str.contains("Médio|Fundamental", case=False, na=False)]
    if fidelizados is not None and "Whatsapp Principal" in fidelizados.columns:
        fidelizados["Whatsapp Principal"] = fidelizados["Whatsapp Principal"].astype(str).str.replace(r"\D", "", regex=True)
        kpi = kpi[~kpi["Whatsapp Principal"].isin(fidelizados["Whatsapp Principal"])]
    if painel is not None and "Telefone (cobrança)" in painel.columns:
        painel["Telefone (cobrança)"] = painel["Telefone (cobrança)"].astype(str).str.replace(r"\D", "", regex=True)
        kpi = kpi[~kpi["Whatsapp Principal"].isin(painel["Telefone (cobrança)"])]
    # Manter apenas colunas principais
    keep_cols = [col for col in ["Contato", "Observação", "Whatsapp Principal"] if col in kpi.columns]
    kpi = kpi[keep_cols].drop_duplicates(subset=["Whatsapp Principal"]).reset_index(drop=True)
    # Renomear colunas
    kpi = kpi.rename(columns={"Contato": "Nome", "Whatsapp Principal": "Numero", "Observação": "Tipo"})
    # Processar nomes
    kpi["Nome"] = kpi["Nome"].astype(str).str.split().str[0].str.upper()
    kpi.loc[kpi["Nome"].str.len().between(1, 3), "Nome"] = "CANDIDATO"
    # Criar aba nome
    aba_nome = kpi[["Nome"]].copy()
    aba_nome["Telefone"] = kpi["Numero"]
    aba_nome = aba_nome.drop_duplicates(subset=["Nome"]).reset_index(drop=True)
    return kpi, aba_nome

if st.button("Gerar Base"):
    with st.spinner("Processando..."):
        kpi = carregar(kpi_file) if kpi_file else None
        fidelizados = carregar(fidelizados_file) if fidelizados_file else None
        painel = carregar(painel_file) if painel_file else None
        kpi_final, aba_nome = processamento_completo(kpi, fidelizados, painel)
        if kpi_final is None:
            st.error("Base KPI inválida ou não carregada!")
        else:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                kpi_final.to_excel(writer, sheet_name="kpi", index=False)
                if aba_nome is not None:
                    aba_nome.to_excel(writer, sheet_name="nome", index=False)
                if fidelizados is not None:
                    fidelizados.to_excel(writer, sheet_name="fidelizados", index=False)
                if painel is not None:
                    painel.to_excel(writer, sheet_name="painel", index=False)
            st.success("Processamento finalizado com sucesso!")
            st.download_button("Baixar Excel Final", output.getvalue(), file_name="base_campanha_final.xlsx")

st.markdown("---")
st.caption("Desenvolvido por Base Campanha - Gratuito 🆓")
