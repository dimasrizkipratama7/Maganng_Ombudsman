import streamlit as st
import pandas as pd
import plotly.express as px

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard Keasistenan IV - Ombudsman RI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS UNTUK ESTETIKA ---
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background-color: #f0f2f6; /* Soft light gray background */
        padding-top: 20px;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff; /* White sidebar */
        box-shadow: 2px 0 5px rgba(0,0,0,0.05);
        padding-top: 20px;
    }
    [data-testid="stSidebar"] .stButton {
        width: 100%;
    }

    /* Metric cards styling */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Softer shadow */
        border: 1px solid #e0e0e0;
        text-align: center;
        margin-bottom: 15px;
    }
    .stMetric > div > div:first-child { /* Value text */
        font-size: 2.5em; /* Larger value font */
        font-weight: bold;
        color: #004a99; /* Ombudsman Blue */
    }
    .stMetric > div > div:nth-child(2) { /* Label text */
        font-size: 1em;
        color: #555555;
    }

    /* Chart containers styling */
    .stPlotlyChart {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    
    /* Header styling */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0); /* Transparent header */
    }

    /* Expander styling */
    [data-testid="stExpander"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        padding: 10px;
    }
    
    /* Title and Subheader styling */
    h1 {
        color: #004a99;
        font-weight: 700;
    }
    h3 {
        color: #333333;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOAD DATA ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("data_tanah.xlsx")
        # Pastikan nama kolom sesuai. Contoh:
        # df.columns = ['ID', 'Terlapor', 'Maladministrasi', 'Status', 'Tanggal Laporan'] 
        # Atau jika nama kolom tidak sesuai, ganti df['Nama_Kolom_Asli'] di bawah
        return df
    except FileNotFoundError:
        st.error("⚠️ File 'data_tanah.xlsx' tidak ditemukan di direktori yang sama.")
        st.stop() # Hentikan eksekusi jika file tidak ada
    except Exception as e:
        st.error(f"⚠️ Gagal memuat data dari 'data_tanah.xlsx'. Pastikan format file benar dan kolom sesuai. Error: {e}")
        st.stop()

# Load data (akan dijalankan sekali karena ada @st.cache_data)
data = load_data()

# --- SIDEBAR DENGAN LOGO ---
with st.sidebar:
    st.image("ombudsman logo.png", 
             width=180, 
             caption="Ombudsman Republik Indonesia")
    st.markdown("---")
    st.header("🔍 Filter Data Laporan")
    
    # Filter Instansi Terlapor
    # Pastikan nama kolom 'Terlapor' ada di file Excel kamu
    if 'Terlapor' in data.columns:
        instansi_options = ["Semua Instansi"] + sorted(data["Terlapor"].unique().tolist())
        selected_instansi = st.selectbox(
            "Pilih Kantor Pertanahan:",
            options=instansi_options,
            index=0 # Default to "Semua Instansi"
        )
        if selected_instansi != "Semua Instansi":
            data_filtered = data[data["Terlapor"] == selected_instansi]
        else:
            data_filtered = data
    else:
        st.warning("Kolom 'Terlapor' tidak ditemukan di data Anda. Filter instansi dinonaktifkan.")
        data_filtered = data

    # Filter Status Laporan
    # Pastikan nama kolom 'Status' ada di file Excel kamu
    if 'Status' in data.columns:
        status_options = ["Semua Status"] + sorted(data["Status"].unique().tolist())
        selected_status = st.multiselect(
            "Pilih Status Laporan:",
            options=status_options,
            default=status_options[0] if "Semua Status" in status_options else []
        )
        if "Semua Status" not in selected_status and selected_status:
            data_filtered = data_filtered[data_filtered["Status"].isin(selected_status)]
    else:
        st.warning("Kolom 'Status' tidak ditemukan di data Anda. Filter status dinonaktifkan.")


    st.markdown("---")
    st.markdown("© 2026")

# --- MAIN CONTENT ---
st.title("⚖️ Dashboard Monitoring Keasistenan Utama IV")
st.subheader("Analisis Pengaduan Bidang Pertanahan")
st.markdown("Selamat datang di dashboard interaktif untuk memantau tren dan kinerja penanganan laporan maladministrasi pertanahan di Ombudsman RI.")
st.markdown("---")

# 4. METRICS (KPIs) - Menggunakan kolom yang lebih dinamis dan delta
if not data_filtered.empty:
    total_laporan = len(data_filtered)
    
    # Pastikan nama kolom 'Status' ada di data Anda
    if 'Status' in data_filtered.columns:
        selesai_count = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)])
        proses_count = len(data_filtered[~data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)])
    else:
        selesai_count = 0
        proses_count = total_laporan # Anggap semua dalam proses jika status tidak ada

    # Pastikan nama kolom 'Maladministrasi' ada di data Anda
    if 'Maladministrasi' in data_filtered.columns:
        kategori_unik = data_filtered['Maladministrasi'].nunique()
    else:
        kategori_unik = 0


    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Laporan", f"{total_laporan} Kasus", delta="Data Terbaru")
    col2.metric("Laporan Selesai", selesai_count, delta=f"{(selesai_count/total_laporan*100):.1f}%")
    col3.metric("Dalam Proses", proses_count)
    col4.metric("Kategori Maladministrasi Unik", kategori_unik)

    st.markdown("---")

    # 5. VISUALISASI UTAMA
    chart_col1, chart_col2 = st.columns([6, 4])

    with chart_col1:
        st.markdown("### 📈 Tren Laporan per Instansi Terlapor")
        # Pastikan nama kolom 'Terlapor' ada di data Anda
        if 'Terlapor' in data_filtered.columns:
            top_terlapor = data_filtered["Terlapor"].value_counts().nlargest(5).reset_index()
            top_terlapor.columns = ["Instansi", "Jumlah"]
            fig_terlapor = px.bar(
                top_terlapor, x="Jumlah", y="Instansi", 
                orientation='h', 
                color_discrete_sequence=['#004a99'], # Warna biru Ombudsman
                template="plotly_white",
                title="Top 5 Instansi dengan Laporan Terbanyak"
            )
            fig_terlapor.update_layout(margin=dict(l=0, r=0, t=30, b=0), yaxis_title="") # Hapus label Y-axis
            st.plotly_chart(fig_terlapor, use_container_width=True)
        else:
            st.warning("Grafik 'Tren Laporan per Instansi' tidak dapat ditampilkan. Kolom 'Terlapor' tidak ditemukan.")

    with chart_col2:
        st.markdown("### 📊 Distribusi Jenis Maladministrasi")
        # Pastikan nama kolom 'Maladministrasi' ada di data Anda
        if 'Maladministrasi' in data_filtered.columns:
            fig_pie = px.pie(
                data_filtered, names="Maladministrasi", 
                hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Plotly, # Palette warna yang lebih cerah
                title="Persentase Kategori Maladministrasi"
            )
            fig_pie.update_layout(margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Grafik 'Distribusi Jenis Maladministrasi' tidak dapat ditampilkan. Kolom 'Maladministrasi' tidak ditemukan.")
    
    st.markdown("---")

    # 6. TABEL DATA MENTAH & DOWNLOAD
    st.markdown("### 📚 Detail Data Laporan (Tersaring)")
    with st.expander("Klik untuk melihat tabel data lengkap"):
        st.dataframe(data_filtered, use_container_width=True)
        
        csv = data_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Data sebagai CSV",
            data=csv,
            file_name='rekap_laporan_pertanahan_filtered.csv',
            mime='text/csv',
            help="Unduh data yang sudah difilter dalam format CSV."
        )

else:
    st.warning("Tidak ada data yang ditemukan berdasarkan filter yang diterapkan.")