import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
import pydeck as pdk

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("tourism_with_id.csv")
    df = df.drop(columns=['Unnamed: 11', 'Unnamed: 12', 'Coordinate'])
    return df

df = load_data()

# Helper functions
def to_radians(series):
    return np.radians(series)

def recommend_places(city, category, n_recommendations=5):
    filtered = df[(df['City'] == city) & (df['Category'] == category)]
    filtered_sorted = filtered.sort_values(by='Rating', ascending=False).head(n_recommendations)

    if not filtered.empty:
        base_location = filtered[['Lat', 'Long']].mean().values
        base_rad = to_radians(base_location)

        candidates = df[(df['City'] == city) & (df['Category'] != category)]

        if not candidates.empty:
            coords_rad = to_radians(candidates[['Lat', 'Long']].values)
            distances = haversine_distances([base_rad], coords_rad)[0] * 6371
            candidates = candidates.copy()
            candidates['Distance_km'] = distances
            closest = candidates.sort_values(by='Distance_km').head(5)
            return filtered_sorted, closest, base_location

    return filtered_sorted, pd.DataFrame(), None

# Streamlit UI
st.set_page_config(page_title="Rekomendasi Tempat Wisata", layout="wide")
st.title("🎯 Sistem Rekomendasi Tempat Wisata")

cities = df['City'].unique()
categories = df['Category'].unique()

city = st.selectbox("Pilih Kota", sorted(cities))
category = st.selectbox("Pilih Tipe Wisata", sorted(categories))

def display_card(place):
    st.markdown(f"""
        <div style='background-color:#f9f9f9;padding:15px;border-radius:10px;margin-bottom:10px;box-shadow: 0 2px 5px rgba(0,0,0,0.1);'>
            <h4 style='margin:0;color:#0066cc;'>{place['Place_Name']}</h4>
            <p style='margin:5px 0;'>📍 <b>{place['City']}</b> | 🏷️ {place['Category']}</p>
            <p style='margin:5px 0;'>⭐ Rating: <b>{place['Rating']}</b> | 💰 Price: <b>{place['Price']}</b></p>
        </div>
    """, unsafe_allow_html=True)

if st.button("Tampilkan Rekomendasi"):
    main_results, nearby_results, base_location = recommend_places(city, category)

    if main_results.empty:
        st.warning("Tidak ditemukan tempat yang sesuai dengan kriteria.")
    else:
        st.success(f"Menampilkan rekomendasi di {city} untuk tipe {category}:")
        for _, row in main_results.iterrows():
            display_card(row)

    if not nearby_results.empty:
        st.markdown("---")
        st.info("Rekomendasi destinasi wisata lain yang mungkin anda ingin kunjungi:")
        for _, row in nearby_results.iterrows():
            display_card(row)

    if base_location is not None:
        map_data = pd.concat([main_results, nearby_results])
        map_data = map_data[['Place_Name', 'Lat', 'Long', 'Category']].copy()

        st.markdown("### 🗺️ Peta Lokasi Rekomendasi")
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/streets-v11',
            initial_view_state=pdk.ViewState(
                latitude=base_location[0],
                longitude=base_location[1],
                zoom=12,
                pitch=50,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=map_data,
                    get_position='[Long, Lat]',
                    get_color='[200, 30, 0, 160]',
                    get_radius=150,
                    pickable=True
                )
            ],
            tooltip={"text": "{Place_Name} ({Category})"}
        ))
