import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
import time

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Executive Dashboard - Keasistenan IV",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'users_db' not in st.session_state:
    st.session_state['users_db'] = {"admin": "ombudsman123", "pimpinan": "rahasia123"}

# --- 3. CUSTOM CSS GLOBAL (TEMA EXECUTIVE PREMIUM) ---
st.markdown("""
    <style>
    /* Menggunakan font premium bergaya startup */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #0f172a; /* Warna teks Slate 900 */
    }

    /* Background Aplikasi Abu-abu Super Muda (Kesan Clean/Apple) */
    .stApp { background-color: #f8fafc; }
    
    /* Sidebar Premium */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid rgba(226, 232, 240, 0.8);
    }

    /* --- STYLING AUTENTIKASI --- */
    .auth-title {
        text-align: center; color: #0f172a; font-weight: 800; letter-spacing: -1px;
        font-size: 2.8rem; margin-bottom: 5px; padding-top: 20px;
    }
    .auth-subtitle {
        text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 30px; font-weight: 500;
    }
    
    /* Tab Menu Premium */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 8px; justify-content: center; }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: transparent; border-radius: 12px;
        padding: 12px 24px; color: #64748b; font-weight: 600; border: none;
        transition: all 0.2s ease;
    }
    [data-testid="stTabs"] [data-baseweb="tab"]:hover { background-color: #f1f5f9; }
    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: #0f172a !important; color: white !important;
        box-shadow: 0 4px 10px rgba(15, 23, 42, 0.2);
    }

    /* --- STYLING DASHBOARD PREMIUM --- */
    /* Header Dark Elegan */
    .header-container {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 2.5rem 3rem; border-radius: 24px; color: white;
        margin-bottom: 2.5rem; 
        box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 10px 10px -5px rgba(15, 23, 42, 0.04);
        position: relative; overflow: hidden;
    }
    .header-title { font-size: 2.4rem; font-weight: 800; margin: 0; color: #ffffff; letter-spacing: -1px;}
    .header-subtitle { font-size: 1.1rem; color: #94a3b8; margin-top: 8px; font-weight: 500; }

    /* Kartu (Card) Melayang dengan Soft Shadow */
    .card-container {
        background-color: #ffffff; padding: 24px; border-radius: 20px;
        margin-bottom: 24px; border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s;
    }
    .card-container:hover { 
        transform: translateY(-4px); 
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02); 
    }
    
    /* Judul dalam Kartu */
    .card-container h4 { color: #0f172a; font-weight: 700; font-size: 1.2rem; letter-spacing: -0.5px; margin-bottom: 20px; }

    /* Metrik (Angka) Modern */
    [data-testid="stMetric"] {
        background-color: #ffffff; padding: 20px; border-radius: 16px;
        border: 1px solid rgba(226, 232, 240, 0.8);
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        transition: all 0.3s ease;
    }
    [data-testid="stMetric"]:hover { border-color: #cbd5e1; transform: translateY(-2px); }
    [data-testid="stMetricLabel"] { color: #64748b; font-size: 0.95rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #0f172a; font-weight: 800; font-size: 2.4rem; letter-spacing: -1px; }
    
    /* Tombol Premium */
    .stButton > button { 
        border-radius: 12px !important; font-weight: 600 !important; 
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"] { background-color: #0f172a !important; color: white !important; }
    .stButton > button[kind="primary"]:hover { background-color: #1e293b !important; transform: scale(1.02); }

    /* Expander Table */
    .streamlit-expanderHeader { background-color: #f8fafc !important; border-radius: 12px; font-weight: 600 !important; color: #0f172a !important; border: 1px solid rgba(226, 232, 240, 0.8) !important;}
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI HALAMAN LOGIN & DAFTAR ---
def auth_page():
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 class='auth-title'>Portal Keasistenan IV</h2>", unsafe_allow_html=True)
        st.markdown("<p class='auth-subtitle'>Sistem Terpadu Monitoring Pengaduan Ombudsman RI</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔒 Secure Login", "📝 Registrasi"])
            
            with tab1:
                st.markdown("<br>", unsafe_allow_html=True)
                username_login = st.text_input("Username", key="log_user")
                password_login = st.text_input("Password", type="password", key="log_pass")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Masuk ke Dashboard", type="primary", use_container_width=True):
                    if username_login in st.session_state['users_db'] and st.session_state['users_db'][username_login] == password_login:
                        st.success("✅ Autentikasi berhasil. Memuat antarmuka...")
                        time.sleep(1)
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("❌ Akses ditolak. Kredensial tidak valid.")

            with tab2:
                st.markdown("<br>", unsafe_allow_html=True)
                new_username = st.text_input("Username Baru", key="reg_user")
                new_password = st.text_input("Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Konfirmasi Password", type="password", key="reg_pass_conf")
                st.markdown("<br>", unsafe_allow_html=True)
                
                if st.button("Daftar Akun", type="primary", use_container_width=True):
                    if not new_username or not new_password:
                        st.warning("⚠️ Mohon lengkapi semua kolom.")
                    elif len(new_username) < 4 or len(new_password) < 4:
                        st.warning("⚠️ Kredensial minimal 4 karakter.")
                    elif new_username in st.session_state['users_db']:
                        st.error("❌ Username sudah digunakan.")
                    elif new_password != confirm_password:
                        st.error("❌ Konfirmasi password tidak cocok.")
                    else:
                        st.session_state['users_db'][new_username] = new_password
                        st.success("🎉 Registrasi berhasil! Silakan login.")

# --- 5. FUNGSI DASHBOARD UTAMA ---
def show_dashboard():
    # --- FUNGSI LOAD DATA (DIAMANKAN) ---
    def get_coordinates(df):
        geolocator = Nominatim(user_agent="ombudsman_premium_dash")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        loc_col = 'Lokasi LM' if 'Lokasi LM' in df.columns else 'Terlapor'
        unique_locations = df[loc_col].dropna().unique()
        location_map = {}
        progress_bar = st.progress(0, text="Menyiapkan data geospasial...")
        for i, loc in enumerate(unique_locations):
            try:
                location = geocode(f"{loc}, Indonesia")
                location_map[loc] = [location.latitude, location.longitude] if location else [-6.2088, 106.8456]
            except:
                location_map[loc] = [-6.2088, 106.8456]
            progress_bar.progress((i + 1) / len(unique_locations))
        progress_bar.empty()
        df['lat'] = df[loc_col].map(lambda x: location_map.get(x, [-6.2088, 106.8456])[0])
        df['lon'] = df[loc_col].map(lambda x: location_map.get(x, [-6.2088, 106.8456])[1])
        return df

    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("data_tanah1.xlsx")
            date_col_found = False
            for col in df.columns:
                if any(x in col.lower() for x in ['tanggal', 'tgl', 'date']):
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df.rename(columns={col: 'Tanggal Laporan'}, inplace=True)
                    date_col_found = True
                    break
            if ('Terlapor' in df.columns or 'Lokasi LM' in df.columns) and ('lat' not in df.columns):
                df = get_coordinates(df)
            return df, date_col_found
        except Exception as e:
            st.error(f"Sistem gagal memuat data referensi. Pastikan file tersedia.")
            st.stop()

    data, has_date = load_data()

    if not data.empty and has_date:
        today = datetime.now()
        data['Hari_Berjalan'] = (today - data['Tanggal Laporan']).dt.days
        if 'Status' in data.columns:
            mangkrak_mask = (data['Hari_Berjalan'] > 30) & (~data['Status'].str.contains('Selesai|Tutup', case=False, na=False))
            total_mangkrak = len(data[mangkrak_mask])
        else:
            total_mangkrak = len(data[data['Hari_Berjalan'] > 30])
    else:
        total_mangkrak = 0

    # --- SIDEBAR PREMIUM ---
    with st.sidebar:
        try: 
            st.image("ombudsman logo.png", width=160)
        except: 
            st.markdown("<h2 style='color:#0f172a; font-weight:800; letter-spacing:-1px;'>⚖️ Ombudsman</h2>", unsafe_allow_html=True)
        
        st.markdown("<br><b>Pencarian Spesifik</b>", unsafe_allow_html=True)
        search_query = st.text_input("Cari Data:", placeholder="Nama / Wilayah...", label_visibility="collapsed")
        
        st.markdown("<br><b>Filter Lanjutan</b>", unsafe_allow_html=True)
        start_date, end_date = None, None
        data_filtered = data.copy()

        if has_date:
            min_date, max_date = data['Tanggal Laporan'].min().date(), data['Tanggal Laporan'].max().date()
            if min_date != max_date:
                date_range = st.date_input("Periode Laporan", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    data_filtered = data_filtered[(data_filtered['Tanggal Laporan'].dt.date >= start_date) & (data_filtered['Tanggal Laporan'].dt.date <= end_date)]

        if search_query:
            mask = data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            data_filtered = data_filtered[mask]

        if 'Asisten' in data.columns:
            sel_asisten = st.selectbox("Penanggung Jawab (Asisten):", ["Semua Asisten"] + sorted(data_filtered["Asisten"].dropna().unique().tolist()))
            if sel_asisten != "Semua Asisten": data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]

        if 'Lokasi LM' in data.columns:
            sel_wilayah = st.selectbox("Wilayah Administratif:", ["Semua Wilayah"] + sorted(data_filtered["Lokasi LM"].dropna().unique().tolist()))
            if sel_wilayah != "Semua Wilayah": data_filtered = data_filtered[data_filtered["Lokasi LM"] == sel_wilayah]
                
        if 'Status' in data.columns:
            sel_status = st.multiselect("Status Penyelesaian:", ["Semua Status"] + sorted(data_filtered["Status"].dropna().unique().tolist()), default="Semua Status")
            if "Semua Status" not in sel_status and sel_status: 
                data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

        st.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("🖨️ Ekspor Laporan PDF", use_container_width=True):
            st.components.v1.html("""<script>setTimeout(function() {window.parent.print();}, 100);</script>""", height=0, width=0)
        
        if st.button("🚪 Akhiri Sesi (Logout)", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:20px;'>© 2026 Keasistenan Utama IV<br>Executive Dashboard v2.0</div>", unsafe_allow_html=True)

    # --- MAIN CONTENT DASHBOARD ---
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">Executive Command Center</h1>
        <p class="header-subtitle">Analisis Data dan Monitoring Resolusi Pengaduan Masyarakat Bidang Pertanahan</p>
    </div>
    """, unsafe_allow_html=True)

    filter_info = []
    if start_date and end_date: filter_info.append(f"<b>Periode:</b> {start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}")
    if search_query: filter_info.append(f"<b>Pencarian:</b> '{search_query}'")
    if filter_info:
        st.markdown(f"<div style='background-color: white; border: 1px solid #e2e8f0; padding:12px 20px; border-radius:12px; margin-bottom:24px; color:#475569; font-size:0.95rem; box-shadow: 0 1px 2px rgba(0,0,0,0.02);'>📌 Filter Aktif: {' &nbsp;|&nbsp; '.join(filter_info)}</div>", unsafe_allow_html=True)

    if not data_filtered.empty:
        total = len(data_filtered)
        selesai = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)]) if 'Status' in data_filtered.columns else 0
        proses = total - selesai
        
        # --- TOP METRICS ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Kasus", f"{total}", "Laporan Masuk")
        col2.metric("Tingkat Penyelesaian", f"{(selesai/total*100 if total>0 else 0):.1f}%", f"{selesai} Selesai")
        col3.metric("Tahap Proses", f"{proses}", "Kasus Berjalan", delta_color="inverse")
        col4.metric("Melewati SLA (>30 Hari)", f"{total_mangkrak}", "Kasus Prioritas", delta_color="inverse") 

        st.markdown('<br>', unsafe_allow_html=True)

        # --- GRAFIK TREN ---
        st.markdown('<div class="card-container"><h4>📈 Analisis Tren Laporan</h4>', unsafe_allow_html=True)
        if has_date:
            trend_data = data_filtered.set_index('Tanggal Laporan').resample('ME').size().reset_index(name='Jumlah')
            if not trend_data.empty:
                fig_trend = px.area(trend_data, x='Tanggal Laporan', y='Jumlah', line_shape='spline')
                fig_trend.update_traces(line_color='#0f172a', fillcolor='rgba(15, 23, 42, 0.1)', line_width=3, marker=dict(size=8, color='#3b82f6'))
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, xaxis_title=None, yaxis_title=None, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig_trend, use_container_width=True)
        elif 'Tahun' in data_filtered.columns:
            trend_data = data_filtered.groupby('Tahun').size().reset_index(name='Jumlah')
            if not trend_data.empty:
                fig_trend = px.bar(trend_data, x='Tahun', y='Jumlah')
                fig_trend.update_traces(marker_color='#0f172a')
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=320, xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- INSIGHT & PETA ---
        c_map, c_sum = st.columns([6.5, 3.5])
        with c_sum:
            st.markdown('<div class="card-container" style="height: 100%;"><h4>📋 Executive Brief</h4>', unsafe_allow_html=True)
            top_wilayah = data_filtered['Lokasi LM'].mode()[0] if 'Lokasi LM' in data_filtered.columns else "N/A"
            rate = (selesai / total * 100) if total > 0 else 0
            
            # Styling Indikator Status
            if rate > 80:
                bg_color, text_color, status_text = "#dcfce7", "#166534", "Sangat Sehat"
            elif rate > 50:
                bg_color, text_color, status_text = "#fef9c3", "#854d0e", "Dalam Kendali"
            else:
                bg_color, text_color, status_text = "#fee2e2", "#991b1b", "Perlu Intervensi"

            st.markdown(f"""
            <div style="font-size: 1rem; color: #475569; line-height: 1.8;">
                <div style="margin-bottom: 20px;">
                    <span style="display:block; font-size:0.9rem; color:#94a3b8; font-weight:600;">STATUS KINERJA</span>
                    <span style="background-color: {bg_color}; color: {text_color}; padding: 6px 16px; border-radius: 20px; font-weight: 700; font-size: 0.95rem;">{status_text}</span>
                </div>
                <div style="margin-bottom: 20px;">
                    <span style="display:block; font-size:0.9rem; color:#94a3b8; font-weight:600;">ZONA TERPADAT</span>
                    <strong style="color: #0f172a; font-size: 1.2rem;">{top_wilayah}</strong>
                </div>
                <div>
                    <span style="display:block; font-size:0.9rem; color:#94a3b8; font-weight:600;">BACKLOG SLA</span>
                    <strong style="color: #b91c1c; font-size: 1.2rem;">{total_mangkrak}</strong> laporan memerlukan atensi pimpinan.
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with c_map:
            st.markdown('<div class="card-container"><h4>🗺️ Pemetaan Geospasial</h4>', unsafe_allow_html=True)
            if 'lat' in data_filtered.columns:
                color_col = 'Status' if 'Status' in data_filtered.columns else None
                hover_col = 'Lokasi LM' if 'Lokasi LM' in data_filtered.columns else None
                
                # Menggunakan peta bergaya minimalis terang (carto-positron)
                fig_map = px.scatter_mapbox(
                    data_filtered, lat='lat', lon='lon', color=color_col, size_max=15, zoom=3.5,
                    hover_name=hover_col, mapbox_style="carto-positron" 
                )
                fig_map.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=380, margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True})
            st.markdown('</div>', unsafe_allow_html=True)

        # --- GRAFIK BAWAH ---
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        row_chart1, row_chart2 = st.columns([5, 5])
        
        with row_chart1:
            st.markdown("<h4>📊 Distribusi per Wilayah</h4>", unsafe_allow_html=True)
            if 'Lokasi LM' in data_filtered.columns:
                top_chart = data_filtered['Lokasi LM'].value_counts().nlargest(7).reset_index()
                top_chart.columns = ['Wilayah', 'Jumlah']
                fig_bar = px.bar(top_chart, x='Jumlah', y='Wilayah', orientation='h', text='Jumlah')
                fig_bar.update_traces(marker_color='#cbd5e1', textposition='outside', textfont=dict(color='#0f172a', weight='bold'))
                fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title=None, yaxis=dict(autorange="reversed"), height=350, margin=dict(l=0, r=20, t=10, b=0))
                # Highlight bar pertama
                if len(fig_bar.data) > 0:
                    colors = ['#0f172a'] + ['#cbd5e1'] * (len(top_chart) - 1)
                    fig_bar.update_traces(marker_color=colors)
                st.plotly_chart(fig_bar, use_container_width=True)

        with row_chart2:
            st.markdown("<h4>🎯 Realisasi Target Bulanan/Tahunan</h4>", unsafe_allow_html=True)
            if 'Tahun' in data_filtered.columns or has_date:
                temp_df = data_filtered.copy()
                if 'Tahun' not in temp_df.columns:
                    temp_df['Tahun'] = temp_df['Tanggal Laporan'].dt.year
                target_df = temp_df.groupby('Tahun').size().reset_index(name='Realisasi')
                target_df['Target'] = 10 
                target_df['Tahun'] = target_df['Tahun'].astype(str)
                fig_target = px.bar(target_df, x='Tahun', y=['Realisasi', 'Target'], barmode='group', color_discrete_map={'Realisasi': '#0f172a', 'Target': '#cbd5e1'})
                fig_target.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, xaxis_title=None, yaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None), margin=dict(l=0, r=0, t=30, b=0))
                st.plotly_chart(fig_target, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- TABEL DATA ---
        with st.expander("📂 Basis Data Resolusi Pengaduan", expanded=False):
            st.markdown('<div style="padding: 10px 0;">', unsafe_allow_html=True)
            kolom_dihapus = ['lat', 'lon', 'Hari_Berjalan', 'ni', 'Ni', 'NI', 'maladministrasi', 'Maladministrasi', 'Jenis Maladministrasi']
            view_df = data_filtered.drop(columns=kolom_dihapus, errors='ignore')
            
            preferred_cols = ['Nomor Arsip', 'Nama Pelapor', 'Lokasi LM', 'Asisten', 'Status', 'Tanggal Laporan', 'Tahun']
            existing_cols = [c for c in preferred_cols if c in view_df.columns]
            other_cols = [c for c in view_df.columns if c not in existing_cols]
            
            st.dataframe(view_df[existing_cols + other_cols], use_container_width=True)
            
            csv = view_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh CSV", data=csv, file_name=f'Data_Ombudsman_Executive_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv', type="primary")
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("ℹ️ Data tidak ditemukan pada kriteria filter ini. Silakan sesuaikan parameter pencarian.")

# --- 6. ROUTING UTAMA ---
if not st.session_state['logged_in']:
    auth_page()
else:
    show_dashboard()