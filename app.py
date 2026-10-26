import streamlit as st
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import pandas as pd
import time

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Monitor de Tanque Inteligente",
    page_icon="💧",
    layout="wide"
)

# --- INICIALIZACIÓN DE FIREBASE ---
@st.cache_resource
def inicializar_firebase():
    # URL CORREGIDA CON EL ID DE TU PROYECTO REAL
    FIREBASE_DB_URL = "https://monitoreo-tanque-oled-default-rtdb.firebaseio.com/"

    
    cred = credentials.Certificate("firebase_credentials.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })

try:
    inicializar_firebase()
except Exception as e:
    st.error(f"Error al conectar con Firebase: {e}")

# --- FUNCIÓN PARA OBTENER DATOS ---
def obtener_datos_tanque():
    try:
        ref = db.reference('/tanque')
        return ref.get()
    except Exception as e:
        st.error(f"Error al leer datos: {e}")
        return None

# --- ESTRUCTURA DEL DASHBOARD ---
st.title("📊 Panel de Monitoreo: Tanque de Agua")
st.markdown("Monitoreo en tiempo real del nivel, volumen y suministro de red.")
st.divider()

# Contenedores dinámicos
bloque_metricas = st.empty()
bloque_grafico = st.empty()

# Histórico temporal en memoria para la sesión de visualización activa
if "historico_porcentaje" not in st.session_state:
    st.session_state.historico_porcentaje = []

# --- BUCLE DE REFRESCO AUTOMÁTICO EN TIEMPO REAL ---
while True:
    datos = obtener_datos_tanque()
    
    if datos:
        porcentaje = datos.get('porcentaje', 0.0)
        metros = datos.get('metros', 0.0)
        entrada_calle = datos.get('entradaCalle', False)
        
        # Añadir al historial local (guardamos los últimos 30 registros para la gráfica de línea)
        st.session_state.historico_porcentaje.append(porcentaje)
        if len(st.session_state.historico_porcentaje) > 30:
            st.session_state.historico_porcentaje.pop(0)
            
        # 1. Renderizar tarjetas de datos métricos
        with bloque_metricas.container():
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    label="Nivel del Tanque (%)", 
                    value=f"{porcentaje:.1f} %",
                    delta=f"{porcentaje - 100:.1f} % para llenado total" if porcentaje < 100 else "¡Tanque Lleno!"
                )
                
            with col2:
                st.metric(
                    label="Altura del Agua", 
                    value=f"{metros:.2f} m"
                )
                
            with col3:
                estado_calle = "✅ Flujo Detectado" if entrada_calle else "❌ Sin Entrada"
                st.metric(
                    label="Estado de Entrada Calle", 
                    value=estado_calle
                )
        
        # 2. Renderizar Gráfico de Línea Temporal
        with bloque_grafico.container():
            st.subheader("📈 Historial de Nivel de Agua (Muestras Recientes)")
            df_historico = pd.DataFrame(st.session_state.historico_porcentaje, columns=["Porcentaje Llenado"])
            st.line_chart(df_historico, y="Porcentaje Llenado")
            
    else:
        st.warning("Buscando datos en Firebase... Asegúrate de que el ESP8266 esté encendido y transmitiendo.")

    # Sincronización de lectura cada 2 segundos
    time.sleep(2)
