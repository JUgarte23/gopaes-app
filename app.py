import os
import pandas as pd
import streamlit as st

try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

from guides_data import (
    ExamType,
    ThematicAxis,
    DEMREExhaustiveGuide,
    get_exhaustive_guides_by_exam,
)
from demre_ingestion_pipeline import (
    GoPAESVectorStore,
    AXIS_LABELS,
    OFFICIAL_PAES_65_DISTRIBUTION,
    DEMREQuestionNode,
)
from adaptive_engine import (
    GoPAESAdaptiveEngine,
    GoPAESProfileManager,
    GoPAESLLMCoach,
    AxisMasteryState,
    SelectionMode,
    OFFICIAL_SECONDS_PER_QUESTION,
    ALL_AXES,
)

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
# INICIALIZACIÓN DE BASE VECTORIAL QDRANT (+190 REACTIVOS DEMRE)
# =====================================================================
if "vector_store" not in st.session_state:
    store = GoPAESVectorStore()
    seeded_nodes = store.seed_official_demre_questions()
    st.session_state.vector_store = store
    st.session_state.total_indexed_nodes = len(seeded_nodes)

if "active_username" not in st.session_state:
    st.session_state.active_username = None

if "nav_section" not in st.session_state:
    # Secciones independientes del menú lateral:
    # 'DASHBOARD' | 'DIAGNOSTIC' | 'EXAMS' | 'GUIDES_M1' | 'GUIDES_M2'
    st.session_state.nav_section = "DASHBOARD"

if "exam_subphase" not in st.session_state:
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

if "interleaved_feedback" not in st.session_state:
    st.session_state.interleaved_feedback = {}

if "selected_guide_id" not in st.session_state:
    # Controla el menú intermedio de guías: None = mostrar catálogo de unidades; str = mostrar guía específica
    st.session_state.selected_guide_id = None

if "guide_active_tab" not in st.session_state:
    # 'THEORY' o 'UNIT_EXERCISES'
    st.session_state.guide_active_tab = "THEORY"

if "unit_custom_workouts" not in st.session_state:
    # Diccionario guide_id -> list[DEMREQuestionNode] generadas según la cantidad elegida por el alumno
    st.session_state.unit_custom_workouts = {}

if "unit_workout_answers" not in st.session_state:
    # Diccionario f"{guide_id}_{node_id}" -> {"selected": str, "state": ResponseState}
    st.session_state.unit_workout_answers = {}

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
# BARRA LATERAL: NAVEGACIÓN EXPANDIDA CON SEPARACIÓN ESTRICTA M1 / M2
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
    st.caption(
        f"🗄️ Banco Vectorial Qdrant: **{st.session_state.get('total_indexed_nodes', 186)} reactivos DEMRE (M1 + M2)**"
    )

    # MENÚ PRINCIPAL CON SEPARACIÓN ESTRICTA ENTRE GUÍAS M1 Y GUÍAS M2
    st.markdown("### 🧭 Menú de Navegación")
    nav_labels = {
        "DASHBOARD": "👤 Perfil / Dashboard",
        "DIAGNOSTIC": "🎯 Diagnóstico",
        "EXAMS": "📝 Ensayos (Full y Adaptativos)",
        "GUIDES_M1": "📘 Guías por Materia: PAES M1",
        "GUIDES_M2": "📕 Guías por Materia: PAES M2",
    }
    if st.session_state.nav_section not in nav_labels:
        st.session_state.nav_section = "DASHBOARD"

    selected_nav = st.radio(
        "Ir a la sección:",
        options=list(nav_labels.keys()),
        format_func=lambda k: nav_labels[k],
        index=list(nav_labels.keys()).index(st.session_state.nav_section),
        label_visibility="collapsed",
    )
    if selected_nav != st.session_state.nav_section:
        st.session_state.nav_section = selected_nav
        st.session_state.selected_guide_id = None
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
            f"API Key ({llm_provider.upper()}) [Opcional si usas Secrets]:",
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
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

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
    col_switch, col_wipe = st.columns(2)
    with col_switch:
        if st.button("👤 Cambiar Usuario", use_container_width=True):
            logout_profile()
    with col_wipe:
        if st.button("🗑️ Resetear Mi Perfil", use_container_width=True):
            fresh = GoPAESProfileManager.load_or_create_profile(profile.username)
            fresh.completed_exams = 0
            fresh.diagnostic_completed = False
            fresh.axes_state = {a: AxisMasteryState(axis=a) for a in ALL_AXES}
            fresh.logs = []
            GoPAESProfileManager.save_profile(fresh)
            st.session_state.engine = GoPAESAdaptiveEngine(profile=fresh)
            st.rerun()


# =====================================================================
# COMPONENTES REUTILIZABLES DE RENDERIZADO (PREGUNTAS Y GUÍAS EXHAUSTIVAS)
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


def build_unit_exercise_queue_safe(
    engine_inst: GoPAESAdaptiveEngine,
    vector_store: GoPAESVectorStore,
    exam: ExamType,
    axis: ThematicAxis,
    subtopic_keyword: str,
    num_questions: int,
    exclude_ids: list[str] | None = None,
) -> list[DEMREQuestionNode]:
    """
    Extrae de forma segura `num_questions` ejercicios específicos para la unidad (`subtopic_keyword`).
    Funciona incluso si en GitHub hay una versión anterior de `adaptive_engine.py`.
    """
    if hasattr(engine_inst, "build_unit_exercise_queue"):
        return engine_inst.build_unit_exercise_queue(
            vector_store=vector_store,
            exam=exam,
            axis=axis,
            subtopic_keyword=subtopic_keyword,
            num_questions=num_questions,
            exclude_ids=exclude_ids,
        )

    excluded = set(exclude_ids or [])
    axis_pool: list[DEMREQuestionNode] = vector_store.query_by_axis_and_exam(
        exam=exam,
        axis=axis,
        exclude_ids=[],
        diagnostic_only=False,
    )
    kw = (subtopic_keyword or "").strip().lower()

    primary_matches = [
        q for q in axis_pool
        if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id not in excluded
    ]
    secondary_matches = [
        q for q in axis_pool
        if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id in excluded
    ]
    axis_unseen = [
        q for q in axis_pool
        if q.node_id not in excluded and q not in primary_matches
    ]
    axis_remaining = [
        q for q in axis_pool
        if q not in primary_matches and q not in secondary_matches and q not in axis_unseen
    ]

    combined: list[DEMREQuestionNode] = []
    for candidate in (primary_matches + secondary_matches + axis_unseen + axis_remaining):
        if candidate.node_id not in [c.node_id for c in combined]:
            combined.append(candidate)
        if len(combined) >= num_questions:
            break

    return combined[:num_questions]


def _get_guide_short_desc(guide) -> str:
    desc = getattr(guide, "short_description", "")
    if desc:
        return desc
    return (
        f"Guía oficial estructurada según el temario DEMRE para {guide.unit_title}. "
        f"Incluye marco teórico, formulario en LaTeX, receta paso a paso y ejercicios de la unidad."
    )


def _get_guide_subtopic_kw(guide) -> str:
    kw = getattr(guide, "subtopic_filter_keyword", "")
    if kw:
        return kw
    title_low = guide.unit_title.lower()
    if "porcentaje" in title_low:
        return "porcentaje"
    if "potencia" in title_low or "raíces" in title_low or "raices" in title_low:
        return "potencias"
    if "logaritmo" in title_low:
        return "logaritmo"
    if "interés" in title_low or "interes" in title_low or "matemática financiera" in title_low:
        return "interés"
    if "sistema" in title_low:
        return "sistemas"
    if "cuadrática" in title_low or "cuadratica" in title_low or "parábola" in title_low:
        return "cuadrática"
    if "lineal" in title_low or "afín" in title_low or "afin" in title_low or "proporción" in title_low:
        return "lineal"
    if "pitágoras" in title_low or "pitagoras" in title_low or "área" in title_low or "perímetro" in title_low:
        return "pitágoras"
    if "vector" in title_low or "isométrica" in title_low or "isometrica" in title_low:
        return "isométrica"
    if "homotecia" in title_low or "trigonometría" in title_low or "trigonometria" in title_low:
        return "homotecia"
    if "cuartil" in title_low or "promedio" in title_low or "estadística" in title_low:
        return "estadística"
    if "probabilidad" in title_low or "laplace" in title_low:
        return "probabilidad"
    if "condicional" in title_low or "combinatoria" in title_low or "dispersión" in title_low:
        return "condicional"
    return "enteros"


def _ensure_multi_unit_guides(
    guides_by_axis: dict[ThematicAxis, list[DEMREExhaustiveGuide]],
    exam_target: ExamType,
) -> dict[ThematicAxis, list[DEMREExhaustiveGuide]]:
    """
    Garantiza que si en GitHub aún está la versión anterior de `guides_data.py` (con 1 sola guía por eje),
    se desglose automáticamente en múltiples unidades seleccionables en el menú intermedio.
    """
    num_list = guides_by_axis.get("NUMEROS", [])
    if len(num_list) > 1:
        return guides_by_axis

    expanded: dict[ThematicAxis, list[DEMREExhaustiveGuide]] = {a: [] for a in ALL_AXES}
    for axis, g_list in guides_by_axis.items():
        if not g_list:
            continue
        base_g = g_list[0]
        if len(base_g.key_formulas) >= 2:
            # Dividir en Unidad A y Unidad B a partir de las fórmulas y ejercicios para que el menú tenga unidades separadas
            mid_f = max(1, len(base_g.key_formulas) // 2)
            u1 = base_g.model_copy(
                update={
                    "guide_id": f"{base_g.guide_id}-U1",
                    "unit_title": f"Unidad 1: {base_g.key_formulas[0].title}",
                    "key_formulas": base_g.key_formulas[:mid_f],
                    "interleaved_exercises": base_g.interleaved_exercises[:1],
                }
            )
            u2 = base_g.model_copy(
                update={
                    "guide_id": f"{base_g.guide_id}-U2",
                    "unit_title": f"Unidad 2: {base_g.key_formulas[mid_f].title}",
                    "key_formulas": base_g.key_formulas[mid_f:],
                    "interleaved_exercises": base_g.interleaved_exercises[1:] or base_g.interleaved_exercises,
                }
            )
            expanded[axis] = [u1, u2]
        else:
            expanded[axis] = [base_g]
    return expanded


def render_exhaustive_study_guides_section(exam_target: ExamType):
    """
    Renderiza la sección de Guías por Materia (PAES M1 o PAES M2) con arquitectura de 2 niveles:
    1. MENÚ INTERMEDIO DE UNIDADES: Muestra el catálogo de guías disponibles en el eje temático
       para que el alumno elija qué guía desarrollar o cuántos ejercicios practicar de esa unidad.
    2. VISTA DE GUÍA SELECCIONADA: Muestra exclusivamente la guía elegida (Teoría + Fórmulas LaTeX + Receta)
       y un generador interactivo donde el alumno elige la cantidad exacta de ejercicios a realizar de esa unidad.
    """
    badge_color = "#1d4ed8" if exam_target == "M1" else "#9333ea"
    exam_title = (
        "PAES M1 (Competencia Matemática 1 • Obligatoria)"
        if exam_target == "M1"
        else "PAES M2 (Competencia Matemática 2 • Electiva Científica)"
    )

    col_head, col_switch_exam = st.columns([3, 1])
    with col_head:
        st.title(f"{'📘' if exam_target == 'M1' else '📕'} Guías por Materia • {exam_title}")
    with col_switch_exam:
        other_exam = "M2" if exam_target == "M1" else "M1"
        if st.button(f"🔄 Cambiar a Guías PAES {other_exam}", use_container_width=True):
            st.session_state.nav_section = f"GUIDES_{other_exam}"
            st.session_state.selected_guide_id = None
            st.rerun()

    guides_by_axis = _ensure_multi_unit_guides(
        get_exhaustive_guides_by_exam(exam_target),
        exam_target=exam_target,
    )

    # Buscar si hay una guía actualmente seleccionada y que pertenezca a este examen (M1 o M2)
    active_guide: DEMREExhaustiveGuide | None = None
    if st.session_state.selected_guide_id:
        for ax_list in guides_by_axis.values():
            for g in ax_list:
                if g.guide_id == st.session_state.selected_guide_id and g.exam == exam_target:
                    active_guide = g
                    break

    # =========================================================================
    # NIVEL 1: MENÚ INTERMEDIO DE SELECCIÓN DE GUÍA (CATÁLOGO DE UNIDADES)
    # =========================================================================
    if active_guide is None:
        st.markdown(
            "Selecciona primero el **Eje Temático** y luego elige en el **Menú de Unidades** "
            "qué guía específica deseas estudiar o cuántos ejercicios quieres desarrollar de esa unidad."
        )

        selected_axis: ThematicAxis = st.selectbox(
            f"1️⃣ Selecciona el Eje Temático de PAES {exam_target}:",
            options=ALL_AXES,
            format_func=lambda a: (
                f"📐 {AXIS_LABELS[a]} — {len(guides_by_axis.get(a, []))} unidad(es) disponible(s) "
                f"(Tu dominio actual: {round(engine.axes_state[a].mastery_score * 100)}%)"
            ),
            key=f"select_axis_guide_{exam_target}",
        )

        axis_guides: list[DEMREExhaustiveGuide] = guides_by_axis.get(selected_axis, [])
        st.markdown(f"### 🗂️ 2️⃣ Menú de Guías Disponibles en **{AXIS_LABELS[selected_axis]} ({exam_target})**")
        st.caption("Elige la unidad que quieres abrir o configura directamente una práctica de ejercicios para esa unidad:")

        for idx_g, guide in enumerate(axis_guides, start=1):
            short_desc = _get_guide_short_desc(guide)
            subtopic_kw = _get_guide_subtopic_kw(guide)

            with st.container(border=True):
                col_info, col_actions = st.columns([3, 2])

                with col_info:
                    st.markdown(
                        f"<div style='display:flex; align-items:center; gap:10px; flex-wrap:wrap;'>"
                        f"<span style='background:{badge_color}; color:white; padding:3px 10px; border-radius:99px; font-size:0.8rem; font-weight:bold;'>"
                        f"Guía #{idx_g} • {guide.exam}</span>"
                        f"<h4 style='margin:0;'>{guide.unit_title}</h4>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"📌 {guide.demre_syllabus_reference}")
                    st.write(short_desc)
                    st.markdown(
                        f"🧮 **{len(guide.key_formulas)}** Fórmulas $\\text{{LaTeX}}$ | "
                        f"🧑‍🍳 **{len(guide.resolution_recipe_steps)}** Pasos de Receta | "
                        f"⚠️ **{len(guide.common_demre_traps)}** Trampas DEMRE"
                    )

                with col_actions:
                    if st.button(
                        "📖 Abrir Guía de Estudio (Teoría + Receta)",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_open_theory_{guide.guide_id}",
                    ):
                        st.session_state.selected_guide_id = guide.guide_id
                        st.session_state.guide_active_tab = "THEORY"
                        st.rerun()

                    c_num, c_go = st.columns([1, 2])
                    with c_num:
                        num_ex_menu = st.number_input(
                            "N° Ejercicios:",
                            min_value=1,
                            max_value=20,
                            value=5,
                            step=1,
                            key=f"menu_num_ex_{guide.guide_id}",
                        )
                    with c_go:
                        st.write("")
                        if st.button(
                            f"🏋️ Practicar {num_ex_menu} Ejercicios",
                            use_container_width=True,
                            key=f"btn_open_ex_{guide.guide_id}",
                        ):
                            st.session_state.selected_guide_id = guide.guide_id
                            st.session_state.guide_active_tab = "UNIT_EXERCISES"
                            st.session_state.unit_custom_workouts[guide.guide_id] = build_unit_exercise_queue_safe(
                                engine_inst=engine,
                                vector_store=st.session_state.vector_store,
                                exam=guide.exam,
                                axis=guide.thematic_axis,
                                subtopic_keyword=subtopic_kw,
                                num_questions=int(num_ex_menu),
                                exclude_ids=st.session_state.asked_ids,
                            )
                            st.rerun()
        return

    # =========================================================================
    # NIVEL 2: VISTA DETALLADA DE LA GUÍA ELEGIDA + PRÁCTICA PERSONALIZADA DE LA UNIDAD
    # =========================================================================
    active_subtopic_kw = _get_guide_subtopic_kw(active_guide)

    col_back, col_unit_badge = st.columns([1, 3])
    with col_back:
        if st.button("⬅️ Volver al Menú de Guías", use_container_width=True):
            st.session_state.selected_guide_id = None
            st.rerun()
    with col_unit_badge:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span style='background:{badge_color}; color:white; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
            f"{AXIS_LABELS[active_guide.thematic_axis]} • Currículo {active_guide.exam}</span></div>",
            unsafe_allow_html=True,
        )

    st.header(active_guide.unit_title)
    st.caption(f"📌 {active_guide.demre_syllabus_reference}")

    # Selector de vista dentro de la unidad: Estudio Teórico vs Ejercicios de la Unidad
    tab_options = {
        "THEORY": "📖 1. Marco Teórico, Fórmulas LaTeX y Receta Paso a Paso",
        "UNIT_EXERCISES": "🏋️ 2. Desarrollar Ejercicios de esta Unidad (Elige la Cantidad)",
    }
    chosen_subview = st.radio(
        "Modo de trabajo en esta guía:",
        options=list(tab_options.keys()),
        format_func=lambda k: tab_options[k],
        index=0 if st.session_state.guide_active_tab == "THEORY" else 1,
        horizontal=True,
        key=f"subview_radio_{active_guide.guide_id}",
    )
    if chosen_subview != st.session_state.guide_active_tab:
        st.session_state.guide_active_tab = chosen_subview
        st.rerun()

    st.divider()

    if st.session_state.guide_active_tab == "THEORY":
        with st.container(border=True):
            # 1. Marco Teórico Exhaustivo
            st.markdown(active_guide.theoretical_framework_md)
            st.divider()

            # 2. Formulario Oficial en LaTeX
            st.markdown("#### 🧮 Formulario y Propiedades Fundamentales ($\\text{LaTeX}$)")
            for f_card in active_guide.key_formulas:
                with st.container(border=True):
                    st.markdown(f"**{f_card.title}**")
                    st.latex(f_card.latex_formula)
                    st.caption(f"💡 *Interpretación DEMRE:* {f_card.explanation}")

            st.divider()

            # 3. Receta Algorítmica Paso a Paso
            st.markdown(f"#### 🧑‍🍳 {active_guide.resolution_recipe_title}")
            st.info(
                "Sigue este algoritmo paso a paso cada vez que te enfrentes a un problema de esta unidad:"
            )
            for recipe_step in active_guide.resolution_recipe_steps:
                st.markdown(f"- ✅ **{recipe_step}**")

            st.divider()

            # 4. Trampas y Distractores Clásicos del DEMRE
            st.markdown("#### ⚠️ Trampas y Errores Frecuentes del DEMRE a Evitar")
            for trap in active_guide.common_demre_traps:
                st.warning(f"🔎 {trap}")

            st.divider()

            # 5. Ejemplos Guiados Intercalados de la Unidad
            st.markdown("#### ✍️ Ejemplos Guiados Paso a Paso de la Unidad")
            for ex in active_guide.interleaved_exercises:
                with st.container(border=True):
                    st.markdown(f"##### 🎯 {ex.title}")
                    st.write(ex.stem_text)
                    st.latex(ex.stem_latex)

                    for opt_k, opt_latex in ex.options.items():
                        c_k, c_lat = st.columns([1, 11])
                        with c_k:
                            st.markdown(f"**`{opt_k})`**")
                        with c_lat:
                            st.latex(opt_latex)

                    chosen_ex_opt = st.radio(
                        "Resuelve este ejemplo:",
                        options=list(ex.options.keys()),
                        format_func=lambda k: f"Alternativa {k}",
                        horizontal=True,
                        key=f"interleaved_radio_{ex.exercise_id}",
                    )

                    if st.button(
                        "✔️ Comprobar Respuesta y Ver Desarrollo Paso a Paso",
                        key=f"btn_check_{ex.exercise_id}",
                    ):
                        st.session_state.interleaved_feedback[ex.exercise_id] = chosen_ex_opt

                    if ex.exercise_id in st.session_state.interleaved_feedback:
                        user_ans = st.session_state.interleaved_feedback[ex.exercise_id]
                        if user_ans == ex.correct_option:
                            st.success(f"🎉 **¡Correcto! La alternativa oficial es la {ex.correct_option}).**")
                        else:
                            st.error(
                                f"❌ **Marcaste {user_ans}), pero la alternativa correcta es la {ex.correct_option}).** "
                                "Revisa el desarrollo paso a paso aplicando la receta:"
                            )
                        st.markdown("**📘 Desarrollo Paso a Paso:**")
                        for s_line in ex.step_by_step_solution:
                            st.markdown(s_line)

        # CTA al final de la teoría para pasar a ejercitar esta unidad eligiendo cantidad
        with st.container(border=True):
            st.subheader("🏋️ ¿Listo para ejercitar esta unidad?")
            col_s1, col_s2 = st.columns([2, 2])
            with col_s1:
                qty_from_theory = st.slider(
                    "Elige cuántos ejercicios de esta unidad quieres realizar ahora:",
                    min_value=1,
                    max_value=20,
                    value=5,
                    key=f"slider_from_theory_{active_guide.guide_id}",
                )
            with col_s2:
                st.write("")
                if st.button(
                    f"🚀 Generar {qty_from_theory} Ejercicios de esta Unidad",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_gen_from_theory_{active_guide.guide_id}",
                ):
                    st.session_state.unit_custom_workouts[active_guide.guide_id] = build_unit_exercise_queue_safe(
                        engine_inst=engine,
                        vector_store=st.session_state.vector_store,
                        exam=active_guide.exam,
                        axis=active_guide.thematic_axis,
                        subtopic_keyword=active_subtopic_kw,
                        num_questions=int(qty_from_theory),
                        exclude_ids=st.session_state.asked_ids,
                    )
                    st.session_state.guide_active_tab = "UNIT_EXERCISES"
                    st.rerun()

    else:
        # =====================================================================
        # PESTAÑA 2: GENERADOR Y ENTRENADOR DE EJERCICIOS DE LA UNIDAD
        # =====================================================================
        with st.container(border=True):
            st.subheader(f"🏋️ Práctica Personalizada • {active_guide.unit_title}")
            st.write(
                "Elige la **cantidad exacta de ejercicios** que deseas realizar sobre esta unidad. "
                "Puedes resolverlos directamente aquí con retroalimentación inmediata en $\\text{LaTeX}$ "
                "o abrirlos en el simulador de ensayo."
            )

            col_cfg_qty, col_btn_inline, col_btn_exam = st.columns([2, 2, 2])
            current_list: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts.get(
                active_guide.guide_id, []
            )
            default_qty = len(current_list) if current_list else 5

            with col_cfg_qty:
                desired_qty = st.slider(
                    "Cantidad de ejercicios de esta unidad:",
                    min_value=1,
                    max_value=20,
                    value=default_qty,
                    key=f"unit_qty_slider_{active_guide.guide_id}",
                )
            with col_btn_inline:
                st.write("")
                if st.button(
                    f"🔄 Cargar {desired_qty} Ejercicios Aquí Mismo",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_reload_inline_{active_guide.guide_id}",
                ):
                    st.session_state.unit_custom_workouts[active_guide.guide_id] = build_unit_exercise_queue_safe(
                        engine_inst=engine,
                        vector_store=st.session_state.vector_store,
                        exam=active_guide.exam,
                        axis=active_guide.thematic_axis,
                        subtopic_keyword=active_subtopic_kw,
                        num_questions=int(desired_qty),
                        exclude_ids=st.session_state.asked_ids,
                    )
                    st.rerun()
            with col_btn_exam:
                st.write("")
                if st.button(
                    f"⏱️ Abrir {desired_qty} Ejercicios en Modo Ensayo",
                    use_container_width=True,
                    key=f"btn_launch_unit_exam_{active_guide.guide_id}",
                ):
                    queue_unit = build_unit_exercise_queue_safe(
                        engine_inst=engine,
                        vector_store=st.session_state.vector_store,
                        exam=active_guide.exam,
                        axis=active_guide.thematic_axis,
                        subtopic_keyword=active_subtopic_kw,
                        num_questions=int(desired_qty),
                        exclude_ids=st.session_state.asked_ids,
                    )
                    st.session_state.exam_config = {
                        "exam": active_guide.exam,
                        "num_questions": len(queue_unit),
                        "timed_mode": False,
                        "allocated_seconds": len(queue_unit) * OFFICIAL_SECONDS_PER_QUESTION[active_guide.exam],
                        "selection_mode": "ADAPTIVE",
                    }
                    st.session_state.exam_queue = queue_unit
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.session_state.nav_section = "EXAMS"
                    st.rerun()

        # Si aún no hay lista cargada para esta guía, generarla automáticamente con `desired_qty`
        if active_guide.guide_id not in st.session_state.unit_custom_workouts:
            st.session_state.unit_custom_workouts[active_guide.guide_id] = build_unit_exercise_queue_safe(
                engine_inst=engine,
                vector_store=st.session_state.vector_store,
                exam=active_guide.exam,
                axis=active_guide.thematic_axis,
                subtopic_keyword=active_subtopic_kw,
                num_questions=int(desired_qty),
                exclude_ids=st.session_state.asked_ids,
            )

        workout_questions: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts[active_guide.guide_id]

        # Mostrar progreso de la batería de ejercicios de la unidad
        answered_in_unit = sum(
            1
            for q_node in workout_questions
            if f"{active_guide.guide_id}_{q_node.node_id}" in st.session_state.unit_workout_answers
        )
        st.progress(
            answered_in_unit / max(1, len(workout_questions)),
            text=f"Progreso en esta unidad: {answered_in_unit} de {len(workout_questions)} ejercicio(s) respondido(s)",
        )

        # Renderizar cada uno de los N ejercicios seleccionados por el usuario
        for q_idx, q_node in enumerate(workout_questions, start=1):
            ans_key = f"{active_guide.guide_id}_{q_node.node_id}"
            with st.container(border=True):
                render_question_card(
                    question=q_node,
                    step_num=q_idx,
                    total_steps=len(workout_questions),
                    badge_text=f"🏋️ Práctica de Unidad ({active_guide.exam})",
                )

                chosen_unit_opt = st.radio(
                    "Selecciona tu respuesta:",
                    options=[o.key for o in q_node.options],
                    format_func=lambda k: f"Alternativa {k}",
                    horizontal=True,
                    key=f"unit_q_radio_{ans_key}_{q_idx}",
                )

                col_check, col_omit_u = st.columns(2)
                with col_check:
                    if st.button(
                        "✅ Comprobar Alternativa",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_unit_check_{ans_key}_{q_idx}",
                    ):
                        state_res = engine.process_response(
                            question=q_node,
                            selected_option=chosen_unit_opt,
                            phase_label=f"Guía {active_guide.exam}",
                        )
                        st.session_state.asked_ids.append(q_node.node_id)
                        st.session_state.unit_workout_answers[ans_key] = {
                            "selected": chosen_unit_opt,
                            "state": state_res,
                        }
                        st.rerun()

                with col_omit_u:
                    if st.button(
                        "🏳️ Dejar en Blanco y Ver Explicación Paso a Paso",
                        use_container_width=True,
                        key=f"btn_unit_omit_{ans_key}_{q_idx}",
                    ):
                        state_res = engine.process_response(
                            question=q_node,
                            selected_option="OMIT",
                            phase_label=f"Guía {active_guide.exam}",
                        )
                        st.session_state.asked_ids.append(q_node.node_id)
                        st.session_state.unit_workout_answers[ans_key] = {
                            "selected": None,
                            "state": state_res,
                        }
                        st.rerun()

                # Si el alumno ya comprobó u omitió este ejercicio, mostrar feedback y Coaching IA en LaTeX
                if ans_key in st.session_state.unit_workout_answers:
                    record = st.session_state.unit_workout_answers[ans_key]
                    u_sel = record["selected"]
                    u_state = record["state"]
                    ai_cache_key = f"unit_{ans_key}_{u_sel}_{u_state}"

                    st.divider()
                    if u_state == "CORRECT":
                        st.success(
                            f"🎉 **¡Correcto!** Marcaste la alternativa **{u_sel})**, que coincide con la pauta oficial DEMRE."
                        )
                    elif u_state == "OMITTED":
                        st.warning(
                            f"🏳️ **Pregunta omitida (Vacío de Conocimiento registrado).** "
                            f"La alternativa correcta según el DEMRE es la **{q_node.correct_option})**."
                        )
                    else:
                        st.error(
                            f"❌ **Respuesta incorrecta.** Marcaste **{u_sel})**, pero la clave oficial DEMRE es la **{q_node.correct_option})**."
                        )

                    if ai_cache_key not in st.session_state.ai_explanations_cache:
                        with st.spinner("🤖 Generando resolución paso a paso en LaTeX..."):
                            explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                                question=q_node,
                                selected_option=u_sel,
                                state=u_state,
                                api_key_override=st.session_state.get("llm_manual_key"),
                                provider_override=st.session_state.get("llm_provider_choice"),
                            )
                            st.session_state.ai_explanations_cache[ai_cache_key] = explanation

                    st.markdown(st.session_state.ai_explanations_cache[ai_cache_key])


# =====================================================================
# SECCIÓN 1: PERFIL / DASHBOARD MOTIVACIONAL
# =====================================================================
if st.session_state.nav_section == "DASHBOARD":
    st.title(f"👤 Dashboard de Rendimiento • {profile.username}")
    st.caption(
        "Resumen persistente de tu progreso hacia la PAES de Matemáticas (M1 y M2), "
        "racha de estudio y prioridades detectadas por el motor adaptativo de GoPAES."
    )

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

            c_g1, c_g2 = st.columns(2)
            with c_g1:
                if st.button("📘 Guías PAES M1", use_container_width=True):
                    st.session_state.selected_guide_id = None
                    st.session_state.nav_section = "GUIDES_M1"
                    st.rerun()
            with c_g2:
                if st.button("📕 Guías PAES M2", use_container_width=True):
                    st.session_state.selected_guide_id = None
                    st.session_state.nav_section = "GUIDES_M2"
                    st.rerun()

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
# SECCIÓN 3A: GUÍAS EXHAUSTIVAS POR MATERIA - EXCLUSIVO PAES M1
# =====================================================================
elif st.session_state.nav_section == "GUIDES_M1":
    render_exhaustive_study_guides_section(exam_target="M1")


# =====================================================================
# SECCIÓN 3B: GUÍAS EXHAUSTIVAS POR MATERIA - EXCLUSIVO PAES M2
# =====================================================================
elif st.session_state.nav_section == "GUIDES_M2":
    render_exhaustive_study_guides_section(exam_target="M2")


# =====================================================================
# SECCIÓN 4: ENSAYOS (DEBILIDADES, ENSAYO FULL 65 Y MODO GENERAL)
# =====================================================================
elif st.session_state.nav_section == "EXAMS":
    st.title("📝 Motor de Ensayos GoPAES")

    if st.session_state.exam_subphase == "CONFIG":
        col_full, col_custom = st.columns(2)

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
                    value=5,
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
                    f"⚖️ Iniciar Ensayo General ({exam_choice})"
                    if ignore_weights
                    else f"🔥 Iniciar Ensayo de Debilidades ({exam_choice})"
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
                    f"🔥 **Ensayo de Debilidades GoPAES ({cfg['exam']}):** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                    f"(Priorizado con **{axis_prob}%** según tu historial)."
                )
            elif mode_active == "GENERAL_STANDARD":
                st.info(
                    f"⚖️ **Ensayo General Estándar ({cfg['exam']}):** Eje **{AXIS_LABELS[q.thematic_axis]}** "
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
