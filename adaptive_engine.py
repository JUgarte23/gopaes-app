import os
import math
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel
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
load_dotenv()

ResponseState = Literal["CORRECT", "INCORRECT", "OMITTED"]
SelectionMode = Literal["ADAPTIVE", "GENERAL_STANDARD", "OFFICIAL_65"]

# Segundos oficiales por pregunta según DEMRE para GoPAES:
# M1: 65 preguntas en 140 min -> ~130 s/preg
# M2: 55 preguntas en 140 min -> ~150 s/preg
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
        Dejar en blanco NO castiga la precisión conceptual igual que una respuesta errónea.
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


class GoPAESAdaptiveEngine:
    """
    Motor de Aprendizaje GoPAES con soporte para 3 modos de selección:
    1. ADAPTIVE: Sobre-muestrea los ejes donde el alumno presenta errores conceptuales y omisiones.
    2. GENERAL_STANDARD (Sin pesos adaptativos): Ignora temporalmente las debilidades al elegir
       preguntas (usa la proporción estándar DEMRE), pero SIGUE actualizando el perfil y memoria del usuario.
    3. OFFICIAL_65 (Ensayo Oficial PAES 65 preguntas): Genera el ensayo completo respetando
       exactamente las cuotas por eje del DEMRE (16 Números, 22 Álgebra, 14 Geometría, 13 Probabilidad).
    """

    def __init__(self):
        self.axes_state: Dict[ThematicAxis, AxisMasteryState] = {
            axis: AxisMasteryState(axis=axis) for axis in ALL_AXES
        }
        self.logs: List[EngineLogEntry] = []

    def compute_sampling_probabilities(
        self, mode: SelectionMode = "ADAPTIVE"
    ) -> Dict[ThematicAxis, float]:
        """
        Si mode == 'GENERAL_STANDARD' o 'OFFICIAL_65', retorna la proporción oficial DEMRE
        ignorando temporalmente los pesos adaptativos de debilidad.
        Si mode == 'ADAPTIVE', calcula los pesos Softmax basados en déficit, errores y omisiones.
        """
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
        """
        Siempre actualiza el historial y perfil del usuario en memoria, incluso cuando el
        ensayo se corre en Modo General Estándar (sin pesos adaptativos).
        """
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
                "🏳️ OMISIÓN ('Dejar en blanco'): GoPAES registra un Vacío de Conocimiento (+0.25 Gap) "
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
        return state

    def build_exam_question_queue(
        self,
        vector_store,
        exam: ExamType,
        num_questions: int,
        mode: SelectionMode,
        asked_ids: List[str]
    ) -> List[DEMREQuestionNode]:
        """
        Construye la cola de preguntas según el modo elegido:
        - OFFICIAL_65: 65 preguntas respetando estrictamente 16 Números, 22 Álgebra, 14 Geometría, 13 Probabilidad.
        - GENERAL_STANDARD: N preguntas distribuidas proporcionalmente según el estándar DEMRE (ignora debilidades).
        - ADAPTIVE: Selecciona dinámicamente priorizando los ejes con mayor peso Softmax de debilidad.
        """
        queue: List[DEMREQuestionNode] = []
        used_ids = list(asked_ids)

        if mode == "OFFICIAL_65":
            quotas = OFFICIAL_PAES_65_DISTRIBUTION.copy()
        elif mode == "GENERAL_STANDARD":
            # Distribución proporcional estándar sin sobre-muestrear debilidades
            quotas = {
                axis: max(1, round(num_questions * OFFICIAL_AXIS_PROPORTIONS[axis]))
                for axis in ALL_AXES
            }
        else:
            # Modo Adaptativo: cuotas ponderadas por las probabilidades Softmax del perfil actual
            probs = self.compute_sampling_probabilities(mode="ADAPTIVE")
            quotas = {
                axis: max(0, round(num_questions * probs[axis]))
                for axis in ALL_AXES
            }

        # Recolectar según cuotas por eje
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
            # Si se acabaron las no vistas en un ensayo de 65, permitir reutilizar las del diagnóstico
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

        # Ajustar longitud exacta a num_questions
        if len(queue) < num_questions:
            all_pool = vector_store.get_all_nodes(exam=exam) or vector_store.get_all_nodes()
            for node in all_pool:
                if node.node_id not in [q.node_id for q in queue]:
                    queue.append(node)
                if len(queue) >= num_questions:
                    break

        return queue[:num_questions]


# =====================================================================
# SERVICIO DE COACHING IA EN VIVO (GEMINI / OPENAI CON LATEX)
# =====================================================================

class GoPAESLLMCoach:
    """
    Conecta GoPAES con un LLM real (Google Gemini o OpenAI GPT-4o) leyendo las credenciales
    desde el archivo `.env` (o desde la sesión de Streamlit).
    Recibe únicamente el enunciado, las alternativas, la clave oficial DEMRE y la respuesta
    del alumno, generando en tiempo real la explicación paso a paso en formato LaTeX.
    """

    @staticmethod
    def get_active_provider(override_key: Optional[str] = None, override_provider: Optional[str] = None) -> Tuple[str, Optional[str]]:
        # Soporte híbrido: lee de variables de entorno (.env) y también de st.secrets (Streamlit Cloud)
        secret_gemini = None
        secret_openai = None
        secret_provider = None
        try:
            import streamlit as st
            secret_gemini = st.secrets.get("GEMINI_API_KEY")
            secret_openai = st.secrets.get("OPENAI_API_KEY")
            secret_provider = st.secrets.get("GOPAES_LLM_PROVIDER")
        except Exception:
            pass

        provider = (override_provider or secret_provider or os.getenv("GOPAES_LLM_PROVIDER", "gemini")).lower()
        if override_key:
            return provider, override_key

        gemini_key = secret_gemini or os.getenv("GEMINI_API_KEY")
        openai_key = secret_openai or os.getenv("OPENAI_API_KEY")

        if provider == "gemini" and gemini_key and "tu_api_key" not in gemini_key:
            return "gemini", gemini_key
        if provider == "openai" and openai_key and "tu_api_key" not in openai_key:
            return "openai", openai_key
        if gemini_key and "tu_api_key" not in gemini_key:
            return "gemini", gemini_key
        if openai_key and "tu_api_key" not in openai_key:
            return "openai", openai_key

        return provider, None

    @classmethod
    def generate_live_latex_explanation(
        cls,
        question: DEMREQuestionNode,
        selected_option: Optional[str],
        state: ResponseState,
        api_key_override: Optional[str] = None,
        provider_override: Optional[str] = None,
    ) -> str:
        provider, api_key = cls.get_active_provider(api_key_override, provider_override)

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
            student_situation = (
                f"El estudiante acertó marcando la alternativa correcta {question.correct_option})."
            )
            task_instruction = (
                "Resume de forma concisa la propiedad oficial del DEMRE aplicada y muestra el desarrollo elegante en LaTeX en 3 pasos."
            )

        system_prompt = (
            "Eres el Tutor de IA Oficial de GoPAES para la preparación de la PAES de Matemáticas (M1 y M2) en Chile. "
            "Tu regla estricta es ceñirte únicamente al currículo oficial del DEMRE/MINEDUC. "
            "Escribe todas las expresiones matemáticas utilizando delimitadores LaTeX ($...$ para fórmulas en línea y $$...$$ en bloques propios para pasos algebraicos destacados)."
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

        if not api_key:
            return (
                "⚠️ **API Key no detectada en `.env`**: Configura `GEMINI_API_KEY` o `OPENAI_API_KEY` en tu archivo `.env` "
                "(o ingrésala en la barra lateral izquierda de GoPAES) para que el LLM genere en vivo el diagnóstico "
                "personalizado de tu error y la resolución paso a paso en LaTeX."
            )

        try:
            if provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    system_instruction=system_prompt
                )
                response = model.generate_content(user_prompt)
                return response.text
            else:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                )
                return response.choices[0].message.content or ""
        except Exception as e:
            return f"❌ **Error al consultar el LLM ({provider})**: `{str(e)}`. Verifica que tu API Key sea válida."
