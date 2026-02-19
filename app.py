import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Keasistenan IV - Ombudsman RI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (TAMPILAN PREMIUM & PRINT) ---
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

    /* Header Gradient */
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

    /* Styling Kartu (Card) */
    .card-container {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        border-top: 4px solid transparent;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    .card-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.08);
    }
    
    /* Aksen Warna Kartu */
    .card-blue { border-top-color: #004a99; }
    .card-orange { border-top-color: #e65100; }

    /* Metric Styles */
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

    /* Sidebar & Print Button */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #eaeaea;
    }
    .print-btn {
        background-color: #e65100;
        color: white;
        padding: 12px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        cursor: pointer;
        transition: 0.3s;
        border: none;
        width: 100%;
        box-shadow: 0 4px 6px rgba(230, 81, 0, 0.2);
    }
    .print-btn:hover {
        background-color: #bf360c;
        box-shadow: 0 6px 8px rgba(230, 81, 0, 0.3);
    }

    /* Mode Cetak */
    /* Mode Cetak - Perbaikan */
    @media print {
        /* Sembunyikan semua elemen UI Streamlit yang ganggu */
        [data-testid="stSidebar"], 
        header, 
        footer, 
        .stDeployButton,
        [data-testid="stToolbar"],
        .no-print { 
            display: none !important; 
        }

        /* Hilangkan scrollbar dan set background putih bersih */
        .main, .stApp {
            background-color: white !important;
            color: black !important;
        }

        /* Paksa grafik Plotly agar lebarnya pas di kertas */
        .js-plotly-plot {
            width: 100% !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FUNGSI LOGIKA ---

def get_coordinates(df):
    """Geocoding otomatis - FIX: Gunakan Lokasi LM agar peta menyebar"""
    geolocator = Nominatim(user_agent="ombudsman_dashboard_final_v2")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    
    # Cek apakah ada kolom 'Lokasi LM', jika tidak pakai 'Terlapor'
    loc_col = 'Lokasi LM' if 'Lokasi LM' in df.columns else 'Terlapor'
    
    # Dropna agar NaN tidak error
    unique_locations = df[loc_col].dropna().unique()
    location_map = {}
    
    progress_bar = st.progress(0, text="Sedang memetakan lokasi...")
    for i, loc in enumerate(unique_locations):
        try:
            location = geocode(f"{loc}, Indonesia")
            if location:
                location_map[loc] = [location.latitude, location.longitude]
            else:
                location_map[loc] = [-6.2088, 106.8456] # Default Jakarta
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
        df = pd.read_excel("data_tanah.xlsx")
        
        # Auto-detect tanggal
        date_col_found = False
        for col in df.columns:
            if any(x in col.lower() for x in ['tanggal', 'tgl', 'date']):
                df[col] = pd.to_datetime(df[col], errors='coerce')
                df.rename(columns={col: 'Tanggal Laporan'}, inplace=True)
                date_col_found = True
                break
        
        # Auto-geocoding
        if ('Terlapor' in df.columns or 'Lokasi LM' in df.columns) and ('lat' not in df.columns):
            df = get_coordinates(df)
            
        return df, date_col_found
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
        st.stop()

data, has_date = load_data()
if not data.empty and has_date:
    today = datetime.now()
    # Hitung laporan yang belum selesai dan sudah lebih dari 30 hari
    data['Hari_Berjalan'] = (today - data['Tanggal Laporan']).dt.days
    mangkrak_mask = (data['Hari_Berjalan'] > 30) & (~data['Status'].str.contains('Selesai|Tutup', case=False, na=False))
    total_mangkrak = len(data[mangkrak_mask])
else:
    total_mangkrak = 0


# --- 4. SIDEBAR (FILTER & SEARCH) ---
with st.sidebar:
    # Handle missing logo gracefully
    try:
        st.image("ombudsman logo.png", width=160)
    except:
        st.markdown("**(Logo Ombudsman)**")
    
    st.markdown("### 🔎 Pencarian & Filter")
    
    # --- FITUR LAMA TAPI DENGAN SEARCH LEBIH LUAS ---
    search_query = st.text_input("Cari Data (Nama/No/Wilayah):", placeholder="Ketik kata kunci...")
    
    st.divider()

    start_date, end_date = None, None

    # Filter Tanggal
    if has_date:
        min_date = data['Tanggal Laporan'].min().date()
        max_date = data['Tanggal Laporan'].max().date()
        
        date_range = st.date_input(
            "📅 Periode Laporan",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        
        # Terapkan Filter Tanggal
        if isinstance(date_range, list) and len(date_range) == 2:
            start_date, end_date = date_range
            data_filtered = data[(data['Tanggal Laporan'].dt.date >= start_date) & 
                                 (data['Tanggal Laporan'].dt.date <= end_date)]
        else:
            data_filtered = data
    else:
        data_filtered = data

    # Terapkan Global Search (Logika AND dengan filter tanggal)
    if search_query:
        mask = data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)
        data_filtered = data_filtered[mask]

    # --- FITUR BARU: FILTER ASISTEN ---
    if 'Asisten' in data.columns:
        asisten_list = ["Semua Asisten"] + sorted(data_filtered["Asisten"].dropna().unique().tolist())
        sel_asisten = st.selectbox("👤 Asisten:", asisten_list)
        if sel_asisten != "Semua Asisten":
            data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]

    # Filter Kategori (Instansi)
    if 'Terlapor' in data.columns:
        instansi_list = ["Semua Instansi"] + sorted(data_filtered["Terlapor"].dropna().unique().tolist())
        sel_instansi = st.selectbox("📍 Instansi:", instansi_list)
        if sel_instansi != "Semua Instansi":
            data_filtered = data_filtered[data_filtered["Terlapor"] == sel_instansi]
            
    # Filter Status
    if 'Status' in data.columns:
        status_list = ["Semua Status"] + sorted(data_filtered["Status"].dropna().unique().tolist())
        sel_status = st.multiselect("📊 Status:", status_list, default="Semua Status")
        if "Semua Status" not in sel_status and sel_status:
            data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

    st.markdown("---")
    
    # Tombol Print
    if st.sidebar.button("🖨️ Cetak Laporan ke PDF"):
        js = "window.print();"
        st.components.v1.html(f"<script>{js}</script>", height=0, width=0)
        st.sidebar.success("Gunakan setelan 'Save as PDF' pada jendela print.")
    
    st.caption("© 2026 Keasistenan Utama IV")

# --- 5. MAIN CONTENT ---

# Header Hero Section
st.markdown("""
<div class="header-container">
    <h1 class="header-title">⚖️ Dashboard Monitoring Keasistenan Utama IV</h1>
    <p class="header-subtitle">Monitoring & Analisis Pengaduan Masyarakat Bidang Pertanahan</p>
</div>
""", unsafe_allow_html=True)

# Tampilkan Indikator Filter Aktif
filter_info = []
if start_date and end_date: filter_info.append(f"Periode: <b>{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</b>")
if search_query: filter_info.append(f"Kata Kunci: <b>'{search_query}'</b>")
if filter_info:
    st.markdown(f"<div style='background-color:#e3f2fd; padding:10px; border-radius:8px; margin-bottom:20px; color:#0d47a1;'>ℹ️ Filter Aktif: {' | '.join(filter_info)}</div>", unsafe_allow_html=True)

# --- SECTION 1: KPI METRICS ---
if not data_filtered.empty:
    total = len(data_filtered)
    selesai = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)]) if 'Status' in data_filtered.columns else 0
    proses = total - selesai
    malad = data_filtered['Maladministrasi'].nunique() if 'Maladministrasi' in data_filtered.columns else 0
    
    # Tambahkan Target Metrik
    col1, col2, col3, col4, col5, col6= st.columns(6)
    col1.metric("Total Laporan", f"{total}", delta="Kasus Masuk")
    col2.metric("Selesai", f"{selesai}", f"{(selesai/total*100 if total>0 else 0):.1f}% Rate")
    col3.metric("Dalam Proses", f"{proses}", delta_color="inverse")
    col4.metric("Maladministrasi", f"{malad}")
    col5.metric("🚨 Mangkrak", f"{total_mangkrak}", delta=">30hr", delta_color="inverse")
    col6.metric("🎯 Target", "10", delta="Tahunan") 
    

    # --- FITUR LAMA: GRAFIK TREN WAKTU (LINE CHART) ---
    if has_date:
        col_tren, col_target = st.columns(2)
        
        with col_tren:
            st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
            st.markdown("#### 📉 Tren Laporan Masuk (Bulanan)")
            
            # Agregasi data per Bulan
            trend_data = data_filtered.set_index('Tanggal Laporan').resample('ME').size().reset_index(name='Jumlah Laporan')
            
            if not trend_data.empty:
                fig_trend = px.line(trend_data, x='Tanggal Laporan', y='Jumlah Laporan', 
                                    markers=True, line_shape='spline')
                fig_trend.update_traces(line_color='#e65100', line_width=3)
                fig_trend.update_layout(
                    plot_bgcolor='white',
                    height=300,
                    xaxis_title=None,
                    yaxis_title="Jumlah Kasus"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.info("Data tidak cukup untuk menampilkan tren bulanan.")
            st.markdown('</div>', unsafe_allow_html=True)

        # --- FITUR BARU: GRAFIK PENCAPAIAN TARGET ---
        with col_target:
            st.markdown('<div class="card-container card-orange">', unsafe_allow_html=True)
            st.markdown("#### 📊 Presentasi Pencapaian Target")
            
            if 'Tahun' in data_filtered.columns:
                target_df = data_filtered.groupby('Tahun').size().reset_index(name='Realisasi')
                target_df['Target'] = 10 # Angka target default
                fig_target = px.bar(target_df, x='Tahun', y=['Realisasi', 'Target'], barmode='group',
                                    color_discrete_map={'Realisasi': '#003366', 'Target': '#e65100'})
                fig_target.update_layout(plot_bgcolor='white', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_target, use_container_width=True)
            else:
                # Jika tidak ada kolom Tahun, fallback ke ekstraksi tahun dari tanggal
                trend_data['Tahun'] = trend_data['Tanggal Laporan'].dt.year
                target_df = trend_data.groupby('Tahun')['Jumlah Laporan'].sum().reset_index()
                target_df.rename(columns={'Jumlah Laporan': 'Realisasi'}, inplace=True)
                target_df['Target'] = 10
                
                fig_target = px.bar(target_df, x='Tahun', y=['Realisasi', 'Target'], barmode='group',
                                    color_discrete_map={'Realisasi': '#003366', 'Target': '#e65100'})
                fig_target.update_layout(plot_bgcolor='white', height=300, xaxis_title=None, yaxis_title="Jumlah Kasus")
                st.plotly_chart(fig_target, use_container_width=True)
                
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION 2: MAP & NARRATIVE ---
    with st.container():
        c_map, c_sum = st.columns([7, 3])
        with c_sum:
            st.markdown('<div class="card-container card-orange"><h4>📝 Ringkasan Eksekutif (Otomatis)</h4>', unsafe_allow_html=True)
            
            # Memastikan data tidak kosong sebelum menghitung
            if not data_filtered.empty:
                top_inst = data_filtered['Terlapor'].mode()[0] if 'Terlapor' in data_filtered.columns else "-"
                
                # Gunakan variabel yang sudah kita hitung di bagian Metrics
                rate = (selesai / total * 100) if total > 0 else 0
                evaluasi = "Sangat Baik" if rate > 80 else "Cukup Baik" if rate > 50 else "Perlu Atensi"
                color_eval = "#2e7d32" if rate > 80 else "#ef6c00" if rate > 50 else "#c62828"
                
                st.markdown(f"""
                <div style="font-size: 0.95rem; line-height: 1.6;">
                <b>Performa Penyelesaian:</b> <span style="color:{color_eval}; font-weight:bold; background-color:#f5f5f5; padding:2px 8px; border-radius:4px;">{evaluasi}</span><br><br>
                Instansi paling sering dilaporkan pada periode ini adalah <b>{top_inst}</b>.<br><br>
                Mohon prioritaskan penyelesaian pada <b>{proses}</b> laporan yang masih berjalan, terutama <b>{total_mangkrak}</b> kasus yang sudah lewat batas waktu (SLA).
                </div>
                """, unsafe_allow_html=True)
            else:
                st.write("Belum ada data untuk dianalisis.")
                
            st.markdown('</div>', unsafe_allow_html=True)
        with c_map:
            st.markdown('<div class="card-container card-blue"><h4>📍 Peta Distribusi Laporan</h4>', unsafe_allow_html=True)
            if 'lat' in data_filtered.columns:
                # Menggunakan Scatter Mapbox (Pin yang lebih cerdas)
                fig_map = px.scatter_mapbox(
                    data_filtered, 
                    lat='lat', 
                    lon='lon',
                    color='Status', # Warna pin otomatis beda tiap status
                    size_max=15, 
                    zoom=3.5,
                    hover_name='Terlapor' if 'Terlapor' in data_filtered.columns else 'Lokasi LM', 
                    mapbox_style="carto-positron"
                )
                fig_map.update_layout(
                    height=400, 
                    margin={"r":0,"t":0,"l":0,"b":0},
                    mapbox_style="carto-positron",
                    dragmode="pan", 
                    hovermode="closest"
                )
                # Tambahkan konfigurasi interaktif Streamlit
                st.plotly_chart(fig_map, use_container_width=True, config={'scrollZoom': True})
            else:
                st.warning("Koordinat tidak tersedia.")
            st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION 3: CATEGORY CHARTS ---
    st.markdown('<div class="card-container card-blue">', unsafe_allow_html=True)
    row_chart1, row_chart2 = st.columns([6, 4])
    
    with row_chart1:
        st.subheader("📊 Instansi Terlapor")
        if 'Terlapor' in data_filtered.columns:
            top_chart = data_filtered['Terlapor'].value_counts().nlargest(10).reset_index()
            top_chart.columns = ['Instansi', 'Jumlah']
            
            fig_bar = px.bar(top_chart, x='Jumlah', y='Instansi', orientation='h', text='Jumlah',
                             color='Jumlah', color_continuous_scale=['#bbdefb', '#0d47a1'])
            fig_bar.update_layout(
                plot_bgcolor="white",
                xaxis_title=None,
                yaxis_title=None,
                yaxis=dict(autorange="reversed"),
                height=350,
                coloraxis_showscale=False
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with row_chart2:
        st.subheader("📊 Jenis Maladministrasi")
        if 'Maladministrasi' in data_filtered.columns:
            fig_pie = px.pie(data_filtered, names='Maladministrasi', hole=0.6,
                             color_discrete_sequence=px.colors.sequential.Oranges_r)
            fig_pie.update_layout(height=350, showlegend=False)
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # --- FITUR BARU & LAMA: DATA TABLE ---
    # Membuka expander secara default agar mentor langsung melihat tabelnya
    with st.expander("📚 Buka Detail Data Tabel", expanded=True):
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        
        # Fitur Baru: Tampilkan Kolom yang Diminta Mentor (No Arsip, Pelapor, Asisten)
        view_df = data_filtered.drop(columns=['lat', 'lon', 'Hari_Berjalan'], errors='ignore')
        
        # Menyusun urutan kolom agar lebih enak dibaca (jika kolom tersebut ada di excel)
        preferred_cols = ['Nomor Arsip', 'Nama Pelapor', 'Lokasi LM', 'Asisten', 'Terlapor', 'Status', 'Tanggal Laporan']
        existing_cols = [c for c in preferred_cols if c in view_df.columns]
        other_cols = [c for c in view_df.columns if c not in existing_cols]
        final_cols = existing_cols + other_cols
        
        st.dataframe(view_df[final_cols], use_container_width=True)
        
        csv = view_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Unduh Data (CSV)",
            data=csv,
            file_name=f'Laporan_Ombudsman_{datetime.now().strftime("%Y%m%d")}.csv',
            mime='text/csv',
        )
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.warning("⚠️ Data tidak ditemukan. Silakan atur ulang kata kunci pencarian atau filter tanggal.")