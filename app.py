import streamlit as st
from pymongo import MongoClient
import pandas as pd
import altair as alt
import json

# Koneksi MongoDB
client = MongoClient('mongodb+srv://user:OG2QqFuCYwkoWBek@capstone.fqvkpyn.mongodb.net/?retryWrites=true&w=majority')
dbcuaca = client['cuaca_db']

# Ambil semua data dari MongoDB
cuaca_data_raw = list(dbcuaca['prakiraan_cuaca'].find())

# Parsing suhu + handle error
for item in cuaca_data_raw:
    suhu_str = item.get('suhu', '0')
    try:
        item['suhu'] = int(suhu_str.split()[0])
    except:
        item['suhu'] = 0

# --- Streamlit UI ---
st.title("Detail Prediksi Cuaca Per Hari ini")

# Input filter search daerah
search_daerah = st.text_input("Masukkan daerah (kota/kab/kec/kel):").lower()

# Pilih mode tampilan
mode = st.radio("Pilih Tampilan:", ('card', 'chart'))

# Filter data sesuai search daerah
if search_daerah:
    cuaca_data = [
        item for item in cuaca_data_raw
        if search_daerah in (item.get('provinsi') or '').lower()
        or search_daerah in (item.get('kab_kota') or '').lower()
        or search_daerah in (item.get('kecamatan') or '').lower()
        or search_daerah in (item.get('kelurahan') or '').lower()
    ]
else:
    cuaca_data = cuaca_data_raw

# Convert ke DataFrame biar gampang diproses di chart
df = pd.DataFrame(cuaca_data)

if mode == 'card':
    # Tampilkan card sederhana (streamlit tidak punya card, kita gunakan expander / container)
    provinsi_groups = df.groupby('provinsi')
    for provinsi, group in provinsi_groups:
        st.header(provinsi)
        for idx, row in group.iterrows():
            suhu = row['suhu']
            icon = "☀" if suhu >= 32 else ("⛅" if suhu >= 24 else "🌧")
            st.markdown(f"""
                *{row.get('kab_kota', '')}*  
                {row.get('kecamatan', '')} - {row.get('kelurahan', '')}  
                Suhu: *{suhu}°C* {icon}  
                Terakhir diperbarui: {row.get('timestamp', 'Tidak diketahui')}
            """)
            st.markdown("---")
else:
    # Mode chart: pakai Altair chart
    if df.empty:
        st.info("Data tidak ditemukan untuk filter yang diberikan.")
    else:
        # Contoh chart suhu per kecamatan, grouped by provinsi dan kab_kota
        for provinsi, prov_group in df.groupby('provinsi'):
            st.subheader(provinsi)
            for kab_kota, kab_group in prov_group.groupby('kab_kota'):
                st.markdown(f"{kab_kota}")
                chart = alt.Chart(kab_group).mark_bar().encode(
                    x='kecamatan:N',
                    y='suhu:Q',
                    tooltip=['kecamatan', 'suhu']
                ).properties(
                    width=600,
                    height=300
                )
                st.altair_chart(chart, use_container_width=True)