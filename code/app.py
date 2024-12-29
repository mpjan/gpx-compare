import streamlit as st
from streamlit_folium import st_folium
import os
from route import Route
from viz_constants import COLORS

GPX_FILE_PATH = '../gpx/'

# Page config
st.set_page_config(
  page_title="Explore Rotas",
  page_icon='🗺️',
  layout='wide'
)

# Sidebar
with st.sidebar:
  st.write('🗺️ Explore rotas')
  st.write('🏃 Eventos')
  st.write('🌍 Mapa mundi')
  
# GPX file selection
gpx_files = [f for f in os.listdir(GPX_FILE_PATH) if f.endswith('.gpx')]
gpx_files.sort()

selected_gpx = st.selectbox(
  'Selecione uma rota',
  gpx_files,
  index=None,
  placeholder='Selecione uma rota...'
)

# Title
if selected_gpx:
  st.markdown(
    f"<h1 style='color: {COLORS['main']}'>{selected_gpx}</h1>",
    unsafe_allow_html=True
  )

# Main content
if selected_gpx:
  # Load the route
  route = Route(os.path.join(GPX_FILE_PATH, selected_gpx))
  
  # Display route stats in columns
  col1, col2, col3, col4, col5 = st.columns(5)
  
  with col1:
    st.metric('Distância', f"{route.total_distance/1000:.1f} km")
  
  with col2:
    st.metric('Ganho de elevação', f"{round(route.elevation_gain):,} m")
  
  with col3:
    st.metric('Perda de elevação', f"{round(route.elevation_loss):,} m")
  
  with col4:
    st.metric(
      label='Ganho médio',
      value=f'{route.avg_elevation_gain_per_km:.1f} m',
      help='Ganho médio de elevação por km'
    )

  with col5:
    st.metric(
      label=f'Subidas íngremes',
      value=f"{100*route.hard_slope_percentage:.1f}%",
      help=f'Percentual do percurso com inclinação acima de {100*route.HARD_SLOPE_THRESHOLD:.0f}%.'
    )
  
  # Elevation profile
  st.subheader('Perfil de elevação')
  elevation_fig = route.plot_elevation_profile()
  st.plotly_chart(elevation_fig, use_container_width=True)

  # Map
  st.subheader('Mapa')
  map_fig = route.plot_map()
  st_folium(
    map_fig,
    width='100%',
    height=500
  )