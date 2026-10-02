import time
import requests
from PIL import Image
import pytesseract
import re
import os
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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
    """Función de servicio para la app web usando Selenium estándar headless."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(URL)
        time.sleep(5)
        
        wait = WebDriverWait(driver, 30)
        input_placa = wait.until(EC.element_to_be_clickable((By.ID, 'nroPlaca')))
        driver.execute_script("const input = document.querySelector('#nroPlaca'); input.value = arguments[0]; input.dispatchEvent(new Event('input', {bubbles: true}));", placa)
        time.sleep(4)
        
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.btn-sunarp-green')))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(16)
        
        screenshot_path = "/tmp/sunarp_resultado.png"
        driver.save_screenshot(screenshot_path)
        driver.quit()

        datos = extraer_texto_desde_imagen(screenshot_path)
        if os.path.exists(screenshot_path): 
            os.remove(screenshot_path)
            
        return datos if datos else {"error": "Sin datos"}
    except Exception as e:
        try:
            driver.quit()
        except:
            pass
        return {"error": f"Error Selenium: {str(e)}"}