import streamlit as st
from streamlit_folium import st_folium
import os
from route import Route, RouteGroup
from utils import COLORS

# Page config
st.set_page_config(
  page_title='Home',
  page_icon='🏠',
  layout='wide'
)

st.markdown('# Todas as rotas')

st.markdown('## Lista')

st.markdown('## Distância vs elevação')

st.markdown('## Mapa mundi')
