import streamlit as st
from streamlit_folium import st_folium
import folium
import os
import pandas as pd
import plotly.express as px
from route import Route, RouteGroup
from utils import COLORS
import numpy as np

ROUTES_INDEX_PATH = '../data/routes-index.csv'

# Page config
st.set_page_config(
  page_title='Home',
  page_icon='🏠',
  layout='wide'
)

st.markdown('# Todas as rotas')

df = (
  pd.read_csv(ROUTES_INDEX_PATH)
  .sort_values(by='route_name')
  .reset_index(drop=True)
  .assign(
    route_distance_m=lambda x: x['route_distance_m'] / 1000,
    latitude=lambda x: x['center_coordinates'].apply(lambda y: float(y.strip('[]').split()[0])),
    longitude=lambda x: x['center_coordinates'].apply(lambda y: float(y.strip('[]').split()[1])),
  )
  .rename(columns={
    'route_name': 'Rota',
    'route_distance_m': 'Distância (km)',
    'avg_elevation_gain_per_km': 'Ganho médio por km (m)'
  })
  .style.format({
    'Distância (km)': '{:.1f}',
    'Ganho médio por km (m)': '{:.1f}'
  })
)

st.markdown('## Lista')

st.dataframe(
  df,
  column_order=[
    'Rota',
    'Distância (km)',
    'Ganho médio por km (m)'
  ],
  hide_index=True,
  use_container_width=True
)

st.markdown('## Distância vs elevação')

fig = px.scatter(
    df.data,  # Need to use .data since df is a Styler object
    x='Distância (km)',
    y='Ganho médio por km (m)',
    hover_data=['Rota'],
)

fig.update_traces(
    marker=dict(size=12, color=COLORS['main'], opacity=0.6),
    hovertemplate="<b>%{customdata[0]}</b><br><br>Distância: %{x:.1f} km<br>Ganho médio por km: %{y:.1f} m",
)

# Display the plot
st.plotly_chart(fig, use_container_width=True)

st.markdown('## Mapa mundi')

# Create a base map centered on the mean coordinates
m = folium.Map(
    location=[df.data['latitude'].mean(), df.data['longitude'].mean()],
    zoom_start=2
)

# Add markers for each route
for idx, row in df.data.iterrows():
    folium.Circle(
        location=[row['latitude'], row['longitude']],
        radius=2_000,
        tooltip=row['Rota'],
        color=COLORS['main'],
        fill=True,
        fill_opacity=0.3
    ).add_to(m)

# Display the map
st_folium(m, use_container_width=True)