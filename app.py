import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
import streamlit.components.v1 as components
import time
from streamlit_gsheets import GSheetsConnection  # Pastikan ini sudah di-import


# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Keasistenan IV - Ombudsman RI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. INISIALISASI SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'users_db' not in st.session_state:
    # Database sementara (Username: Password)
    st.session_state['users_db'] = {"admin": "ombudsman123", "pimpinan": "rahasia123"}

# --- 3. CUSTOM CSS GLOBAL (TEMA TERANG CLEAN PROFESSIONAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        color: #1f2937; /* Teks gelap lembut */
    }

    /* Background Utama Terang Bersih */
    .stApp { 
        background-color: #f4f7f6; 
    }
    
    /* Sidebar Terang */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* --- STYLING AUTENTIKASI (CLEAN) --- */
    .auth-title {
        text-align: center; color: #003366; font-weight: 800;
        font-size: 2.5rem; margin-bottom: 5px; padding-top: 20px;
    }
    .auth-subtitle {
        text-align: center; color: #6b7280; font-size: 1rem; margin-bottom: 30px;
    }
    
    /* Tab Menu Elegan */
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    [data-testid="stTabs"] [data-baseweb="tab"] {
        background-color: #f3f4f6; border-radius: 8px 8px 0px 0px;
        padding: 10px 20px; color: #4b5563; font-weight: 600;
        border: 1px solid transparent;
    }
    [data-testid="stTabs"] [aria-selected="true"] {
        background-color: #004a99; color: white !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        border: 1px solid #e5e7eb !important; /* Border container login lebih halus */
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05);
        background-color: white;
    }

    /* --- STYLING DASHBOARD PROFESSIONAL --- */
    .header-container {
        background: linear-gradient(135deg, #003366 0%, #004a99 100%);
        padding: 2rem; border-radius: 12px; color: white;
        margin-bottom: 2rem; 
        box-shadow: 0 4px 15px rgba(0,74,153,0.2);
    }
    .header-title { font-size: 2.2rem; font-weight: 800; margin: 0; color: #ffffff;}
    .header-subtitle { font-size: 1rem; color: #e5e7eb; margin-top: 5px; opacity: 0.9; }

    /* Kartu (Card) Putih dengan Bayangan Halus */
    .card-container {
        background-color: #ffffff; padding: 25px; border-radius: 12px;
        margin-bottom: 20px; border: 1px solid #f3f4f6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: all 0.3s ease;
    }
    .card-container:hover { transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08); }
    
    .card-blue { border-top: 4px solid #004a99; }
    .card-blue h4 { color: #004a99; }
    
    .card-orange { border-top: 4px solid #e65100; }
    .card-orange h4 { color: #e65100; }

    /* Metrik (Angka) Bersih */
    [data-testid="stMetric"] {
        background-color: #ffffff; padding: 15px; border-radius: 10px;
        border: 1px solid #e5e7eb;
        text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] { color: #6b7280; font-size: 0.9rem; font-weight: 600; }
    [data-testid="stMetricValue"] { 
        color: #003366; font-weight: 800; font-size: 2.2rem; 
    }
    
    /* Expander Table Header */
    .streamlit-expanderHeader { background-color: #f9fafb !important; color: #1f2937 !important; font-weight: 600; }

    /* --- MODE CETAK (PRINT) --- */
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        [data-testid="stSidebar"], [data-testid="stHeader"], footer, [data-testid="stToolbar"], .stDeployButton { display: none !important; }
        html, body, .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            overflow: visible !important; height: auto !important; position: relative !important; display: block !important; 
            background-color: white !important; color: black !important; width: 100% !important;
        }
        .card-container, [data-testid="stMetric"] { 
            background-color: white !important; border: 1px solid #ccc !important;
            box-shadow: none !important; color: black !important; page-break-inside: avoid !important; 
        }
        .header-container { background: white !important; color: black !important; border-bottom: 2px solid #003366; }
        .header-title, .header-subtitle { color: black !important; }
        .js-plotly-plot .plotly { width: 100% !important; }
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI HALAMAN LOGIN & DAFTAR ---
def auth_page():
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 class='auth-title'>⚖️ Portal Keasistenan IV</h2>", unsafe_allow_html=True)
        st.markdown("<p class='auth-subtitle'>Sistem Monitoring Pengaduan Ombudsman RI</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔑 Masuk (Login)", "📝 Daftar Baru"])
            
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
                        st.session_state['users_db'][new_username] = new_password
                        st.success("🎉 Akun berhasil dibuat! Silakan pindah ke tab 'Masuk (Login)'.")
                        st.balloons()

# --- 5. FUNGSI DASHBOARD UTAMA ---
def show_dashboard():
    def get_coordinates(df):
        geolocator = Nominatim(user_agent="ombudsman_dash_v6_light")
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
    
@st.cache_data(ttl=600)
def load_data():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(ttl=600)
        df = df.dropna(how="all")
        
        date_col_found = False
        for col in df.columns:
            if any(x in col.lower() for x in ['tanggal', 'tgl', 'date']):
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df.rename(columns={col: 'Tanggal Laporan'}, inplace=True)
                date_col_found = True
                break
                
        return df, date_col_found

    except Exception as e:
        st.error(f"❌ Koneksi Database Terputus: {e}")
        return pd.DataFrame(), False

    if not data.empty and has_date:
        today = datetime.now()
        data['Hari_Berjalan'] = (today - data['Tanggal Laporan']).dt.days
        # Pastikan kolom status ada sebelum filter
        if 'Status' in data.columns:
            mangkrak_mask = (data['Hari_Berjalan'] > 30) & (~data['Status'].str.contains('Selesai|Tutup', case=False, na=False))
            total_mangkrak = len(data[mangkrak_mask])
        else:
            total_mangkrak = len(data[data['Hari_Berjalan'] > 30])
    else:
        total_mangkrak = 0

    # SIDEBAR
    with st.sidebar:
        try: 
            st.image("ombudsman logo.png", width=160)
        except: 
            st.markdown("<h2 style='color:#003366;'>⚖️ Ombudsman</h2>", unsafe_allow_html=True)
        
        st.markdown("### 🔎 Pencarian & Filter")
        search_query = st.text_input("Cari Data:", placeholder="Nama/No/Wilayah...")
        st.divider()

        start_date, end_date = None, None
        data_filtered = data.copy()

        with st.sidebar:
    # ... (kode logo dan menu navigasi abang yang lain) ...
    
            st.markdown("---")
        if st.button("🔄 Tarik Data Terbaru", use_container_width=True):
            st.cache_data.clear() # Menghapus cache lama
        st.rerun() # Refresh halaman

        # Perbaikan bug tuple pada date_input
        if has_date:
            min_date, max_date = data['Tanggal Laporan'].min().date(), data['Tanggal Laporan'].max().date()
            if min_date != max_date:
                date_range = st.date_input("📅 Periode Laporan", value=(min_date, max_date), min_value=min_date, max_value=max_date)
                if len(date_range) == 2:
                    start_date, end_date = date_range
                    data_filtered = data_filtered[(data_filtered['Tanggal Laporan'].dt.date >= start_date) & (data_filtered['Tanggal Laporan'].dt.date <= end_date)]

        if search_query:
            mask = data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            data_filtered = data_filtered[mask]

        if 'Asisten' in data.columns:
            asisten_list = ["Semua Asisten"] + sorted(data_filtered["Asisten"].dropna().unique().tolist())
            sel_asisten = st.selectbox("👤 Asisten:", asisten_list)
            if sel_asisten != "Semua Asisten": data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]

        if 'Lokasi LM' in data.columns:
            wilayah_list = ["Semua Wilayah"] + sorted(data_filtered["Lokasi LM"].dropna().unique().tolist())
            sel_wilayah = st.selectbox("📍 Wilayah LM:", wilayah_list)
            if sel_wilayah != "Semua Wilayah": data_filtered = data_filtered[data_filtered["Lokasi LM"] == sel_wilayah]
                
        if 'Status' in data.columns:
            status_list = ["Semua Status"] + sorted(data_filtered["Status"].dropna().unique().tolist())
            sel_status = st.multiselect("📊 Status:", status_list, default="Semua Status")
            if "Semua Status" not in sel_status and sel_status: 
                data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

        st.markdown("---")
        if st.button("🖨️ Cetak PDF", type="primary", use_container_width=True):
            st.components.v1.html("""<script>setTimeout(function() {window.parent.print();}, 100);</script>""", height=0, width=0)
        
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.caption("© 2026 Keasistenan Utama IV")

    # MAIN CONTENT DASHBOARD
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">⚖️ Dashboard Monitoring Keasistenan Utama IV</h1>
        <p class="header-subtitle">Monitoring & Analisis Pengaduan Masyarakat Bidang Pertanahan</p>
    </div>
    """, unsafe_allow_html=True)

    filter_info = []
    if start_date and end_date: filter_info.append(f"Periode: <b style='color:#004a99;'>{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</b>")
    if search_query: filter_info.append(f"Kata Kunci: <b style='color:#004a99;'>'{search_query}'</b>")
    if filter_info:
        st.markdown(f"<div style='background-color:#e3edf7; border: 1px solid #d1e5f7; padding:10px; border-radius:8px; margin-bottom:20px; color:#003366;'>ℹ️ Filter Aktif: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

    if not data_filtered.empty:
        total = len(data_filtered)
        selesai = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)]) if 'Status' in data_filtered.columns else 0
        proses = total - selesai
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Laporan", f"{total}", delta="Kasus Masuk")
        col2.metric("Selesai", f"{selesai}", f"{(selesai/total*100 if total>0 else 0):.1f}% Rate")
        col3.metric("Dalam Proses", f"{proses}", delta_color="inverse")
        col4.metric("🎯 Target", "10", delta="Tahunan") 

        st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
        if has_date:
            st.markdown("#### 📉 Tren Laporan Masuk (Bulanan)")
            trend_data = data_filtered.set_index('Tanggal Laporan').resample('ME').size().reset_index(name='Jumlah Laporan')
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Tanggal Laporan', y='Jumlah Laporan', markers=True, line_shape='spline')
                fig_trend.update_traces(line_color='#004a99', line_width=3, marker=dict(size=8, color='#e65100'))
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_trend, use_container_width=True)
        elif 'Tahun' in data_filtered.columns:
            st.markdown("#### 📉 Tren Laporan Masuk (Tahunan)")
            trend_data = data_filtered.groupby('Tahun').size().reset_index(name='Jumlah Laporan')
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Tahun', y='Jumlah Laporan', markers=True)
                fig_trend.update_xaxes(type='category')
                fig_trend.update_traces(line_color='#004a99', line_width=3, marker=dict(size=8, color='#e65100'))
                fig_trend.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.container():
            c_map, c_sum = st.columns([7, 3])
            with c_sum:
                st.markdown('<div class="card-container card-orange"><h4>📝 Ringkasan Eksekutif</h4>', unsafe_allow_html=True)
                top_wilayah = data_filtered['Lokasi LM'].mode()[0] if 'Lokasi LM' in data_filtered.columns else "-"
                rate = (selesai / total * 100) if total > 0 else 0
                evaluasi = "Sangat Baik" if rate > 80 else "Cukup Baik" if rate > 50 else "Perlu Atensi"
                color_eval = "#059669" if rate > 80 else "#d97706" if rate > 50 else "#dc2626" 
                st.markdown(f"""
                <div style="font-size: 0.95rem; line-height: 1.6; color: #374151;">
                <b>Performa:</b> <span style="color:{color_eval}; font-weight:bold; background-color:#f3f4f6; padding:2px 8px; border-radius:4px; border: 1px solid {color_eval};">{evaluasi}</span><br><br>
                Wilayah terbanyak: <b style="color:#e65100;">{top_wilayah}</b>.<br><br>
                Prioritas: <b style="color:#004a99;">{proses}</b> laporan berjalan, <b style="color:#dc2626;">{total_mangkrak}</b> kasus lewat SLA.
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
            with c_map:
                st.markdown('<div class="card-container card-blue"><h4>📍 Peta Distribusi</h4>', unsafe_allow_html=True)
                if 'lat' in data_filtered.columns:
                    # Perbaikan: Cek kolom status agar tidak crash
                    color_col = 'Status' if 'Status' in data_filtered.columns else None
                    hover_col = 'Lokasi LM' if 'Lokasi LM' in data_filtered.columns else None
                    
                    fig_map = px.scatter_mapbox(
                        data_filtered, lat='lat', lon='lon', color=color_col, size_max=15, zoom=3.5,
                        hover_name=hover_col, mapbox_style="carto-positron" 
                    )
                    fig_map.update_layout(paper_bgcolor='rgba(0,0,0,0)', height=400, margin={"r":0,"t":0,"l":0,"b":0}, dragmode="pan")
                    st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True})
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
        row_chart1, row_chart2 = st.columns([6, 4])
        
        with row_chart1:
            st.subheader("📊 Wilayah Laporan Terbanyak")
            if 'Lokasi LM' in data_filtered.columns:
                top_chart = data_filtered['Lokasi LM'].value_counts().nlargest(10).reset_index()
                top_chart.columns = ['Wilayah', 'Jumlah']
                fig_bar = px.bar(top_chart, x='Jumlah', y='Wilayah', orientation='h', text='Jumlah', color='Jumlah', color_continuous_scale=['#a6c9e2', '#004a99'])
                fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title=None, yaxis=dict(autorange="reversed"), height=350, coloraxis_showscale=False)
                st.plotly_chart(fig_bar, use_container_width=True)

        with row_chart2:
            st.subheader("📊 Pencapaian Target")
            if 'Tahun' in data_filtered.columns or has_date:
                temp_df = data_filtered.copy()
                if 'Tahun' not in temp_df.columns:
                    temp_df['Tahun'] = temp_df['Tanggal Laporan'].dt.year
                target_df = temp_df.groupby('Tahun').size().reset_index(name='Realisasi')
                target_df['Target'] = 10 
                target_df['Tahun'] = target_df['Tahun'].astype(str)
                fig_target = px.bar(target_df, x='Tahun', y=['Realisasi', 'Target'], barmode='group', color_discrete_map={'Realisasi': '#004a99', 'Target': '#e65100'})
                fig_target.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, xaxis_title=None, yaxis_title="Jumlah Kasus", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_target, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📚 Buka Detail Data Tabel", expanded=True):
            st.markdown('<div class="card-container" style="border-top: none; box-shadow: none;">', unsafe_allow_html=True)
            kolom_dihapus = ['lat', 'lon', 'Hari_Berjalan', 'ni', 'Ni', 'NI', 'maladministrasi', 'Maladministrasi', 'Jenis Maladministrasi']
            view_df = data_filtered.drop(columns=kolom_dihapus, errors='ignore')
            
            preferred_cols = ['Nomor Arsip', 'Nama Pelapor', 'Lokasi LM', 'Asisten', 'Status', 'Tanggal Laporan', 'Tahun']
            existing_cols = [c for c in preferred_cols if c in view_df.columns]
            other_cols = [c for c in view_df.columns if c not in existing_cols]
            
            st.dataframe(view_df[existing_cols + other_cols], use_container_width=True)
            
            csv = view_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh Data (CSV)", data=csv, file_name=f'Laporan_Ombudsman_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Data tidak ditemukan. Silakan atur ulang kata kunci pencarian atau filter tanggal.")

# --- 6. ROUTING UTAMA ---
if not st.session_state['logged_in']:
    auth_page()
else:
    show_dashboard()