import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Joivy Analytics", layout="wide")

st.title("📊 Dashboard Joivy-Dovevivo")

# Aggiunta di spazio verticale tra il titolo principale e la sezione successiva
st.markdown("<br><br>", unsafe_allow_html=True)

# 1. CARICAMENTO DATI
@st.cache_data
def load_data():
    return pd.read_parquet('data/rooms_df.parquet')

df_global = load_data()

# ==========================================
# FUNZIONE DI GENERAZIONE COLORI CON REGOLE FISSE
# ==========================================
def get_country_color_map(cities):
    """
    Mappatura cromatica definitiva per le 15 città del perimetro.
    Garantisce coerenza per nazione e massima distinzione tra i singoli centri.
    """
    colori_citta = {

        # ==========================================
        # 🇮🇹 ITALIA: Gruppo Verde & Terra (7 città)
        # ==========================================
        "Milano": "#2E7D32",       # Verde Smeraldo deciso
        "Bologna": "#1B5E20",      # Verde Foresta scuro
        "Padova": "#81C784",       # Verde Salvia chiaro
        "Roma": "#4E342E",         # Marrone Caffè scuro
        "Trento": "#8D6E63",       # Marrone Legno medio
        "Torino": "#D7CCC8",       # Beige/Tortora molto chiaro
        "Firenze": "#109618",      # Verde Prato brillante       
        
        # ==========================================
        # 🇫🇷 FRANCIA: Gruppo Blu, Azzurro e Rosa (6 città)
        # ==========================================
        "Parigi": "#0D47A1",       # Blu Notte profondo
        "Lione": "#1976D2",        # Blu Reale standard
        "Bordeaux": "#64B5F6",     # Azzurro Cielo limpido
        "Lille": "#00DEC9",        # Turchese/Acqua intenso
        "Montpellier": "#FF4081",  # Rosa Shocking acceso
        "Tolosa": "#F48FB1",       # Rosa Confetto bilanciato
        
        # ==========================================
        # 🇪🇸 SPAGNA: Arancione Brillante (1 città)
        # ==========================================
        "Madrid": "#FF6D00",       # Arancione Zucca saturo
        
        # ==========================================
        # 🇵🇹 PORTOGALLO: Rosso Intenso (1 città)
        # ==========================================
        "Lisbona": "#D50000"       # Rosso Fuoco vivido
    }
    
    # Ritorna il colore associato o un grigio di fallback per sicurezza
    return {city: colori_citta.get(city, "#757575") for city in cities}

# ==========================================
# 2. BARRA LATERALE - FILTRI
# ==========================================
st.sidebar.header("🎛️ Filtri")

all_cities = sorted(df_global['city'].unique())
default_index = all_cities.index("Milano") if "Milano" in all_cities else 0

selected_city = st.sidebar.selectbox(
    "Seleziona Città Principale:", 
    options=all_cities, 
    index=default_index
)

opzioni_confronto = [c for c in all_cities if c != selected_city]
selected_compare_cities = st.sidebar.multiselect(
    "⚔️ Confronta con (seleziona una o più città):",
    options=opzioni_confronto,
    default=[]
)

min_p, max_p = int(df_global['price'].min()), int(df_global['price'].max())
selected_price_range = st.sidebar.slider("Range Prezzo (€):", min_value=min_p, max_value=max_p, value=(min_p, max_p))

min_t, max_t = int(df_global['max_tenants'].min()), int(df_global['max_tenants'].max())
selected_tenants = st.sidebar.slider("Numero Inquilini:", min_value=min_t, max_value=max_t, value=(min_t, max_t))

min_mq, max_mq = float(df_global['mq'].min()), float(df_global['mq'].max())
selected_mq = st.sidebar.slider("Superficie (m²):", min_value=min_mq, max_value=max_mq, value=(min_mq, max_mq))

# Corretti i valori per renderli coerenti con il controllo logico successivo
bed_choice = st.sidebar.radio("Tipo di letto:", options=["Tutti", "Letto grande", "Letto singolo"])

# --- COSTRUZIONE DATAFRAME FILTRATO ---
citta_da_estrarre = [selected_city] + selected_compare_cities

df_filtered = df_global[
    (df_global['city'].isin(citta_da_estrarre)) &
    (df_global['price'].between(selected_price_range[0], selected_price_range[1])) &
    (df_global['max_tenants'].between(selected_tenants[0], selected_tenants[1])) &
    (df_global['mq'].between(selected_mq[0], selected_mq[1]))
]
if bed_choice == "Letto grande":
    df_filtered = df_filtered[df_filtered['has_large_bed'] == True]
elif bed_choice == "Letto singolo":
    df_filtered = df_filtered[df_filtered['has_large_bed'] == False]

# ==========================================
# 3. TABELLE STATISTICHE
# ==========================================
st.header("Statistiche (Filtrate vs Globale)")

# 1. Recuperiamo la mappa dei colori per la città selezionata
mappa_colori_completa = get_country_color_map([selected_city])
colore_citta_scelta = mappa_colori_completa.get(selected_city, "#4CAF50")

# 2. Mostriamo il titolo: solo la città prende il colore dinamico, il resto rimane nero/scuro
st.markdown(
    f"<h3 style='text-align: left; margin-top: 5px; color: #31333F;'>"
    f"🏙️ <span style='color: {colore_citta_scelta};'>{selected_city}</span> vs Rest of World 🌍"
    f"</h3>", 
    unsafe_allow_html=True
)

# Le tabelle statistiche continuano a fare riferimento solo alla Città Principale selezionata
df_stats_filtered = df_filtered[df_filtered['city'] == selected_city]

def get_stats(df_target):
    if df_target.empty:
        return [0]*3, [0]*3, [0]*3
    
    p = [df_target['price'].min(), df_target['price'].max(), df_target['price'].median()]
    mq = [df_target['mq'].min(), df_target['mq'].max(), df_target['mq'].mean()]
    
    t = [
        int(df_target['max_tenants'].min()), 
        int(df_target['max_tenants'].max()), 
        int(round(df_target['max_tenants'].median()))
    ]
    
    mq[2] = f"{mq[2]:.1f}"
    
    return p, mq, t

p_f, mq_f, t_f = get_stats(df_stats_filtered)
p_g, mq_g, t_g = get_stats(df_global)

col_t1, col_t2, col_t3 = st.columns(3)

# Rimosso il nome della città dai titoli secondari delle tabelle
with col_t1:
    st.subheader("💸 Prezzi")
    df_p = pd.DataFrame({
        "Indicatore": ["Minimo", "Massimo", "Mediana"],
        "Filtrato": p_f, "Globale": p_g
    }).set_index("Indicatore")
    st.table(df_p)

with col_t2:
    st.subheader("📐 Mq")
    df_mq = pd.DataFrame({
        "Indicatore": ["Minimo", "Massimo", "Media"],
        "Filtrato": mq_f, "Globale": mq_g
    }).set_index("Indicatore")
    st.table(df_mq)

with col_t3:
    st.subheader("👥 Inquilini")
    df_t = pd.DataFrame({
        "Indicatore": ["Minimo", "Massimo", "Mediana"],
        "Filtrato": t_f, "Globale": t_g
    }).set_index("Indicatore")
    st.table(df_t)

st.markdown("---")

# ==========================================
# 4. GRAFICI DI RELAZIONE (CON ASSI CONFIGURATI)
# ==========================================
if df_filtered.empty:
    st.warning("⚠️ Nessuna stanza risponde ai criteri di ricerca selezionati.")
else:
    col_g1, col_g2 = st.columns(2)
    
    current_cities = df_filtered['city'].unique()
    custom_color_map = get_country_color_map(current_cities)
    
    with col_g1:
        st.subheader("Numero Inquilini vs Prezzo")
        fig_price_tenants = px.scatter(
            df_filtered, x='max_tenants', y='price', color='city',
            marginal_x="box",
            color_discrete_map=custom_color_map,
            labels={"max_tenants": "Numero Inquilini", "city": "Città", "price": "Prezzo Stanza (€)"}
        )
        fig_price_tenants.update_layout(
            xaxis=dict(tickmode='linear', dtick=1)
        )
        st.plotly_chart(fig_price_tenants, use_container_width=True)
        
    with col_g2:
        st.subheader("Dimensione (Mq) vs Prezzo")
        fig_price_mq = px.scatter(
            df_filtered, x='mq', y='price', color='city',
            marginal_x="box",
            color_discrete_map=custom_color_map,
            labels={"mq": "Metri Quadri (m²)", "city": "Città", "price": "Prezzo Stanza (€)"}
        )
        fig_price_mq.update_layout(
            xaxis=dict(type='linear')
        )
        st.plotly_chart(fig_price_mq, use_container_width=True)

    st.subheader("📋 Elenco delle stanze selezionate")
    st.dataframe(df_filtered, use_container_width=True)

st.markdown("---")

# ==========================================
# 5. MODALITÀ CONFRONTO MULTI-CITTÀ (COLORI COERENTI)
# ==========================================
st.header("⚔️ Confronto Città vs Città")

if len(citta_da_estrarre) >= 2:
    st.write("Confronto dei prezzi basato sui filtri correnti:")
    
    categorie = ['Minimo', 'Medio', 'Mediano', 'Massimo']
    fig_compare = go.Figure()
    
    custom_color_map = get_country_color_map(citta_da_estrarre)
    
    for colonna_citta in citta_da_estrarre:
        df_citta = df_filtered[df_filtered['city'] == colonna_citta]
        
        if not df_citta.empty:
            metrics = [
                df_citta['price'].min(), 
                df_citta['price'].mean(), 
                df_citta['price'].median(), 
                df_citta['price'].max()
            ]
            
            colore_citta = custom_color_map.get(colonna_citta, "#757575")
            
            fig_compare.add_trace(go.Bar(
                x=categorie, 
                y=metrics, 
                name=colonna_citta,
                marker_color=colore_citta,
                text=[f"€{v:.1f}" for v in metrics], 
                textposition='auto'
            ))
        
    fig_compare.update_layout(
        barmode='group',
        xaxis_title="Indicatori di Prezzo",
        yaxis_title="Prezzo (€)",
        legend_title="Città",
        margin=dict(t=20, b=20, l=10, r=10)
    )
    st.plotly_chart(fig_compare, use_container_width=True)
else:
    st.info("💡 **Vuoi confrontare i prezzi con altre città?** Seleziona una o più città nel filtro laterale **'Confronta con'**.")
