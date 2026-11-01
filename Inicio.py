import streamlit as st
import paho.mqtt.client as mqtt
import json
import time

# Configuración de la página
st.set_page_config(
    page_title="Cava de Vinos",
    page_icon="🍷",
    layout="centered"
)

# ------------------------------------------------------------------
# TEMA "CAVA DE VINOS" (solo estilos CSS; la lógica y los inputs no cambian)
# ------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600;700&family=Nunito:wght@400;600;700&display=swap');

:root{
  --vino:#6b1e2e;
  --vino-oscuro:#3f0f1a;
  --dorado:#c9a45c;
  --dorado-claro:#f3e7cc;
  --crema:#faf6ef;
  --piedra:#efe7da;
  --tinta:#1f1a17;
}

/* Fondo: muro de piedra clara de la cava */
.stApp{
  background:
    repeating-linear-gradient(0deg, transparent 0 58px, rgba(140,110,80,.07) 58px 60px),
    var(--piedra);
  background-attachment: fixed;
}
header[data-testid="stHeader"]{ background: transparent; }

/* Panel central: etiqueta de botella */
[data-testid="stMainBlockContainer"], .block-container{
  background:var(--crema);
  border-radius:20px;
  border:1px solid rgba(201,164,92,.55);
  box-shadow:0 20px 50px rgba(63,15,26,.14);
  margin-top:2rem;
  margin-bottom:4rem;
  padding:1.6rem 2.2rem 2.4rem !important;
  max-width:780px;
}
@media (max-width:640px){
  [data-testid="stMainBlockContainer"], .block-container{
    padding:1.1rem 1rem 1.8rem !important;
  }
}

/* Encabezado: placa de la cava */
.cava-hero{
  border-radius:16px;
  padding:1.8rem 1.8rem 1.6rem;
  margin-bottom:.6rem;
  background:linear-gradient(135deg, var(--vino-oscuro) 0%, var(--vino) 100%);
  box-shadow: inset 0 0 0 1px rgba(201,164,92,.5), inset 0 0 0 6px var(--vino-oscuro), inset 0 0 0 7px rgba(201,164,92,.35);
}
.cava-tag{
  display:inline-block;
  font-family:'Nunito', sans-serif;
  font-weight:700; font-size:.78rem; letter-spacing:.16em; text-transform:uppercase;
  color:var(--vino-oscuro);
  background:var(--dorado);
  padding:.3rem .8rem; border-radius:999px;
}
.cava-title{
  font-family:'Cormorant Garamond', serif;
  font-weight:700; font-size:3rem; line-height:1.05;
  color:var(--dorado-claro);
  margin:.8rem 0 .4rem;
}
.cava-sub{
  font-family:'Nunito', sans-serif;
  font-size:1.05rem; line-height:1.55;
  color:#f5ece6;
  max-width:540px;
}
.cava-ideal{ display:flex; flex-wrap:wrap; gap:.5rem; margin-top:1.1rem; }
.cava-ideal span{
  font-family:'Nunito', sans-serif; font-weight:700; font-size:.9rem;
  color:#ffffff;
  background:rgba(255,255,255,.1);
  border:1px solid rgba(201,164,92,.55);
  padding:.35rem .85rem; border-radius:999px;
}
@media (max-width:640px){
  .cava-title{ font-size:2.2rem; }
}

/* Títulos y textos del contenido */
h2, h3{
  font-family:'Cormorant Garamond', serif !important;
  font-weight:700 !important;
  color:var(--vino) !important;
}
h1 a, h2 a, h3 a{ display:none !important; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li{
  font-family:'Nunito', sans-serif;
  line-height:1.6;
}
.stApp hr{ border-color: rgba(201,164,92,.45); }

/* Lecturas: fichas tipo etiqueta de vino */
[data-testid="stMetric"]{
  background:#ffffff;
  border:1px solid rgba(201,164,92,.6);
  border-top:4px solid var(--vino);
  border-radius:14px;
  padding:1rem 1.1rem;
}
[data-testid="stMetricLabel"] p{
  font-weight:700 !important;
  letter-spacing:.08em;
  text-transform:uppercase;
}
.stApp [data-testid="stMetricValue"]{
  font-family:'Cormorant Garamond', serif;
  font-weight:700;
  color:var(--vino) !important;
}

/* Barra lateral: piedra cálida */
section[data-testid="stSidebar"]{
  background:var(--crema);
  border-right:3px solid var(--vino);
}
section[data-testid="stSidebar"] h3{ font-size:1.3rem !important; }

/* Textos sobre fondos claros: siempre en negro (también si Streamlit usa el tema oscuro) */
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stWidgetLabel"] label,
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] li,
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="caption"],
.stApp [data-testid="stAlert"] [data-testid="stMarkdownContainer"] *{
  color:#1a1a1a !important;
}

/* Botones: conservan los colores originales de Streamlit (contraste) */
.stApp button [data-testid="stMarkdownContainer"],
.stApp button [data-testid="stMarkdownContainer"] *,
.stApp button [data-testid="stMarkdownContainer"] p{
  color:inherit !important;
  font-family:inherit !important;
}
</style>
""", unsafe_allow_html=True)


# Variables de estado
if 'sensor_data' not in st.session_state:
    st.session_state.sensor_data = None

def get_mqtt_message(broker, port, topic, client_id):
    """Función para obtener un mensaje MQTT"""
    message_received = {"received": False, "payload": None}
    
    def on_message(client, userdata, message):
        try:
            payload = json.loads(message.payload.decode())
            message_received["payload"] = payload
            message_received["received"] = True
        except:
            # Si no es JSON, guardar como texto
            message_received["payload"] = message.payload.decode()
            message_received["received"] = True
    
    try:
        client = mqtt.Client(client_id=client_id)
        client.on_message = on_message
        client.connect(broker, port, 60)
        client.subscribe(topic)
        client.loop_start()
        
        # Esperar máximo 5 segundos
        timeout = time.time() + 5
        while not message_received["received"] and time.time() < timeout:
            time.sleep(0.1)
        
        client.loop_stop()
        client.disconnect()
        
        return message_received["payload"]
    
    except Exception as e:
        return {"error": str(e)}

# Sidebar - Configuración
with st.sidebar:
    st.subheader('🔌 Conexión con la cava')
    
    broker = st.text_input('Servidor (broker MQTT)', value='broker.mqttdashboard.com', 
                           help='Dirección del servidor MQTT al que publica el sensor de la cava')
    
    port = st.number_input('Puerto', value=1883, min_value=1, max_value=65535,
                           help='Puerto del servidor (generalmente 1883)')
    
    topic = st.text_input('Tópico del sensor', value='Sensor/THP2',
                          help='Canal donde el sensor de la cava publica la temperatura y la humedad')
    
    client_id = st.text_input('ID del cliente', value='streamlit_client',
                              help='Identificador único para esta conexión')

# Título
st.markdown("""
<div class="cava-hero">
  <span class="cava-tag">🍷 Monitor de cava</span>
  <div class="cava-title">Cava de Vinos</div>
  <div class="cava-sub">Revisa la temperatura y la humedad de tu cava en tiempo real. Un buen vino se cuida con calma, en un lugar fresco y estable.</div>
  <div class="cava-ideal"><span>🌡️ Ideal: 10 – 15 °C</span><span>💧 Ideal: 60 – 75 % de humedad</span></div>
</div>
""", unsafe_allow_html=True)

# Información al inicio
with st.expander('ℹ️ Cómo usar esta app', expanded=False):
    st.markdown("""
    ### Cómo revisar tu cava:
    
    1. **Servidor (broker MQTT)**: la dirección del servidor al que publica el sensor (barra lateral)
    2. **Puerto**: generalmente es 1883 para conexiones no seguras
    3. **Tópico del sensor**: el canal donde el sensor de la cava envía sus lecturas
    4. **ID del cliente**: un identificador único para esta conexión
    5. Haz clic en **Revisar la cava** para recibir la lectura más reciente
    
    El sensor envía la temperatura (**Temp**, en °C) y la humedad (**Hum**, en %).
    
    ### Servidores públicos para pruebas:
    - broker.mqttdashboard.com
    - test.mosquitto.org
    - broker.hivemq.com
    """)

st.divider()

# Botón para obtener datos
if st.button('🍷 Revisar la cava', use_container_width=True):
    with st.spinner('Bajando a la cava y leyendo el sensor...'):
        sensor_data = get_mqtt_message(broker, int(port), topic, client_id)
        st.session_state.sensor_data = sensor_data

# Mostrar resultados
if st.session_state.sensor_data:
    st.divider()
    st.subheader('🍇 Condiciones de la cava')
    
    data = st.session_state.sensor_data
    
    # Verificar si hay error
    if isinstance(data, dict) and 'error' in data:
        st.error(f"❌ No pudimos conectar con la cava: {data['error']}")
    else:
        st.success('✅ Lectura recibida de la cava')
        
        # Mostrar datos en formato JSON
        if isinstance(data, dict):
            # Mostrar cada campo en una métrica
            cols = st.columns(len(data))
            for i, (key, value) in enumerate(data.items()):
                with cols[i]:
                    st.metric(label=key, value=value)
            
            # Mostrar JSON completo
            with st.expander('Ver lectura completa (JSON)'):
                st.json(data)
        else:
            # Si no es diccionario, mostrar como texto
            st.code(data)
