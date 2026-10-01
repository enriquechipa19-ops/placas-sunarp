from ultralytics import YOLO
import cv2
import easyocr
import re
import sys
import os
import requests

# Enlace directo de descarga desde tu GitHub Release
URL_MODELO_GITHUB = "https://github.com/enriquechipa19-ops/placas-sunarp/releases/download/v1.0/best2st.pt"
NOMBRE_MODELO = "best2st.pt"

# Función para asegurar que el modelo se encuentre localmente o se descargue desde GitHub Release
def obtener_ruta_modelo(nombre_archivo):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, nombre_archivo)
    
    ruta_local = os.path.join(os.path.abspath("."), nombre_archivo)
    
    # Si no existe (en Streamlit Cloud), lo descargamos automáticamente
    if not os.path.exists(ruta_local):
        print("Descargando el modelo optimizado desde GitHub Release...")
        try:
            response = requests.get(URL_MODELO_GITHUB, stream=True)
            response.raise_for_status()
            with open(ruta_local, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print("¡Modelo descargado y listo con éxito!")
        except Exception as e:
            print(f"Error al descargar el modelo: {e}")
            
    return ruta_local

# 1. Configuración
MODELO_YOLO = obtener_ruta_modelo(NOMBRE_MODELO)
modelo = YOLO(MODELO_YOLO)
lector = easyocr.Reader(['es'], gpu=False)

# 2. Funciones de procesamiento
def generar_preprocesamientos(imagen):
    alto, ancho = imagen.shape[:2]
    recorte = imagen[int(alto*0.2):alto, :] 
    gris = cv2.cvtColor(recorte, cv2.COLOR_BGR2GRAY)
    imagenes = []
    
    # 1. Contraste
    contraste = cv2.convertScaleAbs(gris, alpha=1.2, beta=10)
    imagenes.append(contraste)
    # 2. Otsu
    _, otsu = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    imagenes.append(otsu)
    # 3. Invertido
    _, inv = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    imagenes.append(inv)
    return imagenes

def limpiar(texto):
    texto = texto.upper().replace(" ", "").replace("PERU", "").replace("PER", "")
    if len(texto) >= 3:
        if texto[0] in ['4', '0', 'A', 'O']:
            texto = 'V' + texto[1:]
    texto = re.sub(r'[^A-Z0-9-]', '', texto)
    return texto

def leer_placa(imagenes):
    mejor = ""
    mejor_confianza = 0
    for img in imagenes:
        resultado = lector.readtext(img, detail=1, paragraph=False, allowlist="ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")
        for lectura in resultado:
            texto = limpiar(lectura[1])
            confianza = lectura[2]
            if confianza > mejor_confianza and len(texto) >= 5:
                mejor = texto
                mejor_confianza = confianza
    return mejor, mejor_confianza

# 3. Lógica para el bot
def ejecutar_ocr(imagen_path):
    original = cv2.imread(imagen_path)
    resultados = modelo.predict(source=imagen_path, conf=0.55, iou=0.45, device="cpu", verbose=False)
    
    if not resultados[0].boxes:
        return None

    for caja in resultados[0].boxes:
        x1, y1, x2, y2 = map(int, caja.xyxy[0])
        if (x2 - x1) < 80: continue

        placa_img = original[y1:y2, x1:x2]
        imagenes = generar_preprocesamientos(placa_img)
        texto, conf = leer_placa(imagenes)

        if texto and len(texto) >= 5:
            return texto
    return None