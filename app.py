import streamlit as st
import pandas as pd
import plotly.express as px
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from datetime import datetime
import time

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
    st.session_state['users_db'] = {"admin": "ombudsman123", "pimpinan": "rahasia123"}

# --- 3. CUSTOM CSS GLOBAL (TEMA MODERN OCEAN GLOW) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;800;900&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Nunito', sans-serif;
        color: #1e293b; 
    }

    .stApp { background-color: #f8fafc; } 
    
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e2e8f0; box-shadow: 2px 0 10px rgba(0,0,0,0.02); }

    /* --- STYLING AUTENTIKASI --- */
    .auth-title { text-align: center; color: #0ea5e9; font-weight: 900; font-size: 2.8rem; margin-bottom: 5px; padding-top: 20px; }
    .auth-subtitle { text-align: center; color: #64748b; font-size: 1.1rem; margin-bottom: 30px; }
    
    [data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 10px; justify-content: center; }
    [data-testid="stTabs"] [data-baseweb="tab"] { background-color: transparent; border-radius: 8px 8px 0px 0px; padding: 10px 20px; color: #64748b; font-weight: 800; }
    [data-testid="stTabs"] [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 3px solid #0ea5e9; background-color: #f0f9ff; }

    /* --- STYLING DASHBOARD KEKINIAN --- */
    .header-container {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%); 
        padding: 2.5rem; border-radius: 20px; color: white; margin-bottom: 2rem; 
        box-shadow: 0 15px 25px rgba(0, 114, 255, 0.25); 
        border: none;
    }
    .header-title { font-size: 2.5rem; font-weight: 900; margin: 0; color: #ffffff; text-shadow: 2px 2px 4px rgba(0,0,0,0.1); }
    .header-subtitle { font-size: 1.1rem; color: #e0f2fe; margin-top: 5px; font-weight: 600;}

    /* Kartu (Card) Melayang */
    .card-container {
        background-color: #ffffff; padding: 25px; border-radius: 16px; margin-bottom: 20px; 
        border: 1px solid #f1f5f9; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s;
    }
    .card-container:hover { 
        transform: translateY(-5px) scale(1.01); 
        box-shadow: 0 20px 25px -5px rgba(0, 114, 255, 0.15); 
    }
    
    .card-blue { border-top: 4px solid #0ea5e9; }
    .card-blue h4 { color: #0ea5e9; font-weight: 800;}
    
    .card-orange { border-top: 4px solid #f97316; }
    .card-orange h4 { color: #f97316; font-weight: 800;}

    /* Metrik Tampil Beda */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        padding: 20px; border-radius: 16px; border-left: 6px solid #0ea5e9;
        text-align: left; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    [data-testid="stMetricLabel"] { color: #64748b; font-size: 1rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;}
    [data-testid="stMetricValue"] { color: #0ea5e9; font-weight: 900; font-size: 2.8rem; }

    /* Tombol */
    .stButton > button { border-radius: 10px !important; font-weight: 800 !important; }
    
    /* Expander Table */
    .streamlit-expanderHeader { background-color: #f1f5f9 !important; border-radius: 10px; font-weight: 800 !important; color: #0ea5e9 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 4. FUNGSI HALAMAN LOGIN & DAFTAR ---
def auth_page():
    st.markdown("<style>[data-testid='stSidebar'] {display: none;}</style>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.3, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 class='auth-title'>🚀 Portal Keasistenan IV</h2>", unsafe_allow_html=True)
        st.markdown("<p class='auth-subtitle'>Sistem Monitoring Pengaduan Ombudsman RI</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            tab1, tab2 = st.tabs(["🔑 Masuk (Login)", "📝 Daftar Baru"])
            
            with tab1:
                st.markdown("#### Silakan Masuk")
                username_login = st.text_input("Username", key="log_user")
                password_login = st.text_input("Password", type="password", key="log_pass")
                if st.button("Masuk", type="primary", use_container_width=True):
                    if username_login in st.session_state['users_db'] and st.session_state['users_db'][username_login] == password_login:
                        st.success("✅ Login berhasil!")
                        time.sleep(1)
                        st.session_state['logged_in'] = True
                        st.rerun()
                    else: st.error("❌ Username atau password salah!")

            with tab2:
                st.markdown("#### Buat Akun Baru")
                new_username = st.text_input("Buat Username", key="reg_user")
                new_password = st.text_input("Buat Password", type="password", key="reg_pass")
                confirm_password = st.text_input("Konfirmasi Password", type="password", key="reg_pass_conf")
                if st.button("Daftar Akun", type="primary", use_container_width=True):
                    if new_username and new_password and new_password == confirm_password:
                        st.session_state['users_db'][new_username] = new_password
                        st.success("🎉 Akun dibuat! Silakan pindah ke tab Masuk.")
                        st.balloons()
                    else:
                        st.error("❌ Cek kembali isian Anda!")

# --- 5. FUNGSI DASHBOARD UTAMA ---
def show_dashboard():
    # Load data anti-error
    @st.cache_data
    def load_data():
        try:
            df = pd.read_excel("data_tanah1.xlsx")
            has_date = False
            for col in df.columns:
                if any(x in col.lower() for x in ['tanggal', 'tgl', 'date']):
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    df.rename(columns={col: 'Tanggal Laporan'}, inplace=True)
                    has_date = True
                    break
                    
            loc_col = 'Lokasi LM' if 'Lokasi LM' in df.columns else 'Terlapor' if 'Terlapor' in df.columns else None
            if loc_col and 'lat' not in df.columns:
                # Titik dummy sementara biar map nggak nge-blank kalau gagal narik koordinat
                df['lat'] = -6.1754 
                df['lon'] = 106.8272
                
            return df, has_date
        except Exception as e:
            return pd.DataFrame(), False

    data, has_date = load_data()
    
    if data.empty:
        st.error("❌ Gagal memuat data! Pastikan file 'data_tanah1.xlsx' ada di folder yang benar.")
        return

    # Hitung data mangkrak (Overdue)
    total_mangkrak = 0
    if has_date and 'Status' in data.columns:
        data['Hari_Berjalan'] = (datetime.now() - data['Tanggal Laporan']).dt.days
        total_mangkrak = len(data[(data['Hari_Berjalan'] > 30) & (~data['Status'].str.contains('Selesai|Tutup', case=False, na=False))])

    # --- FILTER SIDEBAR LENGKAP ---
    with st.sidebar:
        st.markdown("<h2 style='color:#0ea5e9; font-weight:900;'>⚖️ Ombudsman</h2>", unsafe_allow_html=True)
        search_query = st.text_input("🔍 Cari Data (Nama/Wilayah):")
        st.divider()
        
        data_filtered = data.copy()
        
        # Filter Tanggal (Safe version)
        if has_date:
            min_d, max_d = data['Tanggal Laporan'].min().date(), data['Tanggal Laporan'].max().date()
            if min_d != max_d:
                dr = st.date_input("📅 Periode Laporan", value=(min_d, max_d), min_value=min_d, max_value=max_d)
                if len(dr) == 2: 
                    data_filtered = data_filtered[(data_filtered['Tanggal Laporan'].dt.date >= dr[0]) & (data_filtered['Tanggal Laporan'].dt.date <= dr[1])]
        
        # Filter Pencarian Teks
        if search_query: 
            data_filtered = data_filtered[data_filtered.astype(str).apply(lambda x: x.str.contains(search_query, case=False)).any(axis=1)]
            
        # Filter Asisten
        if 'Asisten' in data.columns:
            sel_asisten = st.selectbox("👤 Asisten:", ["Semua Asisten"] + sorted(data["Asisten"].dropna().unique().tolist()))
            if sel_asisten != "Semua Asisten": 
                data_filtered = data_filtered[data_filtered["Asisten"] == sel_asisten]
                
        # Filter Wilayah
        if 'Lokasi LM' in data.columns:
            sel_wilayah = st.selectbox("📍 Wilayah LM:", ["Semua Wilayah"] + sorted(data["Lokasi LM"].dropna().unique().tolist()))
            if sel_wilayah != "Semua Wilayah":
                data_filtered = data_filtered[data_filtered["Lokasi LM"] == sel_wilayah]
            
        # Filter Status
        if 'Status' in data.columns:
            sel_status = st.multiselect("📊 Status:", ["Semua Status"] + sorted(data["Status"].dropna().unique().tolist()), default="Semua Status")
            if "Semua Status" not in sel_status and sel_status: 
                data_filtered = data_filtered[data_filtered["Status"].isin(sel_status)]

        st.markdown("---")
        if st.button("🖨️ Cetak PDF", use_container_width=True):
            st.components.v1.html("""<script>setTimeout(function() {window.parent.print();}, 100);</script>""", height=0, width=0)
            
        if st.button("🚪 Keluar", use_container_width=True): 
            st.session_state['logged_in'] = False
            st.rerun()

    # --- HEADER DASHBOARD ---
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">✨ Command Center Keasistenan IV</h1>
        <p class="header-subtitle">Monitoring Pengaduan Pertanahan Modern & Cepat</p>
    </div>
    """, unsafe_allow_html=True)

    if not data_filtered.empty:
        total = len(data_filtered)
        selesai = len(data_filtered[data_filtered['Status'].str.contains('Selesai|Tutup', case=False, na=False)]) if 'Status' in data_filtered.columns else 0
        
        # METRIK ATAS
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Laporan", f"{total}", "+ Kasus Baru")
        c2.metric("Selesai", f"{selesai}", f"{(selesai/total*100 if total>0 else 0):.0f}% Rate")
        c3.metric("Diproses", f"{total-selesai}", delta_color="inverse")
        c4.metric("Overdue (>30 Hari)", f"{total_mangkrak}", delta_color="inverse") 

        # GRAFIK TREN (Area Line)
        st.markdown('<div class="card-container card-blue"><h4>📈 Tren Kasus Masuk</h4>', unsafe_allow_html=True)
        if has_date:
            trend = data_filtered.set_index('Tanggal Laporan').resample('ME').size().reset_index(name='Jumlah')
            # Fix area chart error: Use px.line with fill='tozeroy'
            fig = px.line(trend, x='Tanggal Laporan', y='Jumlah', line_shape='spline', markers=True)
            fig.update_traces(line_color='#0ea5e9', fill='tozeroy', fillcolor='rgba(14, 165, 233, 0.2)', marker=dict(size=8, color='#f97316'))
            fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=300, xaxis_title=None, yaxis_title="Jumlah")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # INSIGHT & MAP
        c_map, c_sum = st.columns([7, 3])
        with c_sum:
            top_w = data_filtered['Lokasi LM'].mode()[0] if 'Lokasi LM' in data_filtered.columns else "-"
            st.markdown(f'''
            <div class="card-container card-orange" style="height:100%;">
                <h4>🔥 Quick Insight</h4><br>
                <div style="background-color:#fff7ed; padding:15px; border-radius:10px; border-left:4px solid #f97316; margin-bottom:15px;">
                    Top Wilayah:<br><b style="font-size:1.5rem; color:#f97316;">{top_w}</b>
                </div>
                <div style="background-color:#f0fdf4; padding:15px; border-radius:10px; border-left:4px solid #22c55e; margin-bottom:15px;">
                    Status Aman:<br><b style="font-size:1.5rem; color:#22c55e;">{selesai} Selesai</b>
                </div>
                <div style="background-color:#fef2f2; padding:15px; border-radius:10px; border-left:4px solid #ef4444;">
                    Perlu Atensi:<br><b style="font-size:1.5rem; color:#ef4444;">{total_mangkrak} Overdue</b>
                </div>
            </div>
            ''', unsafe_allow_html=True)
            
        with c_map:
            st.markdown('<div class="card-container card-blue"><h4>📍 Live Map</h4>', unsafe_allow_html=True)
            if 'lat' in data_filtered.columns:
                fig_map = px.scatter_mapbox(data_filtered, lat='lat', lon='lon', color='Status' if 'Status' in data_filtered.columns else None, size_max=15, zoom=3.5, mapbox_style="carto-positron")
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=380, paper_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_map, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        # GRAFIK BAWAH (YANG TADI SEMPAT DIHAPUS, SEKARANG KEMBALI)
        r1, r2 = st.columns([6, 4])
        with r1:
            st.markdown('<div class="card-container card-blue"><h4>📊 Wilayah Terbanyak</h4>', unsafe_allow_html=True)
            if 'Lokasi LM' in data_filtered.columns:
                tc = data_filtered['Lokasi LM'].value_counts().nlargest(10).reset_index()
                tc.columns = ['Wilayah', 'Jumlah']
                fig_bar = px.bar(tc, x='Jumlah', y='Wilayah', orientation='h', text='Jumlah', color='Jumlah', color_continuous_scale=['#bae6fd', '#0284c7'])
                fig_bar.update_layout(yaxis=dict(autorange="reversed"), height=350, coloraxis_showscale=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title=None)
                st.plotly_chart(fig_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
        with r2:
            st.markdown('<div class="card-container card-orange"><h4>🎯 Target Tahunan</h4>', unsafe_allow_html=True)
            if 'Tahun' in data_filtered.columns or has_date:
                temp = data_filtered.copy()
                if 'Tahun' not in temp.columns: temp['Tahun'] = temp['Tanggal Laporan'].dt.year
                tdf = temp.groupby('Tahun').size().reset_index(name='Realisasi')
                tdf['Target'] = 10
                tdf['Tahun'] = tdf['Tahun'].astype(str)
                fig_t = px.bar(tdf, x='Tahun', y=['Realisasi', 'Target'], barmode='group', color_discrete_map={'Realisasi': '#0ea5e9', 'Target': '#f97316'})
                fig_t.update_layout(height=350, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title=None, yaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig_t, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # TABEL BAWAH
        with st.expander("📚 Buka Detail Data Tabel", expanded=True):
            st.markdown('<div class="card-container" style="border-top: none; box-shadow: none;">', unsafe_allow_html=True)
            kolom_dihapus = ['lat', 'lon', 'Hari_Berjalan', 'ni', 'Ni', 'NI', 'maladministrasi', 'Maladministrasi']
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