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

# --- 2.inisialisasi SESSION STATE UNTUK LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- 3. CUSTOM CSS (GABUNGAN LOGIN, DASHBOARD & PRINT) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* Background Utama */
    .stApp {
        background-color: #f4f6f9;
    }

    /* --- STYLING LOGIN PAGE --- */
    .login-box {
        background-color: white;
        padding: 40px;
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 51, 102, 0.1);
        text-align: center;
        border-top: 5px solid #004a99;
    }
    .login-title {
        color: #003366;
        font-weight: 700;
        font-size: 1.8rem;
        margin-bottom: 5px;
    }
    .login-subtitle {
        color: #666;
        font-size: 0.9rem;
        margin-bottom: 25px;
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
    .header-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
    }
    .header-subtitle {
        font-size: 1rem;
        opacity: 0.9;
        margin-top: 5px;
    }

    .card-container {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border-top: 4px solid transparent;
        transition: transform 0.2s, box-shadow 0.2s;
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
    [data-testid="stMetricLabel"] {
        color: #666;
        font-size: 0.85rem;
        font-weight: 600;
    }
    [data-testid="stMetricValue"] {
        color: #003366;
        font-weight: 800;
        font-size: 2rem;
    }

    /* --- MODE CETAK (PRINT) --- */
    @media print {
        @page { size: A4 portrait; margin: 10mm; }
        [data-testid="stSidebar"], [data-testid="stHeader"], footer, [data-testid="stToolbar"], .stDeployButton { 
            display: none !important; 
        }
        html, body, .stApp, .main, .block-container, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] {
            overflow: visible !important;
            height: auto !important;
            min-height: 0 !important;
            max-height: none !important;
            position: relative !important;
            display: block !important;
            background-color: white !important;
            width: 100% !important;
        }
        .card-container, [data-testid="stMetric"], .js-plotly-plot, .stDataFrame {
            page-break-inside: avoid !important;
            break-inside: avoid !important;
        }
        .js-plotly-plot .plotly { width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. FUNGSI LOGIN ---

# Set Username dan Password di sini!
USER_CREDENTIALS = {
    "admin": "ombudsman123",
    "pimpinan": "rahasia123"
}

def login_page():
    # Menyembunyikan sidebar di halaman login via CSS
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Membuat layout agar form login berada di tengah
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div class="login-box">
                <div style="font-size: 40px; margin-bottom: 10px;">⚖️</div>
                <h2 class="login-title">Portal Keasistenan IV</h2>
                <p class="login-subtitle">Silakan masuk untuk mengakses Dashboard Ombudsman RI</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Form Input di dalam container
        with st.container():
            st.markdown("<div style='background-color: white; padding: 20px; border-radius: 0 0 16px 16px; box-shadow: 0 10px 30px rgba(0, 51, 102, 0.1); margin-top: -20px;'>", unsafe_allow_html=True)
            username = st.text_input("Username", placeholder="Masukkan username...")
            password = st.text_input("Password", type="password", placeholder="Masukkan password...")
            
            if st.button("Masuk / Login", type="primary", use_container_width=True):
                if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
                    st.success("Login berhasil! Memuat dashboard...")
                    time.sleep(1) # Efek loading sebentar
                    st.session_state['logged_in'] = True
                    st.rerun() # Refresh halaman untuk masuk ke dashboard
                else:
                    st.error("Username atau password salah!")
            st.markdown("</div>", unsafe_allow_html=True)


# --- 5. FUNGSI DASHBOARD UTAMA (Kode aslimu diletakkan di dalam fungsi ini) ---

def show_dashboard():
    # Fungsi Logika Peta & Data
    def get_coordinates(df):
        geolocator = Nominatim(user_agent="ombudsman_dashboard_final_v3")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        
        loc_col = 'Lokasi LM' if 'Lokasi LM' in df.columns else 'Terlapor'
        unique_locations = df[loc_col].dropna().unique()
        location_map = {}
        
        progress_bar = st.progress(0, text="Sedang memetakan lokasi...")
        for i, loc in enumerate(unique_locations):
            try:
                location = geocode(f"{loc}, Indonesia")
                if location:
                    location_map[loc] = [location.latitude, location.longitude]
                else:
                    location_map[loc] = [-6.2088, 106.8456] 
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
        try:
            st.image("ombudsman logo.png", width=160)
        except:
            st.markdown("**(Logo Ombudsman)**")
        
        st.markdown("### 🔎 Pencarian & Filter")
        search_query = st.text_input("Cari Data (Nama/No/Wilayah):", placeholder="Ketik kata kunci...")
        st.divider()

        start_date, end_date = None, None
        if has_date:
            min_date = data['Tanggal Laporan'].min().date()
            max_date = data['Tanggal Laporan'].max().date()
            date_range = st.date_input("📅 Periode Laporan", value=[min_date, max_date], min_value=min_date, max_value=max_date)
            if isinstance(date_range, list) and len(date_range) == 2:
                start_date, end_date = date_range
                data_filtered = data[(data['Tanggal Laporan'].dt.date >= start_date) & (data['Tanggal Laporan'].dt.date <= end_date)]
            else:
                data_filtered = data
        else:
            data_filtered = data

        if search_query:
            mask = data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
            data_filtered = data_filtered[mask]

        if 'Asisten' in data.columns:
            asisten_list = ["Semua Asisten"] + sorted(data_filtered["Asisten"].dropna().unique().tolist())
            sel_asisten = st.selectbox("👤 Asisten:", asisten_list)
            if sel_asisten != "Semua Asisten":
                data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]

        if 'Lokasi LM' in data.columns:
            wilayah_list = ["Semua Wilayah"] + sorted(data_filtered["Lokasi LM"].dropna().unique().tolist())
            sel_wilayah = st.selectbox("📍 Wilayah LM:", wilayah_list)
            if sel_wilayah != "Semua Wilayah":
                data_filtered = data_filtered[data_filtered["Lokasi LM"] == sel_wilayah]
                
        if 'Status' in data.columns:
            status_list = ["Semua Status"] + sorted(data_filtered["Status"].dropna().unique().tolist())
            sel_status = st.multiselect("📊 Status:", status_list, default="Semua Status")
            if "Semua Status" not in sel_status and sel_status:
                data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

        st.markdown("---")
        
        if st.button("🖨️ Cetak Laporan ke PDF", type="primary", use_container_width=True):
            st.components.v1.html("""<script>setTimeout(function() {window.parent.print();}, 100);</script>""", height=0, width=0)
        
        st.markdown("<br>", unsafe_allow_html=True)
        # Tombol Logout
        if st.button("🚪 Keluar / Logout", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
            
        st.caption("© 2026 Keasistenan Utama IV")

    # MAIN CONTENT
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">⚖️ Dashboard Monitoring Keasistenan Utama IV</h1>
        <p class="header-subtitle">Monitoring & Analisis Pengaduan Masyarakat Bidang Pertanahan</p>
    </div>
    """, unsafe_allow_html=True)

    filter_info = []
    if start_date and end_date: filter_info.append(f"Periode: <b>{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</b>")
    if search_query: filter_info.append(f"Kata Kunci: <b>'{search_query}'</b>")
    if filter_info:
        st.markdown(f"<div style='background-color:#e3f2fd; padding:10px; border-radius:8px; margin-bottom:20px; color:#0d47a1;'>ℹ️ Filter Aktif: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

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
                fig_trend.update_traces(line_color='#e65100', line_width=3)
                fig_trend.update_layout(plot_bgcolor='white', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_trend, use_container_width=True)
        elif 'Tahun' in data_filtered.columns:
            st.markdown("#### 📉 Tren Laporan Masuk (Tahunan)")
            trend_data = data_filtered.groupby('Tahun').size().reset_index(name='Jumlah Laporan')
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Tahun', y='Jumlah Laporan', markers=True)
                fig_trend.update_xaxes(type='category')
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

        st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
        row_chart1, row_chart2 = st.columns([6, 4])
        with row_chart1:
            st.subheader("📊 Wilayah Terbanyak")
            if 'Lokasi LM' in data_filtered.columns:
                top_chart = data_filtered['Lokasi LM'].value_counts().nlargest(10).reset_index()
                top_chart.columns = ['Wilayah', 'Jumlah']
                fig_bar = px.bar(top_chart, x='Jumlah', y='Wilayah', orientation='h', text='Jumlah', color='Jumlah', color_continuous_scale=['#bbdefb', '#0d47a1'])
                fig_bar.update_layout(plot_bgcolor="white", xaxis_title=None, yaxis_title=None, yaxis=dict(autorange="reversed"), height=350, coloraxis_showscale=False)
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
                fig_target = px.bar(target_df, x='Tahun', y=['Realisasi', 'Target'], barmode='group', color_discrete_map={'Realisasi': '#003366', 'Target': '#e65100'})
                fig_target.update_layout(plot_bgcolor='white', height=350, xaxis_title=None, yaxis_title="Jumlah Kasus", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_target, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        with st.expander("📚 Detail Data Tabel", expanded=True):
            st.markdown('<div class="card-container">', unsafe_allow_html=True)
            kolom_dihapus = ['lat', 'lon', 'Hari_Berjalan', 'ni', 'Ni', 'NI', 'maladministrasi', 'Maladministrasi', 'Jenis Maladministrasi']
            view_df = data_filtered.drop(columns=kolom_dihapus, errors='ignore')
            preferred_cols = ['Nomor Arsip', 'Nama Pelapor', 'Lokasi LM', 'Asisten', 'Status', 'Tanggal Laporan', 'Tahun']
            existing_cols = [c for c in preferred_cols if c in view_df.columns]
            other_cols = [c for c in view_df.columns if c not in existing_cols]
            st.dataframe(view_df[existing_cols + other_cols], use_container_width=True)
            csv = view_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Unduh CSV", data=csv, file_name=f'Laporan_{datetime.now().strftime("%Y%m%d")}.csv', mime='text/csv')
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ Data tidak ditemukan.")


# --- 6. MAIN ROUTER (PENENTU HALAMAN) ---

if not st.session_state['logged_in']:
    login_page()
else:
    show_dashboard()