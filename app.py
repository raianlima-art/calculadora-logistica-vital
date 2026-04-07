import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Logística Vital", page_icon="🚛")
st.title("🚛 Calculadora Logística Vital")

# Inicializar geolocalizador
geolocator = Nominatim(user_agent="calculadora_frete_v3")

# --- BARRA LATERAL: CONFIGURAÇÕES ---
with st.sidebar:
    st.header("⚙️ Configurações Fixas")
    
    # 1. Custos de Propriedade (IPVA, Seguro, Manut)
    with st.expander("💰 Custos Fixos (Anuais)", expanded=False):
        ipva = st.number_input("IPVA Anual (R$)", value=3000.0)
        seguro = st.number_input("Seguro Anual (R$)", value=6000.0)
        manut_anual = st.number_input("Manutenção Fixa Anual (R$)", value=4000.0)
        dias_uteis = st.number_input("Dias Úteis de Trabalho/Ano", value=250)
        custo_fixo_diaria = (ipva + seguro + manut_anual) / dias_uteis
        st.write(f"**Custo Fixo/Dia:** R$ {custo_fixo_diaria:.2f}")

    # 2. Custos de Viagem (Hospedagem e Alimentação)
    with st.expander("🏨 Hospedagem e Refeição", expanded=True):
        valor_alimentacao_dia = st.number_input("Alimentação por Dia (R$)", value=60.0)
        valor_pernoite = st.number_input("Hospedagem/Pernoite (R$)", value=120.0)
        total_viagem_dia = valor_alimentacao_dia + valor_pernoite
        st.write(f"**Total Diário Extra:** R$ {total_viagem_dia:.2f}")

    # 3. Operação e Lucro
    with st.expander("⛽ Operação e Lucro", expanded=True):
        consumo = st.number_input("Consumo (km/L)", value=4.0)
        preco_diesel = st.number_input("Preço Diesel (R$)", value=8.00)
        diaria_motorista = st.number_input("Salário/Diária Motorista (R$)", value=200.0)
        fator_estrada = st.slider("Ajuste de Curvas (%)", 10, 40, 20) / 100
        margem = st.slider("Margem de Lucro (%)", 0, 100, 25)

# --- CORPO PRINCIPAL ---
st.subheader("📍 Planejamento da Rota")

col_t1, col_t2 = st.columns([2, 1])
with col_t1:
    tipo_trajeto = st.radio("Selecione o trajeto:", ("Apenas Ida", "Ida e Volta"), horizontal=True)
with col_t2:
    qtd_dias_viagem = st.number_input("Duração (Dias)", min_value=1, value=1)

col1, col2 = st.columns(2)
with col1:
    origem = st.text_input("Cidade de Origem", "São Paulo, SP")
with col2:
    destino = st.text_input("Cidade de Destino", placeholder="Ex: Rio de Janeiro, RJ")

if destino:
    try:
        loc1 = geolocator.geocode(origem)
        loc2 = geolocator.geocode(destino)

        if loc1 and loc2:
            # Cálculo de distância
            distancia_base = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
            distancia_ajustada = distancia_base * (1 + fator_estrada)
            distancia_total = distancia_ajustada * 2 if tipo_trajeto == "Ida e Volta" else distancia_ajustada

            # --- CÁLCULOS FINANCEIROS ---
            custo_combustivel = (distancia_total / consumo) * preco_diesel
            
            # Custos que dependem dos DIAS de viagem
            custo_estadia_total = (valor_alimentacao_dia + valor_pernoite) * qtd_dias_viagem
            custo_pessoal_total = diaria_motorista * qtd_dias_viagem
            custo_fixo_periodo = custo_fixo_diaria * qtd_dias_viagem
            
            # Custo Total Somado
            custo_operacional = custo_combustivel + custo_estadia_total + custo_pessoal_total + custo_fixo_periodo
            preco_final = custo_operacional * (1 + margem/100)

            # --- RESULTADOS ---
            st.divider()
            st.subheader(f"Valor Sugerido: R$ {preco_final:.2f}")
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("KM Total", f"{distancia_total:.0f} km")
            c2.metric("Diesel", f"R$ {custo_combustivel:.2f}")
            c3.metric("Estadia", f"R$ {custo_estadia_total:.2f}")
            c4.metric("Fixo/Pessoal", f"R$ {(custo_pessoal_total + custo_fixo_periodo):.2f}")

            with st.expander("📊 Detalhes do Orçamento"):
                st.write(f"**Distância considerada:** {distancia_total:.2f} km")
                st.write(f"**Dias de viagem:** {qtd_dias_viagem}")
                st.write(f"---")
                st.write(f"**Custo Alimentação/Hospedagem:** R$ {custo_estadia_total:.2f}")
                st.write(f"**Custo Combustível:** R$ {custo_combustivel:.2f}")
                st.write(f"**Custo Fixo + Motorista:** R$ {custo_pessoal_total + custo_fixo_periodo:.2f}")
                st.write(f"**Margem de Lucro Bruto:** R$ {preco_final - custo_operacional:.2f}")
        else:
            st.error("Cidade não encontrada.")
    except:
        st.error("Erro ao consultar o mapa. Verifique a internet.")