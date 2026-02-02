import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://xavzjoyjausutoscosaw.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhhdnpqb3lqYXVzdXRvc2Nvc2F3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5NjAwNzksImV4cCI6MjA4NTUzNjA3OX0.YjHw-NVeuVpK5l4XkM3hft1vSrERRBXEWZl2wPNjZ0k"
API_FOOTBALL_KEY = "bfac3e4f7d2d5736b2a5463f40876446369b215a1de43eb33983ce5e7ecb5779"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="IA Liga MX - Live", layout="wide")

# --- FUNCIÓN DE AUTO-ACTUALIZACIÓN ---
def auto_sincronizar():
    # Buscamos la jornada más alta que tengas en Supabase para saber qué actualizar
    res_jornada = supabase.table("predicciones").select("jornada").order("jornada", desc=True).limit(1).execute()
    if not res_jornada.data: return
    
    jornada_actual = res_jornada.data[0]['jornada']
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-rapidapi-key': API_FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    params = {"league": "262", "season": "2025", "round": f"Regular Season - {jornada_actual}"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        datos = response.json().get('response', [])
        for p in datos:
            if p['fixture']['status']['short'] == 'FT':
                gl, gv = p['goals']['home'], p['goals']['away']
                local_name = p['teams']['home']['name']
                # Actualiza si los goles aún están vacíos
                supabase.table("predicciones").update({"goles_l": gl, "goles_v": gv})\
                    .ilike("local", f"%{local_name}%").eq("jornada", jornada_actual).execute()
    except:
        pass # Si falla la API, la app carga igual con lo que tenga

# --- EJECUCIÓN AUTOMÁTICA AL INICIO ---
if 'actualizado' not in st.session_state:
    with st.spinner('Actualizando marcadores en tiempo real...'):
        auto_sincronizar()
        st.session_state['actualizado'] = True

# --- INTERFAZ ---
st.title("⚽ Mis Predicciones Real-Time")

res = supabase.table("predicciones").select("*").order("jornada", desc=True).execute()
df = pd.DataFrame(res.data)

if not df.empty:
    for _, r in df.iterrows():
        # Diseño de tarjeta para celular
        with st.container():
            st.markdown(f"### Jornada {r['jornada']}")
            col1, col2, col3 = st.columns([2,1,2])
            
            col1.write(f"**{r['local']}**")
            col2.write(f"VS")
            col3.write(f"**{r['visitante']}**")
            
            # Comparación IA vs Realidad
            pred = r['prediccion']
            ia_score = r['marcador_pred']
            
            if pd.notnull(r.get('goles_l')):
                real_score = f"{int(r['goles_l'])} - {int(r['goles_v'])}"
                ganador_real = "Local" if r['goles_l'] > r['goles_v'] else ("Visitante" if r['goles_v'] > r['goles_l'] else "Empate")
                
                estatus = "✅ ACERTASTE" if ganador_real == pred else "❌ FALLASTE"
                color = "green" if ganador_real == pred else "red"
                
                st.markdown(f"<p style='color:{color}; font-weight:bold;'>{estatus} (Real: {real_score} | IA: {ia_score})</p>", unsafe_allow_html=True)
            else:
                st.info(f"IA predice: {pred} ({ia_score}) | ⏳ Esperando resultado real...")
            st.divider()
else:
    st.warning("No hay datos. Envía predicciones desde tu PC.")

if st.button("🔄 Refrescar ahora"):
    st.rerun()
