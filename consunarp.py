import os
import time
from seleniumbase import sb_cdp


# ============================================================
# CONFIGURACIÓN
# ============================================================

URL_SUNARP = "https://consultavehicular.sunarp.gob.pe/"

CARPETA_CAPTURAS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "capturas_sunarp"
)

os.makedirs(CARPETA_CAPTURAS, exist_ok=True)


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def consultar_sunarp(placa):

    # --------------------------------------------------------
    # 1. VALIDAR Y LIMPIAR PLACA
    # --------------------------------------------------------

    if not placa:
        return {
            "estado": "error",
            "mensaje": "No se recibió ninguna placa."
        }

    placa_original = placa

    placa = (
        placa.upper()
        .replace("-", "")
        .replace(" ", "")
        .strip()
    )

    print()
    print("=" * 60)
    print("CONSULTA SUNARP")
    print("=" * 60)
    print(f"Placa detectada   : {placa_original}")
    print(f"Placa para SUNARP : {placa}")
    print("=" * 60)

    sb = None

    try:

        # ----------------------------------------------------
        # 2. ABRIR SUNARP
        # ----------------------------------------------------

        print("\nAbriendo SUNARP...")

        sb = sb_cdp.Chrome(URL_SUNARP)

        sb.sleep(5)

        print("SUNARP cargado.")

        # ----------------------------------------------------
        # 3. LOCALIZAR CAMPO DE PLACA
        # ----------------------------------------------------

        xpath_placa = '//*[@id="nroPlaca"]'

        print("Buscando campo de placa...")

        sb.assert_element(
            xpath_placa,
            timeout=20
        )

        # ----------------------------------------------------
        # 4. INTRODUCIR PLACA AUTOMÁTICAMENTE
        # ----------------------------------------------------

        print("Introduciendo placa automáticamente...")

        sb.click(xpath_placa)

        sb.clear(xpath_placa)

        sb.type(
            xpath_placa,
            placa
        )

        print(f"Placa introducida: {placa}")

        # ----------------------------------------------------
        # 5. ESPERAR 15 SEGUNDOS
        # ----------------------------------------------------

        print()
        print(
            "Esperando 15 segundos antes de realizar "
            "la consulta..."
        )

        sb.sleep(15)

        print("Tiempo de espera terminado.")

        # ----------------------------------------------------
        # 6. BOTÓN REALIZAR CONSULTA
        # ----------------------------------------------------

        xpath_boton = (
            "/html/body/app-root/nz-content/div/"
            "app-inicio/app-vehicular/nz-layout/nz-content/"
            "div/nz-card/div/app-form-datos-consulta/"
            "div/form/fieldset/nz-form-item[3]/"
            "nz-form-control/div/div/div/button"
        )

        print()
        print(
            "Buscando botón 'Realizar consulta'..."
        )

        sb.assert_element(
            xpath_boton,
            timeout=20
        )

        # ----------------------------------------------------
        # 7. CLIC AUTOMÁTICO
        # ----------------------------------------------------

        print(
            "Realizando consulta automáticamente..."
        )

        sb.click(xpath_boton)

        print("✓ Clic realizado.")

        # ----------------------------------------------------
        # 8. ESPERAR RESULTADO
        # ----------------------------------------------------

        print()
        print(
            "Esperando respuesta de SUNARP..."
        )

        sb.sleep(10)

        print("✓ Respuesta recibida.")

        # ----------------------------------------------------
        # 9. PREPARAR CAPTURA
        # ----------------------------------------------------

        print()
        print(
            "Preparando captura de SUNARP..."
        )

        try:

            # Reducir el zoom para que entre más
            # información en la captura.

            sb.execute_script("""
                document.body.style.zoom = '75%';
            """)

            sb.sleep(2)

        except Exception:

            print(
                "No se pudo aplicar el zoom. "
                "Se continuará con la captura normal."
            )

        # ----------------------------------------------------
        # 10. CREAR NOMBRE DE CAPTURA
        # ----------------------------------------------------

        timestamp = int(time.time())

        nombre_captura = (
            f"SUNARP_{placa}_{timestamp}.png"
        )

        ruta_captura = os.path.join(
            CARPETA_CAPTURAS,
            nombre_captura
        )

        # ----------------------------------------------------
        # 11. GUARDAR CAPTURA
        # ----------------------------------------------------

        print(
            "Guardando captura de SUNARP..."
        )

        sb.save_screenshot(
            nombre_captura,
            folder=CARPETA_CAPTURAS
        )

        print(
            "✓ Captura SUNARP guardada."
        )

        print()
        print("Ruta:")
        print(ruta_captura)

        # ----------------------------------------------------
        # 12. DEVOLVER RESULTADO
        # ----------------------------------------------------

        return {
            "estado": "ok",
            "placa": placa,
            "captura": ruta_captura
        }

    except Exception as e:

        print()
        print("=" * 60)
        print("ERROR EN LA CONSULTA SUNARP")
        print("=" * 60)
        print(str(e))
        print("=" * 60)

        return {
            "estado": "error",
            "mensaje": str(e)
        }

    finally:

        # ----------------------------------------------------
        # 13. CERRAR NAVEGADOR
        # ----------------------------------------------------

        if sb is not None:

            try:

                sb.driver.stop()

                print(
                    "\nNavegador SUNARP cerrado."
                )

            except Exception:

                pass


# ============================================================
# PRUEBA DIRECTA
# ============================================================

if __name__ == "__main__":

    placa_prueba = "BVG-272"

    resultado = consultar_sunarp(
        placa_prueba
    )

    print()
    print("=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)

    print(resultado)