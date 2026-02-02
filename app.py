import streamlit as st
import pandas as pd
import requests
from supabase import create_client, Client
from datetime import datetime, time

# --- CONFIGURACIÓN ---
URL_SUPABASE = "https://xavzjoyjausutoscosaw.supabase.co"
KEY_SUPABASE = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhhdnpqb3lqYXVzdXRvc2Nvc2F3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk5NjAwNzksImV4cCI6MjA4NTUzNjA3OX0.YjHw-NVeuVpK5l4XkM3hft1vSrERRBXEWZl2wPNjZ0k"
API_KEY = "bfac3e4f7d2d5736b2a5463f40876446369b215a1de43eb33983ce5e7ecb5779"

supabase: Client = create_client(URL_SUPABASE, KEY_SUPABASE)

st.set_page_config(page_title="IA Liga MX - Pro", layout="wide")

# --- PANEL DE CONTROL ABIERTO ---
st.title("🏆 Centro de Mando: Modelo Híbrido")

st.markdown("### ⚙️ Configuración de la Agenda (Exacta)")
col1, col2 = st.columns(2)

with col1:
    # Ahora usamos time_input para tener horas y minutos exactos
    h_inicio = st.time_input("¿A qué hora empieza la jornada?", time(17, 00))
    presupuesto = st.slider("Presupuesto de consultas (Máx 100)", 10, 100, 90)

with col2:
    h_fin = st.time_input("¿A qué hora termina la jornada?", time(23, 30))
    st.metric("Límite Diario API", "100/100")

# Switch para el Modo Live
modo_live = st.toggle("🚀 ACTIVAR MODO LIVE (Auto-actualización)")

if modo_live:
    ahora = datetime.now()
    # Convertimos todo a minutos desde el inicio del día para calcular fácil
    minutos_ahora = ahora.hour * 60 + ahora.minute
    minutos_inicio = h_inicio.hour * 60 + h_inicio.minute
    minutos_fin = h_fin.hour * 60 + h_fin.minute
    
    if minutos_inicio <= minutos_ahora < minutos_fin:
        # Cálculo dinámico preciso
        minutos_restantes = minutos_fin - minutos_ahora
        intervalo_minutos = max(minutos_restantes / presupuesto, 0.5) # Mínimo 30 segundos
        
        st.success(f"✅ Modo Live Activo. Actualizando cada {intervalo_minutos:.2f} minutos.")
        st.info(f"Faltan {minutos_restantes} minutos para el cierre programado.")
        
        try:
            from streamlit_autorefresh import st_autorefresh
            st_autorefresh(interval=intervalo_minutos * 60 * 1000, key="live_v3_minutes")
        except:
            st.error("Error: Revisa que 'streamlit-autorefresh' esté en requirements.txt")
    else:
        st.warning("⚠️ Fuera de rango: El Modo Live se activará automáticamente a la hora de inicio.")

st.divider()

# --- VISUALIZACIÓN DE PARTIDOS ---
st.markdown("### 📊 Predicciones")
try:
    res = supabase.table("predicciones").select("*").order("jornada", desc=True).execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # Estilizamos un poco la tabla para que se vea mejor en móvil
        st.dataframe(df[['jornada', 'local', 'visitante', 'prediccion', 'marcador_pred']], use_container_width=True)
    else:
        st.info("No hay datos en Supabase. Sube la Jornada 5 desde tu PC.")
except Exception as e:
    st.error(f"Error de base de datos: {e}")
