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

route1_col, route2_col = st.columns(2)

with route1_col:
  selected_route_name_1 = st.selectbox(
    'Selecione uma rota',
    gpx_files,
    index=None,
    placeholder='Selecione uma rota...'
  )

# Main content
if selected_route_name_1:

  with route2_col:
    selected_route_name_2 = st.selectbox(
      'Comparar com',
      [f for f in gpx_files if f != selected_route_name_1],  # Exclude first selected route
      index=None,
      placeholder='Selecione uma rota...'
    )

  if selected_route_name_1 and not selected_route_name_2:
    
    # Title
    st.markdown(
      f"<h1 style='color: {COLORS['main']}'>{selected_route_name_1}</h1>",
      unsafe_allow_html=True
    )

    # Load the route
    route1 = Route(os.path.join(GPX_FILE_PATH, selected_route_name_1))
    
    # Display route stats in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
      st.metric('Distância', f"{route1.total_distance/1000:.1f} km")
    
    with col2:
      st.metric('Ganho de elevação', f"{round(route1.elevation_gain):,} m")
    
    with col3:
      st.metric('Perda de elevação', f"{round(route1.elevation_loss):,} m")
    
    with col4:
      st.metric(
        label='Ganho médio',
        value=f'{route1.avg_elevation_gain_per_km:.1f} m',
        help='Ganho médio de elevação por km'
      )

    with col5:
      st.metric(
        label=f'Subidas íngremes',
        value=f"{100*route1.hard_slope_percentage:.1f}%",
        help=f'Percentual do percurso com inclinação acima de {100*route1.HARD_SLOPE_THRESHOLD:.0f}%.'
      )
    
    # Elevation profile
    st.subheader('Perfil de elevação')
    elevation_fig = route1.plot_elevation_profile()
    st.plotly_chart(elevation_fig, use_container_width=True)

    # Map
    st.subheader('Mapa')
    map_fig = route1.plot_map()
    st_folium(
      map_fig,
      width='100%',
      height=500
    )

  if selected_route_name_1 and selected_route_name_2:
    
    # Titles
    with route1_col:
      st.markdown(
        f"<h1 style='color: {COLORS['main']}'>{selected_route_name_1}</h1>",
        unsafe_allow_html=True
      )
    
    with route2_col:
      st.markdown(
        f"<h1 style='color: {COLORS['secondary']}'>{selected_route_name_2}</h1>",
        unsafe_allow_html=True
      )