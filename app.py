import os
import math
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

# Importación resiliente del catálogo de Micro-Unidades DEMRE
try:
    from demre_ingestion_pipeline import MICRO_UNITS_CATALOG, get_micro_units_for_exam_and_axis
    from adaptive_engine import MicroUnitMasteryState
except ImportError:
    MICRO_UNITS_CATALOG = {}
    def get_micro_units_for_exam_and_axis(exam, axis=None):
        return []
    MicroUnitMasteryState = None

# =====================================================================
# CONFIGURACIÓN DE PÁGINA STREAMLIT - GOPAES
# =====================================================================
st.set_page_config(
    page_title="GoPAES | Plataforma Adaptativa por Micro-Unidades DEMRE (M1 y M2)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# CATÁLOGO CANÓNICO DE LAS 20 MICRO-UNIDADES OFICIALES DEMRE
# =====================================================================
CANONICAL_MICRO_UNITS = {
    # Eje Números
    "NUM_CONJUNTOS": {
        "name": "Conjuntos Numéricos (Enteros, Racionales y Reales M2)",
        "axis": "NUMEROS",
        "exams": ["M1", "M2"],
        "keyword": "conjuntos",
    },
    "NUM_RAZONES_PROP": {
        "name": "Razones y Proporciones",
        "axis": "NUMEROS",
        "exams": ["M1", "M2"],
        "keyword": "razones",
    },
    "NUM_PORCENTAJES": {
        "name": "Porcentajes",
        "axis": "NUMEROS",
        "exams": ["M1", "M2"],
        "keyword": "porcentaje",
    },
    # Eje Álgebra y Funciones
    "ALG_EXPRESIONES": {
        "name": "Expresiones Algebraicas",
        "axis": "ALGEBRA_Y_FUNCIONES",
        "exams": ["M1", "M2"],
        "keyword": "expresiones",
    },
    "ALG_ECUACIONES_1G": {
        "name": "Ecuaciones e Inecuaciones de 1° Grado",
        "axis": "ALGEBRA_Y_FUNCIONES",
        "exams": ["M1", "M2"],
        "keyword": "inecuación",
    },
    "ALG_SISTEMAS_2X2": {
        "name": "Sistemas de Ecuaciones (2x2)",
        "axis": "ALGEBRA_Y_FUNCIONES",
        "exams": ["M1", "M2"],
        "keyword": "sistemas",
    },
    "ALG_FUNCION_LINEAL": {
        "name": "Función Lineal y Afín",
        "axis": "ALGEBRA_Y_FUNCIONES",
        "exams": ["M1", "M2"],
        "keyword": "lineal",
    },
    "ALG_FUNCION_CUADRATICA": {
        "name": "Función Cuadrática",
        "axis": "ALGEBRA_Y_FUNCIONES",
        "exams": ["M1", "M2"],
        "keyword": "cuadrática",
    },
    # Eje Geometría
    "GEO_FIGURAS_2D": {
        "name": "Perímetro y Área de Figuras 2D",
        "axis": "GEOMETRIA",
        "exams": ["M1", "M2"],
        "keyword": "trapecio",
    },
    "GEO_CUERPOS_3D": {
        "name": "Cuerpos Geométricos 3D",
        "axis": "GEOMETRIA",
        "exams": ["M1", "M2"],
        "keyword": "cilíndrico",
    },
    "GEO_ISOMETRICAS": {
        "name": "Transformaciones Isométricas",
        "axis": "GEOMETRIA",
        "exams": ["M1", "M2"],
        "keyword": "isométrica",
    },
    "GEO_PITAGORAS": {
        "name": "Teorema de Pitágoras",
        "axis": "GEOMETRIA",
        "exams": ["M1", "M2"],
        "keyword": "pitágoras",
    },
    "GEO_SEMEJANZA": {
        "name": "Semejanza y Proporcionalidad",
        "axis": "GEOMETRIA",
        "exams": ["M1", "M2"],
        "keyword": "semejanza",
    },
    "GEO_HOMOTECIA_M2": {
        "name": "Homotecia (Solo M2)",
        "axis": "GEOMETRIA",
        "exams": ["M2"],
        "keyword": "homotecia",
    },
    "GEO_TRIGONOMETRIA_M2": {
        "name": "Razones Trigonométricas (Solo M2)",
        "axis": "GEOMETRIA",
        "exams": ["M2"],
        "keyword": "elevación",
    },
    # Eje Probabilidad y Estadística
    "PROB_TABLAS_GRAFICOS": {
        "name": "Representación de Datos (Tablas y Gráficos)",
        "axis": "PROBABILIDAD_Y_ESTADISTICA",
        "exams": ["M1", "M2"],
        "keyword": "frecuencia",
    },
    "PROB_TENDENCIA_CENTRAL": {
        "name": "Medidas de Tendencia Central",
        "axis": "PROBABILIDAD_Y_ESTADISTICA",
        "exams": ["M1", "M2"],
        "keyword": "promedio",
    },
    "PROB_POSICION": {
        "name": "Medidas de Posición (Cuartiles/Percentiles)",
        "axis": "PROBABILIDAD_Y_ESTADISTICA",
        "exams": ["M1", "M2"],
        "keyword": "cuartil",
    },
    "PROB_REGLAS": {
        "name": "Reglas de Probabilidad",
        "axis": "PROBABILIDAD_Y_ESTADISTICA",
        "exams": ["M1", "M2"],
        "keyword": "probabilidad",
    },
    "PROB_CONTEO_M2": {
        "name": "Técnicas de Conteo / Combinatoria (Solo M2)",
        "axis": "PROBABILIDAD_Y_ESTADISTICA",
        "exams": ["M2"],
        "keyword": "combinatoria",
    },
}

# =====================================================================
# INICIALIZACIÓN DE BASE VECTORIAL QDRANT (+220 REACTIVOS MICRO-UNIDADES)
# =====================================================================
if "vector_store" not in st.session_state:
    store = GoPAESVectorStore()
    seeded_nodes = store.seed_official_demre_questions()
    st.session_state.vector_store = store
    st.session_state.total_indexed_nodes = len(seeded_nodes)

if "active_username" not in st.session_state:
    st.session_state.active_username = None

if "nav_section" not in st.session_state:
    # 'DASHBOARD' | 'DIAGNOSTIC' | 'EXAMS' | 'GUIDES_M1' | 'GUIDES_M2'
    st.session_state.nav_section = "DASHBOARD"

if "exam_subphase" not in st.session_state:
    st.session_state.exam_subphase = "CONFIG"

if "diag_questions" not in st.session_state:
    all_nodes = st.session_state.vector_store.get_all_nodes(exam="M1")
    anchors = [q for q in all_nodes if q.is_diagnostic_anchor][:4]
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
    st.session_state.selected_guide_id = None

if "unit_custom_workouts" not in st.session_state:
    st.session_state.unit_custom_workouts = {}

if "unit_workout_answers" not in st.session_state:
    st.session_state.unit_workout_answers = {}

if "exam_config" not in st.session_state:
    st.session_state.exam_config = {
        "exam": "M1",
        "num_questions": 5,
        "timed_mode": True,
        "selection_mode": "ADAPTIVE",
        "focus_micro_unit_id": None,
    }


# =====================================================================
# FUNCIONES AUXILIARES RESILIENTES PARA MICRO-UNIDADES Y GUÍAS
# =====================================================================
def get_micro_unit_mastery_pct(engine_inst: GoPAESAdaptiveEngine, micro_unit_id: str) -> float:
    mu_dict = getattr(engine_inst, "micro_units_state", None)
    if mu_dict and micro_unit_id in mu_dict:
        return round(mu_dict[micro_unit_id].mastery_score * 100, 1)
    meta = CANONICAL_MICRO_UNITS.get(micro_unit_id)
    if meta:
        ax = meta["axis"]
        return round(engine_inst.axes_state[ax].mastery_score * 100, 1)
    return 50.0


def get_micro_unit_probabilities_safe(
    engine_inst: GoPAESAdaptiveEngine, exam: ExamType = "M1", mode: SelectionMode = "ADAPTIVE"
) -> dict[str, float]:
    if hasattr(engine_inst, "compute_micro_unit_sampling_probabilities"):
        return engine_inst.compute_micro_unit_sampling_probabilities(exam=exam, mode=mode)

    valid_ids = [uid for uid, m in CANONICAL_MICRO_UNITS.items() if exam in m["exams"]]
    if not valid_ids:
        return {}
    uniform = round(1.0 / len(valid_ids), 4)
    return {uid: uniform for uid in valid_ids}


def get_guide_micro_unit_id(guide: DEMREExhaustiveGuide) -> str:
    mu_id = getattr(guide, "micro_unit_id", "")
    if mu_id and mu_id in CANONICAL_MICRO_UNITS:
        return mu_id
    title_l = guide.unit_title.lower()
    if "razones y proporciones" in title_l:
        return "NUM_RAZONES_PROP"
    if "porcentaje" in title_l or "financiera" in title_l:
        return "NUM_PORCENTAJES"
    if "expresiones" in title_l:
        return "ALG_EXPRESIONES"
    if "ecuaciones e inecuaciones" in title_l or "1° grado" in title_l:
        return "ALG_ECUACIONES_1G"
    if "sistemas" in title_l:
        return "ALG_SISTEMAS_2X2"
    if "lineal" in title_l or "afín" in title_l:
        return "ALG_FUNCION_LINEAL"
    if "cuadrática" in title_l:
        return "ALG_FUNCION_CUADRATICA"
    if "2d" in title_l or "perímetro y área" in title_l:
        return "GEO_FIGURAS_2D"
    if "3d" in title_l or "cuerpos" in title_l:
        return "GEO_CUERPOS_3D"
    if "isométrica" in title_l:
        return "GEO_ISOMETRICAS"
    if "pitágoras" in title_l:
        return "GEO_PITAGORAS"
    if "semejanza" in title_l:
        return "GEO_SEMEJANZA"
    if "homotecia" in title_l:
        return "GEO_HOMOTECIA_M2"
    if "trigonométrica" in title_l:
        return "GEO_TRIGONOMETRIA_M2"
    if "tablas" in title_l or "representación" in title_l:
        return "PROB_TABLAS_GRAFICOS"
    if "tendencia central" in title_l:
        return "PROB_TENDENCIA_CENTRAL"
    if "posición" in title_l or "cuartil" in title_l:
        return "PROB_POSICION"
    if "reglas de probabilidad" in title_l:
        return "PROB_REGLAS"
    if "conteo" in title_l or "combinatoria" in title_l:
        return "PROB_CONTEO_M2"
    return "NUM_CONJUNTOS"


def _get_guide_short_desc(guide: DEMREExhaustiveGuide) -> str:
    desc = getattr(guide, "short_description", "")
    if desc:
        return desc
    return (
        f"Micro-unidad oficial del temario DEMRE para {guide.unit_title}. "
        f"Incluye marco teórico, formulario en LaTeX, receta paso a paso y ejercicios con comprobación inmediata."
    )


def _get_guide_subtopic_kw(guide: DEMREExhaustiveGuide) -> str:
    kw = getattr(guide, "subtopic_filter_keyword", "")
    if kw:
        return kw
    mu_id = get_guide_micro_unit_id(guide)
    return CANONICAL_MICRO_UNITS.get(mu_id, {}).get("keyword", "enteros")


def build_unit_exercise_queue_safe(
    engine_inst: GoPAESAdaptiveEngine,
    vector_store: GoPAESVectorStore,
    exam: ExamType,
    axis: ThematicAxis,
    subtopic_keyword: str,
    num_questions: int,
    exclude_ids: list[str] | None = None,
    micro_unit_id: str | None = None,
) -> list[DEMREQuestionNode]:
    """
    Obtiene `num_questions` ejercicios pertenecientes exactamente a la Micro-Unidad (`micro_unit_id`).
    """
    if hasattr(engine_inst, "build_unit_exercise_queue"):
        try:
            return engine_inst.build_unit_exercise_queue(
                vector_store=vector_store,
                exam=exam,
                axis=axis,
                subtopic_keyword=subtopic_keyword,
                num_questions=num_questions,
                exclude_ids=exclude_ids,
                micro_unit_id=micro_unit_id,
            )
        except TypeError:
            return engine_inst.build_unit_exercise_queue(
                vector_store=vector_store,
                exam=exam,
                axis=axis,
                subtopic_keyword=subtopic_keyword,
                num_questions=num_questions,
                exclude_ids=exclude_ids,
            )

    excluded = set(exclude_ids or [])
    combined: list[DEMREQuestionNode] = []

    if micro_unit_id and hasattr(vector_store, "query_by_micro_unit"):
        for cand in (
            vector_store.query_by_micro_unit(micro_unit_id, exam=exam, exclude_ids=list(excluded))
            + vector_store.query_by_micro_unit(micro_unit_id, exam=exam, exclude_ids=[])
        ):
            if cand.node_id not in [c.node_id for c in combined]:
                combined.append(cand)
            if len(combined) >= num_questions:
                return combined[:num_questions]

    axis_pool: list[DEMREQuestionNode] = vector_store.query_by_axis_and_exam(
        exam=exam,
        axis=axis,
        exclude_ids=[],
        diagnostic_only=False,
    )
    kw = (subtopic_keyword or "").strip().lower()
    primary = [
        q for q in axis_pool
        if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id not in excluded
    ]
    secondary = [
        q for q in axis_pool
        if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id in excluded
    ]
    for candidate in primary + secondary + axis_pool:
        if candidate.node_id not in [c.node_id for c in combined]:
            combined.append(candidate)
        if len(combined) >= num_questions:
            break
    return combined[:num_questions]


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
    st.title("🚀 Bienvenido a GoPAES • Preparación Adaptativa por Micro-Unidades DEMRE")
    st.markdown(
        "Ingresa tu nombre para crear o cargar tu **Perfil Persistente de Estudiante**. "
        "GoPAES rastrea tu dominio en las **20 Micro-Unidades oficiales del DEMRE (M1 y M2)** "
        "para que tus prácticas y ensayos de debilidades ataquen exactamente los sub-temas que necesitas reforzar."
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
# BARRA LATERAL: NAVEGACIÓN + RADAR DE MICRO-UNIDADES EN VIVO
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
        f"🗄️ Banco Vectorial Qdrant: **{st.session_state.get('total_indexed_nodes', 228)} reactivos en 20 Micro-Unidades DEMRE**"
    )

    st.markdown("### 🧭 Menú de Navegación")
    nav_labels = {
        "DASHBOARD": "👤 Perfil / Dashboard",
        "DIAGNOSTIC": "🎯 Diagnóstico por Micro-Unidades",
        "EXAMS": "📝 Ensayos (Full y Debilidades)",
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

    # PANEL DE TRANSPARENCIA DEL MOTOR ADAPTATIVO EN VIVO (EJES + TOP MICRO-UNIDADES DÉBILES)
    st.markdown("### 🧠 Radar Adaptativo en Vivo")
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

    rows = []
    for axis in ALL_AXES:
        st_axis = engine.axes_state[axis]
        rows.append({
            "Eje": AXIS_LABELS[axis],
            "Dominio": f"{round(st_axis.mastery_score * 100)}%",
            "Peso IA": f"{round(adaptive_probs[axis] * 100, 1)}%",
            "Errores": st_axis.incorrect_count,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Mostrar las 3 micro-unidades específicas con mayor prioridad de refuerzo
    mu_probs_m1 = get_micro_unit_probabilities_safe(engine, exam="M1", mode="ADAPTIVE")
    if mu_probs_m1:
        top_weak_uids = sorted(mu_probs_m1.keys(), key=lambda u: mu_probs_m1[u], reverse=True)[:3]
        st.caption("🎯 **Micro-Unidades Prioritarias (Nicho a reforzar):**")
        for uid in top_weak_uids:
            u_name = CANONICAL_MICRO_UNITS.get(uid, {}).get("name", uid)
            dom_u = get_micro_unit_mastery_pct(engine, uid)
            prob_u = round(mu_probs_m1[uid] * 100, 1)
            st.markdown(f"- **{u_name}**: Dominio `{dom_u}%` (Prioridad `{prob_u}%`)")

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
            if hasattr(fresh, "micro_units_state"):
                fresh.micro_units_state = {}
            fresh.logs = []
            GoPAESProfileManager.save_profile(fresh)
            st.session_state.engine = GoPAESAdaptiveEngine(profile=fresh)
            st.session_state.unit_workout_answers = {}
            st.session_state.interleaved_feedback = {}
            st.rerun()


# =====================================================================
# COMPONENTES REUTILIZABLES: TARJETA DE PREGUNTA Y GUÍAS POR MICRO-UNIDAD
# =====================================================================
def render_question_card(question: DEMREQuestionNode, step_num: int, total_steps: int, badge_text: str):
    mu_id = getattr(question, "micro_unit_id", "NUM_CONJUNTOS")
    mu_name = CANONICAL_MICRO_UNITS.get(mu_id, {}).get("name", question.subtopic_name)

    col_badge, col_source = st.columns([2, 3])
    with col_badge:
        st.markdown(f"#### {badge_text} • Ejercicio {step_num} de {total_steps}")
    with col_source:
        st.markdown(
            f"<div style='text-align:right; color:#94a3b8; font-size:0.9rem;'>"
            f"📌 <b>PAES {question.exam}</b> | Eje: <b>{AXIS_LABELS[question.thematic_axis]}</b><br>"
            f"🎯 Micro-Unidad: <b>{mu_name}</b></div>",
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


def render_exhaustive_study_guides_section(exam_target: ExamType):
    """
    Renderiza la sección de Guías por Materia (PAES M1 o PAES M2) estructurada en las
    Micro-Unidades oficiales del DEMRE:
    - Eje Números: Conjuntos Numéricos, Razones y Proporciones, Porcentajes.
    - Eje Álgebra y Funciones: Expresiones Algebraicas, Ecuaciones e Inecuaciones de 1° Grado,
      Sistemas de Ecuaciones (2x2), Función Lineal y Afín, Función Cuadrática.
    - Eje Geometría: Perímetro y Área de Figuras 2D, Cuerpos Geométricos 3D,
      Transformaciones Isométricas, Teorema de Pitágoras, Semejanza y Proporcionalidad,
      Homotecia (solo M2), Razones Trigonométricas (solo M2).
    - Eje Probabilidad y Estadística: Representación de Datos (Tablas y Gráficos),
      Medidas de Tendencia Central, Medidas de Posición (Cuartiles/Percentiles),
      Reglas de Probabilidad, Técnicas de Conteo/Combinatoria (solo M2).

    Cada ejercicio práctico dentro de la guía incluye un botón interactivo "✅ Comprobar respuesta"
    con validación inmediata y explicación paso a paso en LaTeX sin salir del modo de estudio.
    """
    badge_color = "#1d4ed8" if exam_target == "M1" else "#9333ea"
    exam_title = (
        "PAES M1 (Competencia Matemática 1 • Obligatoria)"
        if exam_target == "M1"
        else "PAES M2 (Competencia Matemática 2 • Electiva Científica)"
    )

    col_head, col_switch_exam = st.columns([3, 1])
    with col_head:
        st.title(f"{'📘' if exam_target == 'M1' else '📕'} Guías por Micro-Unidad DEMRE • {exam_title}")
    with col_switch_exam:
        other_exam = "M2" if exam_target == "M1" else "M1"
        if st.button(f"🔄 Cambiar a Guías PAES {other_exam}", use_container_width=True):
            st.session_state.nav_section = f"GUIDES_{other_exam}"
            st.session_state.selected_guide_id = None
            st.rerun()

    guides_by_axis = get_exhaustive_guides_by_exam(exam_target)

    # Buscar si hay una guía actualmente seleccionada para este examen
    active_guide: DEMREExhaustiveGuide | None = None
    if st.session_state.selected_guide_id:
        for ax_list in guides_by_axis.values():
            for g in ax_list:
                if g.guide_id == st.session_state.selected_guide_id and g.exam == exam_target:
                    active_guide = g
                    break

    # =========================================================================
    # NIVEL 1: MENÚ INTERMEDIO DE MICRO-UNIDADES DEMRE
    # =========================================================================
    if active_guide is None:
        st.markdown(
            "Selecciona un **Eje Temático** para explorar sus **Micro-Unidades específicas del temario DEMRE**. "
            "Dentro de cada guía podrás estudiar la teoría, seguir la receta paso a paso y usar el botón "
            "**`✅ Comprobar respuesta`** en cada ejercicio práctico sin salir de la guía."
        )

        selected_axis: ThematicAxis = st.selectbox(
            f"1️⃣ Selecciona el Eje Temático de PAES {exam_target}:",
            options=ALL_AXES,
            format_func=lambda a: (
                f"📐 {AXIS_LABELS[a]} — {len(guides_by_axis.get(a, []))} Micro-Unidades DEMRE "
                f"(Dominio del eje: {round(engine.axes_state[a].mastery_score * 100)}%)"
            ),
            key=f"select_axis_guide_{exam_target}",
        )

        axis_guides: list[DEMREExhaustiveGuide] = guides_by_axis.get(selected_axis, [])
        st.markdown(
            f"### 🗂️ 2️⃣ Micro-Unidades de **{AXIS_LABELS[selected_axis]} ({exam_target})**"
        )
        st.caption(
            "Elige qué micro-unidad quieres desarrollar y cuántos ejercicios prácticos quieres incluir en tu sesión de estudio:"
        )

        for idx_g, guide in enumerate(axis_guides, start=1):
            short_desc = _get_guide_short_desc(guide)
            subtopic_kw = _get_guide_subtopic_kw(guide)
            mu_id = get_guide_micro_unit_id(guide)
            mu_dom = get_micro_unit_mastery_pct(engine, mu_id)

            with st.container(border=True):
                col_info, col_actions = st.columns([3, 2])

                with col_info:
                    st.markdown(
                        f"<div style='display:flex; align-items:center; gap:10px; flex-wrap:wrap;'>"
                        f"<span style='background:{badge_color}; color:white; padding:3px 10px; border-radius:99px; font-size:0.8rem; font-weight:bold;'>"
                        f"Micro-Unidad #{idx_g} • {guide.exam}</span>"
                        f"<span style='background:#0f172a; color:#38bdf8; border:1px solid #38bdf8; padding:2px 10px; border-radius:99px; font-size:0.8rem;'>"
                        f"Tu Dominio: {mu_dom}%</span>"
                        f"<h4 style='margin:0;'>{guide.unit_title}</h4>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"📌 {guide.demre_syllabus_reference}")
                    st.write(short_desc)
                    st.markdown(
                        f"🧮 **{len(guide.key_formulas)}** Fórmulas $\\text{{LaTeX}}$ | "
                        f"🧑‍🍳 **{len(guide.resolution_recipe_steps)}** Pasos de Receta | "
                        f"✍️ **Ejercicios con Comprobación Inmediata**"
                    )

                with col_actions:
                    c_num, c_btn = st.columns([1, 2])
                    with c_num:
                        num_ex_menu = st.number_input(
                            "N° Ejercicios:",
                            min_value=1,
                            max_value=20,
                            value=5,
                            step=1,
                            key=f"menu_num_ex_{guide.guide_id}",
                        )
                    with c_btn:
                        st.write("")
                        if st.button(
                            f"📖 Abrir Guía + {num_ex_menu} Ejercicios",
                            type="primary",
                            use_container_width=True,
                            key=f"btn_open_guide_{guide.guide_id}",
                        ):
                            st.session_state.selected_guide_id = guide.guide_id
                            st.session_state.unit_custom_workouts[guide.guide_id] = build_unit_exercise_queue_safe(
                                engine_inst=engine,
                                vector_store=st.session_state.vector_store,
                                exam=guide.exam,
                                axis=guide.thematic_axis,
                                subtopic_keyword=subtopic_kw,
                                num_questions=int(num_ex_menu),
                                exclude_ids=st.session_state.asked_ids,
                                micro_unit_id=mu_id,
                            )
                            st.rerun()

                    if st.button(
                        f"🎯 Ensayo Focalizado en '{guide.unit_title}' ({num_ex_menu} preg.)",
                        use_container_width=True,
                        key=f"btn_focus_exam_{guide.guide_id}",
                    ):
                        queue_mu = build_unit_exercise_queue_safe(
                            engine_inst=engine,
                            vector_store=st.session_state.vector_store,
                            exam=guide.exam,
                            axis=guide.thematic_axis,
                            subtopic_keyword=subtopic_kw,
                            num_questions=int(num_ex_menu),
                            exclude_ids=st.session_state.asked_ids,
                            micro_unit_id=mu_id,
                        )
                        st.session_state.exam_config = {
                            "exam": guide.exam,
                            "num_questions": len(queue_mu),
                            "timed_mode": False,
                            "allocated_seconds": len(queue_mu) * OFFICIAL_SECONDS_PER_QUESTION[guide.exam],
                            "selection_mode": "ADAPTIVE",
                            "focus_micro_unit_id": mu_id,
                        }
                        st.session_state.exam_queue = queue_mu
                        st.session_state.exam_history = []
                        st.session_state.exam_subphase = "ACTIVE_RUN"
                        st.session_state.nav_section = "EXAMS"
                        st.rerun()
        return

    # =========================================================================
    # NIVEL 2: GUÍA DE LA MICRO-UNIDAD CON "COMPROBAR RESPUESTA" EN CADA EJERCICIO
    # =========================================================================
    active_subtopic_kw = _get_guide_subtopic_kw(active_guide)
    active_mu_id = get_guide_micro_unit_id(active_guide)
    active_mu_dom = get_micro_unit_mastery_pct(engine, active_mu_id)

    col_back, col_unit_badge = st.columns([1, 3])
    with col_back:
        if st.button("⬅️ Volver al Menú de Micro-Unidades", use_container_width=True):
            st.session_state.selected_guide_id = None
            st.rerun()
    with col_unit_badge:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span style='background:{badge_color}; color:white; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
            f"{AXIS_LABELS[active_guide.thematic_axis]} • {active_guide.exam}</span> "
            f"<span style='background:#0f172a; color:#38bdf8; border:1px solid #38bdf8; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
            f"Dominio en esta Micro-Unidad: {active_mu_dom}%</span></div>",
            unsafe_allow_html=True,
        )

    st.header(f"📘 {active_guide.unit_title}")
    st.caption(f"📌 {active_guide.demre_syllabus_reference}")

    # -----------------------------------------------------------------
    # BLOQUE A: MARCO TEÓRICO, FORMULARIO LATEX, RECETA Y TRAMPAS DEMRE
    # -----------------------------------------------------------------
    with st.container(border=True):
        st.markdown(active_guide.theoretical_framework_md)
        st.divider()

        st.markdown("#### 🧮 Formulario y Propiedades Fundamentales ($\\text{LaTeX}$)")
        for f_card in active_guide.key_formulas:
            with st.container(border=True):
                st.markdown(f"**{f_card.title}**")
                st.latex(f_card.latex_formula)
                st.caption(f"💡 *Interpretación DEMRE:* {f_card.explanation}")

        st.divider()

        st.markdown(f"#### 🧑‍🍳 {active_guide.resolution_recipe_title}")
        st.info("Aplica este algoritmo paso a paso para resolver los problemas de esta micro-unidad:")
        for recipe_step in active_guide.resolution_recipe_steps:
            st.markdown(f"- ✅ **{recipe_step}**")

        st.divider()

        st.markdown("#### ⚠️ Trampas y Distractores Frecuentes del DEMRE")
        for trap in active_guide.common_demre_traps:
            st.warning(f"🔎 {trap}")

    # -----------------------------------------------------------------
    # BLOQUE B: EJERCICIOS GUIADOS CON BOTÓN "COMPROBAR RESPUESTA" IN-PLACE
    # -----------------------------------------------------------------
    st.markdown("### ✍️ Parte 1: Ejercicios Guiados de la Micro-Unidad (Validación Inmediata)")
    st.caption(
        "Selecciona una alternativa y presiona **`✅ Comprobar respuesta`** para verificar tu resultado "
        "y desplegar la explicación paso a paso sin salir de la guía."
    )

    for ex in active_guide.interleaved_exercises:
        with st.container(border=True):
            st.markdown(f"#### 🎯 {ex.title}")
            st.write(ex.stem_text)
            st.latex(ex.stem_latex)

            for opt_k, opt_latex in ex.options.items():
                c_k, c_lat = st.columns([1, 11])
                with c_k:
                    st.markdown(f"**`{opt_k})`**")
                with c_lat:
                    st.latex(opt_latex)

            chosen_ex_opt = st.radio(
                "Selecciona tu respuesta para este ejercicio:",
                options=list(ex.options.keys()),
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"interleaved_radio_{ex.exercise_id}",
            )

            if st.button(
                "✅ Comprobar respuesta",
                type="primary",
                key=f"btn_check_{ex.exercise_id}",
            ):
                st.session_state.interleaved_feedback[ex.exercise_id] = chosen_ex_opt

            if ex.exercise_id in st.session_state.interleaved_feedback:
                user_ans = st.session_state.interleaved_feedback[ex.exercise_id]
                st.divider()
                if user_ans == ex.correct_option:
                    st.success(f"🎉 **¡Respuesta Correcta! La alternativa oficial es la {ex.correct_option}).**")
                else:
                    st.error(
                        f"❌ **Respuesta Incorrecta.** Marcaste la alternativa **{user_ans})**, "
                        f"pero la alternativa correcta es la **{ex.correct_option})**."
                    )
                st.markdown("#### 📘 Explicación Paso a Paso:")
                for s_line in ex.step_by_step_solution:
                    st.markdown(s_line)

    st.divider()

    # -----------------------------------------------------------------
    # BLOQUE C: PRÁCTICA PERSONALIZADA DE LA MICRO-UNIDAD CON "COMPROBAR RESPUESTA"
    # -----------------------------------------------------------------
    st.markdown(f"### 🏋️ Parte 2: Ejercicios Prácticos de **{active_guide.unit_title}** (Elige la Cantidad)")
    with st.container(border=True):
        st.write(
            "Elige cuántos ejercicios de esta micro-unidad deseas resolver aquí mismo. "
            "Cada ejercicio cuenta con su botón **`✅ Comprobar respuesta`** para entregarte validación inmediata, "
            "explicación paso a paso en $\\text{LaTeX}$ y actualizar tu dominio en esta micro-unidad sin abandonar el modo estudio."
        )

        current_list: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts.get(
            active_guide.guide_id, []
        )
        default_qty = len(current_list) if current_list else 5

        col_slider, col_btn_load = st.columns([3, 2])
        with col_slider:
            desired_qty = st.slider(
                "Cantidad de ejercicios a desarrollar de esta micro-unidad:",
                min_value=1,
                max_value=15,
                value=min(15, default_qty),
                key=f"unit_qty_slider_{active_guide.guide_id}",
            )
        with col_btn_load:
            st.write("")
            if st.button(
                f"🔄 Generar {desired_qty} Ejercicios de esta Micro-Unidad",
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
                    micro_unit_id=active_mu_id,
                )
                st.rerun()

    if active_guide.guide_id not in st.session_state.unit_custom_workouts:
        st.session_state.unit_custom_workouts[active_guide.guide_id] = build_unit_exercise_queue_safe(
            engine_inst=engine,
            vector_store=st.session_state.vector_store,
            exam=active_guide.exam,
            axis=active_guide.thematic_axis,
            subtopic_keyword=active_subtopic_kw,
            num_questions=int(desired_qty),
            exclude_ids=st.session_state.asked_ids,
            micro_unit_id=active_mu_id,
        )

    workout_questions: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts[active_guide.guide_id]

    answered_in_unit = sum(
        1
        for q_node in workout_questions
        if f"{active_guide.guide_id}_{q_node.node_id}" in st.session_state.unit_workout_answers
    )
    st.progress(
        answered_in_unit / max(1, len(workout_questions)),
        text=f"Progreso en '{active_guide.unit_title}': {answered_in_unit} de {len(workout_questions)} ejercicio(s) comprobado(s)",
    )

    for q_idx, q_node in enumerate(workout_questions, start=1):
        ans_key = f"{active_guide.guide_id}_{q_node.node_id}"
        with st.container(border=True):
            render_question_card(
                question=q_node,
                step_num=q_idx,
                total_steps=len(workout_questions),
                badge_text=f"🏋️ Ejercicio de Micro-Unidad ({active_guide.exam})",
            )

            chosen_unit_opt = st.radio(
                "Selecciona tu alternativa:",
                options=[o.key for o in q_node.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"unit_q_radio_{ans_key}_{q_idx}",
            )

            col_check, col_omit_u = st.columns(2)
            with col_check:
                if st.button(
                    "✅ Comprobar respuesta",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_unit_check_{ans_key}_{q_idx}",
                ):
                    state_res = engine.process_response(
                        question=q_node,
                        selected_option=chosen_unit_opt,
                        phase_label=f"Guía {active_guide.unit_title}",
                    )
                    st.session_state.asked_ids.append(q_node.node_id)
                    st.session_state.unit_workout_answers[ans_key] = {
                        "selected": chosen_unit_opt,
                        "state": state_res,
                    }
                    st.rerun()

            with col_omit_u:
                if st.button(
                    "🏳️ Dejar en blanco y ver explicación paso a paso",
                    use_container_width=True,
                    key=f"btn_unit_omit_{ans_key}_{q_idx}",
                ):
                    state_res = engine.process_response(
                        question=q_node,
                        selected_option="OMIT",
                        phase_label=f"Guía {active_guide.unit_title}",
                    )
                    st.session_state.asked_ids.append(q_node.node_id)
                    st.session_state.unit_workout_answers[ans_key] = {
                        "selected": None,
                        "state": state_res,
                    }
                    st.rerun()

            if ans_key in st.session_state.unit_workout_answers:
                record = st.session_state.unit_workout_answers[ans_key]
                u_sel = record["selected"]
                u_state = record["state"]
                ai_cache_key = f"unit_{ans_key}_{u_sel}_{u_state}"

                st.divider()
                if u_state == "CORRECT":
                    st.success(
                        f"🎉 **¡Respuesta Correcta!** Marcaste la alternativa **{u_sel})**, que coincide con la pauta oficial DEMRE. "
                        f"Tu dominio en **{active_guide.unit_title}** ha subido a **{get_micro_unit_mastery_pct(engine, active_mu_id)}%**."
                    )
                elif u_state == "OMITTED":
                    st.warning(
                        f"🏳️ **Ejercicio omitido (Vacío de Conocimiento registrado en '{active_guide.unit_title}').** "
                        f"La alternativa correcta según el DEMRE es la **{q_node.correct_option})**."
                    )
                else:
                    st.error(
                        f"❌ **Respuesta Incorrecta.** Marcaste **{u_sel})**, pero la alternativa correcta es la **{q_node.correct_option})**. "
                        f"El motor adaptativo reforzará **{active_guide.unit_title}** en tus próximos ensayos."
                    )

                if ai_cache_key not in st.session_state.ai_explanations_cache:
                    with st.spinner("🤖 Generando explicación paso a paso en LaTeX..."):
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
# SECCIÓN 1: PERFIL / DASHBOARD CON RADAR DE MICRO-UNIDADES DEMRE
# =====================================================================
if st.session_state.nav_section == "DASHBOARD":
    st.title(f"👤 Dashboard de Rendimiento • {profile.username}")
    st.caption(
        "Seguimiento granular por **Ejes Temáticos** y **Micro-Unidades DEMRE (M1 y M2)**. "
        "El algoritmo adaptativo detecta tus nichos específicos de error (ej. *Función Cuadrática* o *Medidas de Posición*) "
        "para personalizar tus ensayos de debilidades."
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
            st.subheader("📊 Dominio Global por Eje Temático DEMRE")
            adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

            for axis in ALL_AXES:
                st_axis = engine.axes_state[axis]
                dom_pct = round(st_axis.mastery_score * 100, 1)
                prob_pct = round(adaptive_probs[axis] * 100, 1)
                st.markdown(
                    f"**{AXIS_LABELS[axis]}** — Dominio: `{dom_pct}%` | "
                    f"Precisión Neta: `{st_axis.net_accuracy}%` | "
                    f"Peso del Eje: **{prob_pct}%**"
                )
                st.progress(min(1.0, st_axis.mastery_score))

    with col_right:
        with st.container(border=True):
            st.subheader("🚀 Acciones Rápidas de Estudio")
            if not profile.diagnostic_completed:
                st.warning("🎯 **Diagnóstico Pendiente:** Realiza las 4 preguntas ancla para calibrar tu perfil inicial.")
            else:
                st.success("✅ **Diagnóstico Inicial Calibrado**")

            if st.button("🎯 Ir al Diagnóstico por Micro-Unidades", use_container_width=True):
                st.session_state.diag_idx = 0
                st.session_state.nav_section = "DIAGNOSTIC"
                st.rerun()

            if st.button("🔥 Iniciar Ensayo de Debilidades (Ataca tus Micro-Unidades Débiles)", type="primary", use_container_width=True):
                st.session_state.exam_config["selection_mode"] = "ADAPTIVE"
                st.session_state.exam_config["focus_micro_unit_id"] = None
                st.session_state.exam_subphase = "CONFIG"
                st.session_state.nav_section = "EXAMS"
                st.rerun()

            if st.button("🏛️ Ir a Ensayo Full Oficial PAES (65 Preguntas)", use_container_width=True):
                st.session_state.exam_config["selection_mode"] = "OFFICIAL_65"
                st.session_state.exam_config["focus_micro_unit_id"] = None
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

    # DESGLOSE COMPLETO DE LAS 20 MICRO-UNIDADES DEMRE
    with st.container(border=True):
        st.subheader("🎯 Mapa Granular de Micro-Unidades DEMRE (Detección de Nichos de Debilidad)")
        st.caption(
            "Aquí puedes ver tu dominio y prioridad de refuerzo en cada sub-tema específico del temario oficial:"
        )
        mu_probs_all = get_micro_unit_probabilities_safe(engine, exam="M2", mode="ADAPTIVE")
        mu_rows = []
        for uid, meta in CANONICAL_MICRO_UNITS.items():
            u_obj = getattr(engine, "micro_units_state", {}).get(uid)
            dom_val = get_micro_unit_mastery_pct(engine, uid)
            err_cnt = u_obj.incorrect_count if u_obj else 0
            omit_cnt = u_obj.omitted_count if u_obj else 0
            ok_cnt = u_obj.correct_count if u_obj else 0
            prob_val = round(mu_probs_all.get(uid, 0.05) * 100, 1)
            mu_rows.append({
                "Eje Temático": AXIS_LABELS[meta["axis"]],
                "Micro-Unidad DEMRE": meta["name"],
                "Pruebas": " / ".join(meta["exams"]),
                "Dominio": f"{dom_val}%",
                "Prioridad IA": f"{prob_val}%",
                "Correctas": ok_cnt,
                "Errores": err_cnt,
                "Omitidas": omit_cnt,
            })
        st.dataframe(pd.DataFrame(mu_rows), use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("📜 Historial Reciente del Motor Adaptativo (Por Micro-Unidad)")
        if not engine.logs:
            st.info("Aún no registras respuestas en este perfil. Comienza por el Diagnóstico, una Guía o un Ensayo.")
        else:
            for log in engine.logs[:6]:
                delta_str = f"+{log.delta_mastery}%" if log.delta_mastery >= 0 else f"{log.delta_mastery}%"
                u_label = getattr(log, "micro_unit_name", "") or AXIS_LABELS[log.axis]
                st.markdown(
                    f"- **{log.step_label}** ({AXIS_LABELS[log.axis]} • *{u_label}*): "
                    f"Dominio `{log.old_mastery}%` → `{log.new_mastery}%` (`{delta_str}`) — {log.explanation}"
                )


# =====================================================================
# SECCIÓN 2: DIAGNÓSTICO DE CALIBRACIÓN POR MICRO-UNIDADES
# =====================================================================
elif st.session_state.nav_section == "DIAGNOSTIC":
    st.title("🎯 Diagnóstico de Calibración por Micro-Unidades DEMRE")
    st.write(
        "Responde estas preguntas ancla del DEMRE o usa **'Dejar en blanco'** para que GoPAES "
        "identifique tus brechas iniciales por micro-unidad sin penalizar tu precisión por azar."
    )

    diag_qs: list[DEMREQuestionNode] = st.session_state.diag_questions
    idx: int = st.session_state.diag_idx

    if idx >= len(diag_qs):
        st.success("🎉 **¡Diagnóstico completado y guardado en tu perfil de Micro-Unidades!**")
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("👤 Ver mi Mapa de Micro-Unidades en el Dashboard", type="primary", use_container_width=True):
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
                badge_text="🎯 Calibración GoPAES",
            )

            st.divider()
            selected_choice = st.radio(
                "Elige una alternativa:",
                options=[o.key for o in current_q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"diag_radio_{current_q.node_id}",
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
# SECCIÓN 3A: GUÍAS POR MICRO-UNIDAD - EXCLUSIVO PAES M1
# =====================================================================
elif st.session_state.nav_section == "GUIDES_M1":
    render_exhaustive_study_guides_section(exam_target="M1")


# =====================================================================
# SECCIÓN 3B: GUÍAS POR MICRO-UNIDAD - EXCLUSIVO PAES M2
# =====================================================================
elif st.session_state.nav_section == "GUIDES_M2":
    render_exhaustive_study_guides_section(exam_target="M2")


# =====================================================================
# SECCIÓN 4: ENSAYOS (DEBILIDADES POR MICRO-UNIDAD, FULL 65 Y MODO GENERAL)
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
                        "focus_micro_unit_id": None,
                    }
                    st.session_state.exam_queue = queue_65
                    st.session_state.exam_history = []
                    st.session_state.exam_subphase = "ACTIVE_RUN"
                    st.rerun()

        with col_custom:
            with st.container(border=True):
                st.subheader("🔥 Ensayo de Debilidades (Por Micro-Unidades) / Personalizado")
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

                # Permitir atacar todas las micro-unidades débiles automáticamente o elegir una micro-unidad específica
                valid_mu_options = ["ALL_ADAPTIVE"] + [
                    uid for uid, m in CANONICAL_MICRO_UNITS.items() if exam_choice in m["exams"]
                ]
                selected_mu_filter = st.selectbox(
                    "Nicho / Micro-Unidad objetivo:",
                    options=valid_mu_options,
                    format_func=lambda uid: (
                        "🧠 Automático IA (Atacar mis Micro-Unidades más débiles)"
                        if uid == "ALL_ADAPTIVE"
                        else f"🎯 Solo '{CANONICAL_MICRO_UNITS[uid]['name']}' (Dominio: {get_micro_unit_mastery_pct(engine, uid)}%)"
                    ),
                )

                num_q = st.slider(
                    "Cantidad de preguntas:",
                    min_value=2,
                    max_value=65 if exam_choice == "M1" else 55,
                    value=6,
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
                    focus_uid = None if selected_mu_filter == "ALL_ADAPTIVE" else selected_mu_filter
                    if focus_uid:
                        meta_u = CANONICAL_MICRO_UNITS[focus_uid]
                        queue = build_unit_exercise_queue_safe(
                            engine_inst=engine,
                            vector_store=st.session_state.vector_store,
                            exam=exam_choice,
                            axis=meta_u["axis"],  # type: ignore
                            subtopic_keyword=meta_u["keyword"],
                            num_questions=num_q,
                            exclude_ids=st.session_state.asked_ids,
                            micro_unit_id=focus_uid,
                        )
                    else:
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
                        "focus_micro_unit_id": focus_uid,
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
        q_mu_id = getattr(q, "micro_unit_id", "NUM_CONJUNTOS")
        q_mu_name = CANONICAL_MICRO_UNITS.get(q_mu_id, {}).get("name", q.subtopic_name)
        q_mu_dom = get_micro_unit_mastery_pct(engine, q_mu_id)
        mu_probs = get_micro_unit_probabilities_safe(engine, exam=cfg["exam"], mode=mode_active)
        mu_prob_pct = round(mu_probs.get(q_mu_id, 0.05) * 100, 1)

        col_reason, col_clock, col_finish = st.columns([3, 1, 1])
        with col_reason:
            if mode_active == "ADAPTIVE":
                st.warning(
                    f"🔥 **Ensayo de Debilidades GoPAES ({cfg['exam']}):** "
                    f"Atacando Micro-Unidad **{q_mu_name}** "
                    f"(Tu dominio actual: `{q_mu_dom}%` • Peso IA: **{mu_prob_pct}%**)."
                )
            elif mode_active == "GENERAL_STANDARD":
                st.info(
                    f"⚖️ **Ensayo General Estándar ({cfg['exam']}):** "
                    f"Eje **{AXIS_LABELS[q.thematic_axis]}** • Micro-Unidad: **{q_mu_name}**."
                )
            else:
                st.info(
                    f"🏛️ **Ensayo Full 65 Preguntas:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                    f"({q_mu_name} • Cuota del eje: {OFFICIAL_PAES_65_DISTRIBUTION[q.thematic_axis]}/65)."
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
                badge_text=f"🚀 GoPAES {cfg['exam']}",
            )

            st.divider()
            user_choice = st.radio(
                "Selecciona una alternativa:",
                options=[o.key for o in q.options],
                format_func=lambda k: f"Alternativa {k}",
                horizontal=True,
                key=f"exam_radio_{step_idx}_{q.node_id}",
            )

            col_ans, col_blank = st.columns([1, 1])

            def record_and_advance(chosen_opt):
                state = engine.process_response(
                    question=q,
                    selected_option=chosen_opt,
                    phase_label="Ensayo GoPAES",
                )
                st.session_state.asked_ids.append(q.node_id)
                st.session_state.exam_history.append({
                    "question": q,
                    "selected_option": chosen_opt,
                    "state": state,
                })

                # Re-adaptar dinámicamente la cola restante en modo ADAPTIVE según la micro-unidad fallada
                if (
                    cfg.get("selection_mode") == "ADAPTIVE"
                    and not cfg.get("focus_micro_unit_id")
                    and (step_idx + 1) < total_q
                ):
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
        st.subheader("🎓 GoPAES Coaching IA • Análisis por Micro-Unidad en LaTeX")

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
            q_mu_id = getattr(q, "micro_unit_id", "NUM_CONJUNTOS")
            q_mu_name = CANONICAL_MICRO_UNITS.get(q_mu_id, {}).get("name", q.subtopic_name)
            cache_key = f"{idx}_{q.node_id}_{sel}_{st_resp}"

            with st.container(border=True):
                if st_resp == "CORRECT":
                    st.success(
                        f"**Pregunta {idx + 1} ({AXIS_LABELS[q.thematic_axis]} • Micro-Unidad: {q_mu_name}): "
                        f"✅ CORRECTA (Marcaste {sel})**"
                    )
                elif st_resp == "OMITTED":
                    st.warning(
                        f"**Pregunta {idx + 1} ({AXIS_LABELS[q.thematic_axis]} • Micro-Unidad: {q_mu_name}): "
                        f"🏳️ DEJADA EN BLANCO (Vacío de Conocimiento • Clave Oficial: {q.correct_option})**"
                    )
                else:
                    st.error(
                        f"**Pregunta {idx + 1} ({AXIS_LABELS[q.thematic_axis]} • Micro-Unidad: {q_mu_name}): "
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
            if st.button("👤 Ir a mi Dashboard de Micro-Unidades", use_container_width=True):
                st.session_state.exam_subphase = "CONFIG"
                st.session_state.nav_section = "DASHBOARD"
                st.rerun()
