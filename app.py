import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://xavzjoyjausutoscosaw.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhhdnpqb3lqYXVzdXRvc2Nvc2F3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5NjAwNzksImV4cCI6MjA4NTUzNjA3OX0.YjHw-NVeuVpK5l4XkM3hft1vSrERRBXEWZl2wPNjZ0k"
API_KEY = "bfac3e4f7d2d5736b2a5463f40876446369b215a1de43eb33983ce5e7ecb5779"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="IA Liga MX - Pro", layout="wide")

# --- SIDEBAR: CONTROLADOR DE PRESUPUESTO ---
st.sidebar.header("⚙️ Control de API")
presupuesto_diario = 100
# Simulamos un contador (Streamlit Cloud reinicia sesión, pero esto ayuda a trackear)
if 'consultas_hoy' not in st.session_state:
    st.session_state['consultas_hoy'] = 0

consultas_restantes = presupuesto_diario - st.session_state['consultas_hoy']
st.sidebar.metric("Consultas Restantes", f"{consultas_restantes}/100")

modo_live = st.sidebar.toggle("Activar Modo Live (Auto-refresco)")
if modo_live:
    intervalo = st.sidebar.slider("Refrescar cada (minutos)", 1, 15, 5)
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=intervalo * 60 * 1000, key="auto_refresco")

# --- FUNCIÓN DE ACTUALIZACIÓN ---
def sincronizar_datos():
    st.session_state['consultas_hoy'] += 1
    # Traemos la última jornada de Supabase
    res = supabase.table("predicciones").select("jornada").order("jornada", desc=True).limit(1).execute()
    if not res.data: return
    jor = res.data[0]['jornada']
    
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {'x-rapidapi-key': API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
    params = {"league": "262", "season": "2025", "round": f"Regular Season - {jor}"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        partidos = response.json().get('response', [])
        for p in partidos:
            if p['fixture']['status']['short'] == 'FT':
                gl, gv = p['goals']['home'], p['goals']['away']
                equipo_local = p['teams']['home']['name']
                supabase.table("predicciones").update({"goles_l": gl, "goles_v": gv})\
                    .ilike("local", f"%{equipo_local}%").eq("jornada", jor).execute()
    except Exception as e:
        st.error(f"Error de conexión: {e}")

# Ejecución al cargar
if st.sidebar.button("🔄 Sincronizar Ahora"):
    with st.spinner("Conectando con la API..."):
        sincronizar_datos()

# --- DASHBOARD PRINCIPAL ---
st.title("🏆 Resultados Modelo Híbrido")

data = supabase.table("predicciones").select("*").order("jornada", desc=True).execute()
df = pd.DataFrame(data.data)

if not df.empty:
    for _, r in df.iterrows():
        with st.expander(f"Jornada {r['jornada']}: {r['local']} vs {r['visitante']}", expanded=True):
            c1, c2, c3 = st.columns(3)
            
            # Mostrar Marcador Real si existe
            if pd.notnull(r['goles_l']):
                real_l, real_v = int(r['goles_l']), int(r['goles_v'])
                ganador_real = "Local" if real_l > real_v else ("Visitante" if real_v > real_l else "Empate")
                es_acierto = ganador_real == r['prediccion']
                
                c1.metric("Resultado Real", f"{real_l} - {real_v}")
                c2.metric("Predicción IA", r['prediccion'], delta="✅ ACERTO" if es_acierto else "❌ ERROR")
                c3.write(f"**Marcador IA:** {r['marcador_pred']}")
            else:
                c1.warning("Esperando juego...")
                c2.info(f"Predicción: {r['prediccion']}")
                c3.write(f"Sugerido: {r['marcador_pred']}")
else:
    st.info("Sube tus predicciones de la Jornada 5 desde tu PC para empezar.")
