import os
import json
import math
import datetime
import requests
from pathlib import Path
from typing import Dict, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from demre_ingestion_pipeline import (
    ThematicAxis,
    ExamType,
    DEMREQuestionNode,
    AXIS_LABELS,
    OFFICIAL_PAES_65_DISTRIBUTION,
    OFFICIAL_AXIS_PROPORTIONS,
)

# Cargar variables de entorno desde .env
load_dotenv(override=True)

ResponseState = Literal["CORRECT", "INCORRECT", "OMITTED"]
SelectionMode = Literal["ADAPTIVE", "GENERAL_STANDARD", "OFFICIAL_65"]

OFFICIAL_SECONDS_PER_QUESTION: Dict[ExamType, int] = {
    "M1": 130,
    "M2": 150,
}

ALL_AXES: List[ThematicAxis] = [
    "NUMEROS",
    "ALGEBRA_Y_FUNCIONES",
    "GEOMETRIA",
    "PROBABILIDAD_Y_ESTADISTICA",
]


class AxisMasteryState(BaseModel):
    axis: ThematicAxis
    mastery_score: float = 0.50         # Dominio estimado theta en [0.05, 0.99]
    knowledge_gap_index: float = 0.0    # Índice acumulado de "Vacío de Conocimiento" por omisiones
    conceptual_error_index: float = 0.0 # Índice acumulado de "Errores Conceptuales"
    correct_count: int = 0
    incorrect_count: int = 0
    omitted_count: int = 0
    total_seen: int = 0

    @property
    def net_accuracy(self) -> float:
        """
        Precisión Neta GoPAES (Sin sesgo por omisión):
        Se calcula únicamente sobre las preguntas que el alumno decidió responder.
        """
        attempted = self.correct_count + self.incorrect_count
        if attempted == 0:
            return 0.0
        return round((self.correct_count / attempted) * 100, 1)


class EngineLogEntry(BaseModel):
    step_label: str
    axis: ThematicAxis
    state: ResponseState
    old_mastery: float
    new_mastery: float
    delta_mastery: float
    explanation: str


# =====================================================================
# 1. SISTEMA DE PERFILES PERSISTENTES GOPAES (JSON + MEMORIA)
# =====================================================================

class UserProfileData(BaseModel):
    username: str
    created_at: str = Field(default_factory=lambda: datetime.date.today().isoformat())
    last_activity_date: str = Field(default_factory=lambda: datetime.date.today().isoformat())
    study_streak: int = 1
    completed_exams: int = 0
    diagnostic_completed: bool = False
    axes_state: Dict[ThematicAxis, AxisMasteryState] = Field(
        default_factory=lambda: {axis: AxisMasteryState(axis=axis) for axis in ALL_AXES}
    )
    logs: List[EngineLogEntry] = Field(default_factory=list)


class GoPAESProfileManager:
    """
    Gestiona la persistencia en disco (`./storage/gopaes_profiles.json`) de los perfiles
    de usuario, rachas de estudio (streaks), ensayos completados y precisión global.
    """
    STORAGE_PATH = Path("./storage/gopaes_profiles.json")

    @classmethod
    def _ensure_storage(cls) -> Dict[str, dict]:
        cls.STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not cls.STORAGE_PATH.exists():
            cls.STORAGE_PATH.write_text("{}", encoding="utf-8")
            return {}
        try:
            return json.loads(cls.STORAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @classmethod
    def list_existing_profiles(cls) -> List[str]:
        data = cls._ensure_storage()
        return sorted(list(data.keys()))

    @classmethod
    def load_or_create_profile(cls, username: str) -> UserProfileData:
        clean_name = username.strip()
        data = cls._ensure_storage()
        today_str = datetime.date.today().isoformat()

        if clean_name in data:
            profile = UserProfileData(**data[clean_name])
            # Actualizar racha de estudio (streak) según fecha de última actividad
            try:
                last_date = datetime.date.fromisoformat(profile.last_activity_date)
                today_date = datetime.date.today()
                diff_days = (today_date - last_date).days
                if diff_days == 1:
                    profile.study_streak += 1
                elif diff_days > 1:
                    profile.study_streak = 1
                profile.last_activity_date = today_str
            except Exception:
                profile.last_activity_date = today_str
        else:
            profile = UserProfileData(username=clean_name)

        cls.save_profile(profile)
        return profile

    @classmethod
    def save_profile(cls, profile: UserProfileData) -> None:
        data = cls._ensure_storage()
        data[profile.username] = profile.model_dump()
        cls.STORAGE_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )


# =====================================================================
# 2. MOTOR ADAPTATIVO GOPAES VINCULADO AL PERFIL DEL ALUMNO
# =====================================================================

class GoPAESAdaptiveEngine:
    """
    Motor de Aprendizaje GoPAES sincronizado con el perfil persistente del usuario.
    Soporta:
    - ADAPTIVE (Ensayo de Debilidades)
    - GENERAL_STANDARD (Ensayo General sin pesos adaptativos, sin borrar historial)
    - OFFICIAL_65 (Ensayo Full Oficial PAES de 65 preguntas, cronometrado o libre)
    """

    def __init__(self, profile: Optional[UserProfileData] = None):
        self.profile = profile or UserProfileData(username="Invitado")
        self.axes_state = self.profile.axes_state
        self.logs = self.profile.logs

    def sync_to_disk(self):
        self.profile.axes_state = self.axes_state
        self.profile.logs = self.logs[:25]
        GoPAESProfileManager.save_profile(self.profile)

    @property
    def global_net_accuracy(self) -> float:
        total_correct = sum(s.correct_count for s in self.axes_state.values())
        total_incorrect = sum(s.incorrect_count for s in self.axes_state.values())
        attempted = total_correct + total_incorrect
        if attempted == 0:
            return 0.0
        return round((total_correct / attempted) * 100, 1)

    @property
    def total_questions_answered(self) -> int:
        return sum(s.total_seen for s in self.axes_state.values())

    @property
    def total_omitted(self) -> int:
        return sum(s.omitted_count for s in self.axes_state.values())

    def register_completed_exam(self):
        self.profile.completed_exams += 1
        self.sync_to_disk()

    def mark_diagnostic_completed(self):
        self.profile.diagnostic_completed = True
        self.sync_to_disk()

    def compute_sampling_probabilities(
        self, mode: SelectionMode = "ADAPTIVE"
    ) -> Dict[ThematicAxis, float]:
        if mode in ("GENERAL_STANDARD", "OFFICIAL_65"):
            return {axis: round(OFFICIAL_AXIS_PROPORTIONS[axis], 4) for axis in ALL_AXES}

        logits: Dict[ThematicAxis, float] = {}
        temperature = 2.8

        for axis, st in self.axes_state.items():
            deficit = 1.0 - st.mastery_score
            priority = (
                (deficit * 0.50)
                + (st.conceptual_error_index * 0.35)
                + (st.knowledge_gap_index * 0.30)
            )
            logits[axis] = math.exp(priority * temperature)

        total = sum(logits.values()) or 1.0
        return {axis: round(val / total, 4) for axis, val in logits.items()}

    def process_response(
        self,
        question: DEMREQuestionNode,
        selected_option: Optional[str],
        phase_label: str = "Ensayo GoPAES"
    ) -> ResponseState:
        axis = question.thematic_axis
        st = self.axes_state[axis]
        old_m = st.mastery_score
        st.total_seen += 1

        expected_p = 1.0 / (1.0 + math.exp(-3.5 * (old_m - question.difficulty)))
        base_lr = 0.16

        if selected_option is None or selected_option == "OMIT":
            state: ResponseState = "OMITTED"
            st.omitted_count += 1
            st.knowledge_gap_index = min(1.0, round(st.knowledge_gap_index + 0.25, 3))
            delta = - (base_lr * 0.45) * expected_p
            reason = (
                "🏳️ OMISIÓN ('Dejar en blanco'): Se registra Vacío de Conocimiento (+0.25 Gap) "
                "sin castigar tu Precisión Neta."
            )

        elif selected_option == question.correct_option:
            state = "CORRECT"
            st.correct_count += 1
            st.knowledge_gap_index = max(0.0, round(st.knowledge_gap_index - 0.15, 3))
            st.conceptual_error_index = max(0.0, round(st.conceptual_error_index - 0.15, 3))
            delta = base_lr * (1.15 - expected_p)
            reason = "✅ RESPUESTA CORRECTA: Sube el dominio del eje en tu perfil GoPAES."

        else:
            state = "INCORRECT"
            st.incorrect_count += 1
            st.conceptual_error_index = min(1.0, round(st.conceptual_error_index + 0.35, 3))
            delta = - (base_lr * 1.25) * expected_p
            reason = (
                f"❌ ERROR CONCEPTUAL (Marcaste {selected_option}): Penalización en dominio "
                "y alerta de distractor (+0.35 Error Index)."
            )

        new_m = max(0.08, min(0.98, round(old_m + delta, 4)))
        st.mastery_score = new_m

        self.logs.insert(
            0,
            EngineLogEntry(
                step_label=f"[{phase_label}] P#{question.question_number}",
                axis=axis,
                state=state,
                old_mastery=round(old_m * 100, 1),
                new_mastery=round(new_m * 100, 1),
                delta_mastery=round((new_m - old_m) * 100, 1),
                explanation=reason,
            )
        )
        self.sync_to_disk()
        return state

    def build_unit_exercise_queue(
        self,
        vector_store,
        exam: ExamType,
        axis: ThematicAxis,
        subtopic_keyword: str,
        num_questions: int,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[DEMREQuestionNode]:
        """
        Construye una batería de ejercicios de longitud exacta `num_questions`
        filtrada específicamente para una unidad/guía de estudio (`subtopic_keyword`),
        rellenando con reactivos del mismo eje temático y prueba si el usuario pide
        más preguntas de las disponibles con esa palabra clave exacta.
        """
        excluded = set(exclude_ids or [])
        axis_pool: List[DEMREQuestionNode] = vector_store.query_by_axis_and_exam(
            exam=exam,
            axis=axis,
            exclude_ids=[],
            diagnostic_only=False,
        )
        kw = (subtopic_keyword or "").strip().lower()

        # 1. Prioridad máxima: coincidencia por subtopic_keyword y no vistas recientemente
        primary_matches = [
            q for q in axis_pool
            if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id not in excluded
        ]
        # 2. Coincidencia por subtopic_keyword aunque ya hayan sido vistas
        secondary_matches = [
            q for q in axis_pool
            if (kw in q.subtopic_name.lower() or kw in q.stem_text.lower()) and q.node_id in excluded
        ]
        # 3. Mismo eje temático y prueba (no vistas)
        axis_unseen = [
            q for q in axis_pool
            if q.node_id not in excluded and q not in primary_matches
        ]
        # 4. Resto del mismo eje temático
        axis_remaining = [
            q for q in axis_pool
            if q not in primary_matches and q not in secondary_matches and q not in axis_unseen
        ]

        combined: List[DEMREQuestionNode] = []
        for candidate in (primary_matches + secondary_matches + axis_unseen + axis_remaining):
            if candidate.node_id not in [c.node_id for c in combined]:
                combined.append(candidate)
            if len(combined) >= num_questions:
                break

        return combined[:num_questions]

    def build_exam_question_queue(
        self,
        vector_store,
        exam: ExamType,
        num_questions: int,
        mode: SelectionMode,
        asked_ids: List[str],
        focus_axis: Optional[ThematicAxis] = None,
        subtopic_keyword: Optional[str] = None,
    ) -> List[DEMREQuestionNode]:
        if focus_axis is not None and subtopic_keyword:
            return self.build_unit_exercise_queue(
                vector_store=vector_store,
                exam=exam,
                axis=focus_axis,
                subtopic_keyword=subtopic_keyword,
                num_questions=num_questions,
                exclude_ids=asked_ids,
            )

        queue: List[DEMREQuestionNode] = []
        used_ids = list(asked_ids)

        if focus_axis is not None:
            quotas = {axis: (num_questions if axis == focus_axis else 0) for axis in ALL_AXES}
        elif mode == "OFFICIAL_65":
            quotas = OFFICIAL_PAES_65_DISTRIBUTION.copy()
        elif mode == "GENERAL_STANDARD":
            quotas = {
                axis: max(1, round(num_questions * OFFICIAL_AXIS_PROPORTIONS[axis]))
                for axis in ALL_AXES
            }
        else:
            probs = self.compute_sampling_probabilities(mode="ADAPTIVE")
            quotas = {
                axis: max(0, round(num_questions * probs[axis]))
                for axis in ALL_AXES
            }

        ordered_axes = (
            ALL_AXES
            if mode in ("OFFICIAL_65", "GENERAL_STANDARD")
            else sorted(ALL_AXES, key=lambda a: self.compute_sampling_probabilities("ADAPTIVE")[a], reverse=True)
        )

        for axis in ordered_axes:
            needed = quotas.get(axis, 0)
            if needed <= 0:
                continue
            candidates = vector_store.query_by_axis_and_exam(
                exam=exam,
                axis=axis,
                exclude_ids=used_ids,
                diagnostic_only=False
            )
            if len(candidates) < needed:
                candidates = vector_store.query_by_axis_and_exam(
                    exam=exam,
                    axis=axis,
                    exclude_ids=[q.node_id for q in queue],
                    diagnostic_only=False
                )

            selected = candidates[:needed]
            for s in selected:
                queue.append(s)
                used_ids.append(s.node_id)

        if len(queue) < num_questions:
            all_pool = vector_store.get_all_nodes(exam=exam) or vector_store.get_all_nodes()
            for node in all_pool:
                if node.node_id not in [q.node_id for q in queue]:
                    queue.append(node)
                if len(queue) >= num_questions:
                    break

        return queue[:num_questions]


# =====================================================================
# 3. CONECTOR DE IA BLINDADO (REST MULTI-MODELO + DIAGNÓSTICO DE AUTH)
# =====================================================================

class GoPAESLLMCoach:
    """
    Cliente LLM con autenticación blindada, limpieza de credenciales,
    fallback automático de modelos Gemini (gemini-2.5-flash -> gemini-2.0-flash -> gemini-1.5-flash)
    mediante API REST directa (evita fallos de gRPC en Streamlit Cloud) y respaldo
    matemático simbólico para garantizar cero pantallas de error.
    """

    GEMINI_MODELS_CASCADE = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash",
    ]

    @staticmethod
    def _clean_key(raw_key: Optional[str]) -> Optional[str]:
        if not raw_key:
            return None
        cleaned = str(raw_key).strip().strip('"').strip("'").strip()
        if not cleaned or "tu_api_key" in cleaned.lower():
            return None
        return cleaned

    @classmethod
    def resolve_credentials(
        cls,
        override_key: Optional[str] = None,
        override_provider: Optional[str] = None
    ) -> Tuple[str, Optional[str], str]:
        """
        Retorna (provider, api_key, key_source_info).
        Detecta automáticamente el proveedor según el prefijo de la clave si es necesario:
        - 'AIza...' -> Google Gemini API Key
        - 'sk-...'  -> OpenAI API Key
        """
        load_dotenv(override=True)

        secret_gemini = None
        secret_openai = None
        secret_provider = None
        try:
            import streamlit as st
            secret_gemini = cls._clean_key(st.secrets.get("GEMINI_API_KEY"))
            secret_openai = cls._clean_key(st.secrets.get("OPENAI_API_KEY"))
            secret_provider = st.secrets.get("GOPAES_LLM_PROVIDER")
        except Exception:
            pass

        env_gemini = cls._clean_key(os.getenv("GEMINI_API_KEY"))
        env_openai = cls._clean_key(os.getenv("OPENAI_API_KEY"))
        manual_clean = cls._clean_key(override_key)

        provider = (override_provider or secret_provider or os.getenv("GOPAES_LLM_PROVIDER", "gemini")).lower()

        if manual_clean:
            if manual_clean.startswith("sk-"):
                return "openai", manual_clean, "Ingresada manualmente en barra lateral (OpenAI)"
            if manual_clean.startswith("AIza"):
                return "gemini", manual_clean, "Ingresada manualmente en barra lateral (Gemini)"
            return provider, manual_clean, "Ingresada manualmente en barra lateral"

        if provider == "gemini":
            if secret_gemini:
                return "gemini", secret_gemini, "Streamlit Cloud Secrets (GEMINI_API_KEY)"
            if env_gemini:
                return "gemini", env_gemini, "Archivo local .env (GEMINI_API_KEY)"
            if secret_openai or env_openai:
                return "openai", (secret_openai or env_openai), "Fallback automático a OPENAI_API_KEY"
        else:
            if secret_openai:
                return "openai", secret_openai, "Streamlit Cloud Secrets (OPENAI_API_KEY)"
            if env_openai:
                return "openai", env_openai, "Archivo local .env (OPENAI_API_KEY)"
            if secret_gemini or env_gemini:
                return "gemini", (secret_gemini or env_gemini), "Fallback automático a GEMINI_API_KEY"

        return provider, None, "Sin clave configurada"

    @classmethod
    def validate_key_format(cls, provider: str, api_key: Optional[str]) -> Tuple[bool, str]:
        if not api_key:
            return False, "No se encontró ninguna API Key configurada en `.env`, `st.secrets` ni en la barra lateral."

        if provider == "gemini":
            if api_key.startswith("AQ."):
                return (
                    False,
                    "La clave ingresada comienza con `AQ.` (token de sesión/OAuth), no es una API Key de Gemini. "
                    "Las API Keys válidas de Google AI Studio siempre comienzan con **`AIzaSy...`**. "
                    "Obtén una gratis en https://aistudio.google.com/apikey y pégala en el cuadro de la izquierda."
                )
            if not api_key.startswith("AIza"):
                return (
                    False,
                    f"El formato de la clave (`{api_key[:6]}...`) no parece una clave estándar de Google AI Studio (`AIzaSy...`)."
                )
        elif provider == "openai":
            if not api_key.startswith("sk-"):
                return (
                    False,
                    f"El formato de la clave (`{api_key[:6]}...`) no parece una clave estándar de OpenAI (`sk-...`)."
                )

        return True, "Formato de API Key válido."

    @classmethod
    def test_connection(
        cls,
        override_key: Optional[str] = None,
        override_provider: Optional[str] = None
    ) -> Tuple[bool, str]:
        provider, api_key, source = cls.resolve_credentials(override_key, override_provider)
        is_valid_fmt, fmt_msg = cls.validate_key_format(provider, api_key)
        if not is_valid_fmt:
            return False, fmt_msg

        try:
            if provider == "gemini":
                ok, text_or_err, used_model = cls._call_gemini_rest(
                    api_key=api_key,  # type: ignore
                    system_prompt="Responde en 1 línea.",
                    user_prompt="Di 'Conexión GoPAES exitosa'."
                )
                if ok:
                    return True, f"✅ Conexión verificada con **{used_model}** ({source})."
                return False, f"❌ Error de API Gemini: {text_or_err}"
            else:
                ok, text_or_err = cls._call_openai_rest(
                    api_key=api_key,  # type: ignore
                    system_prompt="Responde en 1 línea.",
                    user_prompt="Di 'Conexión GoPAES exitosa'."
                )
                if ok:
                    return True, f"✅ Conexión verificada con **OpenAI gpt-4o-mini** ({source})."
                return False, f"❌ Error de API OpenAI: {text_or_err}"
        except Exception as e:
            return False, f"❌ Excepción de red al probar la API: {str(e)}"

    @classmethod
    def _call_gemini_rest(
        cls, api_key: str, system_prompt: str, user_prompt: str
    ) -> Tuple[bool, str, str]:
        """
        Llama directamente al endpoint HTTPS v1beta de Google Generative Language
        probando los modelos activos en cascada. Evita bloqueos de gRPC y errores de versión SDK.
        """
        last_error = "No se pudo conectar con ningún modelo Gemini."
        payload = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1200},
        }

        for model_name in cls.GEMINI_MODELS_CASCADE:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        text = "".join(p.get("text", "") for p in parts)
                        if text.strip():
                            return True, text, model_name
                else:
                    err_json = resp.json() if resp.text else {}
                    err_msg = err_json.get("error", {}).get("message", resp.text[:200])
                    last_error = f"[{resp.status_code} en {model_name}] {err_msg}"
                    # Si la API Key es inválida (400 / 403), no tiene sentido seguir probando otros modelos
                    if resp.status_code in (400, 401, 403) and "API_KEY" in resp.text.upper():
                        break
            except Exception as exc:
                last_error = str(exc)

        return False, last_error, ""

    @classmethod
    def _call_openai_rest(
        cls, api_key: str, system_prompt: str, user_prompt: str
    ) -> Tuple[bool, str]:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                return True, data["choices"][0]["message"]["content"]
            err_json = resp.json() if resp.text else {}
            err_msg = err_json.get("error", {}).get("message", resp.text[:200])
            return False, f"[{resp.status_code}] {err_msg}"
        except Exception as exc:
            return False, str(exc)

    @classmethod
    def generate_live_latex_explanation(
        cls,
        question: DEMREQuestionNode,
        selected_option: Optional[str],
        state: ResponseState,
        api_key_override: Optional[str] = None,
        provider_override: Optional[str] = None,
    ) -> str:
        provider, api_key, _ = cls.resolve_credentials(api_key_override, provider_override)
        is_valid_fmt, fmt_warning = cls.validate_key_format(provider, api_key)

        options_formatted = "\n".join(
            [f"- Alternativa {o.key}): ${o.latex_content}$" for o in question.options]
        )

        if state == "OMITTED":
            student_situation = (
                "El estudiante decidió DEJAR EN BLANCO (Omitir) la pregunta para no adivinar al azar. "
                "Tiene un vacío de conocimiento sobre qué propiedad o fórmula del temario DEMRE aplicar."
            )
            task_instruction = (
                "1. Explica desde cero qué propiedad o fórmula oficial del temario PAES DEMRE se debe utilizar.\n"
                "2. Desarrolla la resolución matemática paso a paso usando notación LaTeX clara hasta llegar a la alternativa correcta."
            )
        elif state == "INCORRECT":
            chosen_obj = next((o for o in question.options if o.key == selected_option), None)
            chosen_latex = chosen_obj.latex_content if chosen_obj else ""
            student_situation = (
                f"El estudiante respondió erróneamente marcando la Alternativa {selected_option}) (${chosen_latex}$), "
                f"mientras que la alternativa correcta de la pauta oficial DEMRE es la {question.correct_option})."
            )
            task_instruction = (
                f"1. **Diagnóstico del Error Conceptual**: Deduce y explica con empatía qué error algebraico, numérico o conceptual llevó al alumno a obtener el distractor {selected_option}) (${chosen_latex}$).\n"
                f"2. **Fórmula Oficial DEMRE**: Enuncia la propiedad o fórmula correcta del temario PAES {question.exam}.\n"
                f"3. **Resolución Paso a Paso**: Desarrolla el ejercicio paso a paso en LaTeX hasta demostrar por qué la alternativa correcta es la {question.correct_option})."
            )
        else:
            student_situation = f"El estudiante acertó marcando la alternativa correcta {question.correct_option})."
            task_instruction = (
                "Resume de forma concisa la propiedad oficial del DEMRE aplicada y muestra el desarrollo elegante en LaTeX en 3 pasos."
            )

        system_prompt = (
            "Eres el Tutor de IA Oficial de GoPAES para la preparación de la PAES de Matemáticas (M1 y M2) en Chile. "
            "Tu regla estricta es ceñirte únicamente al currículo oficial del DEMRE/MINEDUC. "
            "Escribe todas las expresiones matemáticas utilizando delimitadores LaTeX ($...$ para fórmulas en línea y $$...$$ en bloques propios)."
        )

        user_prompt = f"""Analiza el siguiente ejercicio oficial de la PAES {question.exam} (Eje: {AXIS_LABELS[question.thematic_axis]} - {question.subtopic_name}):

**Enunciado:**
{question.stem_text}
$${question.stem_latex}$$

**Alternativas:**
{options_formatted}

**Alternativa Correcta según Pauta DEMRE:** {question.correct_option})

**Situación del Estudiante:**
{student_situation}

**Instrucciones para tu respuesta:**
{task_instruction}
"""

        # Si el formato es válido, intentar llamada en vivo al LLM
        api_error_detail = fmt_warning
        if is_valid_fmt and api_key:
            if provider == "gemini":
                ok, response_text, used_model = cls._call_gemini_rest(api_key, system_prompt, user_prompt)
                if ok:
                    return f"*(Generado en vivo por GoPAES IA • `{used_model}`)*\n\n{response_text}"
                api_error_detail = response_text
            else:
                ok, response_text = cls._call_openai_rest(api_key, system_prompt, user_prompt)
                if ok:
                    return f"*(Generado en vivo por GoPAES IA • `gpt-4o-mini`)*\n\n{response_text}"
                api_error_detail = response_text

        # Respaldo Simbólico Inteligente GoPAES (nunca deja al estudiante sin resolución LaTeX)
        return cls._generate_symbolic_fallback_explanation(
            question=question,
            selected_option=selected_option,
            state=state,
            auth_notice=api_error_detail
        )

    @staticmethod
    def _generate_symbolic_fallback_explanation(
        question: DEMREQuestionNode,
        selected_option: Optional[str],
        state: ResponseState,
        auth_notice: str
    ) -> str:
        correct_obj = next(o for o in question.options if o.key == question.correct_option)
        chosen_obj = next((o for o in question.options if o.key == selected_option), None)

        header_notice = (
            f"> ⚠️ **Aviso de Conexión API LLM:** {auth_notice}\n>\n"
            f"> *Activando **Motor Matemático Interno de Respaldo GoPAES** para que puedas revisar la resolución en $\\text{{LaTeX}}$ sin interrumpir tu estudio:*\n\n"
        )

        if state == "OMITTED":
            diag_section = (
                f"### 1. Abordaje desde Cero (Pregunta Omitida)\n"
                f"Dejaste esta pregunta en blanco en el eje de **{AXIS_LABELS[question.thematic_axis]}** "
                f"(*{question.subtopic_name}*). Para plantear este ejercicio según el temario DEMRE, "
                f"observa la estructura matemática principal:\n"
                f"$${question.stem_latex}$$\n"
            )
        elif state == "INCORRECT" and chosen_obj:
            diag_section = (
                f"### 1. Análisis de tu Respuesta vs. Pauta DEMRE\n"
                f"- **Tu elección:** Alternativa **{selected_option})** $\\longrightarrow {chosen_obj.latex_content}$\n"
                f"- **Clave Oficial DEMRE:** Alternativa **{question.correct_option})** $\\longrightarrow {correct_obj.latex_content}$\n\n"
                f"**Diagnóstico del Distractor:** En el subtema de *{question.subtopic_name}*, el distractor **{selected_option})** "
                f"suele aparecer al omitir una propiedad de signos, un exponente o una condición del enunciado antes de despejar.\n"
            )
        else:
            diag_section = (
                f"### 1. Verificación Oficial DEMRE\n"
                f"¡Excelente! Identificaste correctamente la clave **{question.correct_option})** ($ {correct_obj.latex_content} $) "
                f"aplicando los principios de *{question.subtopic_name}*.\n"
            )

        steps_section = (
            f"### 2. Planteamiento y Resolución en $\\text{{LaTeX}}$\n"
            f"1. **Identificación del modelo matemático ({question.cognitive_skill}):**\n"
            f"   Partimos de la expresión oficial del enunciado:\n"
            f"   $${question.stem_latex}$$\n"
            f"2. **Desarrollo algebraico / numérico según el currículo {question.exam}:**\n"
            f"   Al aplicar las propiedades de **{question.subtopic_name}** y reducir términos semejantes, "
            f"se descartan los distractores y se llega al valor exacto de la pauta oficial:\n"
            f"   $$\\text{{Resultado Oficial}} = {correct_obj.latex_content} \\quad \\left(\\text{{Alternativa {question.correct_option}}}\\right)$$"
        )

        return header_notice + diag_section + "\n" + steps_section
