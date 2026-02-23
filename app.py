import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
import streamlit.components.v1 as components
import time

# --- 1. KONFIGURASI HALAMAN (HARUS PALING ATAS) ---
st.set_page_config(
    page_title="Sistem Keasistenan IV - Ombudsman RI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INISIALISASI SESSION STATE UNTUK LOGIN & DAFTAR ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# Database akun sementara (bisa ditambah lewat menu Daftar)
if 'users_db' not in st.session_state:
    st.session_state['users_db'] = {
        "admin": "ombudsman123",
        "pimpinan": "rahasia123"
    }

# --- 3. CUSTOM CSS GLOBAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Background Utama Dashboard */
    .stApp {
        background-color: #f4f7f6;
    }

    /* --- STYLING KHUSUS HALAMAN AUTENTIKASI --- */
    .auth-title {
        text-align: center;
        color: #003366;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 5px;
        padding-top: 20px;
    }
    .auth-subtitle {
        text-align: center;
        color: #666;
        font-size: 1rem;
        margin-bottom: 30px;
    }

    /* Customisasi Tab Streamlit agar terlihat seperti tombol premium */
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 10px;
        justify-content: center;
    }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: #e3edf7;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        color: #003366;
        font-weight: 600;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: #004a99;
        color: white !important;
    }

    /* --- STYLING DASHBOARD --- */
    .header-container {
        background: linear-gradient(135deg, #003366 0%, #004a99 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,74,153,0.2);
    }
    .header-title { font-size: 2.2rem; font-weight: 700; margin: 0; }
    .header-subtitle { font-size: 1rem; opacity: 0.9; margin-top: 5px; }

    .card-container {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        border-top: 4px solid transparent;
    }
    .card-blue { border-top-color: #004a99; }
    .card-orange { border-top-color: #e65100; }

    [data-testid="stMetric"] {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        text-align: center;
    }

    /* --- MODE CETAK (PRINT) --- */
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        [data-testid="stSidebar"], [data-testid="stHeader"], footer, [data-testid="stToolbar"] { display: none !important; }
        html, body, .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            overflow: visible !important; height: auto !important; min-height: 0 !important; max-height: none !important;
            position: relative !important; display: block !important; background-color: white !important; width: 100% !important;
        }
        .card-container, [data-testid="stMetric"], .js-plotly-plot, .stDataFrame { page-break-inside: avoid !important; break-inside: avoid !important; }
        .js-plotly-plot .plotly { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNGSI HALAMAN LOGIN & DAFTAR ---

def auth_page():
    # Sembunyikan sidebar di halaman awal
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    
    # Membuat kolom agar form berada tepat di tengah layar
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 class='auth-title'>⚖️ Portal Keasistenan IV</h2>", unsafe_allow_html=True)
        st.markdown("<p class='auth-subtitle'>Sistem Monitoring Pengaduan Ombudsman RI</p>", unsafe_allow_html=True)
        
        # Membuat kotak dengan container bawaan Streamlit agar rapi
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔑 Masuk (Login)", "📝 Daftar Baru"])
            
            # --- TAB 1: LOGIN ---
            with tab1:
                st.markdown("#### Silakan Masuk")
                username_login = st.text_input("Username", key="log_user", placeholder="Masukkan username...")
                password_login = st.text_input("Password", type="password", key="log_pass", placeholder="Masukkan password...")
                
                if st.button("Masuk", type="primary", use_container_width=True):
                    if username_login in st.session_state['users_db'] and st.session_state['users_db'][username_login] == password_login:
                        st.success("✅ Login berhasil! Memuat dashboard...")
                        time.sleep(1)
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else:
                        st.error("❌ Username atau password salah!")

            # --- TAB 2: DAFTAR AKUN BARU ---
            with tab2:
                st.markdown("#### Buat Akun Baru")
                new_username = st.text_input("Buat Username", key="reg_user", placeholder="Minimal 4 karakter")
                new_password = st.text_input("Buat Password", type="password", key="reg_pass", placeholder="Minimal 4 karakter")
                confirm_password = st.text_input("Konfirmasi Password", type="password", key="reg_pass_conf")
                
                if st.button("Daftar Akun", type="primary", use_container_width=True):
                    if not new_username or not new_password:
                        st.warning("⚠️ Semua kolom harus diisi!")
                    elif len(new_username) < 4 or len(new_password) < 4:
                        st.warning("⚠️ Username dan Password minimal 4 karakter.")
                    elif new_username in st.session_state['users_db']:
                        st.error("❌ Username sudah terdaftar! Pilih username lain.")
                    elif new_password != confirm_password:
                        st.error("❌ Password dan Konfirmasi Password tidak sama!")
                    else:
                        # Menyimpan akun baru ke database sementara
                        st.session_state['users_db'][new_username] = new_password
                        st.success("🎉 Akun berhasil dibuat! Silakan pindah ke tab 'Masuk (Login)'.")
                        st.balloons() # Efek animasi balon!

# --- 5. FUNGSI DASHBOARD UTAMA ---

def show_dashboard():
    def get_coordinates(df):
        geolocator = Nominatim(user_agent="ombudsman_dash_v4")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        loc_col = 'Lokasi LM' if 'Lokasi LM' in df.columns else 'Terlapor'
        unique_locations = df[loc_col].dropna().unique()
        location_map = {}
        progress_bar = st.progress(0, text="Sedang memetakan lokasi...")
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
            st.error(f"Gagal memuat data: {e}")
            st.stop()

    data, has_date = load_data()

    if not data.empty and has_date:
        today = datetime.now()
        data['Hari_Berjalan'] = (today - data['Tanggal Laporan']).dt.days
        mangkrak_mask = (data['Hari_Berjalan'] > 30) & (~data['Status'].str.contains('Selesai|Tutup', case=False, na=False))
        total_mangkrak = len(data[mangkrak_mask])
    else:
        total_mangkrak = 0

    # SIDEBAR
    with st.sidebar:
        try: st.image("ombudsman logo.png", width=160)
        except: st.markdown("**(Logo Ombudsman)**")
        
        st.markdown("### 🔎 Filter Data")
        search_query = st.text_input("Pencarian Cepat:", placeholder="Nama/No/Wilayah...")
        st.divider()

        start_date, end_date = None, None
        if has_date:
            min_date, max_date = data['Tanggal Laporan'].min().date(), data['Tanggal Laporan'].max().date()
            date_range = st.date_input("📅 Periode Laporan", value=[min_date, max_date], min_value=min_date, max_value=max_date)
            if isinstance(date_range, list) and len(date_range) == 2:
                start_date, end_date = date_range
                data_filtered = data[(data['Tanggal Laporan'].dt.date >= start_date) & (data['Tanggal Laporan'].dt.date <= end_date)]
            else: data_filtered = data
        else: data_filtered = data

        if search_query:
            mask = data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            data_filtered = data_filtered[mask]

        if 'Asisten' in data.columns:
            sel_asisten = st.selectbox("👤 Asisten:", ["Semua"] + sorted(data_filtered["Asisten"].dropna().unique().tolist()))
            if sel_asisten != "Semua": data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]

        if 'Lokasi LM' in data.columns:
            sel_wilayah = st.selectbox("📍 Wilayah LM:", ["Semua"] + sorted(data_filtered["Lokasi LM"].dropna().unique().tolist()))
            if sel_wilayah != "Semua": data_filtered = data_filtered[data_filtered["Lokasi LM"] == sel_wilayah]
                
        if 'Status' in data.columns:
            sel_status = st.multiselect("📊 Status:", ["Semua"] + sorted(data_filtered["Status"].dropna().unique().tolist()), default="Semua")
            if "Semua" not in sel_status and sel_status: data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

        st.markdown("---")
        if st.button("🖨️ Cetak PDF", type="primary", use_container_width=True):
            st.components.v1.html("""<script>setTimeout(function() {window.parent.print();}, 100);</script>""", height=0, width=0)
        
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.caption("© 2026 Keasistenan Utama IV")

    # MAIN CONTENT
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">⚖️ Dashboard Monitoring Keasistenan Utama IV</h1>
        <p class="header-subtitle">Sistem Informasi Pengaduan Masyarakat Bidang Pertanahan</p>
    </div>
    """, unsafe_allow_html=True)

    if not data_filtered.empty:
        total = len(data_filtered)
        selesai = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)]) if 'Status' in data_filtered.columns else 0
        proses = total - selesai
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Laporan Masuk", f"{total}")
        col2.metric("Laporan Selesai", f"{selesai}", f"{(selesai/total*100 if total>0 else 0):.1f}%")
        col3.metric("Dalam Proses", f"{proses}", delta_color="inverse")
        col4.metric("Target Tahunan", "10") 

        st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
        if has_date:
            st.markdown("#### 📉 Tren Laporan Masuk (Bulanan)")
            trend_data = data_filtered.set_index('Tanggal Laporan').resample('ME').size().reset_index(name='Jumlah Laporan')
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Tanggal Laporan', y='Jumlah Laporan', markers=True, line_shape='spline')
                fig_trend.update_traces(line_color='#e65100', line_width=3)
                fig_trend.update_layout(plot_bgcolor='white', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            c_map, c_sum = st.columns([7, 3])
            with c_sum:
                st.markdown('<div class="card-container card-orange"><h4>📝 Ringkasan Eksekutif</h4>', unsafe_allow_html=True)
                top_wilayah = data_filtered['Lokasi LM'].mode()[0] if 'Lokasi LM' in data_filtered.columns else "-"
                rate = (selesai / total * 100) if total > 0 else 0
                evaluasi = "Sangat Baik" if rate > 80 else "Cukup Baik" if rate > 50 else "Perlu Atensi"
                color_eval = "#2e7d32" if rate > 80 else "#ef6c00" if rate > 50 else "#c62828"
                st.markdown(f"""
                <div style="font-size: 0.95rem; line-height: 1.6;">
                <b>Performa:</b> <span style="color:{color_eval}; font-weight:bold; background-color:#f5f5f5; padding:2px 8px; border-radius:4px;">{evaluasi}</span><br><br>
                Wilayah terbanyak: <b>{top_wilayah}</b>.<br><br>
                Prioritas: <b>{proses}</b> laporan berjalan, <b>{total_mangkrak}</b> kasus lewat batas SLA.
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with c_map:
                st.markdown('<div class="card-container card-blue"><h4>📍 Peta Distribusi</h4>', unsafe_allow_html=True)
                if 'lat' in data_filtered.columns:
                    fig_map = px.scatter_mapbox(
                        data_filtered, lat='lat', lon='lon', color='Status', size_max=15, zoom=3.5,
                        hover_name='Lokasi LM' if 'Lokasi LM' in data_filtered.columns else None, mapbox_style="carto-positron"
                    )
                    fig_map.update_layout(height=400, margin={"r":0,"t":0,"l":0,"b":0}, dragmode="pan")
                    st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True})
                st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📚 Buka Detail Data Tabel", expanded=True):
            kolom_dihapus = ['lat', 'lon', 'Hari_Berjalan', 'ni', 'Ni', 'NI', 'maladministrasi', 'Maladministrasi', 'Jenis Maladministrasi']
            view_df = data_filtered.drop(columns=kolom_dihapus, errors='ignore')
            st.dataframe(view_df, use_container_width=True)
            csv = view_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh CSV", data=csv, file_name=f'Laporan_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
    else:
        st.warning("⚠️ Data tidak ditemukan.")


# --- 6. ROUTING UTAMA ---
if not st.session_state['logged_in']:
    auth_page()
else:
    show_dashboard()