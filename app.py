import streamlit as st
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Logística Vital", 
    page_icon="logo.png"
)

# Função para formatar números no padrão brasileiro (1.000,00)
def formar_real(valor):
    # Formata com milhar em vírgula e decimal em ponto, depois inverte
    ajustado = "{:,.2f}".format(valor)
    return ajustado.replace(",", "X").replace(".", ",").replace("X", ".")

# Inicializar geolocalizador
geolocator = Nominatim(user_agent="calculadora_frete_v3")

# --- BARRA LATERAL: CONFIGURAÇÕES ---
with st.sidebar:
    st.header("⚙️ Configurações Fixas")
    
    # 1. Custos de Propriedade (IPVA, Seguro, Manut)
    with st.expander("💰 Custos Fixos (Anuais)", expanded=False):
        ipva = st.number_input("IPVA Anual (R$)", value=10000.0)
        seguro = st.number_input("Seguro Anual (R$)", value=10000.0)
        manut_anual = st.number_input("Manutenção Fixa Anual (R$)", value=10000.0)
        dias_uteis = st.number_input("Dias Úteis/Ano", value=365)
        custo_fixo_diaria = (ipva + seguro + manut_anual) / dias_uteis
        st.write(f"**Custo Fixo/Dia:** R$ {formar_real(custo_fixo_diaria)}")

    # 2. Custos de Viagem (Hospedagem e Alimentação)
    with st.expander("🏨 Hospedagem e Refeição", expanded=True):
        valor_alimentacao_dia = st.number_input("Alimentação/Dia (R$)", value=70.0)
        valor_pernoite = st.number_input("Hospedagem (R$)", value=250.0)

    # 3. Operação e Lucro
    with st.expander("⛽ Operação e Lucro", expanded=True):
        consumo = st.number_input("Consumo (km/L)", value=8.0)
        preco_diesel = st.number_input("Preço Diesel (R$)", value=8.00)
        diaria_motorista = st.number_input("Salário/Diária Motorista (R$)", value=200.0)
        fator_estrada = st.slider("Ajuste de Curvas (%)", 10, 40, 25) / 100
        margem = st.slider("Margem de Lucro (%)", 0, 100, 40)

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
            distancia_base = geodesic((loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)).km
            distancia_ajustada = distancia_base * (1 + fator_estrada)
            distancia_total = distancia_ajustada * 2 if tipo_trajeto == "Ida e Volta" else distancia_ajustada

            custo_combustivel = (distancia_total / consumo) * preco_diesel
            custo_estadia_total = (valor_alimentacao_dia + valor_pernoite) * qtd_dias_viagem
            custo_pessoal_total = diaria_motorista * qtd_dias_viagem
            custo_fixo_periodo = custo_fixo_diaria * qtd_dias_viagem
            
            custo_operacional = custo_combustivel + custo_estadia_total + custo_pessoal_total + custo_fixo_periodo
            preco_final = custo_operacional * (1 + margem/100)

            # --- RESULTADOS COM DESIGN PREMIUM E LIMPO ---
            st.divider()
            
            # Card de Destaque (Foco total no preço)
            st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #134E5E 0%, #71B280 100%);
                    padding: 40px;
                    border-radius: 20px;
                    box-shadow: 0px 12px 25px rgba(0,0,0,0.15);
                    text-align: center;
                    margin-bottom: 35px;
                    border: 1px solid rgba(255,255,255,0.1);
                ">
                    <h3 style="color: white; margin: 0; font-size: 1.1rem; opacity: 0.8; letter-spacing: 2px; font-weight: 400;">
                        VALOR TOTAL SUGERIDO
                    </h3>
                    <h1 style="color: white; margin: 10px 0 0 0; font-size: 4rem; font-weight: 900; line-height: 1;">
                        R$ {formar_real(preco_final)}
                    </h1>
                </div>
            """, unsafe_allow_html=True)
            
            # Métricas em colunas (Alinhadas e Escaneáveis)
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"<div style='text-align: center;'><strong>🛣️ KM Total</strong><br><span style='font-size: 1.4rem;'>{formar_real(distancia_total).split(',')[0]} km</span></div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='text-align: center;'><strong>⛽ Diesel</strong><br><span style='font-size: 1.4rem; color: #E74C3C;'>R$ {formar_real(custo_combustivel)}</span></div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='text-align: center;'><strong>🏨 Estadia</strong><br><span style='font-size: 1.4rem;'>R$ {formar_real(custo_estadia_total)}</span></div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='text-align: center;'><strong>🚚 Fixo/Pess.</strong><br><span style='font-size: 1.4rem;'>R$ {formar_real(custo_pessoal_total + custo_fixo_periodo)}</span></div>", unsafe_allow_html=True)

            st.write(" ") 

            with st.expander("📊 Detalhes do Orçamento"):
                st.write(f"**Trajeto:** {tipo_trajeto} | **Margem:** {margem}% | **Curvas:** {fator_estrada*100:.0f}%")
                st.write(f"**Custo Total Operacional:** R$ {formar_real(custo_operacional)}")
                st.write(f"**Lucro Bruto (Valor limpo):** R$ {formar_real(preco_final - custo_operacional)}")
                st.write("---")
                st.write(f"Origem: {loc1.address}")
                st.write(f"Destino: {loc2.address}")
        else:
            st.error("Cidade não encontrada.")
    except Exception as e:
        st.error(f"Erro ao consultar o mapa: {e}")
