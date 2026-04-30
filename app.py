import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
from geopy.extra.rate_limiter import RateLimiter

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Logística Vital", 
    page_icon="logo.png" 
)

@st.cache_data(show_spinner="Consultando mapa...")
def obter_localizacao(cidade):
    geolocator = Nominatim(user_agent="vital_logistica_v15_final", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    try:
        return geocode(cidade)
    except:
        return None

def formar_real(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# --- BARRA LATERAL ---
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

col_t1, col_t2, col_t3 = st.columns([2, 1, 1])

with col_t1:
    tipo_trajeto = st.radio("Modelo de Rota:", ("Apenas Ida", "Ida e Volta"), horizontal=True)

with col_t2:
    # Este número agora controla diretamente a quantidade de diárias de hotel
    dias_por_trecho = st.number_input("Dias por Trecho", min_value=1, value=1)

with col_t3:
    st.write(" ") 
    st.write(" ") 
    is_viagem_curta = st.checkbox("Viagem Curta", value=False, help="Zera apenas o valor do hotel")

col1, col2 = st.columns(2)
with col1:
    origem = st.text_input("Origem", "São Paulo, SP")
with col2:
    destino = st.text_input("Destino", "Rio de Janeiro, RJ")

if destino:
    loc1 = obter_localizacao(origem)
    loc2 = obter_localizacao(destino)

    if loc1 and loc2:
        try:
            multiplicador = 2 if tipo_trajeto == "Apenas Ida" else 4
            
            dist_direta = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
            dist_total_km = dist_direta * (1 + fator_estrada) * multiplicador
            
            # Dias para cálculos que acompanham a rodagem total (Alimentação, Salário, Fixo)
            dias_totais_trabalho = dias_por_trecho * multiplicador

            # --- LÓGICA DE CÁLCULO ---
            custo_diesel = (dist_total_km / consumo) * preco_diesel
            custo_alimentacao = valor_alimentacao_dia * dias_totais_trabalho
            
            # CORREÇÃO AQUI: Hospedagem multiplicada APENAS pelo dia de trecho inserido
            if is_viagem_curta:
                custo_hospedagem_total = 0.0
            else:
                custo_hospedagem_total = valor_pernoite * dias_por_trecho

            custo_pessoal = diaria_motorista * dias_totais_trabalho
            custo_fixo_veiculo = custo_fixo_diaria * dias_totais_trabalho
            
            custo_operacional_total = (custo_diesel + custo_alimentacao + custo_pessoal + 
                                       custo_fixo_veiculo + custo_hospedagem_total)
            
            preco_final = custo_operacional_total * (1 + margem/100)

            st.divider()
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 35px; border-radius: 15px; text-align: center; color: white;">
                    <p style="margin:0; font-size: 1.1rem; text-transform: uppercase;">Valor Total Sugerido</p>
                    <h1 style="margin:10px 0; font-size: 3.8rem; font-weight: 800;">R$ {formar_real(preco_final)}</h1>
                    <p style="margin:0; opacity: 0.8;">{tipo_trajeto} | Hotel cobrado por {dias_por_trecho} dia(s) | Alimentação por {dias_totais_trabalho} dias</p>
                </div>
            """, unsafe_allow_html=True)

            st.write("")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🛣️ KM Total", f"{int(dist_total_km)} km")
            m2.metric("⛽ Diesel", f"R$ {formar_real(custo_diesel)}")
            m3.metric("🏨 Hotel/Alim", f"R$ {formar_real(custo_hospedagem_total + custo_alimentacao)}")
            m4.metric("🚛 Gastos Fixos", f"R$ {formar_real(custo_pessoal + custo_fixo_veiculo)}")

        except Exception as e:
            st.error(f"Erro no cálculo: {e}")
    else:
        st.error("Erro na consulta do mapa.")