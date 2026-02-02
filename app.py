import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://xavzjoyjausutoscosaw.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhhdnpqb3lqYXVzdXRvc2Nvc2F3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5NjAwNzksImV4cCI6MjA4NTUzNjA3OX0.YjHw-NVeuVpK5l4XkM3hft1vSrERRBXEWZl2wPNjZ0k"
API_FOOTBALL_KEY = "bfac3e4f7d2d5736b2a5463f40876446369b215a1de43eb33983ce5e7ecb5779"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="IA Liga MX - Dashboard", layout="wide")

# --- FUNCIÓN DE SINCRONIZACIÓN AUTOMÁTICA ---
def sincronizar_con_api(jornada):
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-rapidapi-key': API_FOOTBALL_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    params = {"league": "262", "season": "2025", "round": f"Regular Season - {jornada}"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        datos = response.json().get('response', [])
        
        actualizados = 0
        for p in datos:
            if p['fixture']['status']['short'] == 'FT': # Partido Terminado
                gl, gv = p['goals']['home'], p['goals']['away']
                local_name = p['teams']['home']['name']
                
                # Buscamos por nombre de equipo local y jornada
                supabase.table("predicciones").update({
                    "goles_l": gl, 
                    "goles_v": gv
                }).ilike("local", f"%{local_name}%").eq("jornada", jornada).execute()
                actualizados += 1
        return actualizados
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return 0

# --- INTERFAZ ---
st.title("🏆 IA Predictor & Live Tracker")

menu = st.sidebar.selectbox("Acción", ["Ver Mis Predicciones", "Sincronizar Resultados Real-Time"])

if menu == "Ver Mis Predicciones":
    st.subheader("📊 Seguimiento de la Jornada")
    res = supabase.table("predicciones").select("*").order("jornada", desc=True).execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        for _, r in df.iterrows():
            with st.expander(f"J{r['jornada']} | {r['local']} vs {r['visitante']}"):
                col1, col2, col3 = st.columns(3)
                col1.metric("Predicción", r['prediccion'])
                col2.metric("Marcador IA", r['marcador_pred'])
                
                # Lógica de acierto
                if pd.notnull(r.get('goles_l')):
                    real = f"{int(r['goles_l'])} - {int(r['goles_v'])}"
                    ganador_real = "Local" if r['goles_l'] > r['goles_v'] else ("Visitante" if r['goles_v'] > r['goles_l'] else "Empate")
                    
                    if ganador_real == r['prediccion']:
                        col3.success(f"REAL: {real} ✅")
                    else:
                        col3.error(f"REAL: {real} ❌")
                else:
                    col3.info("Esperando resultado...")
    else:
        st.write("No hay datos en la nube.")

elif menu == "Sincronizar Resultados Real-Time":
    st.subheader("🔄 Actualizador Automático")
    j_sync = st.number_input("¿Qué jornada quieres actualizar?", min_value=1, max_value=17, value=1)
    
    if st.button("🚀 TRAER RESULTADOS DE LA API"):
        with st.spinner("Conectando con la API de Football..."):
            n = sincronizar_con_api(j_sync)
            if n > 0:
                st.balloons()
                st.success(f"¡Sincronización completa! Se actualizaron {n} partidos.")
            else:
                st.warning("No se encontraron partidos finalizados para esta jornada en la API.")