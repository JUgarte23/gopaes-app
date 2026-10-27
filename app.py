import os
import json
import hmac
import hashlib
import secrets
from pathlib import Path
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
    page_title="GoPAES | Plataforma Adaptativa PAES (M1 y M2)",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================================
# INICIALIZACIÓN DE BASE VECTORIAL QDRANT
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

if "selected_guide_axis" not in st.session_state:
    # Controla el menú intermedio de las 4 Unidades (None = mostrar catálogo de las 4 unidades)
    st.session_state.selected_guide_axis = None

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
        "focus_axis": None,
    }


# =====================================================================
# SISTEMA DE AUTENTICACIÓN SEGURO (USUARIO + CONTRASEÑA CON HASH SHA-256)
# =====================================================================
AUTH_CREDENTIALS_PATH = Path("./storage/gopaes_credentials.json")


def _hash_pwd_local(password: str, salt_hex: str) -> str:
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        100_000,
    )
    return dk.hex()


def _load_credentials_store() -> dict:
    AUTH_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not AUTH_CREDENTIALS_PATH.exists():
        AUTH_CREDENTIALS_PATH.write_text("{}", encoding="utf-8")
        return {}
    try:
        return json.loads(AUTH_CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_credentials_store(data: dict) -> None:
    AUTH_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUTH_CREDENTIALS_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def register_student_account(username: str, password: str, confirm_password: str) -> tuple[bool, str]:
    clean_user = username.strip()
    if not clean_user:
        return False, "Por favor escribe un nombre de usuario."
    if len(clean_user) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres."
    if len(password) < 4:
        return False, "La contraseña debe tener al menos 4 caracteres."
    if password != confirm_password:
        return False, "Las contraseñas no coinciden. Verifícalas e inténtalo de nuevo."

    # Si GoPAESProfileManager tiene register_user nativo, usarlo y sincronizar
    if hasattr(GoPAESProfileManager, "register_user"):
        ok, msg, prof = GoPAESProfileManager.register_user(clean_user, password)
        if not ok or prof is None:
            return False, msg
        st.session_state.active_username = prof.username
        st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
        st.session_state.nav_section = "DASHBOARD"
        return True, msg

    # Respaldo local en caso de versión previa de adaptive_engine.py
    creds = _load_credentials_store()
    existing_key = next((k for k in creds.keys() if k.lower() == clean_user.lower()), None)
    if existing_key is not None:
        return False, f"El usuario '{existing_key}' ya está registrado. Ve a la pestaña 'Iniciar Sesión'."

    salt_hex = secrets.token_hex(16)
    pwd_hash = _hash_pwd_local(password, salt_hex)
    creds[clean_user] = {"salt": salt_hex, "hash": pwd_hash}
    _save_credentials_store(creds)

    prof = GoPAESProfileManager.load_or_create_profile(clean_user)
    st.session_state.active_username = prof.username
    st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
    st.session_state.nav_section = "DASHBOARD"
    return True, f"Cuenta creada exitosamente para {prof.username}."


def authenticate_student_account(username: str, password: str) -> tuple[bool, str]:
    clean_user = username.strip()
    if not clean_user or not password:
        return False, "Por favor ingresa tu nombre de usuario y tu contraseña."

    if hasattr(GoPAESProfileManager, "authenticate_user"):
        ok, msg, prof = GoPAESProfileManager.authenticate_user(clean_user, password)
        if not ok or prof is None:
            return False, msg
        st.session_state.active_username = prof.username
        st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
        st.session_state.nav_section = "DASHBOARD"
        return True, msg

    creds = _load_credentials_store()
    matched_key = next((k for k in creds.keys() if k.lower() == clean_user.lower()), None)
    existing_profiles = GoPAESProfileManager.list_existing_profiles()
    matched_prof_name = next((p for p in existing_profiles if p.lower() == clean_user.lower()), None)

    if matched_key is None:
        if matched_prof_name is not None:
            # Perfil legado creado antes de activar contraseñas: le asignamos la contraseña actual
            salt_hex = secrets.token_hex(16)
            creds[matched_prof_name] = {
                "salt": salt_hex,
                "hash": _hash_pwd_local(password, salt_hex),
            }
            _save_credentials_store(creds)
            prof = GoPAESProfileManager.load_or_create_profile(matched_prof_name)
            st.session_state.active_username = prof.username
            st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
            st.session_state.nav_section = "DASHBOARD"
            return True, f"Contraseña vinculada e inicio de sesión exitoso para {prof.username}."
        return False, f"No existe una cuenta con el usuario '{clean_user}'. Regístrate en la pestaña 'Registrarse'."

    entry = creds[matched_key]
    cand_hash = _hash_pwd_local(password, entry["salt"])
    if not hmac.compare_digest(entry["hash"], cand_hash):
        return False, "❌ Contraseña incorrecta. Inténtalo de nuevo."

    prof = GoPAESProfileManager.load_or_create_profile(matched_key)
    st.session_state.active_username = prof.username
    st.session_state.engine = GoPAESAdaptiveEngine(profile=prof)
    st.session_state.nav_section = "DASHBOARD"
    return True, f"Bienvenido nuevamente, {prof.username}."


def logout_profile():
    st.session_state.active_username = None
    st.session_state.selected_guide_axis = None
    st.rerun()


# =====================================================================
# PANTALLA DE INICIO DE SESIÓN Y REGISTRO CON CONTRASEÑA
# =====================================================================
if not st.session_state.active_username:
    st.title("🚀 Bienvenido a GoPAES • Preparación Adaptativa PAES (M1 y M2)")
    st.markdown(
        "Accede con tu **Usuario y Contraseña** para resguardar de forma privada tu progreso, "
        "racha de estudio, ensayos completados y dominio en las **4 Unidades Oficiales DEMRE** "
        "(**Números**, **Álgebra y Funciones**, **Geometría**, **Probabilidad y Estadística**)."
    )

    tab_login, tab_register = st.tabs([
        "🔐 Iniciar Sesión (Ya tengo cuenta)",
        "📝 Registrarse (Crear cuenta nueva)",
    ])

    with tab_login:
        with st.container(border=True):
            st.subheader("🔐 Iniciar Sesión en GoPAES")
            st.caption("Ingresa tus credenciales para cargar tu perfil protegido:")
            login_user = st.text_input(
                "Nombre de Usuario:",
                placeholder="Ej: agustin_paes",
                key="login_username_input",
            )
            login_pwd = st.text_input(
                "Contraseña:",
                type="password",
                placeholder="Ingresa tu contraseña",
                key="login_password_input",
            )

            if st.button("🔓 Iniciar Sesión", type="primary", use_container_width=True, key="btn_do_login"):
                ok, msg = authenticate_student_account(login_user, login_pwd)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_register:
        with st.container(border=True):
            st.subheader("📝 Crear Nueva Cuenta de Estudiante")
            st.caption(
                "Registra tu usuario y una contraseña personal para que nadie más pueda modificar tus estadísticas ni tu historial."
            )
            reg_user = st.text_input(
                "Elige un Nombre de Usuario:",
                placeholder="Ej: agustin2026",
                key="reg_username_input",
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                reg_pwd = st.text_input(
                    "Crea tu Contraseña (mín. 4 caracteres):",
                    type="password",
                    key="reg_pwd_input",
                )
            with col_p2:
                reg_pwd_confirm = st.text_input(
                    "Confirma tu Contraseña:",
                    type="password",
                    key="reg_pwd_confirm_input",
                )

            if st.button("✨ Registrarme y Entrar a GoPAES", type="primary", use_container_width=True, key="btn_do_register"):
                ok, msg = register_student_account(reg_user, reg_pwd, reg_pwd_confirm)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    st.stop()


# =====================================================================
# BARRA LATERAL: NAVEGACIÓN + MOTOR ADAPTATIVO EN LAS 4 UNIDADES
# =====================================================================
engine: GoPAESAdaptiveEngine = st.session_state.engine
profile = engine.profile

UNIT_ICONS: dict[ThematicAxis, str] = {
    "NUMEROS": "🔢",
    "ALGEBRA_Y_FUNCIONES": "📈",
    "GEOMETRIA": "📐",
    "PROBABILIDAD_Y_ESTADISTICA": "📊",
}

UNIT_NUMBER_LABELS: dict[ThematicAxis, str] = {
    "NUMEROS": "Unidad 1: Números",
    "ALGEBRA_Y_FUNCIONES": "Unidad 2: Álgebra y Funciones",
    "GEOMETRIA": "Unidad 3: Geometría",
    "PROBABILIDAD_Y_ESTADISTICA": "Unidad 4: Probabilidad y Estadística",
}

with st.sidebar:
    st.markdown(f"## 🚀 GoPAES • Hola, **{profile.username}**")
    st.caption("🔒 Sesión protegida con contraseña")
    st.caption(
        f"🔥 Racha: **{profile.study_streak} día(s)** | "
        f"🏅 Ensayos: **{profile.completed_exams}** | "
        f"🎯 Precisión Neta: **{engine.global_net_accuracy}%**"
    )

    st.markdown("### 🧭 Menú de Navegación")
    nav_labels = {
        "DASHBOARD": "👤 Perfil / Dashboard",
        "DIAGNOSTIC": "🎯 Diagnóstico",
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
        st.session_state.selected_guide_axis = None
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

    # CONEXIÓN A BASE DE DATOS EN LA NUBE (SUPABASE)
    supa_url, supa_key, supa_src = GoPAESProfileManager.resolve_supabase_credentials(
        st.session_state.get("supabase_manual_url"),
        st.session_state.get("supabase_manual_key"),
    )
    if supa_url and supa_key:
        st.caption("☁️ Almacenamiento: **✅ Supabase (Permanente)**")
    else:
        st.caption("☁️ Almacenamiento: **⚠️ Disco Local (Se reinicia en la nube)**")

    with st.expander("☁️ Base de Datos Supabase (Guardado Permanente)", expanded=False):
        st.markdown(
            "Conecta tu proyecto gratuito de **Supabase** para que tus usuarios, contraseñas y progreso "
            "se guarden para siempre y no se borren al reiniciar Streamlit Cloud."
        )
        s_url = st.text_input(
            "Supabase Project URL:",
            value=os.getenv("SUPABASE_URL", ""),
            placeholder="https://xyzcompany.supabase.co",
            key="input_supabase_url",
        )
        s_key = st.text_input(
            "Supabase Anon / Service Key:",
            value=os.getenv("SUPABASE_KEY", "") or os.getenv("SUPABASE_ANON_KEY", ""),
            type="password",
            placeholder="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            key="input_supabase_key",
        )
        st.session_state.supabase_manual_url = s_url
        st.session_state.supabase_manual_key = s_key

        if st.button("🔌 Probar Conexión Supabase", use_container_width=True):
            with st.spinner("Conectando con Supabase..."):
                ok_s, msg_s = GoPAESProfileManager.supabase_test_connection(s_url, s_key)
                if ok_s:
                    st.success(msg_s)
                else:
                    st.error(msg_s)

    # PANEL DE TRANSPARENCIA EN LAS 4 UNIDADES (IDÉNTICAS AL DASHBOARD Y LAS GUÍAS)
    st.markdown("### 🧠 Dominio por Unidad")
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

    rows = []
    for axis in ALL_AXES:
        st_axis = engine.axes_state[axis]
        rows.append({
            "Unidad": AXIS_LABELS[axis],
            "Dominio": f"{round(st_axis.mastery_score * 100)}%",
            "Peso IA": f"{round(adaptive_probs[axis] * 100, 1)}%",
            "Errores": st_axis.incorrect_count,
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    col_switch, col_wipe = st.columns(2)
    with col_switch:
        if st.button("🔒 Cerrar Sesión", use_container_width=True):
            logout_profile()
    with col_wipe:
        if st.button("🗑️ Resetear Progreso", use_container_width=True):
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
# FUNCIONES DE CONSOLIDACIÓN DE LAS 4 GUÍAS POR UNIDAD (M1 Y M2)
# =====================================================================
def get_consolidated_unit_guide(exam_target: ExamType, axis: ThematicAxis) -> DEMREExhaustiveGuide:
    """
    Garantiza que exista exactamente 1 Guía Maestra unificada para cada una de las
    4 Unidades del Dashboard (Números, Álgebra y Funciones, Geometría, Probabilidad y Estadística),
    consolidando todas las fórmulas, recetas y ejercicios prácticos si `guides_data.py` tenía sub-guías.
    """
    guides_by_axis = get_exhaustive_guides_by_exam(exam_target)
    axis_list = guides_by_axis.get(axis, [])
    if len(axis_list) == 1:
        return axis_list[0]

    # Si `guides_data.py` devuelve múltiples sub-guías en ese eje, fusionarlas en la Guía de la Unidad
    base = axis_list[0]
    all_formulas = []
    all_recipes = []
    all_traps = []
    all_exercises = []
    md_parts = []

    for g in axis_list:
        md_parts.append(g.theoretical_framework_md)
        all_formulas.extend(g.key_formulas)
        all_recipes.extend(g.resolution_recipe_steps)
        all_traps.extend(g.common_demre_traps)
        all_exercises.extend(g.interleaved_exercises)

    return base.model_copy(
        update={
            "guide_id": f"GUIDE-{exam_target}-{axis}",
            "unit_title": f"{UNIT_NUMBER_LABELS[axis]} (PAES {exam_target})",
            "theoretical_framework_md": "\n\n---\n\n".join(md_parts),
            "key_formulas": all_formulas,
            "resolution_recipe_steps": all_recipes,
            "common_demre_traps": all_traps,
            "interleaved_exercises": all_exercises,
        }
    )


def get_unit_questions_from_store(
    vector_store: GoPAESVectorStore,
    exam: ExamType,
    axis: ThematicAxis,
    num_questions: int,
    exclude_ids: list[str] | None = None,
) -> list[DEMREQuestionNode]:
    """
    Obtiene `num_questions` ejercicios de la base vectorial correspondientes a la Unidad (`axis`)
    y prueba (`exam`) seleccionada.
    """
    excluded = set(exclude_ids or [])
    unseen = vector_store.query_by_axis_and_exam(
        exam=exam, axis=axis, exclude_ids=list(excluded), diagnostic_only=False
    )
    all_axis = vector_store.query_by_axis_and_exam(
        exam=exam, axis=axis, exclude_ids=[], diagnostic_only=False
    )
    combined: list[DEMREQuestionNode] = []
    for q in unseen + all_axis:
        if q.node_id not in [c.node_id for c in combined]:
            combined.append(q)
        if len(combined) >= num_questions:
            break
    return combined[:num_questions]


def render_question_card(question: DEMREQuestionNode, step_num: int, total_steps: int, badge_text: str):
    col_badge, col_source = st.columns([2, 2])
    with col_badge:
        st.markdown(f"#### {badge_text} • Ejercicio {step_num} de {total_steps}")
    with col_source:
        st.markdown(
            f"<div style='text-align:right; color:#94a3b8; font-size:0.9rem;'>"
            f"📌 <b>PAES {question.exam}</b> | Unidad: <b>{AXIS_LABELS[question.thematic_axis]}</b> "
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
# RENDERIZADOR DE GUÍAS ALINEADO CON LAS 4 UNIDADES DEL DASHBOARD
# =====================================================================
def render_exhaustive_study_guides_section(exam_target: ExamType):
    """
    Renderiza las Guías por Materia organizadas exactamente en las mismas 4 Unidades
    del Dashboard:
      1. Números
      2. Álgebra y Funciones
      3. Geometría
      4. Probabilidad y Estadística
    Con un Menú Intermedio de las 4 Unidades y botón interactivo '✅ Comprobar respuesta'
    en cada ejercicio práctico dentro de la guía.
    """
    badge_color = "#1d4ed8" if exam_target == "M1" else "#9333ea"
    exam_title = (
        "PAES M1 (Competencia Matemática 1 • Obligatoria)"
        if exam_target == "M1"
        else "PAES M2 (Competencia Matemática 2 • Electiva Científica)"
    )

    col_head, col_switch_exam = st.columns([3, 1])
    with col_head:
        st.title(f"{'📘' if exam_target == 'M1' else '📕'} Guías por Unidad • {exam_title}")
    with col_switch_exam:
        other_exam = "M2" if exam_target == "M1" else "M1"
        if st.button(f"🔄 Cambiar a Guías PAES {other_exam}", use_container_width=True):
            st.session_state.nav_section = f"GUIDES_{other_exam}"
            st.session_state.selected_guide_axis = None
            st.rerun()

    # =========================================================================
    # NIVEL 1: MENÚ INTERMEDIO DE LAS 4 UNIDADES (IDÉNTICAS AL DASHBOARD)
    # =========================================================================
    if st.session_state.selected_guide_axis is None:
        st.markdown(
            "Las guías están organizadas exactamente en las **4 Unidades Oficiales** de tu Dashboard "
            "(**Números**, **Álgebra y Funciones**, **Geometría**, **Probabilidad y Estadística**). "
            "Elige qué unidad deseas estudiar y cuántos ejercicios quieres desarrollar:"
        )

        adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

        # Mostrar las 4 Unidades en una cuadrícula 2x2 limpia y ordenada
        col_u1, col_u2 = st.columns(2)
        grid_cols = [col_u1, col_u2, col_u1, col_u2]

        for idx_axis, axis in enumerate(ALL_AXES):
            guide = get_consolidated_unit_guide(exam_target, axis)
            st_axis = engine.axes_state[axis]
            dom_pct = round(st_axis.mastery_score * 100, 1)
            weight_pct = round(adaptive_probs[axis] * 100, 1)

            with grid_cols[idx_axis]:
                with st.container(border=True):
                    st.markdown(
                        f"<div style='display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;'>"
                        f"<h3 style='margin:0;'>{UNIT_ICONS[axis]} {UNIT_NUMBER_LABELS[axis]}</h3>"
                        f"<span style='background:{badge_color}; color:white; padding:3px 12px; border-radius:99px; font-size:0.8rem; font-weight:bold;'>"
                        f"PAES {exam_target}</span></div>",
                        unsafe_allow_html=True,
                    )
                    st.caption(f"📌 {guide.demre_syllabus_reference}")

                    # Barra de dominio sincronizada con el Dashboard
                    st.markdown(
                        f"**Tu Dominio en {AXIS_LABELS[axis]}:** `{dom_pct}%` | "
                        f"**Precisión Neta:** `{st_axis.net_accuracy}%` | "
                        f"**Prioridad IA:** `{weight_pct}%`"
                    )
                    st.progress(min(1.0, st_axis.mastery_score))

                    short_desc = getattr(guide, "short_description", "") or (
                        f"Marco teórico completo, fórmulas en LaTeX, receta de resolución y ejercicios prácticos de {AXIS_LABELS[axis]}."
                    )
                    st.write(short_desc)

                    st.markdown(
                        f"🧮 **{len(guide.key_formulas)}** Fórmulas $\\text{{LaTeX}}$ | "
                        f"🧑‍🍳 **{len(guide.resolution_recipe_steps)}** Pasos de Receta | "
                        f"✍️ **Ejercicios con 'Comprobar respuesta'**"
                    )

                    st.divider()
                    c_num, c_open = st.columns([1, 2])
                    with c_num:
                        num_ex_unit = st.number_input(
                            "N° Ejercicios:",
                            min_value=1,
                            max_value=20,
                            value=5,
                            step=1,
                            key=f"menu_num_{exam_target}_{axis}",
                        )
                    with c_open:
                        st.write("")
                        if st.button(
                            f"📖 Abrir Guía de {AXIS_LABELS[axis]} ({num_ex_unit} ejercicios)",
                            type="primary",
                            use_container_width=True,
                            key=f"btn_open_unit_{exam_target}_{axis}",
                        ):
                            st.session_state.selected_guide_axis = axis
                            workout_key = f"{exam_target}_{axis}"
                            st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
                                vector_store=st.session_state.vector_store,
                                exam=exam_target,
                                axis=axis,
                                num_questions=int(num_ex_unit),
                                exclude_ids=st.session_state.asked_ids,
                            )
                            st.rerun()
        return

    # =========================================================================
    # NIVEL 2: VISTA COMPLETA DE LA UNIDAD SELECCIONADA + "COMPROBAR RESPUESTA"
    # =========================================================================
    active_axis: ThematicAxis = st.session_state.selected_guide_axis
    active_guide = get_consolidated_unit_guide(exam_target, active_axis)
    st_axis_active = engine.axes_state[active_axis]
    dom_active = round(st_axis_active.mastery_score * 100, 1)
    workout_key = f"{exam_target}_{active_axis}"

    col_back, col_unit_badge = st.columns([1, 3])
    with col_back:
        if st.button("⬅️ Volver a las 4 Unidades", use_container_width=True):
            st.session_state.selected_guide_axis = None
            st.rerun()
    with col_unit_badge:
        st.markdown(
            f"<div style='text-align:right;'>"
            f"<span style='background:{badge_color}; color:white; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
            f"{UNIT_NUMBER_LABELS[active_axis]} • PAES {exam_target}</span> "
            f"<span style='background:#0f172a; color:#38bdf8; border:1px solid #38bdf8; padding:5px 14px; border-radius:99px; font-size:0.88rem; font-weight:bold;'>"
            f"Tu Dominio en {AXIS_LABELS[active_axis]}: {dom_active}%</span></div>",
            unsafe_allow_html=True,
        )

    st.header(f"{UNIT_ICONS[active_axis]} {active_guide.unit_title}")
    st.caption(f"📌 {active_guide.demre_syllabus_reference}")

    # -----------------------------------------------------------------
    # PARTE 1: MARCO TEÓRICO, FORMULARIO LATEX, RECETA Y TRAMPAS DEMRE
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
        st.info(
            f"Sigue este algoritmo paso a paso para resolver los problemas de **{AXIS_LABELS[active_axis]}**:"
        )
        for recipe_step in active_guide.resolution_recipe_steps:
            st.markdown(f"- ✅ **{recipe_step}**")

        st.divider()

        st.markdown("#### ⚠️ Trampas y Errores Frecuentes del DEMRE a Evitar")
        for trap in active_guide.common_demre_traps:
            st.warning(f"🔎 {trap}")

    st.divider()

    # -----------------------------------------------------------------
    # PARTE 2: EJERCICIOS GUIADOS CON BOTÓN "COMPROBAR RESPUESTA"
    # -----------------------------------------------------------------
    st.markdown(f"### ✍️ Ejercicios Guiados de {AXIS_LABELS[active_axis]} (Con Comprobación Inmediata)")
    st.caption(
        "Selecciona tu alternativa y presiona **`✅ Comprobar respuesta`** debajo de cada ejercicio "
        "para validar tu resultado y ver la explicación paso a paso sin salir de la guía."
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
                "Selecciona tu respuesta:",
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
                        f"❌ **Respuesta Incorrecta.** Marcaste **{user_ans})**, "
                        f"pero la alternativa correcta es la **{ex.correct_option})**."
                    )
                st.markdown("#### 📘 Explicación Paso a Paso:")
                for s_line in ex.step_by_step_solution:
                    st.markdown(s_line)

    st.divider()

    # -----------------------------------------------------------------
    # PARTE 3: BATERÍA PERSONALIZABLE DE EJERCICIOS DE LA UNIDAD
    # -----------------------------------------------------------------
    st.markdown(
        f"### 🏋️ Práctica de Ejercicios de **{AXIS_LABELS[active_axis]}** (Elige cuántos realizar)"
    )
    with st.container(border=True):
        st.write(
            f"Elige la cantidad de ejercicios de la unidad **{AXIS_LABELS[active_axis]} ({exam_target})** "
            "que deseas desarrollar aquí mismo. Cada ejercicio tiene su botón **`✅ Comprobar respuesta`** "
            "con resolución paso a paso en $\\text{LaTeX}$ y actualiza tu barra de dominio en el Dashboard."
        )

        current_list: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts.get(workout_key, [])
        default_qty = len(current_list) if current_list else 5

        col_slider, col_btn_load = st.columns([3, 2])
        with col_slider:
            desired_qty = st.slider(
                f"Cantidad de ejercicios para practicar en {AXIS_LABELS[active_axis]}:",
                min_value=1,
                max_value=20,
                value=min(20, default_qty),
                key=f"unit_qty_slider_{workout_key}",
            )
        with col_btn_load:
            st.write("")
            if st.button(
                f"🔄 Cargar {desired_qty} Ejercicios de {AXIS_LABELS[active_axis]}",
                type="primary",
                use_container_width=True,
                key=f"btn_reload_inline_{workout_key}",
            ):
                st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
                    vector_store=st.session_state.vector_store,
                    exam=exam_target,
                    axis=active_axis,
                    num_questions=int(desired_qty),
                    exclude_ids=st.session_state.asked_ids,
                )
                st.rerun()

    if workout_key not in st.session_state.unit_custom_workouts:
        st.session_state.unit_custom_workouts[workout_key] = get_unit_questions_from_store(
            vector_store=st.session_state.vector_store,
            exam=exam_target,
            axis=active_axis,
            num_questions=int(desired_qty),
            exclude_ids=st.session_state.asked_ids,
        )

    workout_questions: list[DEMREQuestionNode] = st.session_state.unit_custom_workouts[workout_key]

    answered_in_unit = sum(
        1
        for q_node in workout_questions
        if f"{workout_key}_{q_node.node_id}" in st.session_state.unit_workout_answers
    )
    st.progress(
        answered_in_unit / max(1, len(workout_questions)),
        text=f"Progreso en la unidad {AXIS_LABELS[active_axis]}: {answered_in_unit} de {len(workout_questions)} ejercicio(s) comprobado(s)",
    )

    for q_idx, q_node in enumerate(workout_questions, start=1):
        ans_key = f"{workout_key}_{q_node.node_id}"
        with st.container(border=True):
            render_question_card(
                question=q_node,
                step_num=q_idx,
                total_steps=len(workout_questions),
                badge_text=f"🏋️ Práctica de {AXIS_LABELS[active_axis]} ({exam_target})",
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
                    "✅ Comprobar respuesta",
                    type="primary",
                    use_container_width=True,
                    key=f"btn_unit_check_{ans_key}_{q_idx}",
                ):
                    state_res = engine.process_response(
                        question=q_node,
                        selected_option=chosen_unit_opt,
                        phase_label=f"Guía {AXIS_LABELS[active_axis]}",
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
                        phase_label=f"Guía {AXIS_LABELS[active_axis]}",
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
                new_dom_pct = round(engine.axes_state[active_axis].mastery_score * 100, 1)
                if u_state == "CORRECT":
                    st.success(
                        f"🎉 **¡Respuesta Correcta!** Marcaste la alternativa **{u_sel})**. "
                        f"Tu dominio en la unidad **{AXIS_LABELS[active_axis]}** ahora es **{new_dom_pct}%**."
                    )
                elif u_state == "OMITTED":
                    st.warning(
                        f"🏳️ **Ejercicio omitido (Vacío de Conocimiento registrado en {AXIS_LABELS[active_axis]}).** "
                        f"La alternativa correcta según el DEMRE es la **{q_node.correct_option})**."
                    )
                else:
                    st.error(
                        f"❌ **Respuesta Incorrecta.** Marcaste **{u_sel})**, pero la alternativa correcta es la **{q_node.correct_option})**."
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
# SECCIÓN 1: PERFIL / DASHBOARD (4 UNIDADES SINCRONIZADAS CON LAS GUÍAS)
# =====================================================================
if st.session_state.nav_section == "DASHBOARD":
    st.title(f"👤 Dashboard de Rendimiento • {profile.username}")
    st.caption(
        "Tu progreso está resguardado bajo tu cuenta personal y organizado en las **4 Unidades Oficiales DEMRE** "
        "(**Números**, **Álgebra y Funciones**, **Geometría**, **Probabilidad y Estadística**)."
    )

    # Estado de persistencia en la nube
    supa_u, supa_k, supa_src = GoPAESProfileManager.resolve_supabase_credentials(
        st.session_state.get("supabase_manual_url"),
        st.session_state.get("supabase_manual_key"),
    )
    col_cloud_status, col_backup_btn = st.columns([3, 1])
    with col_cloud_status:
        if supa_u and supa_k:
            st.success("☁️ **Almacenamiento Permanente Activo:** Tu perfil, racha y dominio están sincronizados con tu base de datos **Supabase**.")
        else:
            st.info("💡 **Almacenamiento Local:** Si despliegas en Streamlit Cloud, conecta **Supabase** en la barra lateral para guardar tus datos para siempre.")
    with col_backup_btn:
        prof_json = json.dumps(profile.model_dump(), ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 Descargar Respaldo (.json)",
            data=prof_json,
            file_name=f"gopaes_respaldo_{profile.username}.json",
            mime="application/json",
            use_container_width=True,
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
            st.subheader("📊 Dominio y Acceso Directo a las 4 Unidades DEMRE")
            adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")

            for axis in ALL_AXES:
                st_axis = engine.axes_state[axis]
                dom_pct = round(st_axis.mastery_score * 100, 1)
                prob_pct = round(adaptive_probs[axis] * 100, 1)

                c_bar, c_btn_m1, c_btn_m2 = st.columns([4, 1, 1])
                with c_bar:
                    st.markdown(
                        f"**{UNIT_ICONS[axis]} {UNIT_NUMBER_LABELS[axis]}** — Dominio: `{dom_pct}%` | "
                        f"Precisión Neta: `{st_axis.net_accuracy}%` | "
                        f"Prioridad IA: **{prob_pct}%**"
                    )
                    st.progress(min(1.0, st_axis.mastery_score))
                with c_btn_m1:
                    st.write("")
                    if st.button("📘 Guía M1", key=f"dash_gm1_{axis}", use_container_width=True):
                        st.session_state.selected_guide_axis = axis
                        st.session_state.nav_section = "GUIDES_M1"
                        st.rerun()
                with c_btn_m2:
                    st.write("")
                    if st.button("📕 Guía M2", key=f"dash_gm2_{axis}", use_container_width=True):
                        st.session_state.selected_guide_axis = axis
                        st.session_state.nav_section = "GUIDES_M2"
                        st.rerun()

    with col_right:
        with st.container(border=True):
            st.subheader("🚀 Acciones Rápidas de Estudio")
            if not profile.diagnostic_completed:
                st.warning("🎯 **Diagnóstico Pendiente:** Realiza las preguntas de calibración para personalizar tus 4 unidades.")
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
                if st.button("📘 Menú Guías PAES M1", use_container_width=True):
                    st.session_state.selected_guide_axis = None
                    st.session_state.nav_section = "GUIDES_M1"
                    st.rerun()
            with c_g2:
                if st.button("📕 Menú Guías PAES M2", use_container_width=True):
                    st.session_state.selected_guide_axis = None
                    st.session_state.nav_section = "GUIDES_M2"
                    st.rerun()

    with st.container(border=True):
        st.subheader("📜 Últimos Movimientos del Motor Adaptativo en tu Cuenta")
        if not engine.logs:
            st.info("Aún no registras respuestas en esta cuenta. Comienza por el Diagnóstico, una Guía o un Ensayo.")
        else:
            for log in engine.logs[:6]:
                delta_str = f"+{log.delta_mastery}%" if log.delta_mastery >= 0 else f"{log.delta_mastery}%"
                st.markdown(
                    f"- **{log.step_label}** ({AXIS_LABELS[log.axis]}): Dominio `{log.old_mastery}%` → `{log.new_mastery}%` (`{delta_str}`) — {log.explanation}"
                )


# =====================================================================
# SECCIÓN 2: DIAGNÓSTICO DE CALIBRACIÓN EN LAS 4 UNIDADES
# =====================================================================
elif st.session_state.nav_section == "DIAGNOSTIC":
    st.title("🎯 Diagnóstico de Calibración en las 4 Unidades GoPAES")
    st.write(
        "Responde estas preguntas ancla del DEMRE (una por cada unidad: **Números**, **Álgebra y Funciones**, "
        "**Geometría** y **Probabilidad y Estadística**) o usa **'Dejar en blanco'** para calibrar tu perfil."
    )

    diag_qs: list[DEMREQuestionNode] = st.session_state.diag_questions
    idx: int = st.session_state.diag_idx

    if idx >= len(diag_qs):
        st.success("🎉 **¡Diagnóstico completado y guardado en tu cuenta!**")
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
# SECCIÓN 3A: GUÍAS POR MATERIA (4 UNIDADES) - PAES M1
# =====================================================================
elif st.session_state.nav_section == "GUIDES_M1":
    render_exhaustive_study_guides_section(exam_target="M1")


# =====================================================================
# SECCIÓN 3B: GUÍAS POR MATERIA (4 UNIDADES) - PAES M2
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
                    "Simulación con la estructura y proporción exacta de las 4 Unidades del DEMRE:\n"
                    "- **16** de Unidad 1: Números (24,6%)\n"
                    "- **22** de Unidad 2: Álgebra y Funciones (33,8%)\n"
                    "- **14** de Unidad 3: Geometría (21,5%)\n"
                    "- **13** de Unidad 4: Probabilidad y Estadística (20,0%)"
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
                        "focus_axis": None,
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

                unit_filter = st.selectbox(
                    "Unidad a evaluar:",
                    options=["ALL_UNITS"] + list(ALL_AXES),
                    format_func=lambda a: (
                        "🧠 Todas las 4 Unidades (Adaptativo según mis debilidades)"
                        if a == "ALL_UNITS"
                        else f"{UNIT_ICONS[a]} Solo {UNIT_NUMBER_LABELS[a]} (Dominio: {round(engine.axes_state[a].mastery_score * 100)}%)"
                    ),
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
                    focus_ax = None if unit_filter == "ALL_UNITS" else unit_filter
                    queue = engine.build_exam_question_queue(
                        vector_store=st.session_state.vector_store,
                        exam=exam_choice,
                        num_questions=num_q,
                        mode=chosen_mode,
                        asked_ids=st.session_state.asked_ids,
                        focus_axis=focus_ax,  # type: ignore
                    )
                    st.session_state.exam_config = {
                        "exam": exam_choice,
                        "num_questions": len(queue),
                        "timed_mode": custom_timed,
                        "allocated_seconds": len(queue) * sec_per_q,
                        "selection_mode": chosen_mode,
                        "focus_axis": focus_ax,
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
                    f"🔥 **Ensayo de Debilidades GoPAES ({cfg['exam']}):** "
                    f"**{UNIT_NUMBER_LABELS[q.thematic_axis]}** — Subtema: *{q.subtopic_name}* "
                    f"(Prioridad IA de la unidad: **{axis_prob}%**)."
                )
            elif mode_active == "GENERAL_STANDARD":
                st.info(
                    f"⚖️ **Ensayo General Estándar ({cfg['exam']}):** "
                    f"**{UNIT_NUMBER_LABELS[q.thematic_axis]}** (Proporción estándar DEMRE: **{axis_prob}%**)."
                )
            else:
                st.info(
                    f"🏛️ **Ensayo Full 65 Preguntas:** **{UNIT_NUMBER_LABELS[q.thematic_axis]}** "
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

                if (
                    cfg.get("selection_mode") == "ADAPTIVE"
                    and not cfg.get("focus_axis")
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
                        f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]} - {q.subtopic_name}): "
                        f"✅ CORRECTA (Marcaste {sel})**"
                    )
                elif st_resp == "OMITTED":
                    st.warning(
                        f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]} - {q.subtopic_name}): "
                        f"🏳️ DEJADA EN BLANCO (Vacío de Conocimiento • Clave Oficial: {q.correct_option})**"
                    )
                else:
                    st.error(
                        f"**Pregunta {idx + 1} ({UNIT_NUMBER_LABELS[q.thematic_axis]} - {q.subtopic_name}): "
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
