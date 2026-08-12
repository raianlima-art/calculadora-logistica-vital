import streamlit as st
from geopy.geocoders import Photon
from geopy.distance import geodesic
import time

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Logística Vital", 
    page_icon="🚚" 
)

# Função de geolocalização mantida
@st.cache_data(show_spinner="Consultando mapa...")
def obter_localizacao(cidade):
    geolocator = Photon(user_agent="vital_logistica_v18", timeout=10)
    try:
        return geolocator.geocode(cidade)
    except Exception as e:
        return None

def formar_real(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# --- BARRA LATERAL (PARÂMETROS ORIGINAIS) ---
with st.sidebar:
    st.header("⚙️ Configurações Fixas")
    
    with st.expander("💰 Custos Fixos Veículo", expanded=False):
        ipva = st.number_input("IPVA Anual (R$)", value=10000.0)
        seguro = st.number_input("Seguro Anual (R$)", value=10000.0)
        manut_anual = st.number_input("Manutenção Fixa Anual (R$)", value=10000.0)
        dias_uteis = st.number_input("Dias Úteis/Ano", value=365)
        custo_fixo_diaria = (ipva + seguro + manut_anual) / dias_uteis

    with st.expander("🍴 Custos Unitários", expanded=True):
        valor_alimentacao_dia = st.number_input("Alimentação/Dia (R$)", value=70.0)
        valor_pernoite = st.number_input("Hospedagem/Noite (R$)", value=250.0)

    with st.expander("⛽ Operação e Lucro", expanded=True):
        consumo = st.number_input("Consumo (km/L)", value=8.0)
        preco_diesel = st.number_input("Preço Diesel (R$)", value=8.00)
        diaria_motorista = st.number_input("Salário Motorista (R$)", value=200.0)
        fator_estrada = st.slider("Ajuste de Curvas (%)", 10, 40, 25) / 100
        margem = st.slider("Margem de Lucro (%)", 0, 100, 20)

# --- CORPO PRINCIPAL ---
st.title("🚚 Calculadora de Frete Vital")

# Formulário para disparar a busca apenas no clique do botão
with st.form("form_rota"):
    col_t1, col_t2, col_t3 = st.columns([2, 1, 1])

    with col_t1:
        tipo_trajeto = st.radio("Modelo de Rota:", ("Apenas Ida", "Ida e Volta"), horizontal=True)

    with col_t2:
        dias_por_trecho = st.number_input("Dias por Trecho", min_value=1, value=1)

    with col_t3:
        st.write(" ") 
        st.write(" ") 
        is_viagem_curta = st.checkbox("Viagem Curta", value=False, help="Zera o valor do hotel")

    col1, col2 = st.columns(2)
    with col1:
        origem = st.text_input("Origem", "São Paulo, SP")
    with col2:
        destino = st.text_input("Destino", "Rio de Janeiro, RJ")

    btn_calcular = st.form_submit_button("🔍 Calcular Frete", use_container_width=True)

if btn_calcular:
    if destino and origem:
        loc1 = obter_localizacao(origem)
        loc2 = obter_localizacao(destino)

        if loc1 and loc2:
            try:
                # Lógica de multiplicador mantida intacta
                multiplicador = 2 if tipo_trajeto == "Apenas Ida" else 4
                
                dist_direta = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
                dist_total_km = dist_direta * (1 + fator_estrada) * multiplicador
                dias_totais_operacao = dias_por_trecho * multiplicador

                # --- LÓGICA DE CÁLCULO MANTIDA ---
                custo_diesel = (dist_total_km / consumo) * preco_diesel
                
                custo_alimentacao_total = valor_alimentacao_dia * 1
                
                if is_viagem_curta:
                    custo_hospedagem_total = 0.0
                else:
                    custo_hospedagem_total = valor_pernoite * dias_por_trecho

                custo_pessoal = diaria_motorista * dias_totais_operacao
                custo_fixo_veiculo = custo_fixo_diaria * dias_totais_operacao
                
                custo_operacional_total = (custo_diesel + custo_alimentacao_total + custo_pessoal + 
                                           custo_fixo_veiculo + custo_hospedagem_total)
                
                preco_final = custo_operacional_total * (1 + margem/100)

                st.divider()
                
                # Card de Resultado
                st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 45px; border-radius: 15px; text-align: center; color: white;">
                        <p style="margin:0; font-size: 1.2rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.9;">Valor Total Sugerido</p>
                        <h1 style="margin:15px 0 0 0; font-size: 4rem; font-weight: 800;">R$ {formar_real(preco_final)}</h1>
                    </div>
                """, unsafe_allow_html=True)

                st.write("")
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("🛣️ KM Total", f"{int(dist_total_km)} km")
                m2.metric("⛽ Diesel", f"R$ {formar_real(custo_diesel)}")
                m3.metric("🏨 Hotel/Alim", f"R$ {formar_real(custo_hospedagem_total + custo_alimentacao_total)}")
                m4.metric("🚛 Gastos Fixos", f"R$ {formar_real(custo_pessoal + custo_fixo_veiculo)}")

            except Exception as e:
                st.error(f"Erro no cálculo: {e}")
        else:
            if not loc1:
                st.error(f"❌ Não conseguimos encontrar a Origem: '{origem}'. Verifique a grafia ou o estado.")
            if not loc2:
                st.error(f"❌ Não conseguimos encontrar o Destino: '{destino}'. Verifique a grafia ou o estado.")
