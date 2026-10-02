import time
import requests
from seleniumbase import sb_cdp
from PIL import Image
import pytesseract
import re
import os
import cv2
import numpy as np

# ======================== CONFIGURACIÓN ========================
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

def consultar_sunarp(placa):
    """Función de servicio para la app web usando SeleniumBase CDP."""
    try:
        # Abrir el navegador en modo headless nativo para la nube
        sb = sb_cdp.Chrome(URL, headless=True)
        
        try:
            # Esperar a que el campo de placa sea visible
            xpath_placa = '//*[@id="nroPlaca"]'
            sb.assert_element(xpath_placa, timeout=15)
            sb.click(xpath_placa)
            sb.type(xpath_placa, placa)
            
            # Click en el botón Buscar de Sunarp
            xpath_boton = "/html/body/app-root/nz-content/div/app-inicio/app-vehicular/nz-layout/nz-content/div/nz-card/div/app-form-datos-consulta/div/form/fieldset/nz-form-item[3]/nz-form-control/div/div/div/button"
            sb.click(xpath_boton)
            
            # Esperar a que carguen los resultados en pantalla
            sb.sleep(8)
            
            # Guardar la captura directamente en la carpeta temporal /tmp
            screenshot_path = "/tmp/sunarp_resultado.png"
            sb.save_screenshot(screenshot_path)
            
            # Procesar la imagen con OCR
            datos = extraer_texto_desde_imagen(screenshot_path)
            if os.path.exists(screenshot_path): 
                os.remove(screenshot_path)
                
            return datos if datos else {"error": "Sin datos"}
        finally:
            sb.driver.quit()
            
    except Exception as e:
        return {"error": f"Error CDP: {str(e)}"}