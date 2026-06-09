import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Analisi Immobiliare Avanzata", layout="wide")

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
    Assegna colori fissi alle città italiane specificate dall'utente:
    - Bologna: Verde Scuro | Milano: Verde | Padova: Verde Chiaro
    - Roma: Castano Scuro | Trento: Castano | Torino: Castano Chiaro
    
    Per tutte le altre città applica i gradienti dinamici per nazione.
    """
    # Regole fisse richieste dall'utente
    explicit_colors = {
        "Bologna": "#1B5E20",       # Verde scuro
        "Milano": "#4CAF50",        # Verde
        "Padova": "#A5D6A7",        # Verde chiaro
        "Roma": "#3E2723",          # Castano scuro
        "Trento": "#795548",        # Castano
        "Torino": "#D7CCC8"         # Castano chiaro / Beige
    }
    
    # Palette di fallback per altre città italiane (non incluse nelle fisse)
    palette_italia_fallback = ["#2E7D32", "#81C784", "#6D4C41", "#8D6E63", "#F1F8E9", "#DCEDC8"]
    
    # Palette Francia (da Blu a Rosa)
    palette_francia = [
        "#0D47A1", "#1565C0", "#2196F3", "#64B5F6", 
        "#F8BBD0", "#F48FB1", "#F06292", "#E91E63", 
        "#D81B60", "#880E4F"
    ]
    
    palette_spagna = ["#F57F17", "#FBC02D", "#FDD835", "#FFEE58", "#FFF59D"]
    palette_portogallo = ["#B71C1C", "#C62828", "#E53935", "#EF5350", "#EF9A9A"]
    
    # Liste di controllo geografico per le altre città
    italian_cities = ["Firenze", "Napoli", "Venezia", "Genova", "Bari", "Palermo", "Pisa"]
    french_cities = ["Parigi", "Lione", "Marsiglia", "Nizza", "Bordeaux", "Tolosa", "Lilla", "Nantes", "Paris", "Lyon", "Marseille", "Nice", "Lille"]
    spanish_cities = ["Madrid", "Barcellona", "Valencia", "Siviglia", "Saragozza", "Barcelona", "Sevilla"]
    portuguese_cities = ["Lisbona", "Porto", "Coimbra", "Braga", "Lisbon"]
    
    color_map = {}
    it_idx, fr_idx, es_idx, pt_idx = 0, 0, 0, 0
    
    for city in cities:
        if city in explicit_colors:
            color_map[city] = explicit_colors[city]
        elif city in italian_cities:
            color_map[city] = palette_italia_fallback[it_idx % len(palette_italia_fallback)]
            it_idx += 1
        elif city in french_cities:
            color_map[city] = palette_francia[fr_idx % len(palette_francia)]
            fr_idx += 1
        elif city in spanish_cities:
            color_map[city] = palette_spagna[es_idx % len(palette_spagna)]
            es_idx += 1
        elif city in portuguese_cities:
            color_map[city] = palette_portogallo[pt_idx % len(palette_portogallo)]
            pt_idx += 1
        else:
            if it_idx <= fr_idx:
                color_map[city] = palette_italia_fallback[it_idx % len(palette_italia_fallback)]
                it_idx += 1
            else:
                color_map[city] = palette_francia[fr_idx % len(palette_francia)]
                fr_idx += 1
                
    return color_map

# ==========================================
# 2. BARRA LATERALE - FILTRI
# ==========================================
st.sidebar.header("🎛️ Filtri")

all_cities = sorted(df_global['city'].unique())
default_city = ["Milano"] if "Milano" in all_cities else [all_cities[0]]

selected_cities = st.sidebar.multiselect(
    "Seleziona Città:", 
    options=all_cities, 
    default=default_city
)

citta_confronto = None
if len(selected_cities) == 1:
    citta_principale = selected_cities[0]
    opzioni_confronto = [c for c in all_cities if c != citta_principale]
    opzioni_confronto.insert(0, "Nessuna")
    
    citta_confronto = st.sidebar.selectbox(
        "⚔️ Confronta con:",
        options=opzioni_confronto,
        index=0
    )
    if citta_confronto == "Nessuna":
        citta_confronto = None

min_p, max_p = int(df_global['price'].min()), int(df_global['price'].max())
selected_price_range = st.sidebar.slider("Range Prezzo (€):", min_value=min_p, max_value=max_p, value=(min_p, max_p))

min_t, max_t = int(df_global['max_tenants'].min()), int(df_global['max_tenants'].max())
selected_tenants = st.sidebar.slider("Numero Inquilini:", min_value=min_t, max_value=max_t, value=(min_t, max_t))

min_mq, max_mq = float(df_global['mq'].min()), float(df_global['mq'].max())
selected_mq = st.sidebar.slider("Superficie (m²):", min_value=min_mq, max_value=max_mq, value=(min_mq, max_mq))

bed_choice = st.sidebar.radio("Tipo di letto:", options=["Tutti", "Letto grande", "Letto singolo"])

# --- COSTRUZIONE DATAFRAME FILTRATO ---
citta_da_estrarre = selected_cities.copy()
if citta_confronto:
    citta_da_estrarre.append(citta_confronto)

df_filtered = df_global[
    (df_global['city'].isin(citta_da_estrarre)) &
    (df_global['price'].between(selected_price_range[0], selected_price_range[1])) &
    (df_global['max_tenants'].between(selected_tenants[0], selected_tenants[1])) &
    (df_global['mq'].between(selected_mq[0], selected_mq[1]))
]

if bed_choice == "Letto Grande":
    df_filtered = df_filtered[df_filtered['has_large_bed'] == True]
elif bed_choice == "Letto Singolo":
    df_filtered = df_filtered[df_filtered['has_large_bed'] == False]


# ==========================================
# 3. TABELLE STATISTICHE SPLITTATE
# ==========================================
st.header("Statistiche (Filtrate vs Globale)")

df_stats_filtered = df_filtered[df_filtered['city'].isin(selected_cities)]

def get_stats(df_target):
    if df_target.empty:
        return [0]*3, [0]*3, [0]*3
    
    # Prezzo: rimosso il valore medio per allineare il numero di righe (ora sono 3)
    p = [df_target['price'].min(), df_target['price'].max(), df_target['price'].median()]
    mq = [df_target['mq'].min(), df_target['mq'].max(), df_target['mq'].mean()]
    
    # Mediana inquilini espressa come intero puro
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
    st.subheader("👥 Numero Inquilini")
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
        st.subheader("Numero Inquilini VS Prezzo")
        fig_price_tenants = px.scatter(
            df_filtered, x='max_tenants', y='price', color='city',
            marginal_x="box",
            color_discrete_map=custom_color_map,
            labels={"max_tenants": "Numero Inquilini", "city": "Città", "price": "Prezzo Stanza (€)"}
        )
        # Forza la visualizzazione di soli numeri interi (passo = 1) sull'asse X
        fig_price_tenants.update_layout(
            xaxis=dict(tickmode='linear', dtick=1)
        )
        st.plotly_chart(fig_price_tenants, use_container_width=True)
        
    with col_g2:
        st.subheader("Dimensione (Mq) VS Prezzo")
        fig_price_mq = px.scatter(
            df_filtered, x='mq', y='price', color='city',
            marginal_x="box",
            color_discrete_map=custom_color_map,
            labels={"mq": "Metri Quadri (m²)", "city": "Città", "price": "Prezzo Stanza (€)"}
        )
        # Asse X esplicitamente configurato come di tipo lineare (continuo, non forzato a interi)
        fig_price_mq.update_layout(
            xaxis=dict(type='linear')
        )
        st.plotly_chart(fig_price_mq, use_container_width=True)

    st.subheader("📋 Elenco delle stanze selezionate")
    st.dataframe(df_filtered, use_container_width=True)

st.markdown("---")


# ==========================================
# 5. MODALITÀ CONFRONTO (COLORI INVERTITI)
# ==========================================
st.header("⚔️ Città VS Città")

attiva_confronto = False
c1, c2 = None, None

if len(selected_cities) == 2:
    attiva_confronto = True
    c1, c2 = selected_cities[0], selected_cities[1]
elif len(selected_cities) == 1 and citta_confronto is not None:
    attiva_confronto = True
    c1, c2 = selected_cities[0], citta_confronto

if attiva_confronto:
    st.write(f"Confronto dei prezzi applicando i criteri scelti per **{c1}** e **{c2}**:")
    
    df_c1 = df_filtered[df_filtered['city'] == c1]
    df_c2 = df_filtered[df_filtered['city'] == c2]
    
    if df_c1.empty or df_c2.empty:
        st.info(f"ℹ️ Per generare il grafico, entrambe le città devono avere dati coerenti con i filtri. Al momento una delle due città ({c1} o {c2}) non ha stanze corrispondenti ai criteri impostati.")
    else:
        metrics_c1 = [df_c1['price'].min(), df_c1['price'].mean(), df_c1['price'].median(), df_c1['price'].max()]
        metrics_c2 = [df_c2['price'].min(), df_c2['price'].mean(), df_c2['price'].median(), df_c2['price'].max()]
        
        categorie = ['Minimo', 'Medio', 'Mediano', 'Massimo']
        
        fig_compare = go.Figure()
        
        # Città 1: Colore invertito -> ora è Viola Chiaro
        fig_compare.add_trace(go.Bar(
            x=categorie, y=metrics_c1, name=c1,
            marker_color='#CE93D8',
            text=[f"€{v:.1f}" for v in metrics_c1], textposition='auto'
        ))
        
        # Città 2: Colore invertito -> ora è Viola Scuro
        fig_compare.add_trace(go.Bar(
            x=categorie, y=metrics_c2, name=c2,
            marker_color='#4A148C',
            text=[f"€{v:.1f}" for v in metrics_c2], textposition='auto'
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
    st.info("💡 **Vuoi confrontare i prezzi tra due città?** Seleziona una singola città e usa il menu 'Confronta con' oppure inserisci due città nel selettore principale.")