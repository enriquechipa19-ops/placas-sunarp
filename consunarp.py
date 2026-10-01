import time
import requests
from seleniumbase import SB
from PIL import Image
import pytesseract
import re
import os
import cv2
import numpy as np

# ======================== CONFIGURACIÓN ========================
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

URL = "https://consultavehicular.sunarp.gob.pe/consulta-vehicular/inicio"

PREFIJOS_A_MANTENER = [
    "DATOS DEL VEHÍCULO", "N° PLACA:", "N* PLACA:", "NO PLACA:", "N? PLACA:", 
    "N° SERIE:", "N* SERIE:", "NO SERIE:", "N° VIN:", "N° MOTOR:", "COLOR:", 
    "MARCA:", "MODELO:", "PLACA VIGENTE:", "PLACA ANTERIOR:", "ESTADO:", 
    "ANOTACIONES:", "SEDE:", "AÑO DE MODELO:", "PROPIETARIO(S):"
]

EQUIVALENCIAS_PREFIJOS = {
    "NO9PLACA": "N° PLACA", "NOSERIE": "N° SERIE", "N*MOTOR": "N° MOTOR", 
    "NEVIN": "N° VIN", "N*VIN": "N° VIN", "N? PLACA": "N° PLACA", "N?PLACA": "N° PLACA", 
    "PLACAVIGENTE": "PLACA VIGENTE", "PLACA ANTERIOR": "PLACA ANTERIOR", 
    "N°PLACA": "N° PLACA", "N°SERIE": "N° SERIE", "N°MOTOR": "N° MOTOR", 
    "N°VIN": "N° VIN", "NO PLACA": "N° PLACA", "NO SERIE": "N° SERIE", 
    "NO MOTOR": "N° MOTOR", "NO VIN": "N° VIN"
}

# ==================== FUNCIONES DE PROCESAMIENTO ====================
def preprocesar_para_ocr(ruta_imagen):
    img = cv2.imread(ruta_imagen)
    if img is None: return
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharpened = cv2.filter2D(enhanced, -1, kernel)
    _, binary = cv2.threshold(sharpened, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    cv2.imwrite(ruta_imagen, binary)

def limpiar_valor(texto):
    texto = re.sub(r'[^A-Z0-9\s\-]', '', texto, flags=re.IGNORECASE)
    partes = texto.split()
    partes_filtradas = [p for p in partes if not (len(p) == 1 and p.isalpha())]
    texto = ' '.join(partes_filtradas).strip()
    texto = re.sub(r'^\d+\s+', '', texto)
    texto = re.sub(r'\s+\d+$', '', texto)
    texto = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def extraer_texto_desde_imagen(ruta_imagen):
    try:
        preprocesar_para_ocr(ruta_imagen)
        img = Image.open(ruta_imagen)
        configs = ['--psm 6', '--psm 4', '--psm 3']
        texto = ""
        for cfg in configs:
            texto = pytesseract.image_to_string(img, lang='spa', config=cfg)
            if len(texto.strip()) > 50: break
        
        lineas = texto.splitlines()
        datos = {}
        ultima_clave = None
        for linea in lineas:
            linea_limpia = linea.strip()
            if not linea_limpia: continue
            clave_detectada = None
            for deformado, normalizado in EQUIVALENCIAS_PREFIJOS.items():
                if re.search(rf'\b{re.escape(deformado)}\b', linea_limpia, re.IGNORECASE):
                    partes = re.split(r':\s*', linea_limpia, maxsplit=1)
                    if len(partes) == 2:
                        valor = limpiar_valor(partes[1])
                        if valor: datos[normalizado] = valor
                        else: ultima_clave = normalizado
                    else: ultima_clave = normalizado
                    clave_detectada = normalizado
                    break
            if not clave_detectada:
                for prefijo in PREFIJOS_A_MANTENER:
                    if linea_limpia.upper().startswith(prefijo.upper()):
                        partes = linea_limpia.split(':', 1)
                        if len(partes) == 2:
                            valor = limpiar_valor(partes[1])
                            if valor: datos[prefijo.rstrip(':')] = valor
                            else: ultima_clave = prefijo.rstrip(':')
                        else: ultima_clave = prefijo.rstrip(':')
                        clave_detectada = prefijo.rstrip(':')
                        break
            if not clave_detectada and ultima_clave:
                valor = limpiar_valor(linea_limpia)
                if valor: datos[ultima_clave] = valor
                ultima_clave = None
        return datos
    except Exception as e:
        return None

def encontrar_imagen_resultado(sb):
    todas = sb.find_elements("img")
    filtradas = [img for img in todas if int(img.get_attribute("width") or 0) > 100]
    if filtradas:
        return max(filtradas, key=lambda img: int(img.get_attribute("width") or 0) * int(img.get_attribute("height") or 0))
    return None

def consultar_sunarp(placa):
    """Función de servicio para el bot y la app web."""
    try:
        with SB(uc=True, headed=False) as sb:
            sb.uc_open_with_reconnect(URL, reconnect_time=5)
            sb.wait_for_element("#nroPlaca", timeout=30)
            time.sleep(8)
            sb.execute_script("const input = document.querySelector('#nroPlaca'); input.value = arguments[0]; input.dispatchEvent(new Event('input', {bubbles: true}));", placa)
            time.sleep(4)
            sb.execute_script("document.querySelector('.btn-sunarp-green').click();")
            time.sleep(16)
            
            img_element = encontrar_imagen_resultado(sb)
            if img_element:
                img_element.screenshot("sunarp_resultado.png")
            else:
                sb.save_screenshot("sunarp_resultado.png")

            datos = extraer_texto_desde_imagen("sunarp_resultado.png")
            if os.path.exists("sunarp_resultado.png"): os.remove("sunarp_resultado.png")
            return datos if datos else {"error": "Sin datos"}
    except Exception as e:
        return {"error": str(e)}