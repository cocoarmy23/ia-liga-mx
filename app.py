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

# --- PANEL DE CONTROL ABIERTO ---
st.title("🏆 Centro de Mando: Modelo Híbrido")

st.markdown("### ⚙️ Configuración de la Agenda")
col1, col2 = st.columns(2)

with col1:
    hora_inicio = st.number_input("Hora de Inicio (24h)", value=17, min_value=0, max_value=23)
    presupuesto = st.slider("Presupuesto de consultas", 10, 100, 90)

with col2:
    hora_fin = st.number_input("Hora de Fin (24h)", value=23, min_value=0, max_value=23)
    st.metric("Límite Diario API", "100/100")

# Botón de Sincronización Manual
if st.button("🔄 SINCRONIZAR AHORA (Gasta 1 consulta)"):
    st.write("Conectando con la API...")
    # Aquí irá la lógica de actualización que ya tenemos

# Switch para el Modo Live
modo_live = st.toggle("🚀 ACTIVAR MODO LIVE (Auto-actualización)")

if modo_live:
    ahora = datetime.now()
    if hora_inicio <= ahora.hour < hora_fin:
        # Cálculo dinámico del intervalo
        minutos_restantes = (hora_fin - ahora.hour) * 60
        intervalo_minutos = max(minutos_restantes / presupuesto, 1.0)
        
        st.success(f"Modo Live Activo. Actualizando cada {intervalo_minutos:.1f} minutos.")
        
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=intervalo_minutos * 60 * 1000, key="live_v2")
        except:
            st.error("Error: Revisa que 'streamlit-autorefresh' esté en requirements.txt")
    else:
        st.info("Modo Live en espera: Fuera del horario establecido.")

st.divider()

# --- VISUALIZACIÓN DE PARTIDOS ---
st.markdown("### 📊 Predicciones Jornada 5")
# Aquí cargamos los datos de Supabase como ya lo hacíamos
try:
    data = supabase.table("predicciones").select("*").order("jornada", desc=True).execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        st.table(df[['jornada', 'local', 'visitante', 'prediccion', 'marcador_pred']])
    else:
        st.info("No hay datos de la Jornada 5 en Supabase aún.")
except:
    st.error("Error al conectar con la base de datos.")
