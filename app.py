import streamlit as st
import main
import consunarp
import citvv
import os


# ============================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="Consulta Vehicular Inteligente",
    page_icon="🚗",
    layout="centered"
)


# ============================================================
# ENCABEZADO
# ============================================================

st.title("🚗 Sistema Automatizado de Consulta Vehicular")

st.markdown(
    "### Plataforma Inteligente de Identificación y Auditoría Legal"
)

st.write(
    "Sube una fotografía de la placa del vehículo para realizar "
    "la detección automática y consultar información de SUNARP "
    "y MTC (CITV)."
)


# ============================================================
# CARGAR IMAGEN
# ============================================================

uploaded_file = st.file_uploader(
    "📷 Selecciona o arrastra una imagen de la placa...",
    type=["jpg", "jpeg", "png"]
)


if uploaded_file is not None:

    # --------------------------------------------------------
    # GUARDAR IMAGEN TEMPORAL
    # --------------------------------------------------------

    path_foto = "temp_placa.jpg"

    with open(path_foto, "wb") as f:
        f.write(uploaded_file.getbuffer())


    # --------------------------------------------------------
    # MOSTRAR IMAGEN
    # --------------------------------------------------------

    st.image(
        path_foto,
        caption="Fotografía analizada por YOLO + EasyOCR",
        width=350
    )


    # --------------------------------------------------------
    # BOTÓN PRINCIPAL
    # --------------------------------------------------------

    if st.button(
        "🚀 Ejecutar Consulta Completa",
        use_container_width=True
    ):

        # ====================================================
        # 1. DETECCIÓN DE PLACA
        # ====================================================

        with st.spinner(
            "🤖 Analizando imagen con YOLO + EasyOCR..."
        ):

            try:

                placa = main.ejecutar_ocr(
                    path_foto
                )

            except Exception as e:

                st.error(
                    f"Error durante la detección de placa: {e}"
                )

                placa = None


        # ====================================================
        # VALIDAR PLACA
        # ====================================================

        if not placa:

            st.error(
                "❌ No se pudo detectar una placa válida. "
                "Intenta con una fotografía más clara."
            )

        else:

            # ------------------------------------------------
            # NORMALIZAR PLACA
            # ------------------------------------------------

            placa_neta = (
                placa
                .upper()
                .replace("-", "")
                .replace(" ", "")
                .strip()
            )


            st.success(
                f"✅ Placa detectada: **{placa}**"
            )

            st.info(
                f"Placa utilizada para las consultas: `{placa_neta}`"
            )


            # =================================================
            # CONSULTA SUNARP
            # =================================================

            st.markdown("---")

            st.header("📋 Consulta SUNARP")

            with st.spinner(
                "🌐 Consultando SUNARP..."
            ):

                try:

                    datos_sunarp = (
                        consunarp.consultar_sunarp(
                            placa_neta
                        )
                    )


                    # -----------------------------------------
                    # RESULTADO SUNARP
                    # -----------------------------------------

                    if (
                        isinstance(datos_sunarp, dict)
                        and datos_sunarp.get("estado") == "ok"
                    ):

                        st.success(
                            "✅ Consulta SUNARP realizada correctamente."
                        )


                        # Mostrar información
                        for clave, valor in datos_sunarp.items():

                            if clave not in [
                                "estado",
                                "captura"
                            ]:

                                st.write(
                                    f"**{clave}:** {valor}"
                                )


                        # -------------------------------------
                        # MOSTRAR CAPTURA SUNARP
                        # -------------------------------------

                        ruta_sunarp = (
                            datos_sunarp.get("captura")
                        )

                        if (
                            ruta_sunarp
                            and os.path.exists(ruta_sunarp)
                        ):

                            st.image(
                                ruta_sunarp,
                                caption=(
                                    "📸 Resultado de SUNARP"
                                ),
                                use_container_width=True
                            )

                        else:

                            st.warning(
                                "⚠️ La captura de SUNARP "
                                "no fue encontrada."
                            )


                    else:

                        mensaje = (
                            datos_sunarp.get(
                                "mensaje",
                                "No se pudo realizar la consulta SUNARP."
                            )
                            if isinstance(
                                datos_sunarp,
                                dict
                            )
                            else str(datos_sunarp)
                        )

                        st.error(
                            f"❌ SUNARP: {mensaje}"
                        )


                except Exception as e:

                    st.error(
                        f"❌ Error al consultar SUNARP: {e}"
                    )


            # =================================================
            # CONSULTA CITV / MTC
            # =================================================

            st.markdown("---")

            st.header("🛠 Consulta MTC / CITV")

            with st.spinner(
                "🌐 Consultando registros de CITV..."
            ):

                try:

                    datos_mtc = (
                        citvv.consultar_mtc(
                            placa_neta
                        )
                    )


                    # -----------------------------------------
                    # RESULTADO CITV
                    # -----------------------------------------

                    if (
                        isinstance(datos_mtc, dict)
                        and datos_mtc.get("estado") == "ok"
                    ):

                        st.success(
                            "✅ Consulta CITV realizada correctamente."
                        )


                        # -------------------------------------
                        # MOSTRAR DATOS
                        # -------------------------------------

                        for clave, valor in datos_mtc.items():

                            if clave not in [
                                "estado",
                                "captura"
                            ]:

                                st.write(
                                    f"**{clave}:** {valor}"
                                )


                        # -------------------------------------
                        # MOSTRAR CAPTURA CITV
                        # -------------------------------------

                        ruta_citv = (
                            datos_mtc.get("captura")
                        )

                        if (
                            ruta_citv
                            and os.path.exists(ruta_citv)
                        ):

                            st.image(
                                ruta_citv,
                                caption=(
                                    "📸 Resultado de MTC / CITV"
                                ),
                                use_container_width=True
                            )

                        else:

                            st.warning(
                                "⚠️ La captura de CITV "
                                "no fue encontrada."
                            )


                    else:

                        mensaje = (
                            datos_mtc.get(
                                "error",
                                "No se pudo realizar la consulta CITV."
                            )
                            if isinstance(
                                datos_mtc,
                                dict
                            )
                            else str(datos_mtc)
                        )

                        st.error(
                            f"❌ CITV: {mensaje}"
                        )


                except Exception as e:

                    st.error(
                        f"❌ Error al consultar CITV: {e}"
                    )


            # =================================================
            # RESUMEN FINAL
            # =================================================

            st.markdown("---")

            st.header("📊 Resumen de la consulta")

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "🚗 Placa detectada",
                    placa
                )

            with col2:

                st.metric(
                    "🇵🇪 Estado",
                    "Consulta realizada"
                )


            st.success(
                "✅ Proceso de consulta vehicular finalizado."
            )