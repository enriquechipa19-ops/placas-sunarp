import streamlit as st
import main
import consunarp
import citvv
import os

# Configuración de la página web
st.set_page_config(
    page_title="Consulta Vehicular Inteligente", 
    page_icon="🚗", 
    layout="centered"
)

# Estilo visual y encabezado
st.title("🚗 Sistema Automatizado de Consulta Vehicular")
st.markdown("### Plataforma Inteligente de Identificación y Auditoría Legal")
st.write("Sube una fotografía de la placa del vehículo para realizar una consulta automatizada en tiempo real a las bases de datos de **SUNARP** y el **MTC (CITV)**.")

# Componente para subir la imagen
uploaded_file = st.file_uploader("Selecciona o arrastra una imagen de la placa...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Guardar la imagen temporalmente
    path_foto = "temp_placa.jpg"
    with open(path_foto, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    # Mostrar la imagen cargada
    st.image(path_foto, caption="Fotografía analizada por el modelo YOLO", width=350)
    
    if st.button("🚀 Ejecutar Consulta Completa"):
        with st.spinner("Analizando imagen con Inteligencia Artificial (YOLO + EasyOCR)..."):
            placa = main.ejecutar_ocr(path_foto)
            
        if not placa:
            st.error("❌ No se pudo detectar una placa válida en la imagen. Intenta con otra fotografía más clara.")
        else:
            placa_neta = placa.replace("-", "")
            st.success(f"✅ Placa detectada con éxito: **{placa}** (Normalizada: `{placa_neta}`)")
            
            # Crear columnas para organizar los reportes institucionales
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### 📋 Reporte SUNARP")
                with st.spinner("Consultando registros de propiedad..."):
                    try:
                        datos_sunarp = consunarp.consultar_sunarp(placa_neta)
                        if isinstance(datos_sunarp, dict):
                            for k, v in datos_sunarp.items():
                                st.markdown(f"**• {k}:** {v}")
                        else:
                            st.write(datos_sunarp)
                    except Exception as e:
                        st.error(f"Error al consultar SUNARP: {e}")
                    
            with col2:
                st.markdown("### 🛠 Reporte MTC (CITV)")
                with st.spinner("Consultando revisiones técnicas..."):
                    try:
                        datos_mtc = citvv.consultar_mtc(placa_neta)
                        if isinstance(datos_mtc, dict):
                            for k, v in datos_mtc.items():
                                st.markdown(f"**• {k}:** {v}")
                        else:
                            st.write(datos_mtc)
                    except Exception as e:
                        st.error(f"Error al consultar MTC: {e}")