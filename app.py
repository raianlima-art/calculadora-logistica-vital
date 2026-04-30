import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
# A logo aparecerá apenas na aba do navegador (miniatura)
st.set_page_config(
    page_title="Logística Vital", 
    page_icon="logo.png" 
)

# Função para formatar moeda
def formar_real(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

# Inicializar geolocalizador
geolocator = Nominatim(user_agent="calculadora_frete_vital_v7", timeout=10)

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("⚙️ Configurações Fixas")
    
    # 1. Custos Fixos do Veículo
    with st.expander("💰 Custos Fixos Veículo", expanded=False):
        ipva = st.number_input("IPVA Anual (R$)", value=10000.0)
        seguro = st.number_input("Seguro Anual (R$)", value=10000.0)
        manut_anual = st.number_input("Manutenção Fixa Anual (R$)", value=10000.0)
        dias_uteis = st.number_input("Dias Úteis/Ano", value=365)
        custo_fixo_diaria = (ipva + seguro + manut_anual) / dias_uteis

    # 2. Estadia com opção de Viagem Curta lado a lado
    with st.expander("🏨 Estadia e Viagens Curtas", expanded=True):
        col_est1, col_est2 = st.columns([1, 1])
        with col_est1:
            valor_alimentacao_dia = st.number_input("Alimentação (R$)", value=70.0)
        with col_est2:
            st.write(" ") # Alinhamento vertical
            is_viagem_curta = st.checkbox("Viagem Curta", value=False, help="Zera hotel e comida")

        valor_pernoite = st.number_input("Hospedagem/Noite (R$)", value=250.0)
        
        # Define se cobra estadia ou não
        custo_estadia_diario = 0.0 if is_viagem_curta else (valor_alimentacao_dia + valor_pernoite)

    # 3. Operação
    with st.expander("⛽ Operação e Lucro", expanded=True):
        consumo = st.number_input("Consumo (km/L)", value=8.0)
        preco_diesel = st.number_input("Preço Diesel (R$)", value=8.00)
        diaria_motorista = st.number_input("Salário Motorista (R$)", value=200.0)
        fator_estrada = st.slider("Ajuste de Curvas (%)", 10, 40, 25) / 100
        margem = st.slider("Margem de Lucro (%)", 0, 100, 40)

# --- CORPO PRINCIPAL ---
st.title("🚚 Calculadora de Frete Vital")

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    tipo_trajeto = st.radio("Modelo de Rota:", ("Apenas Ida", "Ida e Volta"), horizontal=True)
with col_t2:
    dias_por_trecho = st.number_input("Dias por Trecho", min_value=1, value=1)

col1, col2 = st.columns(2)
with col1:
    origem = st.text_input("Origem", "São Paulo, SP")
with col2:
    destino = st.text_input("Destino", "Rio de Janeiro, RJ")

if destino:
    try:
        loc1 = geolocator.geocode(origem)
        loc2 = geolocator.geocode(destino)

        if loc1 and loc2:
            # Lógica solicitada: Apenas Ida (x2) | Ida e Volta (x4)
            multiplicador = 2 if tipo_trajeto == "Apenas Ida" else 4
            
            # Cálculos de Distância e Tempo
            dist_direta = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
            dist_total_km = dist_direta * (1 + fator_estrada) * multiplicador
            dias_totais = dias_por_trecho * multiplicador

            # Cálculos Financeiros
            custo_diesel = (dist_total_km / consumo) * preco_diesel
            custo_estadia = custo_estadia_diario * dias_totais
            custo_pessoal = diaria_motorista * dias_totais
            custo_fixo_veiculo = custo_fixo_diaria * dias_totais
            
            custo_operacional_total = custo_diesel + custo_estadia + custo_pessoal + custo_fixo_veiculo
            preco_final = custo_operacional_total * (1 + margem/100)

            # --- RESULTADO VISUAL ---
            st.divider()
            
            st.markdown(f"""
                <div style="background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); padding: 35px; border-radius: 15px; text-align: center; color: white;">
                    <p style="margin:0; font-size: 1.1rem; text-transform: uppercase;">Valor Total Sugerido</p>
                    <h1 style="margin:10px 0; font-size: 3.8rem; font-weight: 800;">R$ {formar_real(preco_final)}</h1>
                    <p style="margin:0; opacity: 0.8;">{tipo_trajeto} ({multiplicador} Trechos) | {'Sem Estadia' if is_viagem_curta else 'Com Estadia'}</p>
                </div>
            """, unsafe_allow_html=True)

            st.write("")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("🛣️ KM Total", f"{int(dist_total_km)} km")
            m2.metric("⛽ Diesel", f"R$ {formar_real(custo_diesel)}")
            m3.metric("🏨 Estadia", f"R$ {formar_real(custo_estadia)}")
            m4.metric("🚛 Custos Fixos", f"R$ {formar_real(custo_pessoal + custo_fixo_veiculo)}")

            with st.expander("📊 Detalhes do Orçamento"):
                st.write(f"**KM base (um trecho):** {int(dist_direta * (1 + fator_estrada))} km")
                st.write(f"**Tempo total de operação:** {dias_totais} dias")
                st.write(f"**Custo Operacional Total:** R$ {formar_real(custo_operacional_total)}")
                st.write(f"**Lucro Bruto:** R$ {formar_real(preco_final - custo_operacional_total)}")
        else:
            st.warning("Cidade não localizada. Tente inserir: Cidade, UF")
    except Exception as e:
        st.error(f"Erro na consulta: {e}")