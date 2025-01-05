import streamlit as st
from streamlit_folium import st_folium
import os
import pandas as pd
from route import Route, RouteGroup
from utils import COLORS

GPX_FILE_PATH = 'data/gpx/'
ROUTES_INDEX_PATH = 'data/routes-index.csv'

# Page config
st.set_page_config(
  page_title="Analise rotas",
  page_icon='🗺️',
  layout='wide'
)
  
# GPX file selection
gpx_files = [f for f in os.listdir(GPX_FILE_PATH) if f.endswith('.gpx')]
gpx_files.sort()

# GPX file to route name mapping dictionary
routes_index = pd.read_csv(ROUTES_INDEX_PATH)
gpx_files_to_route_names = {
  row['file_name']: row['route_name']
  for index, row in routes_index.iterrows()
}
route_names_to_gpx_files = {
  v: k for k, v in gpx_files_to_route_names.items()
}

route1_col, route2_col, col3 = st.columns(3)

with route1_col:
  selected_route_name_1 = st.selectbox(
    'Selecione uma rota',
    gpx_files_to_route_names.values(),
    index=None,
    placeholder='Digite ou selecione...'
  )

# Main content
if selected_route_name_1:

  with route2_col:
    selected_route_name_2 = st.selectbox(
      'Comparar com',
      [f for f in gpx_files_to_route_names.values() if f != selected_route_name_1],  # Exclude first selected route
      index=None,
      placeholder='Digite ou selecione...'
    )

  if selected_route_name_1 and not selected_route_name_2:
    
    # Title
    st.markdown(
      f"<h1 style='color: {COLORS['main']}'>{selected_route_name_1}</h1>",
      unsafe_allow_html=True
    )

    # Load the route
    route1 = Route(os.path.join(GPX_FILE_PATH, route_names_to_gpx_files[selected_route_name_1]))
    
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
    map_fig = route1.plot_map(COLORS['main'])
    st_folium(
      map_fig,
      width='100%',
      height=500
    )

  if selected_route_name_1 and selected_route_name_2:
    
    # Titles
    with route1_col:
      st.markdown(
        f"<h2 style='color: {COLORS['main']}'>{selected_route_name_1}</h2>",
        unsafe_allow_html=True
      )
    
    with route2_col:
      st.markdown(
        f"<h2 style='color: {COLORS['secondary']}'>{selected_route_name_2}</h2>",
        unsafe_allow_html=True
      )

    # Load both routes
    route1 = Route(os.path.join(GPX_FILE_PATH, route_names_to_gpx_files[selected_route_name_1]))
    route2 = Route(os.path.join(GPX_FILE_PATH, route_names_to_gpx_files[selected_route_name_2]))
    
    # Create RouteGroup for comparison
    route_group = RouteGroup(
      routes=[route1, route2],
      labels=[selected_route_name_1, selected_route_name_2]
    )
    
    # Compare stats
    stats_df = route_group.compare_stats()

    # Create comparison table
    comparison_table = f"""
    <style>
      table, tr, td, th {{
        border: none !important;
        border-collapse: collapse !important;
        border-spacing: 0 !important;
        padding: 0 !important;
        margin: 0 !important;
      }}
    </style>
    <table width="100%">
      <tr>
        <td width="33%"><h4 style="color: {COLORS['main']}">{stats_df.loc['Distance (km)'][selected_route_name_1]:.1f} km</h4></td>
        <td width="33%"><h4 style="color: {COLORS['secondary']}">{stats_df.loc['Distance (km)'][selected_route_name_2]:.1f} km</h4></td>
        <td><h4>Distância</h4></td>
      </tr>
      <tr>
        <td><h4 style="color: {COLORS['main']}">{stats_df.loc['Elevation Gain (m)'][selected_route_name_1]:,.0f} m</h4></td>
        <td><h4 style="color: {COLORS['secondary']}">{stats_df.loc['Elevation Gain (m)'][selected_route_name_2]:,.0f} m</h4></td>
        <td><h4>Ganho de elevação</h4></td>
      </tr>
      <tr>
        <td><h4 style="color: {COLORS['main']}">{stats_df.loc['Elevation Loss (m)'][selected_route_name_1]:,.0f} m</h4></td>
        <td><h4 style="color: {COLORS['secondary']}">{stats_df.loc['Elevation Loss (m)'][selected_route_name_2]:,.0f} m</h4></td>
        <td><h4>Perda de elevação</h4></td>
      </tr>
      <tr>
        <td><h4 style="color: {COLORS['main']}">{stats_df.loc['Avg Gain per km (m)'][selected_route_name_1]:.1f} m</h4></td>
        <td><h4 style="color: {COLORS['secondary']}">{stats_df.loc['Avg Gain per km (m)'][selected_route_name_2]:.1f} m</h4></td>
        <td><h4>Ganho médio</h4></td>
      </tr>
      <tr>
        <td><h4 style="color: {COLORS['main']}">{stats_df.loc['Hard Slopes (%)'][selected_route_name_1]:.1f}%</h4></td>
        <td><h4 style="color: {COLORS['secondary']}">{stats_df.loc['Hard Slopes (%)'][selected_route_name_2]:.1f}%</h4></td>
        <td><h4>Subidas íngremes</h4></td>
      </tr>
    </table>
    """

    st.markdown(comparison_table, unsafe_allow_html=True)

    # Elevation comparison
    st.subheader('Perfil de elevação')
    elevation_fig = route_group.plot_elevation_comparison()
    st.plotly_chart(elevation_fig, use_container_width=True)
    
    # Plot routes on map
    st.subheader('Mapas')

    # Calculate distance between routes
    distance = route_group.calculate_routes_distance()

    if distance < 50_000:
      map_fig = route_group.plot_combined_map()
      st_folium(map_fig, width='100%', height=500)
    else:
      map1_col, map2_col = st.columns(2)
      
      with map1_col:
        map1 = route1.plot_map(COLORS['main'])
        st_folium(map1, width='100%', height=500)
        
      with map2_col:
        map2 = route2.plot_map(COLORS['secondary'])
        st_folium(map2, width='100%', height=500)
