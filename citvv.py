import cv2
import numpy as np
import easyocr
import time
import base64
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException

# ========== CONFIGURACIÓN ==========
reader = easyocr.Reader(['en'], gpu=False)

def resolver_captcha(driver):
    try:
        img_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'imgCaptcha')))
        b64_data = driver.execute_async_script("""
            var ele = arguments[0], callback = arguments[1];
            var cnv = document.createElement('canvas');
            cnv.width = ele.naturalWidth;
            cnv.height = ele.naturalHeight;
            cnv.getContext('2d').drawImage(ele, 0, 0);
            callback(cnv.toDataURL('image/png').substring(22));
        """, img_element)
        
        with open("/tmp/temp_captcha.png", 'wb') as f:
            f.write(base64.b64decode(b64_data))
            
        img = cv2.imread("/tmp/temp_captcha.png")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
        results = reader.readtext(binary)
        if results:
            texto = "".join([res[1] for res in results])
            return "".join(filter(str.isdigit, texto))
        return None
    except Exception:
        return None

def extraer_ultima_inspeccion(driver):
    datos = {}
    try:
        datos['Empresa Certificadora'] = driver.find_element(By.XPATH, "//span[@id='Spv1_1']").text.strip()
        datos['Observaciones'] = driver.find_element(By.XPATH, "//span[@id='Spv1_11']").text.strip()
    except Exception:
        datos['Empresa Certificadora'] = "No encontrada"
        datos['Observaciones'] = "No encontrada"
    return datos

def consulta_exitosa(driver):
    return len(driver.find_elements(By.XPATH, "//*[contains(text(),'ÚLTIMO DOCUMENTO REGISTRADO')]")) > 0

def consultar_mtc(placa_buscar):
    options = webdriver.ChromeOptions()
    # Opciones obligatorias para que funcione en el servidor de Streamlit Cloud
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    driver = webdriver.Chrome(options=options)
    
    # Limpiamos la placa: quitamos guiones para asegurar el formato que espera el MTC
    placa_limpia = placa_buscar.replace("-", "")
    
    try:
        driver.get("https://rec.mtc.gob.pe/Citv/ArConsultaCitv")
        time.sleep(6) # Pausa inicial prudente para asegurar la carga completa de la web

        for intento in range(3):
            codigo = resolver_captcha(driver)
            if not codigo or len(codigo) < 4:
                driver.refresh()
                time.sleep(6) # Pausa tras refrescar captcha fallido
                continue

            try:
                wait = WebDriverWait(driver, 10)
                
                # Inyección JS para placa y captcha simulando comportamiento humano
                input_placa = wait.until(EC.element_to_be_clickable((By.ID, 'texFiltro')))
                driver.execute_script(f"arguments[0].value = '{placa_limpia}';", input_placa)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", input_placa)
                time.sleep(1)
                
                input_captcha = wait.until(EC.element_to_be_clickable((By.ID, 'texCaptcha')))
                driver.execute_script(f"arguments[0].value = '{codigo}';", input_captcha)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", input_captcha)
                time.sleep(1)
                
                btn = wait.until(EC.element_to_be_clickable((By.ID, 'btnBuscar')))
                driver.execute_script("arguments[0].click();", btn)
                
                time.sleep(4) # Pausa para procesar la búsqueda
                
                # Manejo de Alertas (Código inválido o error en pantalla)
                try:
                    alert = driver.switch_to.alert
                    alert.accept()
                    driver.refresh()
                    time.sleep(5)
                    continue
                except NoAlertPresentException:
                    pass
                
                time.sleep(6) # Tiempo de espera para que renderice la tabla de resultados del MTC
                if consulta_exitosa(driver):
                    return extraer_ultima_inspeccion(driver)
                else:
                    driver.refresh()
                    time.sleep(6)
            except Exception as e:
                driver.refresh()
                time.sleep(5)
                
        return {"error": "Se superó el límite de intentos o el MTC bloqueó temporalmente la consulta."}
    except Exception as e:
        return {"error": f"Error crítico: {str(e)}"}
    finally:
        driver.quit()