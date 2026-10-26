import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from demre_ingestion_pipeline import (
    GoPAESVectorStore,
    AXIS_LABELS,
    OFFICIAL_PAES_65_DISTRIBUTION,
    ExamType,
    ThematicAxis,
    DEMREQuestionNode,
    get_official_study_guides,
)
from adaptive_engine import (
    GoPAESAdaptiveEngine,
    GoPAESProfileManager,
    GoPAESLLMCoach,
    SelectionMode,
    OFFICIAL_SECONDS_PER_QUESTION,
    ALL_AXES,
)

# Cargar variables de entorno desde .env
load_dotenv(override=True)

# =====================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT - GOPAES
# =====================================================================
st.set_page_config(
    page_title="GoPAES | Plataforma Adaptativa IA (M1 y M2)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# INICIALIZACIÓN DE BASE VECTORIAL QDRANT Y GESTIÓN DE SESIÓN
# =====================================================================
if "vector_store" not in st.session_state:
    store = GoPAESVectorStore()
    store.seed_official_demre_questions()
    st.session_state.vector_store = store

if "active_username" not in st.session_state:
    st.session_state.active_username = None

if "nav_section" not in st.session_state:
    # Secciones del menú lateral:
    # 'DASHBOARD' | 'DIAGNOSTIC' | 'EXAMS' | 'STUDY_GUIDES'
    st.session_state.nav_section = "DASHBOARD"

if "exam_subphase" not in st.session_state:
    # Subfases dentro de 'EXAMS': 'CONFIG' | 'ACTIVE_RUN' | 'COACHING_RESULTS'
    st.session_state.exam_subphase = "CONFIG"

if "diag_questions" not in st.session_state:
    all_nodes = st.session_state.vector_store.get_all_nodes(exam="M1")
    anchors = [q for q in all_nodes if q.is_diagnostic_anchor][:3]
    st.session_state.diag_questions = anchors
    st.session_state.diag_idx = 0

if "asked_ids" not in st.session_state:
    st.session_state.asked_ids = []

if "exam_queue" not in st.session_state:
    st.session_state.exam_queue = []

if "exam_history" not in st.session_state:
    st.session_state.exam_history = []

if "ai_explanations_cache" not in st.session_state:
    st.session_state.ai_explanations_cache = {}

if "exam_config" not in st.session_state:
    st.session_state.exam_config = {
        "exam": "M1",
        "num_questions": 4,
        "timed_mode": True,
        "selection_mode": "ADAPTIVE",
    }


def login_with_profile(username: str):
    profile = GoPAESProfileManager.load_or_create_profile(username)
    st.session_state.active_username = profile.username
    st.session_state.engine = GoPAESAdaptiveEngine(profile=profile)
    # Si es un usuario nuevo que no ha hecho diagnóstico, sugerirle ir a Diagnóstico o Dashboard
    st.session_state.nav_section = "DASHBOARD"
    st.rerun()


def logout_profile():
    st.session_state.active_username = None
    st.rerun()


# =====================================================================
# PANTALLA DE INICIO / CREACIÓN DE PERFIL PERSISTENTE GOPAES
# =====================================================================
if not st.session_state.active_username:
    st.title("🚀 Bienvenido a GoPAES • Preparación Adaptativa PAES (M1 y M2)")
    st.markdown(
        "Ingresa tu nombre para crear o cargar tu **Perfil Persistente de Estudiante**. "
        "Toda tu racha de estudio, ensayos completados, vacíos de conocimiento y dominio por eje se guardan automáticamente."
    )

    col_new_user, col_existing = st.columns(2)

    with col_new_user:
        with st.container(border=True):
            st.subheader("✨ Crear o Ingresar a mi Perfil")
            input_name = st.text_input(
                "Nombre o Apodo del Estudiante:",
                placeholder="Ej: Agustín, Camila, Matías...",
            )
            if st.button("🚀 Entrar a GoPAES", type="primary", use_container_width=True):
                if input_name.strip():
                    login_with_profile(input_name.strip())
                else:
                    st.warning("Por favor escribe tu nombre para inicializar tu perfil.")

    with col_existing:
        with st.container(border=True):
            st.subheader("📂 Perfiles Guardados en este Equipo")
            existing_names = GoPAESProfileManager.list_existing_profiles()
            if not existing_names:
                st.caption("Aún no hay perfiles registrados. Crea el primero a la izquierda.")
            else:
                selected_existing = st.selectbox("Selecciona tu perfil guardado:", options=existing_names)
                if st.button("🔓 Cargar Perfil Seleccionado", use_container_width=True):
                    login_with_profile(selected_existing)

    st.stop()


# =====================================================================
# BARRA LATERAL: MENÚ DE NAVEGACIÓN EXPANDIDO + MOTOR IA EN VIVO
# =====================================================================
engine: GoPAESAdaptiveEngine = st.session_state.engine
profile = engine.profile

with st.sidebar:
    st.markdown(f"## 🚀 GoPAES • Hola, **{profile.username}**")
    st.caption(
        f"🔥 Racha: **{profile.study_streak} día(s)** | "
        f"🏅 Ensayos: **{profile.completed_exams}** | "
        f"🎯 Precisión Neta: **{engine.global_net_accuracy}%**"
    )

    # MENÚ PRINCIPAL DE 4 SECCIONES
    st.markdown("### 🧭 Menú de Navegación")
    nav_labels = {
        "DASHBOARD": "👤 Perfil / Dashboard",
        "DIAGNOSTIC": "🎯 Diagnóstico",
        "EXAMS": "📝 Ensayos",
        "STUDY_GUIDES": "📚 Guías por Materia",
    }
    selected_nav = st.radio(
        "Ir a la sección:",
        options=list(nav_labels.keys()),
        format_func=lambda k: nav_labels[k],
        index=list(nav_labels.keys()).index(st.session_state.nav_section),
        label_visibility="collapsed",
    )
    if selected_nav != st.session_state.nav_section:
        st.session_state.nav_section = selected_nav
        st.rerun()

    st.divider()

    # CONEXIÓN Y DIAGNÓSTICO DE AUTENTICACIÓN DEL LLM
    with st.expander("🔑 Conexión API LLM (Gemini / OpenAI)", expanded=False):
        default_prov = os.getenv("GOPAES_LLM_PROVIDER", "gemini").lower()
        llm_provider = st.selectbox(
            "Proveedor IA:",
            options=["gemini", "openai"],
            index=0 if default_prov == "gemini" else 1,
        )
        manual_api_key = st.text_input(
            f"API Key ({llm_provider.upper()}) [Opcional si usas .env]:",
            type="password",
            placeholder="AIzaSy... (Gemini) o sk-... (OpenAI)",
        )

        st.session_state.llm_provider_choice = llm_provider
        st.session_state.llm_manual_key = manual_api_key

        _, resolved_key, key_source = GoPAESLLMCoach.resolve_credentials(manual_api_key, llm_provider)
        is_valid_fmt, fmt_msg = GoPAESLLMCoach.validate_key_format(llm_provider, resolved_key)

        if is_valid_fmt:
            st.success(f"Clave detectada ({key_source})")
        else:
            st.warning(fmt_msg)

        if st.button("🔌 Probar Conexión IA Ahora", use_container_width=True):
            with st.spinner("Verificando credenciales con el servidor LLM..."):
                ok, msg = GoPAESLLMCoach.test_connection(manual_api_key, llm_provider)
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # PANEL DE TRANSPARENCIA DEL MOTOR ADAPTATIVO EN VIVO
    st.markdown("### 🧠 Motor Adaptativo en Vivo")
    active_mode: SelectionMode = st.session_state.exam_config.get("selection_mode", "ADAPTIVE")
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")
    effective_probs = engine.compute_sampling_probabilities(mode=active_mode)

    rows = []
    for axis in ALL_AXES:
        st_axis = engine.axes_state[axis]
        rows.append({
            "Eje": AXIS_LABELS[axis],
            "Dominio": f"{round(st_axis.mastery_score * 100)}%",
            "Peso IA": f"{round(adaptive_probs[axis] * 100, 1)}%",
            "Omisiones": st_axis.omitted_count,
            "Errores": st_axis.incorrect_count,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    col_switch, col_ wipe = st.columns(2)
    with col_switch:
        if st.button("👤 Cambiar Usuario", use_container_width=True):
            logout_profile()
    with col_wipe:
        if st.button("🗑️ Resetear Mi Perfil", use_container_width=True):
            fresh = GoPAESProfileManager.load_or_create_profile(profile.username)
            fresh.completed_exams = 0
            fresh.diagnostic_completed = False
            fresh.axes_state = {a: fresh.axes_state[a].__class__(axis=a) for a in ALL_AXES}
            fresh.logs = []
            GoPAESProfileManager.save_profile(fresh)
            st.session_state.engine = GoPAESAdaptiveEngine(profile=fresh)
            st.rerun()


# =====================================================================
# COMPONENTE REUTILIZABLE PARA RENDERIZAR PREGUNTAS CON ST.LATEX
# =====================================================================
def render_question_card(question: DEMREQuestionNode, step_num: int, total_steps: int, badge_text: str):
    col_badge, col_source = st.columns([2, 2])
    with col_badge:
        st.markdown(f"#### {badge_text} • Pregunta {step_num} de {total_steps}")
    with col_source:
        st.markdown(
            f"<div style='text-align:right; color:#94a3b8; font-size:0.9rem;'>"
            f"📌 <b>GoPAES {question.exam}</b> | Eje: <b>{AXIS_LABELS[question.thematic_axis]}</b> "
            f"({question.subtopic_name})</div>",
            unsafe_allow_html=True,
        )

    st.markdown(f"**Enunciado Oficial (DEMRE #{question.question_number}):**")
    st.write(question.stem_text)
    st.latex(question.stem_latex)

    if question.figure_svg:
        st.markdown("**Figura Geométrica Asociada:**")
        st.markdown(question.figure_svg, unsafe_allow_html=True)

    st.markdown("**Alternativas Oficiales:**")
    for opt in question.options:
        col_key, col_formula = st.columns([1, 11])
        with col_key:
            st.markdown(f"### `{opt.key})`")
        with col_formula:
            st.latex(opt.latex_content)


# =====================================================================
# SECCIÓN 1: PERFIL / DASHBOARD MOTIVACIONAL
# =====================================================================
if st.session_state.nav_section == "DASHBOARD":
    st.title(f"👤 Dashboard de Rendimiento • {profile.username}")
    st.caption(
        "Resumen persistente de tu progreso hacia la PAES de Matemáticas (M1 y M2), "
        "racha de estudio y prioridades detectadas por el motor adaptativo de GoPAES."
    )

    # 4 KPIs Motivacionales Principales
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🔥 Racha de Estudio", f"{profile.study_streak} día(s)", "Activa hoy")
    k2.metric("🏅 Ensayos Completados", profile.completed_exams)
    k3.metric("🎯 Precisión Neta Global", f"{engine.global_net_accuracy}%", "Sin castigo por omisión")
    k4.metric("📝 Preguntas Practicadas", engine.total_questions_answered, f"{engine.total_omitted} omitidas")

    st.divider()

    col_left, col_right = st.columns([3, 2])

    with col_left:
        with st.container(border=True):
            st.subheader("📊 Dominio Actual y Prioridad Adaptativa por Eje DEMRE")
            adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

            for axis in ALL_AXES:
                st_axis = engine.axes_state[axis]
                dom_pct = round(st_axis.mastery_score * 100, 1)
                prob_pct = round(adaptive_probs[axis] * 100, 1)
                st.markdown(
                    f"**{AXIS_LABELS[axis]}** — Dominio: `{dom_pct}%` | "
                    f"Precisión Neta: `{st_axis.net_accuracy}%` | "
                    f"Frecuencia en Ensayo de Debilidades: **{prob_pct}%**"
                )
                st.progress(min(1.0, st_axis.mastery_score))

    with col_right:
        with st.container(border=True):
            st.subheader("🚀 Acciones Rápidas de Estudio")
            if not profile.diagnostic_completed:
                st.warning("🎯 **Diagnóstico Pendiente:** Realiza las 3 preguntas de calibración para personalizar tus pesos iniciales.")
            else:
                st.success("✅ **Diagnóstico Inicial Calibrado**")

            if st.button("🎯 Ir al Diagnóstico de Calibración", use_container_width=True):
                st.session_state.diag_idx = 0
                st.session_state.nav_section = "DIAGNOSTIC"
                st.rerun()

            if st.button("🔥 Iniciar Ensayo de Debilidades (Adaptativo)", type="primary", use_container_width=True):
                st.session_state.exam_config["selection_mode"] = "ADAPTIVE"
                st.session_state.exam_subphase = "CONFIG"
                st.session_state.nav_section = "EXAMS"
                st.rerun()

            if st.button("🏛️ Ir a Ensayo Full Oficial PAES (65 Preguntas)", use_container_width=True):
                st.session_state.exam_config["selection_mode"] = "OFFICIAL_65"
                st.session_state.exam_subphase = "CONFIG"
                st.session_state.nav_section = "EXAMS"
                st.rerun()

            if st.button("📚 Consultar Guías Teóricas y Fórmulas por Materia", use_container_width=True):
                st.session_state.nav_section = "STUDY_GUIDES"
                st.rerun()

    # Bitácora reciente del alumno
    with st.container(border=True):
        st.subheader("📜 Últimos Movimientos del Motor Adaptativo en tu Perfil")
        if not engine.logs:
            st.info("Aún no registras respuestas en este perfil. Comienza por el Diagnóstico o un Ensayo.")
        else:
            for log in engine.logs[:6]:
                delta_str = f"+{log.delta_mastery}%" if log.delta_mastery >= 0 else f"{log.delta_mastery}%"
                st.markdown(
                    f"- **{log.step_label}** ({AXIS_LABELS[log.axis]}): Dominio `{log.old_mastery}%` → `{log.new_mastery}%` (`{delta_str}`) — {log.explanation}"
                )


# =====================================================================
# SECCIÓN 2: DIAGNÓSTICO DE CALIBRACIÓN
# =====================================================================
elif st.session_state.nav_section == "DIAGNOSTIC":
    st.title("🎯 Diagnóstico Dinámico de Calibración GoPAES")
    st.write(
        "Responde estas 3 preguntas ancla del DEMRE o usa **'Dejar en blanco'** para que GoPAES "
        "mapee tu línea base en Números, Álgebra y Geometría sin penalizar tu precisión por azar."
    )

    diag_qs: list[DEMREQuestionNode] = st.session_state.diag_questions
    idx: int = st.session_state.diag_idx

    if idx >= len(diag_qs):
        st.success("🎉 **¡Diagnóstico completado y guardado en tu perfil!**")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("👤 Ver mi Dashboard Actualizado", type="primary", use_container_width=True):
                st.session_state.nav_section = "DASHBOARD"
                st.rerun()
        with col_d2:
            if st.button("🔄 Repetir Calibración Diagnóstica", use_container_width=True):
                st.session_state.diag_idx = 0
                st.rerun()
    else:
        current_q = diag_qs[idx]
        with st.container(border=True):
            render_question_card(
                question=current_q,
                step_num=idx + 1,
                total_steps=len(diag_qs),
                badge_text="🎯 Calibración GoPAES"
            )

            st.divider()
            selected_choice = st.radio(
                "Elige una alternativa:",
                options=[o.key for o in current_q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"diag_radio_{current_q.node_id}"
            )

            col_submit, col_omit = st.columns([1, 1])
            with col_submit:
                if st.button("✅ Confirmar Alternativa", type="primary", use_container_width=True):
                    engine.process_response(current_q, selected_choice, phase_label="Diagnóstico")
                    st.session_state.asked_ids.append(current_q.node_id)
                    if idx + 1 < len(diag_qs):
                        st.session_state.diag_idx += 1
                    else:
                        engine.mark_diagnostic_completed()
                        st.session_state.diag_idx += 1
                    st.rerun()

            with col_omit:
                if st.button("🏳️ Dejar en blanco (Declarar Vacío de Conocimiento)", use_container_width=True):
                    engine.process_response(current_q, "OMIT", phase_label="Diagnóstico")
                    st.session_state.asked_ids.append(current_q.node_id)
                    if idx + 1 < len(diag_qs):
                        st.session_state.diag_idx += 1
                    else:
                        engine.mark_diagnostic_completed()
                        st.session_state.diag_idx += 1
                    st.rerun()


# =====================================================================
# SECCIÓN 3: MÓDULO DE GUÍAS POR MATERIA (TEORÍA + FÓRMULAS LATEX)
# =====================================================================
elif st.session_state.nav_section == "STUDY_GUIDES":
    st.title("📚 Guías Oficiales por Materia y Formulario PAES")
    st.write(
        "Consulta los resúmenes teóricos, propiedades clave en $\\text{LaTeX}$ y las trampas más frecuentes "
        "de los modelos oficiales del DEMRE antes de ejercitar."
    )

    guides_catalog = get_official_study_guides()

    selected_axis_guide: ThematicAxis = st.selectbox(
        "Selecciona el Eje Temático del Temario Oficial DEMRE:",
        options=ALL_AXES,
        format_func=lambda a: f"📐 {AXIS_LABELS[a]} (Dominio actual en tu perfil: {round(engine.axes_state[a].mastery_score * 100)}%)",
    )

    axis_guides = guides_catalog.get(selected_axis_guide, [])
    for guide in axis_guides:
        with st.container(border=True):
            col_title, col_scope = st.columns([3, 1])
            with col_title:
                st.subheader(f"📘 {guide.title}")
            with col_scope:
                st.markdown(
                    f"<div style='text-align:right;'><span style='background:#312e81; color:#c7d2fe; "
                    f"padding:4px 10px; border-radius:99px; font-size:0.85rem; font-weight:bold;'>"
                    f"Temario {guide.exam_scope}</span></div>",
                    unsafe_allow_html=True,
                )

            st.markdown(guide.summary_markdown)
            st.divider()

            st.markdown("#### 🧮 Fórmulas y Propiedades Clave ($\\text{LaTeX}$)")
            for f_card in guide.key_formulas:
                st.markdown(f"**• {f_card.title}:**")
                st.latex(f_card.latex_formula)
                st.caption(f"💡 {f_card.explanation}")

            st.divider()
            st.markdown("#### ⚠️ Trampas y Distractores Frecuentes del DEMRE en este Tema")
            for trap in guide.common_demre_traps:
                st.warning(f"🔎 {trap}")

    # Botón directo para entrenar este eje específico después de leer la guía
    if st.button(
        f"🔥 Practicar ahora un Mini-Ensayo Focalizado en {AXIS_LABELS[selected_axis_guide]}",
        type="primary",
        use_container_width=True,
    ):
        queue_focus = engine.build_exam_question_queue(
            vector_store=st.session_state.vector_store,
            exam="M1",
            num_questions=3,
            mode="ADAPTIVE",
            asked_ids=st.session_state.asked_ids,
            focus_axis=selected_axis_guide,
        )
        st.session_state.exam_config = {
            "exam": "M1",
            "num_questions": len(queue_focus),
            "timed_mode": False,
            "allocated_seconds": len(queue_focus) * OFFICIAL_SECONDS_PER_QUESTION["M1"],
            "selection_mode": "ADAPTIVE",
        }
        st.session_state.exam_queue = queue_focus
        st.session_state.exam_history = []
        st.session_state.exam_subphase = "ACTIVE_RUN"
        st.session_state.nav_section = "EXAMS"
        st.rerun()


# =====================================================================
# SECCIÓN 4: ENSAYOS (DEBILIDADES, ENSAYO FULL 65 Y MODO GENERAL)
# =====================================================================
elif st.session_state.nav_section == "EXAMS":
    st.title("📝 Motor de Ensayos GoPAES")

    # -----------------------------------------------------------------
    # SUBFASE 4.1: CONFIGURACIÓN DEL ENSAYO
    # -----------------------------------------------------------------
    if st.session_state.exam_subphase == "CONFIG":
        col_full, col_custom = st.columns(2)

        # TARJETA 1: ENSAYO FULL OFICIAL PAES (65 PREGUNTAS - CRONOMETRADO O LIBRE)
        with col_full:
            with st.container(border=True):
                st.subheader("🏛️ Ensayo Full Oficial PAES (65 Preguntas)")
                st.write(
                    "Simulación con la estructura y proporción exacta de ejes del DEMRE:\n"
                    "- **16** de Números (24,6%)\n"
                    "- **22** de Álgebra y Funciones (33,8%)\n"
                    "- **14** de Geometría (21,5%)\n"
                    "- **13** de Probabilidad y Estadística (20,0%)"
                )
                full_timed = st.radio(
                    "Modalidad de Tiempo para el Ensayo Full:",
                    options=[True, False],
                    format_func=lambda t: "⏱️ Cronometrado Oficial (2h 20m / 140 min)" if t else "🧘 Modo Libre (Sin límite de reloj)",
                    key="full_65_timer_radio",
                )
                if st.button("🏛️ Iniciar Ensayo Full (65 Preguntas)", type="primary", use_container_width=True):
                    queue_65 = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam="M1",
                        num_questions=65,
                        mode="OFFICIAL_65",
                        asked_ids=st.session_state.asked_ids,
                    )
                    st.session_state.exam_config = {
                        "exam": "M1",
                        "num_questions": 65,
                        "timed_mode": full_timed,
                        "allocated_seconds": 65 * OFFICIAL_SECONDS_PER_QUESTION["M1"],
                        "selection_mode": "OFFICIAL_65",
                    }
                    st.session_state.exam_queue = queue_65
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.rerun()

        # TARJETA 2: ENSAYO DE DEBILIDADES (ADAPTATIVO) Y ENSAYO GENERAL ESTÁNDAR
        with col_custom:
            with st.container(border=True):
                st.subheader("🔥 Ensayo de Debilidades / Personalizado")
                ignore_weights = st.toggle(
                    "⚖️ Modo Ensayo General (Ignorar temporalmente mis debilidades al elegir preguntas, pero guardar todo en mi perfil)",
                    value=(st.session_state.exam_config.get("selection_mode") == "GENERAL_STANDARD"),
                )
                chosen_mode: SelectionMode = "GENERAL_STANDARD" if ignore_weights else "ADAPTIVE"

                exam_choice: ExamType = st.radio(
                    "Prueba PAES:",
                    options=["M1", "M2"],
                    horizontal=True,
                    format_func=lambda x: "M1 (Obligatoria)" if x == "M1" else "M2 (Electiva Científica)",
                )
                num_q = st.slider(
                    "Cantidad de preguntas:",
                    min_value=2,
                    max_value=65 if exam_choice == "M1" else 55,
                    value=4,
                )
                custom_timed = st.radio(
                    "Modalidad de Tiempo:",
                    options=[True, False],
                    horizontal=True,
                    format_func=lambda t: "⏱️ Cuenta Regresiva" if t else "🧘 Modo Libre",
                )

                sec_per_q = OFFICIAL_SECONDS_PER_QUESTION[exam_choice]
                total_seconds = num_q * sec_per_q
                st.info(
                    f"⏱️ Tiempo oficial estimado DEMRE: **{total_seconds // 60} min {total_seconds % 60} s**"
                )

                btn_label = (
                    "⚖️ Iniciar Ensayo General Estándar"
                    if ignore_weights
                    else "🔥 Iniciar Ensayo de Debilidades (Adaptativo)"
                )
                if st.button(btn_label, type="primary", use_container_width=True):
                    queue = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam=exam_choice,
                        num_questions=num_q,
                        mode=chosen_mode,
                        asked_ids=st.session_state.asked_ids,
                    )
                    st.session_state.exam_config = {
                        "exam": exam_choice,
                        "num_questions": len(queue),
                        "timed_mode": custom_timed,
                        "allocated_seconds": len(queue) * sec_per_q,
                        "selection_mode": chosen_mode,
                    }
                    st.session_state.exam_queue = queue
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.rerun()

    # -----------------------------------------------------------------
    # SUBFASE 4.2: EJECUCIÓN DEL ENSAYO EN VIVO
    # -----------------------------------------------------------------
    elif st.session_state.exam_subphase == "ACTIVE_RUN":
        cfg = st.session_state.exam_config
        step_idx = len(st.session_state.exam_history)
        total_q = len(st.session_state.exam_queue)

        if step_idx >= total_q:
            engine.register_completed_exam()
            st.session_state.exam_subphase = "COACHING_RESULTS"
            st.rerun()

        q: DEMREQuestionNode = st.session_state.exam_queue[step_idx]
        mode_active: SelectionMode = cfg.get("selection_mode", "ADAPTIVE")
        probs = engine.compute_sampling_probabilities(mode=mode_active)
        axis_prob = round(probs[q.thematic_axis] * 100, 1)

        col_reason, col_clock, col_finish = st.columns([3, 1, 1])
        with col_reason:
            if mode_active == "ADAPTIVE":
                st.warning(
                    f"🔥 **Ensayo de Debilidades GoPAES:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                    f"(Priorizado con **{axis_prob}%** según tu historial)."
                )
            elif mode_active == "GENERAL_STANDARD":
                st.info(
                    f"⚖️ **Ensayo General Estándar:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                    f"(Proporción estándar DEMRE: **{axis_prob}%**)."
                )
            else:
                st.info(
                    f"🏛️ **Ensayo Full 65 Preguntas:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                    f"(Cuota oficial DEMRE: {OFFICIAL_PAES_65_DISTRIBUTION[q.thematic_axis]}/65)."
                )
        with col_clock:
            if cfg["timed_mode"]:
                st.metric("⏱️ Tiempo Oficial", f"{cfg['allocated_seconds'] // 60}m {cfg['allocated_seconds'] % 60}s")
            else:
                st.metric("🧘 Modalidad", "Modo Libre")
        with col_finish:
            if st.button("🏁 Finalizar y Ver Coaching IA", use_container_width=True):
                if st.session_state.exam_history:
                    engine.register_completed_exam()
                st.session_state.exam_subphase = "COACHING_RESULTS"
                st.rerun()

        with st.container(border=True):
            render_question_card(
                question=q,
                step_num=step_idx + 1,
                total_steps=total_q,
                badge_text=f"🚀 GoPAES {cfg['exam']}"
            )

            st.divider()
            user_choice = st.radio(
                "Selecciona una alternativa:",
                options=[o.key for o in q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"exam_radio_{step_idx}_{q.node_id}"
            )

            col_ans, col_blank = st.columns([1, 1])

            def record_and_advance(chosen_opt):
                state = engine.process_response(
                    question=q,
                    selected_option=chosen_opt,
                    phase_label="Ensayo GoPAES"
                )
                st.session_state.asked_ids.append(q.node_id)
                st.session_state.exam_history.append({
                    "question": q,
                    "selected_option": chosen_opt,
                    "state": state,
                })

                if cfg.get("selection_mode") == "ADAPTIVE" and (step_idx + 1) < total_q:
                    remaining_count = total_q - (step_idx + 1)
                    new_tail = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam=cfg["exam"],
                        num_questions=remaining_count,
                        mode="ADAPTIVE",
                        asked_ids=st.session_state.asked_ids,
                    )
                    st.session_state.exam_queue = (
                        st.session_state.exam_queue[: step_idx + 1] + new_tail
                    )

                if len(st.session_state.exam_history) >= total_q:
                    engine.register_completed_exam()
                    st.session_state.exam_subphase = "COACHING_RESULTS"
                st.rerun()

            with col_ans:
                if st.button("✅ Responder y Avanzar", type="primary", use_container_width=True):
                    record_and_advance(user_choice)

            with col_blank:
                if st.button("🏳️ Dejar en blanco (Declarar Vacío de Conocimiento)", use_container_width=True):
                    record_and_advance(None)

    # -----------------------------------------------------------------
    # SUBFASE 4.3: COACHING IA POST-ENSAYO
    # -----------------------------------------------------------------
    elif st.session_state.exam_subphase == "COACHING_RESULTS":
        st.balloons()
        st.subheader("🎓 GoPAES Coaching IA • Análisis de Errores y Omisiones en LaTeX")

        history = st.session_state.exam_history
        correct_total = sum(1 for h in history if h["state"] == "CORRECT")
        incorrect_total = sum(1 for h in history if h["state"] == "INCORRECT")
        omitted_total = sum(1 for h in history if h["state"] == "OMITTED")
        attempted_total = correct_total + incorrect_total
        net_acc = round((correct_total / attempted_total) * 100, 1) if attempted_total > 0 else 0.0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("✅ Correctas", correct_total)
        m2.metric("❌ Errores Conceptuales", incorrect_total)
        m3.metric("🏳️ Dejadas en Blanco", omitted_total)
        m4.metric("🎯 Precisión Neta del Ensayo", f"{net_acc}%")

        st.divider()

        for idx, item in enumerate(history):
            q: DEMREQuestionNode = item["question"]
            sel = item["selected_option"]
            st_resp = item["state"]
            cache_key = f"{idx}_{q.node_id}_{sel}_{st_resp}"

            with st.container(border=True):
                if st_resp == "CORRECT":
                    st.success(
                        f"**Pregunta {idx + 1} (DEMRE #{q.question_number} - {AXIS_LABELS[q.thematic_axis]}): "
                        f"✅ CORRECTA (Marcaste {sel})**"
                    )
                elif st_resp == "OMITTED":
                    st.warning(
                        f"**Pregunta {idx + 1} (DEMRE #{q.question_number} - {AXIS_LABELS[q.thematic_axis]}): "
                        f"🏳️ DEJADA EN BLANCO (Vacío de Conocimiento • Clave Oficial: {q.correct_option})**"
                    )
                else:
                    st.error(
                        f"**Pregunta {idx + 1} (DEMRE #{q.question_number} - {AXIS_LABELS[q.thematic_axis]}): "
                        f"❌ ERROR CONCEPTUAL (Marcaste {sel} • Clave Oficial: {q.correct_option})**"
                    )

                st.write(q.stem_text)
                st.latex(q.stem_latex)

                should_auto_generate = (st_resp != "CORRECT") and (len(history) <= 10)
                if should_auto_generate and cache_key not in st.session_state.ai_explanations_cache:
                    with st.spinner(f"🤖 Generando explicación matemática para la Pregunta {idx + 1}..."):
                        explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                            question=q,
                            selected_option=sel,
                            state=st_resp,
                            api_key_override=st.session_state.get("llm_manual_key"),
                            provider_override=st.session_state.get("llm_provider_choice"),
                        )
                        st.session_state.ai_explanations_cache[cache_key] = explanation

                if cache_key in st.session_state.ai_explanations_cache:
                    st.markdown(st.session_state.ai_explanations_cache[cache_key])

                if st.button(
                    "✨ Solicitar / Regenerar Explicación con IA en Vivo",
                    key=f"btn_regen_{cache_key}",
                ):
                    with st.spinner("Consultando al LLM..."):
                        explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                            question=q,
                            selected_option=sel,
                            state=st_resp,
                            api_key_override=st.session_state.get("llm_manual_key"),
                            provider_override=st.session_state.get("llm_provider_choice"),
                        )
                        st.session_state.ai_explanations_cache[cache_key] = explanation
                        st.rerun()

        col_back_cfg, col_go_dash = st.columns(2)
        with col_back_cfg:
            if st.button("➕ Configurar Otro Ensayo", type="primary", use_container_width=True):
                st.session_state.exam_subphase = "CONFIG"
                st.rerun()
        with col_go_dash:
            if st.button("👤 Ir a mi Dashboard de Progreso", use_container_width=True):
                st.session_state.exam_subphase = "CONFIG"
                st.session_state.nav_section = "DASHBOARD"
                st.rerun()
