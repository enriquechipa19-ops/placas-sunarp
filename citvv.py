import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoAlertPresentException


# ============================================================
# CONFIGURACIÓN
# ============================================================

URL_MTC = "https://rec.mtc.gob.pe/Citv/ArConsultaCitv"

CARPETA_CAPTURAS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "capturas_citv"
)

os.makedirs(
    CARPETA_CAPTURAS,
    exist_ok=True
)


# ============================================================
# EXTRAER DATOS DE CITV
# ============================================================

def extraer_ultima_inspeccion(driver):

    datos = {}

    try:

        datos["Empresa Certificadora"] = driver.find_element(
            By.XPATH,
            "//span[@id='Spv1_1']"
        ).text.strip()

    except Exception:

        datos["Empresa Certificadora"] = "No encontrada"


    try:

        datos["Observaciones"] = driver.find_element(
            By.XPATH,
            "//span[@id='Spv1_11']"
        ).text.strip()

    except Exception:

        datos["Observaciones"] = "No encontrada"


    return datos


# ============================================================
# VERIFICAR RESULTADO
# ============================================================

def consulta_exitosa(driver):

    elementos = driver.find_elements(
        By.XPATH,
        "//*[contains(text(),'ÚLTIMO DOCUMENTO REGISTRADO')]"
    )

    return len(elementos) > 0


# ============================================================
# CONSULTA CITV / MTC
# ============================================================

def consultar_mtc(placa_buscar):

    # --------------------------------------------------------
    # VALIDAR PLACA
    # --------------------------------------------------------

    if not placa_buscar:

        return {
            "estado": "error",
            "error": "No se recibió ninguna placa."
        }


    placa_original = placa_buscar

    placa_limpia = (
        placa_buscar
        .upper()
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )


    print()
    print("=" * 60)
    print("CONSULTA CITV / MTC")
    print("=" * 60)
    print(
        f"Placa detectada : {placa_original}"
    )
    print(
        f"Placa para MTC  : {placa_limpia}"
    )
    print("=" * 60)


    # ========================================================
    # CONFIGURAR CHROME
    # ========================================================

    options = webdriver.ChromeOptions()

    # Chrome visible para que pueda completarse
    # el CAPTCHA manualmente.

    options.add_argument(
        "--start-maximized"
    )


    driver = webdriver.Chrome(
        options=options
    )


    try:

        # ====================================================
        # 1. ABRIR MTC
        # ====================================================

        print()
        print("Abriendo página del MTC...")

        driver.get(
            URL_MTC
        )

        time.sleep(6)

        print(
            "Página MTC cargada."
        )


        # ====================================================
        # 2. CAMPO DE PLACA
        # ====================================================

        print(
            "Buscando campo de placa..."
        )

        wait = WebDriverWait(
            driver,
            20
        )

        input_placa = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "texFiltro")
            )
        )


        # ====================================================
        # 3. INTRODUCIR PLACA
        # ====================================================

        print(
            "Introduciendo placa automáticamente..."
        )

        input_placa.clear()

        input_placa.send_keys(
            placa_limpia
        )

        print(
            f"Placa introducida: {placa_limpia}"
        )


        # ====================================================
        # 4. ESPERAR 15 SEGUNDOS
        # ====================================================

        print()
        print("=" * 60)
        print("ESPERANDO CAPTCHA")
        print("=" * 60)
        print(
            "Tienes 15 segundos para completar "
            "el CAPTCHA."
        )
        print("=" * 60)

        time.sleep(15)

        print(
            "Tiempo terminado."
        )


        # ====================================================
        # 5. BOTÓN BUSCAR
        # ====================================================

        print()
        print(
            "Buscando botón de consulta..."
        )

        btn = wait.until(
            EC.element_to_be_clickable(
                (By.ID, "btnBuscar")
            )
        )


        # ====================================================
        # 6. CLIC AUTOMÁTICO
        # ====================================================

        print(
            "Realizando consulta automáticamente..."
        )

        btn.click()

        print(
            "✓ Clic realizado."
        )


        # ====================================================
        # 7. ESPERAR RESULTADO
        # ====================================================

        print()
        print(
            "Esperando resultado CITV..."
        )

        time.sleep(8)

        print(
            "✓ Resultado cargado."
        )


        # ====================================================
        # 8. REDUCIR ZOOM
        # ====================================================

        print(
            "Preparando captura CITV..."
        )

        try:

            driver.execute_script("""
                document.body.style.zoom = '75%';
            """)

            time.sleep(2)

        except Exception:

            pass


        # ====================================================
        # 9. CREAR NOMBRE DE CAPTURA
        # ====================================================

        timestamp = int(
            time.time()
        )

        nombre_captura = (
            f"CITV_{placa_limpia}_{timestamp}.png"
        )

        ruta_captura = os.path.join(
            CARPETA_CAPTURAS,
            nombre_captura
        )


        # ====================================================
        # 10. GUARDAR CAPTURA
        # ====================================================

        print()
        print(
            "Guardando captura de CITV..."
        )

        driver.save_screenshot(
            ruta_captura
        )

        print(
            "✓ Captura CITV guardada."
        )

        print(
            f"Ruta: {ruta_captura}"
        )


        # ====================================================
        # 11. EXTRAER DATOS
        # ====================================================

        print()
        print(
            "Extrayendo información..."
        )

        datos = extraer_ultima_inspeccion(
            driver
        )


        # ====================================================
        # 12. AGREGAR DATOS
        # ====================================================

        datos["Placa"] = placa_original

        datos["captura"] = ruta_captura

        datos["estado"] = "ok"


        # ====================================================
        # 13. MOSTRAR DATOS
        # ====================================================

        print()
        print(
            "✓ Consulta CITV finalizada."
        )

        print(
            f"Empresa: "
            f"{datos['Empresa Certificadora']}"
        )

        print(
            f"Observaciones: "
            f"{datos['Observaciones']}"
        )


        return datos


    except Exception as e:

        print()
        print("=" * 60)
        print("ERROR EN CONSULTA CITV")
        print("=" * 60)
        print(
            str(e)
        )
        print("=" * 60)


        return {
            "estado": "error",
            "error": str(e)
        }


    finally:

        # ====================================================
        # CERRAR NAVEGADOR
        # ====================================================

        try:

            driver.quit()

            print()
            print(
                "Navegador CITV cerrado."
            )

        except Exception:

            pass


# ============================================================
# PRUEBA DIRECTA
# ============================================================

if __name__ == "__main__":

    placa_prueba = "BVG-272"

    resultado = consultar_mtc(
        placa_prueba
    )

    print()
    print("=" * 60)
    print("RESULTADO FINAL CITV")
    print("=" * 60)

    print(
        resultado
    )