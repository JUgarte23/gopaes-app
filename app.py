import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from demre_ingestion_pipeline import (
    GoPAESVectorStore,
    AXIS_LABELS,
    OFFICIAL_PAES_65_DISTRIBUTION,
    ExamType,
    DEMREQuestionNode,
)
from adaptive_engine import (
    GoPAESAdaptiveEngine,
    GoPAESLLMCoach,
    SelectionMode,
    OFFICIAL_SECONDS_PER_QUESTION,
    ALL_AXES,
)

# Cargar automáticamente las variables del archivo .env
load_dotenv()

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
# INICIALIZACIÓN DE ESTADO EN MEMORIA (QDRANT + MOTOR GOPAES)
# =====================================================================
if "vector_store" not in st.session_state:
    store = GoPAESVectorStore()
    store.seed_official_demre_questions()
    st.session_state.vector_store = store

if "engine" not in st.session_state:
    st.session_state.engine = GoPAESAdaptiveEngine()

if "phase" not in st.session_state:
    # Fases: 'DIAGNOSTIC' -> 'CONFIG_EXAM' -> 'ADAPTIVE_EXAM' -> 'COACHING_RESULTS'
    st.session_state.phase = "DIAGNOSTIC"

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

if "selection_mode" not in st.session_state:
    st.session_state.selection_mode = "ADAPTIVE"

if "exam_config" not in st.session_state:
    st.session_state.exam_config = {
        "exam": "M1",
        "num_questions": 4,
        "timed_mode": True,
        "selection_mode": "ADAPTIVE",
    }


def reset_prototype():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# =====================================================================
# BARRA LATERAL: TRANSPARENCIA DEL MOTOR ADAPTATIVO Y CONEXIÓN LLM
# =====================================================================
with st.sidebar:
    st.markdown("## 🚀 GoPAES • Motor IA en Vivo")
    st.caption(
        "Panel **Detrás de Escena**: observa cómo **GoPAES** actualiza tu perfil en "
        "**Qdrant (`:memory:`)** y cómo operan los pesos según el modo activo."
    )

    # Estado de conexión LLM (.env o manual)
    with st.expander("🔑 Conexión LLM (Coaching IA Real)", expanded=False):
        default_prov = os.getenv("GOPAES_LLM_PROVIDER", "gemini").lower()
        llm_provider = st.selectbox(
            "Proveedor IA:",
            options=["gemini", "openai"],
            index=0 if default_prov == "gemini" else 1,
        )
        env_key = os.getenv("GEMINI_API_KEY") if llm_provider == "gemini" else os.getenv("OPENAI_API_KEY")
        has_valid_env = bool(env_key and "tu_api_key" not in env_key)

        if has_valid_env:
            st.success(f"✅ API Key de **{llm_provider.upper()}** cargada desde `.env`")
            manual_api_key = None
        else:
            st.warning("⚠️ Sin API Key en `.env`. Puedes ingresarla aquí temporalmente:")
            manual_api_key = st.text_input(
                f"API Key ({llm_provider.upper()}):",
                type="password",
                placeholder="Pega tu clave aquí...",
            )

        st.session_state.llm_provider_choice = llm_provider
        st.session_state.llm_manual_key = manual_api_key

    engine: GoPAESAdaptiveEngine = st.session_state.engine
    active_mode: SelectionMode = st.session_state.exam_config.get("selection_mode", "ADAPTIVE")
    adaptive_probs = engine.compute_sampling_probabilities(mode="ADAPTIVE")
    effective_probs = engine.compute_sampling_probabilities(mode=active_mode)

    st.markdown("### 📊 Estado del Perfil y Pesos por Eje")
    if active_mode == "GENERAL_STANDARD":
        st.info(
            "⚖️ **Modo Ensayo General Activo:** El selector ignora temporalmente tus debilidades "
            "(usa proporción estándar DEMRE), pero **tu perfil sigue registrando cada respuesta**."
        )
    elif active_mode == "OFFICIAL_65":
        st.info(
            "🏛️ **Modo PAES Oficial (65 pregs):** Distribución fija oficial DEMRE "
            "(16 Números, 22 Álgebra, 14 Geometría, 13 Probabilidad)."
        )
    else:
        st.caption("🧠 **Modo Adaptativo Activo:** Sobre-muestreando tus ejes con mayor debilidad:")

    rows = []
    for axis in ALL_AXES:
        st_axis = engine.axes_state[axis]
        rows.append({
            "Eje DEMRE": AXIS_LABELS[axis],
            "Dominio (θ)": f"{round(st_axis.mastery_score * 100)}%",
            "Peso Adaptativo": f"{round(adaptive_probs[axis] * 100, 1)}%",
            "Peso Efectivo": f"{round(effective_probs[axis] * 100, 1)}%",
            "Vacíos (Omisión)": st_axis.omitted_count,
            "Errores": st_axis.incorrect_count,
            "Precisión Neta": f"{st_axis.net_accuracy}%",
        })

    df_state = pd.DataFrame(rows)
    st.dataframe(df_state, use_container_width=True, hide_index=True)

    for axis in ALL_AXES:
        p_pct = round(effective_probs[axis] * 100, 1)
        m_pct = round(engine.axes_state[axis].mastery_score * 100)
        st.progress(
            min(1.0, effective_probs[axis] * 1.6),
            text=f"**{AXIS_LABELS[axis]}** • Dominio: {m_pct}% → Muestreo actual: **{p_pct}%**"
        )

    st.divider()
    st.markdown("### 📜 Bitácora del Algoritmo GoPAES")
    if not engine.logs:
        st.info("Responde o deja en blanco la primera pregunta de calibración GoPAES para ver el cálculo interno.")
    else:
        for log in engine.logs[:4]:
            delta_str = f"+{log.delta_mastery}%" if log.delta_mastery >= 0 else f"{log.delta_mastery}%"
            st.markdown(
                f"**{log.step_label}** ({AXIS_LABELS[log.axis]})\n"
                f"- Dominio: `{log.old_mastery}%` → `{log.new_mastery}%` (`{delta_str}`)\n"
                f"- {log.explanation}"
            )

    st.divider()
    if st.button("🔄 Reiniciar GoPAES Completo (Borrar Memoria)", use_container_width=True):
        reset_prototype()


# =====================================================================
# FUNCIÓN REUTILIZABLE PARA RENDERIZAR UN NODO PREGUNTA CON ST.LATEX
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

    st.markdown(f"**Enunciado Oficial (Nodo Qdrant #{question.question_number}):**")
    st.write(question.stem_text)

    # Renderizado matemático nativo de Streamlit (st.latex)
    st.latex(question.stem_latex)

    if question.figure_svg:
        st.markdown("**Figura Geométrica Asociada (Extraída del PDF por GoPAES):**")
        st.markdown(question.figure_svg, unsafe_allow_html=True)

    st.markdown("**Alternativas Oficiales (Solo Enunciado + Clave en Vector DB):**")
    for opt in question.options:
        col_key, col_formula = st.columns([1, 11])
        with col_key:
            st.markdown(f"### `{opt.key})`")
        with col_formula:
            st.latex(opt.latex_content)


# =====================================================================
# ENCABEZADO PRINCIPAL GOPAES
# =====================================================================
st.title("🚀 GoPAES • Preparación Adaptativa PAES Matemáticas (M1 y M2)")
st.caption(
    "Base Vectorial **Qdrant (`:memory:`)** con nodos puros del **DEMRE** (enunciado + clave oficial) "
    "y **Coaching IA en vivo (Gemini / OpenAI)** que genera el paso a paso en $\\text{LaTeX}$ según tu error."
)

# =====================================================================
# FASE 1: DIAGNÓSTICO INICIAL DE CALIBRACIÓN GOPAES (3 PREGUNTAS)
# =====================================================================
if st.session_state.phase == "DIAGNOSTIC":
    diag_qs: list[DEMREQuestionNode] = st.session_state.diag_questions
    idx: int = st.session_state.diag_idx
    current_q = diag_qs[idx]

    st.info(
        "**Fase 1: Diagnóstico Inicial GoPAES (Calibración de 3 Preguntas)** — "
        "Responde estas 3 preguntas ancla o usa **'Dejar en blanco'** si no recuerdas cómo plantearlas."
    )

    with st.container(border=True):
        render_question_card(
            question=current_q,
            step_num=idx + 1,
            total_steps=len(diag_qs),
            badge_text="🎯 Diagnóstico GoPAES"
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
            if st.button("✅ Confirmar Alternativa Seleccionada", type="primary", use_container_width=True):
                st.session_state.engine.process_response(
                    question=current_q,
                    selected_option=selected_choice,
                    phase_label="Diagnóstico GoPAES"
                )
                st.session_state.asked_ids.append(current_q.node_id)
                if idx + 1 < len(diag_qs):
                    st.session_state.diag_idx += 1
                else:
                    st.session_state.phase = "CONFIG_EXAM"
                st.rerun()

        with col_omit:
            if st.button(
                "🏳️ Dejar en blanco (Omitir sin adivinar al azar)",
                use_container_width=True,
            ):
                st.session_state.engine.process_response(
                    question=current_q,
                    selected_option="OMIT",
                    phase_label="Diagnóstico GoPAES"
                )
                st.session_state.asked_ids.append(current_q.node_id)
                if idx + 1 < len(diag_qs):
                    st.session_state.diag_idx += 1
                else:
                    st.session_state.phase = "CONFIG_EXAM"
                st.rerun()


# =====================================================================
# FASE 2: CONFIGURADOR FLEXIBLE + MODO GENERAL + MODO OFICIAL 65 PREGS
# =====================================================================
elif st.session_state.phase == "CONFIG_EXAM":
    st.success(
        "✅ **Perfil de Usuario Activo en GoPAES.** Ahora puedes lanzar un ensayo adaptativo (enfocado en tus debilidades), "
        "activar el **Modo Ensayo General (sin pesos adaptativos)** o iniciar el **Ensayo Oficial de 65 preguntas**."
    )

    # ACCESO RÁPIDO AL MODO ENSAYO OFICIAL PAES (65 PREGUNTAS)
    with st.container(border=True):
        st.subheader("🏛️ Simulación Oficial PAES Completa (65 Preguntas)")
        st.write(
            "Inicia inmediatamente un ensayo con la estructura, duración (**2 horas y 20 minutos**) y proporción exacta "
            "de ejes temáticos del DEMRE: **16 de Números (24,6%)**, **22 de Álgebra y Funciones (33,8%)**, "
            "**14 de Geometría (21,5%)** y **13 de Probabilidad y Estadística (20,0%)**."
        )
        if st.button("🏛️ Iniciar Ensayo Oficial PAES (65 Preguntas • Proporción Oficial DEMRE)", use_container_width=True):
            queue_65 = st.session_state.engine.build_exam_question_queue(
                vector_store=st.session_state.vector_store,
                exam="M1",
                num_questions=65,
                mode="OFFICIAL_65",
                asked_ids=st.session_state.asked_ids,
            )
            st.session_state.exam_config = {
                "exam": "M1",
                "num_questions": 65,
                "timed_mode": True,
                "allocated_seconds": 65 * OFFICIAL_SECONDS_PER_QUESTION["M1"],
                "selection_mode": "OFFICIAL_65",
            }
            st.session_state.exam_queue = queue_65
            st.session_state.exam_history = []
            st.session_state.phase = "ADAPTIVE_EXAM"
            st.rerun()

    # CONFIGURADOR PERSONALIZADO CON TOGGLE DE MODO GENERAL (SIN PESOS ADAPTATIVOS)
    with st.container(border=True):
        st.subheader("⚙️ Configurador de Ensayo Personalizado GoPAES")

        # Toggle de Modo Adaptativo vs Modo General Estándar
        ignore_adaptive_weights = st.toggle(
            "⚖️ Activar Modo Ensayo General (Ignorar temporalmente mis debilidades al elegir preguntas, pero conservar mi historial y memoria)",
            value=(st.session_state.exam_config.get("selection_mode") == "GENERAL_STANDARD"),
        )
        chosen_mode: SelectionMode = "GENERAL_STANDARD" if ignore_adaptive_weights else "ADAPTIVE"
        st.session_state.exam_config["selection_mode"] = chosen_mode

        if ignore_adaptive_weights:
            st.caption(
                "ℹ️ En **Modo Ensayo General**, GoPAES selecciona las preguntas de forma balanceada según el temario DEMRE "
                "sin sobre-muestrear los ejes que te cuestan. Tus respuestas seguirán alimentando tu perfil en segundo plano."
            )
        else:
            st.caption(
                "ℹ️ En **Modo Adaptativo Inteligente**, GoPAES prioriza automáticamente los ejes donde tuviste errores conceptuales o dejaste preguntas en blanco."
            )

        col_exam, col_count, col_timer = st.columns(3)

        with col_exam:
            exam_choice: ExamType = st.radio(
                "1. Prueba PAES Oficial:",
                options=["M1", "M2"],
                format_func=lambda x: "M1 (Obligatoria General)" if x == "M1" else "M2 (Electiva Científica)",
            )

        with col_count:
            max_q = 65 if exam_choice == "M1" else 55
            num_q = st.slider(
                "2. Cantidad exacta de preguntas:",
                min_value=2,
                max_value=max_q,
                value=4,
            )

        with col_timer:
            timed_mode = st.radio(
                "3. Modalidad de Tiempo:",
                options=[True, False],
                format_func=lambda t: "⏱️ Temporizador Cuenta Regresiva" if t else "🧘 Modo Libre (Sin presión)",
            )

        sec_per_q = OFFICIAL_SECONDS_PER_QUESTION[exam_choice]
        total_seconds = num_q * sec_per_q
        mins = total_seconds // 60
        rem_s = total_seconds % 60

        st.info(
            f"⏱️ **Tiempo Oficial Estimado GoPAES ({exam_choice}):** Para **{num_q} preguntas**, "
            f"el tiempo proporcional según el estándar DEMRE es de **{mins} minutos y {rem_s} segundos** "
            f"({sec_per_q} seg/pregunta)."
        )

        if st.button("🚀 Generar y Comenzar Ensayo GoPAES", type="primary", use_container_width=True):
            queue = st.session_state.engine.build_exam_question_queue(
                vector_store=st.session_state.vector_store,
                exam=exam_choice,
                num_questions=num_q,
                mode=chosen_mode,
                asked_ids=st.session_state.asked_ids,
            )
            st.session_state.exam_config = {
                "exam": exam_choice,
                "num_questions": len(queue),
                "timed_mode": timed_mode,
                "allocated_seconds": len(queue) * sec_per_q,
                "selection_mode": chosen_mode,
            }
            st.session_state.exam_queue = queue
            st.session_state.exam_history = []
            st.session_state.phase = "ADAPTIVE_EXAM"
            st.rerun()


# =====================================================================
# FASE 3: MOTOR DE ENSAYO GOPAES EN VIVO
# =====================================================================
elif st.session_state.phase == "ADAPTIVE_EXAM":
    cfg = st.session_state.exam_config
    step_idx = len(st.session_state.exam_history)
    total_q = len(st.session_state.exam_queue)

    if step_idx >= total_q:
        st.session_state.phase = "COACHING_RESULTS"
        st.rerun()

    q: DEMREQuestionNode = st.session_state.exam_queue[step_idx]
    mode_active: SelectionMode = cfg.get("selection_mode", "ADAPTIVE")
    probs = st.session_state.engine.compute_sampling_probabilities(mode=mode_active)
    axis_prob = round(probs[q.thematic_axis] * 100, 1)

    col_reason, col_clock, col_finish = st.columns([3, 1, 1])
    with col_reason:
        if mode_active == "ADAPTIVE":
            st.warning(
                f"🧠 **Selección Adaptativa GoPAES:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                f"(Priorizado por tu perfil con **{axis_prob}%** de peso)."
            )
        elif mode_active == "GENERAL_STANDARD":
            st.info(
                f"⚖️ **Modo Ensayo General (Sin pesos adaptativos):** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                f"(Proporción estándar DEMRE: **{axis_prob}%**)."
            )
        else:
            st.info(
                f"🏛️ **Ensayo Oficial 65 Preguntas:** Eje **{AXIS_LABELS[q.thematic_axis]}** "
                f"(Cuota oficial DEMRE: {OFFICIAL_PAES_65_DISTRIBUTION[q.thematic_axis]}/65)."
            )
    with col_clock:
        if cfg["timed_mode"]:
            st.metric("⏱️ Tiempo Oficial", f"{cfg['allocated_seconds'] // 60}m {cfg['allocated_seconds'] % 60}s")
        else:
            st.metric("🧘 Modalidad", "Modo Libre")
    with col_finish:
        if st.button("🏁 Terminar y Ver Coaching IA", use_container_width=True):
            st.session_state.phase = "COACHING_RESULTS"
            st.rerun()

    with st.container(border=True):
        render_question_card(
            question=q,
            step_num=step_idx + 1,
            total_steps=total_q,
            badge_text=f"🔥 Ensayo GoPAES {cfg['exam']}"
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
            state = st.session_state.engine.process_response(
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

            # Si estamos en modo ADAPTIVE puro, re-ordenar el resto de la cola según los nuevos pesos en vivo
            if cfg.get("selection_mode") == "ADAPTIVE" and (step_idx + 1) < total_q:
                remaining_count = total_q - (step_idx + 1)
                new_tail = st.session_state.engine.build_exam_question_queue(
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
                st.session_state.phase = "COACHING_RESULTS"
            st.rerun()

        with col_ans:
            if st.button("✅ Responder y Avanzar", type="primary", use_container_width=True):
                record_and_advance(user_choice)

        with col_blank:
            if st.button(
                "🏳️ Dejar en blanco (Declarar Vacío de Conocimiento)",
                use_container_width=True,
            ):
                record_and_advance(None)


# =====================================================================
# FASE 4: COACHING IA REAL POST-ENSAYO (GENERADO POR LLM EN LATEX)
# =====================================================================
elif st.session_state.phase == "COACHING_RESULTS":
    st.balloons()
    st.header("🎓 GoPAES Coaching IA en Vivo (Gemini / OpenAI)")
    st.write(
        "La base vectorial Qdrant solo entregó el **enunciado** y la **clave oficial de la pauta DEMRE**. "
        "Ahora el **LLM de GoPAES** analiza tu respuesta específica para diagnosticar tu error o vacío de conocimiento "
        "y redactar la resolución paso a paso en $\\text{LaTeX}$."
    )

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
    m4.metric("🎯 Precisión Neta GoPAES", f"{net_acc}%")

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
                    f"🏳️ DEJADA EN BLANCO (Vacío de Conocimiento • Clave Oficial Pauta: {q.correct_option})**"
                )
            else:
                st.error(
                    f"**Pregunta {idx + 1} (DEMRE #{q.question_number} - {AXIS_LABELS[q.thematic_axis]}): "
                    f"❌ ERROR CONCEPTUAL (Marcaste {sel} • Clave Oficial Pauta: {q.correct_option})**"
                )

            st.write(q.stem_text)
            st.latex(q.stem_latex)

            # Generar explicación con el LLM automáticamente para errores/omisiones o bajo demanda
            should_auto_generate = (st_resp != "CORRECT") and (len(history) <= 10)
            if should_auto_generate and cache_key not in st.session_state.ai_explanations_cache:
                with st.spinner(f"🤖 El Tutor IA de GoPAES está analizando tu respuesta en la Pregunta {idx + 1}..."):
                    explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                        question=q,
                        selected_option=sel,
                        state=st_resp,
                        api_key_override=st.session_state.get("llm_manual_key"),
                        provider_override=st.session_state.get("llm_provider_choice"),
                    )
                    st.session_state.ai_explanations_cache[cache_key] = explanation

            if cache_key in st.session_state.ai_explanations_cache:
                st.markdown("#### 🤖 Resolución y Diagnóstico Generado por el Tutor IA de GoPAES:")
                st.markdown(st.session_state.ai_explanations_cache[cache_key])

            if st.button(
                "✨ Solicitar / Regenerar Explicación Paso a Paso con IA en Vivo",
                key=f"btn_regen_{cache_key}",
            ):
                with st.spinner("Consultando al LLM con el enunciado y tu alternativa seleccionada..."):
                    explanation = GoPAESLLMCoach.generate_live_latex_explanation(
                        question=q,
                        selected_option=sel,
                        state=st_resp,
                        api_key_override=st.session_state.get("llm_manual_key"),
                        provider_override=st.session_state.get("llm_provider_choice"),
                    )
                    st.session_state.ai_explanations_cache[cache_key] = explanation
                    st.rerun()

    col_new, col_reset = st.columns(2)
    with col_new:
        if st.button("➕ Configurar Nuevo Ensayo GoPAES (Manteniendo mi Perfil y Memoria)", type="primary", use_container_width=True):
            st.session_state.phase = "CONFIG_EXAM"
            st.rerun()
    with col_reset:
        if st.button("🔄 Reiniciar GoPAES desde Cero (Borrar Perfil)", use_container_width=True):
            reset_prototype()
