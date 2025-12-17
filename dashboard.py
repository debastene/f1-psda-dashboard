import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ==========================================
# 1. SETTINGS & STYLING
# ==========================================
st.set_page_config(page_title="F1 Data Storytelling", layout="wide", page_icon="🏎️")

st.markdown("""
    <style>
    .main { background-color: #0b0d10; }
    h1, h2, h3 { color: #ff1801 !important; font-family: 'Arial Black'; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #ff1801; }
    .insight-box { 
        background-color: #1f2937; padding: 15px; border-radius: 8px; 
        border-left: 4px solid #10b981; margin-bottom: 20px; font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING & ROBUST CLEANING
# ==========================================
@st.cache_data
def load_and_clean_data():
    folder = 'archive (1)'
    try:
        results = pd.read_csv(f'{folder}/results.csv', encoding='latin1')
        drivers = pd.read_csv(f'{folder}/drivers.csv', encoding='latin1')
        races = pd.read_csv(f'{folder}/races.csv', encoding='latin1')
        status = pd.read_csv(f'{folder}/status.csv', encoding='latin1')
        constructors = pd.read_csv(f'{folder}/constructors.csv', encoding='latin1')
        
        # Bersihkan string "\N" agar tidak error
        for df_temp in [results, races, drivers]:
            df_temp.replace(r'\N', pd.NA, inplace=True)

        df = results.merge(drivers[['driverId', 'forename', 'surname', 'nationality']], on='driverId')
        df = df.merge(races[['raceId', 'year', 'name']], on='raceId')
        df = df.merge(status[['statusId', 'status']], on='statusId')
        df = df.merge(constructors[['constructorId', 'name']], on='constructorId', suffixes=('', '_team'))
        df['full_name'] = df['forename'] + " " + df['surname']
        
        for col in ['points', 'grid', 'positionOrder']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        return df
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        return None

df = load_and_clean_data()

# ==========================================
# 3. DASHBOARD RENDER
# ==========================================
if df is not None:
    st.markdown("<h1 style='text-align: center;'>🏎️ F1 STRATEGIC DATA INSIGHTS</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #9ca3af;'>Menganalisis Sejarah, Performa Tim, dan Faktor Kegagalan</p>", unsafe_allow_html=True)

    # --- SIDEBAR FILTER ---
    st.sidebar.title("🎮 Interactive Control")
    year_range = st.sidebar.slider("Pilih Era Balapan", 1950, 2023, (2000, 2023))
    f_df = df[(df['year'] >= year_range[0]) & (df['year'] <= year_range[1])]

    # --- ROW 1: TOP HIGHLIGHTS ---
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Grand Prix", f_df['raceId'].nunique())
    with c2: st.metric("Pembalap Berpartisipasi", f_df['driverId'].nunique())
    with c3: st.metric("Konstruktor (Tim)", f_df['constructorId'].nunique())
    with c4: 
        top_driver = f_df[f_df['positionOrder'] == 1]['full_name'].value_counts().idxmax()
        st.metric("Pemenang Terbanyak", top_driver.split()[-1])

    st.divider()

    # --- ROW 2: DOMINANCE & GEOGRAPHY ---
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("🏆 Dominasi Konstruktor (Top 10)")
        team_pts = f_df.groupby('name_team')['points'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_team = px.bar(team_pts, x='points', y='name_team', orientation='h', 
                          color='points', color_continuous_scale='Reds', text_auto='.2s')
        fig_team.update_layout(template="plotly_dark", yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_team, use_container_width=True)
        
        st.markdown(f"""<div class='insight-box'>
        <b>Interpretasi:</b> Tim <b>{team_pts.iloc[0]['name_team']}</b> memimpin perolehan poin di era {year_range[0]}-{year_range[1]}. 
        Hal ini menunjukkan kesenjangan finansial dan teknologi yang signifikan antar tim papan atas dan papan bawah.
        </div>""", unsafe_allow_html=True)

    with col_b:
        st.subheader("🌍 Peta Kekuatan Negara")
        nat_data = f_df.drop_duplicates('driverId')['nationality'].value_counts().head(8).reset_index()
        fig_pie = px.pie(nat_data, values='count', names='nationality', hole=0.5,
                         color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_pie.update_layout(template="plotly_dark")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        st.markdown(f"""<div class='insight-box'>
        <b>Interpretasi:</b> Kewarganegaraan <b>{nat_data.iloc[0]['nationality']}</b> masih mendominasi grid. 
        Ini mencerminkan infrastruktur akademi balap yang lebih maju di wilayah tersebut dibandingkan negara lain.
        </div>""", unsafe_allow_html=True)

    # --- ROW 3: COMPETITION TREND ---
    st.divider()
    st.subheader("📈 Tren Intensitas Kompetisi (Rata-rata Poin per Musim)")
    yearly_avg = f_df.groupby('year')['points'].mean().reset_index()
    fig_line = px.line(yearly_avg, x='year', y='points', markers=True)
    fig_line.update_traces(line_color='#ff1801', line_width=3)
    fig_line.update_layout(template="plotly_dark", hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)
    
    st.markdown("""<div class='insight-box'>
    <b>Interpretasi:</b> Lonjakan rata-rata poin biasanya terjadi saat FIA mengubah regulasi sistem poin. 
    Tren yang stabil menunjukkan dominasi tim tertentu, sedangkan fluktuasi tajam menandakan musim yang kompetitif.
    </div>""", unsafe_allow_html=True)

    # --- ROW 4: RELIABILITY ---
    st.divider()
    st.subheader("🛠️ Analisis Keandalan Mesin & Insiden")
    dnf_data = f_df[~f_df['status'].str.contains('Finished|\+')]['status'].value_counts().head(10).reset_index()
    fig_dnf = px.treemap(dnf_data, path=['status'], values='count', 
                         color='count', color_continuous_scale='OrRd')
    fig_dnf.update_layout(template="plotly_dark")
    st.plotly_chart(fig_dnf, use_container_width=True)
    
    st.markdown(f"""<div class='insight-box'>
    <b>Interpretasi:</b> Masalah <b>{dnf_data.iloc[0]['status']}</b> merupakan penyebab kegagalan teknis tertinggi. 
    Data ini krusial bagi tim untuk menentukan area R&D (Research & Development) guna meningkatkan <i>reliability</i> mobil.
    </div>""", unsafe_allow_html=True)

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Data Source: Ergast F1 Database")
st.sidebar.write("✅ Filter Aktif: Era " + str(year_range[0]) + " - " + str(year_range[1]))
