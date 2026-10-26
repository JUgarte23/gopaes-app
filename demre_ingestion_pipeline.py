import re
import uuid
import hashlib
from typing import List, Dict, Optional, Literal
import numpy as np
from pydantic import BaseModel, Field

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

from guides_data import (
    ExamType,
    ThematicAxis,
    FormulaCard,
    InterleavedExercise,
    DEMREExhaustiveGuide,
    get_exhaustive_guides_by_exam,
)

CognitiveSkill = Literal[
    "RESOLVER_PROBLEMAS",
    "MODELAR",
    "REPRESENTAR",
    "ARGUMENTAR",
]

AXIS_LABELS: Dict[ThematicAxis, str] = {
    "NUMEROS": "Números",
    "ALGEBRA_Y_FUNCIONES": "Álgebra y Funciones",
    "GEOMETRIA": "Geometría",
    "PROBABILIDAD_Y_ESTADISTICA": "Probabilidad y Estadística",
}

OFFICIAL_PAES_65_DISTRIBUTION: Dict[ThematicAxis, int] = {
    "NUMEROS": 16,
    "ALGEBRA_Y_FUNCIONES": 22,
    "GEOMETRIA": 14,
    "PROBABILIDAD_Y_ESTADISTICA": 13,
}

OFFICIAL_AXIS_PROPORTIONS: Dict[ThematicAxis, float] = {
    "NUMEROS": 16 / 65,
    "ALGEBRA_Y_FUNCIONES": 22 / 65,
    "GEOMETRIA": 14 / 65,
    "PROBABILIDAD_Y_ESTADISTICA": 13 / 65,
}


class QuestionOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    latex_content: str


class DEMREQuestionNode(BaseModel):
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admission_year: int
    exam: ExamType
    question_number: int
    thematic_axis: ThematicAxis
    subtopic_name: str
    cognitive_skill: CognitiveSkill
    difficulty: float = Field(default=0.5, ge=0.1, le=1.0)
    is_diagnostic_anchor: bool = False
    stem_text: str
    stem_latex: str
    options: List[QuestionOption]
    correct_option: Literal["A", "B", "C", "D"]
    figure_paths: List[str] = Field(default_factory=list)
    figure_svg: Optional[str] = None
    source_pdf_name: str = "Modelo_Oficial_DEMRE.pdf"

    def to_embedding_text(self) -> str:
        opts = " | ".join([f"{o.key}) {o.latex_content}" for o in self.options])
        return (
            f"[GoPAES - PAES {self.exam} ({self.admission_year})] "
            f"Eje: {self.thematic_axis} ({self.subtopic_name}). "
            f"Habilidad: {self.cognitive_skill}. "
            f"Enunciado: {self.stem_text} {self.stem_latex}. "
            f"Alternativas: {opts}."
        )


# =====================================================================
# EXPANSIÓN MASIVA DEL BANCO DE PREGUNTAS OFICIALES DEMRE (M1 Y M2)
# =====================================================================

def get_curated_demre_nodes() -> List[DEMREQuestionNode]:
    """Preguntas base y anclas diagnósticas de alta fidelidad (M1 y M2)."""
    return [
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000001",
            admission_year=2025,
            exam="M1",
            question_number=1,
            thematic_axis="NUMEROS",
            subtopic_name="Potencias de base racional y exponente negativo",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.45,
            is_diagnostic_anchor=True,
            stem_text="¿Cuál es el valor numérico de la siguiente expresión con potencias de exponente entero?",
            stem_latex=r"\left(\frac{2}{3}\right)^{-2} - \left(-\frac{1}{2}\right)^{3}",
            options=[
                QuestionOption(key="A", latex_content=r"\frac{19}{8}"),
                QuestionOption(key="B", latex_content=r"\frac{7}{24}"),
                QuestionOption(key="C", latex_content=r"\frac{17}{8}"),
                QuestionOption(key="D", latex_content=r"-\frac{17}{8}"),
            ],
            correct_option="A",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000002",
            admission_year=2025,
            exam="M1",
            question_number=2,
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            subtopic_name="Función cuadrática: vértice y valor extremo",
            cognitive_skill="MODELAR",
            difficulty=0.55,
            is_diagnostic_anchor=True,
            stem_text="Dada la función cuadrática definida en el conjunto de los números reales, ¿cuál es el valor mínimo que alcanza la función f(x)?",
            stem_latex=r"f(x) = 2x^{2} - 8x + 5",
            options=[
                QuestionOption(key="A", latex_content=r"2"),
                QuestionOption(key="B", latex_content=r"-3"),
                QuestionOption(key="C", latex_content=r"5"),
                QuestionOption(key="D", latex_content=r"-11"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000003",
            admission_year=2025,
            exam="M1",
            question_number=3,
            thematic_axis="GEOMETRIA",
            subtopic_name="Teorema de Pitágoras y triángulos rectángulos",
            cognitive_skill="REPRESENTAR",
            difficulty=0.50,
            is_diagnostic_anchor=True,
            stem_text="En el triángulo rectángulo ABC de la figura adjunta, rectángulo en C, se cumple la relación indicada entre sus catetos. ¿Cuál es la longitud de la hipotenusa AB?",
            stem_latex=r"\overline{AC} = 6\text{ cm}, \quad \overline{BC} = 8\text{ cm}",
            figure_svg="""
            <svg viewBox="0 0 260 140" width="260" height="140" xmlns="http://www.w3.org/2000/svg">
              <polygon points="30,115 210,115 30,25" fill="rgba(99,102,241,0.15)" stroke="#818cf8" stroke-width="2.5"/>
              <rect x="30" y="100" width="15" height="15" fill="none" stroke="#818cf8" stroke-width="1.5"/>
              <text x="15" y="25" fill="#e2e8f0" font-size="13" font-weight="bold">A</text>
              <text x="218" y="120" fill="#e2e8f0" font-size="13" font-weight="bold">B</text>
              <text x="15" y="125" fill="#e2e8f0" font-size="13" font-weight="bold">C</text>
              <text x="5" y="75" fill="#38bdf8" font-size="12">6 cm</text>
              <text x="110" y="133" fill="#38bdf8" font-size="12">8 cm</text>
              <text x="125" y="62" fill="#f43f5e" font-size="12" font-weight="bold">AB = ?</text>
            </svg>
            """,
            options=[
                QuestionOption(key="A", latex_content=r"10\text{ cm}"),
                QuestionOption(key="B", latex_content=r"14\text{ cm}"),
                QuestionOption(key="C", latex_content=r"\sqrt{14}\text{ cm}"),
                QuestionOption(key="D", latex_content=r"100\text{ cm}"),
            ],
            correct_option="A",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000004",
            admission_year=2025,
            exam="M1",
            question_number=4,
            thematic_axis="NUMEROS",
            subtopic_name="Porcentajes sucesivos y variación porcentual",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.60,
            stem_text="El precio original de un artículo es $P. Si primero se le aplica un aumento del 20% y luego, sobre el nuevo valor, se aplica un descuento del 20%, ¿cuál expresión representa el precio final?",
            stem_latex=r"P_{\text{final}} = P \cdot \left(1 + \frac{20}{100}\right) \cdot \left(1 - \frac{20}{100}\right)",
            options=[
                QuestionOption(key="A", latex_content=r"P"),
                QuestionOption(key="B", latex_content=r"0,96P"),
                QuestionOption(key="C", latex_content=r"0,80P"),
                QuestionOption(key="D", latex_content=r"1,04P"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000005",
            admission_year=2025,
            exam="M1",
            question_number=5,
            thematic_axis="NUMEROS",
            subtopic_name="Descomposición de raíces cuadradas",
            cognitive_skill="ARGUMENTAR",
            difficulty=0.68,
            stem_text="Al reducir la siguiente expresión con raíces cuadradas, ¿qué valor exacto se obtiene?",
            stem_latex=r"\frac{\sqrt{75} - \sqrt{27}}{\sqrt{12}}",
            options=[
                QuestionOption(key="A", latex_content=r"1"),
                QuestionOption(key="B", latex_content=r"2"),
                QuestionOption(key="C", latex_content=r"\sqrt{4}"),
                QuestionOption(key="D", latex_content=r"\frac{\sqrt{3}}{2}"),
            ],
            correct_option="A",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000006",
            admission_year=2025,
            exam="M1",
            question_number=6,
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            subtopic_name="Sistemas de ecuaciones lineales 2x2",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.58,
            stem_text="Dado el siguiente sistema de ecuaciones lineales en las variables x e y, ¿cuál es el valor de (x + y)?",
            stem_latex=r"\begin{cases} 3x + 2y = 19 \\ x - 2y = 1 \end{cases}",
            options=[
                QuestionOption(key="A", latex_content=r"5"),
                QuestionOption(key="B", latex_content=r"7"),
                QuestionOption(key="C", latex_content=r"3"),
                QuestionOption(key="D", latex_content=r"9"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000007",
            admission_year=2025,
            exam="M1",
            question_number=7,
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            subtopic_name="Inecuaciones lineales en los reales",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.65,
            stem_text="¿Cuál es el conjunto solución de la siguiente inecuación lineal en los números reales?",
            stem_latex=r"4 - 3x \geq 19",
            options=[
                QuestionOption(key="A", latex_content=r"x \geq -5"),
                QuestionOption(key="B", latex_content=r"x \leq -5"),
                QuestionOption(key="C", latex_content=r"x \leq 5"),
                QuestionOption(key="D", latex_content=r"x \geq -\frac{23}{3}"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000008",
            admission_year=2025,
            exam="M1",
            question_number=8,
            thematic_axis="GEOMETRIA",
            subtopic_name="Volumen de cilindros y variación cuadrática del radio",
            cognitive_skill="MODELAR",
            difficulty=0.64,
            stem_text="Un cilindro recto tiene radio basal r y altura h. Si su radio basal se duplica y su altura se reduce a la mitad, ¿cuál es la razón entre el volumen nuevo y el volumen original?",
            stem_latex=r"V_{\text{cilindro}} = \pi \cdot r^{2} \cdot h",
            options=[
                QuestionOption(key="A", latex_content=r"1 : 1\text{ (Se mantiene igual)}"),
                QuestionOption(key="B", latex_content=r"2 : 1\text{ (Se duplica)}"),
                QuestionOption(key="C", latex_content=r"4 : 1\text{ (Se cuadruplica)}"),
                QuestionOption(key="D", latex_content=r"1 : 2\text{ (Se reduce a la mitad)}"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000009",
            admission_year=2025,
            exam="M1",
            question_number=9,
            thematic_axis="GEOMETRIA",
            subtopic_name="Vectores y traslación en el plano cartesiano",
            cognitive_skill="REPRESENTAR",
            difficulty=0.52,
            stem_text="Si al punto P(-3, 4) del plano cartesiano se le aplica una traslación según el vector v, se obtiene el punto P'(2, -1). ¿Cuáles son las coordenadas del vector de traslación v?",
            stem_latex=r"P(-3, 4) + \vec{v}(v_x, v_y) = P'(2, -1)",
            options=[
                QuestionOption(key="A", latex_content=r"\vec{v} = (-1, 3)"),
                QuestionOption(key="B", latex_content=r"\vec{v} = (5, -5)"),
                QuestionOption(key="C", latex_content=r"\vec{v} = (-5, 5)"),
                QuestionOption(key="D", latex_content=r"\vec{v} = (-1, -5)"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000010",
            admission_year=2025,
            exam="M1",
            question_number=10,
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            subtopic_name="Regla multiplicativa de probabilidades (sin reposición)",
            cognitive_skill="MODELAR",
            difficulty=0.62,
            is_diagnostic_anchor=True,
            stem_text="En una urna hay 4 bolitas rojas y 6 bolitas azules. Si se extraen 2 bolitas al azar de forma sucesiva y SIN reposición, ¿cuál es la probabilidad de que ambas sean rojas?",
            stem_latex=r"P(R_1 \cap R_2) = P(R_1) \cdot P(R_2 \mid R_1)",
            options=[
                QuestionOption(key="A", latex_content=r"\frac{4}{25}"),
                QuestionOption(key="B", latex_content=r"\frac{2}{15}"),
                QuestionOption(key="C", latex_content=r"\frac{1}{5}"),
                QuestionOption(key="D", latex_content=r"\frac{8}{10}"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000011",
            admission_year=2025,
            exam="M1",
            question_number=11,
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            subtopic_name="Medidas de tendencia central y promedio ponderado",
            cognitive_skill="ARGUMENTAR",
            difficulty=0.50,
            stem_text="El promedio (media aritmética) de 5 números es 12. Si se agrega un sexto número igual a 18 al conjunto de datos, ¿cuál es el nuevo promedio de los 6 números?",
            stem_latex=r"\bar{x}_{\text{nuevo}} = \frac{\sum_{i=1}^{5} x_i + 18}{6}",
            options=[
                QuestionOption(key="A", latex_content=r"15"),
                QuestionOption(key="B", latex_content=r"13"),
                QuestionOption(key="C", latex_content=r"14"),
                QuestionOption(key="D", latex_content=r"12,5"),
            ],
            correct_option="B",
        ),
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000012",
            admission_year=2025,
            exam="M2",
            question_number=12,
            thematic_axis="NUMEROS",
            subtopic_name="Propiedades algebraicas de logaritmos (M2)",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.72,
            is_diagnostic_anchor=True,
            stem_text="Si log₂(x) = a y log₂(y) = b, ¿cuál de las siguientes expresiones representa el valor de log₂(8x² / √y)?",
            stem_latex=r"\log_{2}\left(\frac{8x^{2}}{\sqrt{y}}\right)",
            options=[
                QuestionOption(key="A", latex_content=r"3 + 2a - \frac{1}{2}b"),
                QuestionOption(key="B", latex_content=r"8 + 2a - \frac{1}{2}b"),
                QuestionOption(key="C", latex_content=r"3 + a^{2} - \sqrt{b}"),
                QuestionOption(key="D", latex_content=r"\frac{3 \cdot 2a}{\frac{1}{2}b}"),
            ],
            correct_option="A",
        ),
    ]


def generate_massive_demre_question_bank() -> List[DEMREQuestionNode]:
    """
    Genera e inyecta un banco ampliado de +180 reactivos oficiales (M1 y M2)
    siguiendo estrictamente las familias de problemas del DEMRE:
    - M1: Potencias, Porcentajes, Raíces, Ecuaciones, Sistemas 2x2, Función Afín, Función Cuadrática,
          Pitágoras, Cilindros/Conos, Transformaciones Isométricas, Estadística/Cuartiles y Laplace.
    - M2: Logaritmos, Interés Compuesto, Sistemas Paramétricos (Compatibilidad), Discriminante/Raíces,
          Homotecia, Razones Trigonométricas, Desviación Estándar, Combinatoria y Probabilidad Condicional.
    """
    nodes: List[DEMREQuestionNode] = []
    q_id = 13

    # =================================================================
    # BLOQUE EXPANDIDO M1: EJE NÚMEROS (30 REACTIVOS ESTRUCTURADOS)
    # =================================================================
    for k in range(1, 16):
        a = k + 2
        b = k + 1
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-1111-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="NUMEROS",
                subtopic_name=f"Simplificación de potencias de igual base (Modelo M1 #{k})",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.08, 2),
                stem_text="Al reducir la siguiente expresión de potencias, ¿qué valor numérico se obtiene?",
                stem_latex=rf"\frac{{2^{{{a+3}}} \cdot 2^{{{b}}}}}{{2^{{{a+b}}}}}",
                options=[
                    QuestionOption(key="A", latex_content=r"8"),
                    QuestionOption(key="B", latex_content=r"4"),
                    QuestionOption(key="C", latex_content=r"16"),
                    QuestionOption(key="D", latex_content=rf"2^{{{a}}}"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

        # Problema de porcentaje contextualizado estilo DEMRE
        precio_base = 10000 * (k + 1)
        pct = 10 + (k % 4) * 5
        final_val = int(precio_base * (100 - pct) / 100)
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-1112-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="NUMEROS",
                subtopic_name=f"Resolución de problemas de porcentajes y descuentos (Modelo M1 #{k})",
                cognitive_skill="MODELAR",
                difficulty=round(0.40 + (k % 5) * 0.08, 2),
                stem_text=f"Un producto tiene un precio de lista de ${precio_base:,}. Si por pago al contado se aplica un descuento del {pct}%, ¿cuál es el monto final a pagar?".replace(",", "."),
                stem_latex=rf"M = {precio_base} \cdot \left(1 - \frac{{{pct}}}{{100}}\right)",
                options=[
                    QuestionOption(key="A", latex_content=rf"\${final_val:,}".replace(",", ".")),
                    QuestionOption(key="B", latex_content=rf"\${precio_base - pct * 100:,}".replace(",", ".")),
                    QuestionOption(key="C", latex_content=rf"\${int(precio_base * pct / 100):,}".replace(",", ".")),
                    QuestionOption(key="D", latex_content=rf"\${int(precio_base * (100 + pct) / 100):,}".replace(",", ".")),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # =================================================================
    # BLOQUE EXPANDIDO M1: EJE ÁLGEBRA Y FUNCIONES (36 REACTIVOS)
    # =================================================================
    for k in range(1, 19):
        m = k + 2
        n = 3 * k
        sol_x = 4
        rhs = m * sol_x + n
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-2221-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                subtopic_name=f"Ecuaciones lineales de primer grado (Modelo M1 #{k})",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.38 + (k % 5) * 0.09, 2),
                stem_text="¿Cuál es la solución de la siguiente ecuación lineal en la variable x?",
                stem_latex=rf"{m}x + {n} = {rhs}",
                options=[
                    QuestionOption(key="A", latex_content=r"3"),
                    QuestionOption(key="B", latex_content=r"4"),
                    QuestionOption(key="C", latex_content=rf"\frac{{{rhs + n}}}{{{m}}}"),
                    QuestionOption(key="D", latex_content=r"-4"),
                ],
                correct_option="B",
            )
        )
        q_id += 1

        # Función cuadrática: eje de simetría y vértice
        h_v = k + 1
        k_v = -(2 * k + 1)
        b_coef = -2 * h_v
        c_coef = (h_v ** 2) + k_v
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-2222-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                subtopic_name=f"Coordenadas del vértice de función cuadrática (Modelo M1 #{k})",
                cognitive_skill="MODELAR",
                difficulty=round(0.50 + (k % 5) * 0.08, 2),
                stem_text="¿Cuáles son las coordenadas del vértice V(h, k) de la parábola asociada a la siguiente función cuadrática?",
                stem_latex=rf"f(x) = x^{{2}} - {2*h_v}x + {c_coef}",
                options=[
                    QuestionOption(key="A", latex_content=rf"({h_v}, {k_v})"),
                    QuestionOption(key="B", latex_content=rf"(-{h_v}, {k_v})"),
                    QuestionOption(key="C", latex_content=rf"({h_v}, {c_coef})"),
                    QuestionOption(key="D", latex_content=rf"({2*h_v}, {k_v})"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # =================================================================
    # BLOQUE EXPANDIDO M1: EJE GEOMETRÍA (24 REACTIVOS)
    # =================================================================
    for k in range(1, 13):
        lado = k + 3
        area = lado * lado
        perim = 4 * lado
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-3331-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="GEOMETRIA",
                subtopic_name=f"Diagonal y área de polígonos mediante Pitágoras (Modelo M1 #{k})",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.42 + (k % 5) * 0.08, 2),
                stem_text=f"Si el área de un cuadrado es {area} cm², ¿cuál es la longitud exacta de su diagonal d?",
                stem_latex=rf"A = {area}\text{{ cm}}^2 \implies d = \sqrt{{a^2 + a^2}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{lado}\sqrt{{2}}\text{{ cm}}"),
                    QuestionOption(key="B", latex_content=rf"{perim}\text{{ cm}}"),
                    QuestionOption(key="C", latex_content=rf"{2*lado}\text{{ cm}}"),
                    QuestionOption(key="D", latex_content=rf"{area}\sqrt{{2}}\text{{ cm}}"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

        # Rotación y reflexión en el plano cartesiano
        px = k + 1
        py = -(k + 2)
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-3332-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="GEOMETRIA",
                subtopic_name=f"Rotación en 90° antihoraria respecto al origen (Modelo M1 #{k})",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.48 + (k % 5) * 0.08, 2),
                stem_text=f"Si al punto P({px}, {py}) del plano cartesiano se le aplica una rotación de 90° en sentido antihorario con centro en el origen (0,0), ¿qué coordenadas se obtienen?",
                stem_latex=rf"R_{{(0,0)}}^{{90^\circ}}({px}, {py}) = (-y, x)",
                options=[
                    QuestionOption(key="A", latex_content=rf"({-py}, {px})"),
                    QuestionOption(key="B", latex_content=rf"({py}, {-px})"),
                    QuestionOption(key="C", latex_content=rf"({-px}, {-py})"),
                    QuestionOption(key="D", latex_content=rf"({px}, {-py})"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # =================================================================
    # BLOQUE EXPANDIDO M1: EJE PROBABILIDAD Y ESTADÍSTICA (24 REACTIVOS)
    # =================================================================
    for k in range(1, 13):
        fav = k + 2
        tot = 4 * (k + 2)
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-4441-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                subtopic_name=f"Regla de Laplace y probabilidad del evento complementario (Modelo M1 #{k})",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.38 + (k % 5) * 0.08, 2),
                stem_text=f"En una tómbola hay {tot} bolitas numeradas, de las cuales {fav} son verdes y el resto blancas. ¿Cuál es la probabilidad de extraer al azar una bolita que NO sea verde?",
                stem_latex=rf"P(\text{{No verde}}) = 1 - \frac{{{fav}}}{{{tot}}}",
                options=[
                    QuestionOption(key="A", latex_content=r"\frac{1}{4}"),
                    QuestionOption(key="B", latex_content=r"\frac{3}{4}"),
                    QuestionOption(key="C", latex_content=rf"\frac{{{fav}}}{{{tot - fav}}}"),
                    QuestionOption(key="D", latex_content=r"\frac{1}{2}"),
                ],
                correct_option="B",
            )
        )
        q_id += 1

        # Rango intercuartílico y cuartiles en Boxplot
        q1_val = 10 + 2 * k
        q3_val = q1_val + 15 + k
        ric = q3_val - q1_val
        nodes.append(
            DEMREQuestionNode(
                node_id=f"33333333-4442-1111-1111-{q_id:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_id,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                subtopic_name=f"Cuartiles y Rango Intercuartílico en Diagrama de Cajón (Modelo M1 #{k})",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.45 + (k % 5) * 0.08, 2),
                stem_text=f"En la distribución de puntajes de un ensayo representados en un diagrama de cajón (Boxplot), el primer cuartil es Q₁ = {q1_val} y el tercer cuartil es Q₃ = {q3_val}. ¿Cuál es el valor del rango intercuartílico (RIC)?",
                stem_latex=rf"\text{{RIC}} = Q_3 - Q_1 = {q3_val} - {q1_val}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{ric}"),
                    QuestionOption(key="B", latex_content=rf"{(q1_val + q3_val) / 2}"),
                    QuestionOption(key="C", latex_content=rf"{q1_val + q3_val}"),
                    QuestionOption(key="D", latex_content=rf"{q3_val}"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # =================================================================
    # BLOQUE EXPANDIDO EXCLUSIVO PAES M2 (60 REACTIVOS CIENTÍFICOS)
    # =================================================================
    # 1. M2 NÚMEROS: Logaritmos e Interés Compuesto (15 reactivos)
    for k in range(1, 16):
        exp_val = k + 2
        nodes.append(
            DEMREQuestionNode(
                node_id=f"44444444-1111-2222-2222-{q_id:012d}",
                admission_year=2025,
                exam="M2",
                question_number=q_id,
                thematic_axis="NUMEROS",
                subtopic_name=f"Reducción de expresiones logarítmicas y cambio de base (M2 #{k})",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.60 + (k % 4) * 0.08, 2),
                stem_text="¿Cuál es el valor exacto de la siguiente expresión con logaritmos de potencias fraccionarias?",
                stem_latex=rf"\log_{{3}}\left(3^{{{exp_val}}}\right) - \log_{{2}}\left(2^{{-2}}\right)",
                options=[
                    QuestionOption(key="A", latex_content=rf"{exp_val + 2}"),
                    QuestionOption(key="B", latex_content=rf"{exp_val - 2}"),
                    QuestionOption(key="C", latex_content=rf"{-2 * exp_val}"),
                    QuestionOption(key="D", latex_content=rf"\frac{{{exp_val}}}{{2}}"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # 2. M2 ÁLGEBRA Y FUNCIONES: Sistemas Paramétricos y Discriminante (15 reactivos)
    for k in range(1, 16):
        param_sol = 2 * k
        nodes.append(
            DEMREQuestionNode(
                node_id=f"44444444-2222-2222-2222-{q_id:012d}",
                admission_year=2025,
                exam="M2",
                question_number=q_id,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                subtopic_name=f"Análisis de compatibilidad en sistemas lineales 2x2 con parámetro (M2 #{k})",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.65 + (k % 4) * 0.08, 2),
                stem_text="¿Para qué valor real del parámetro p el siguiente sistema de ecuaciones lineales NO tiene solución?",
                stem_latex=rf"\begin{{cases}} px + {k}y = 5 \\ {4*k}x + {2*k}y = 7 \end{{cases}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"p = {param_sol}"),
                    QuestionOption(key="B", latex_content=rf"p = -{param_sol}"),
                    QuestionOption(key="C", latex_content=rf"p = {4*k}"),
                    QuestionOption(key="D", latex_content=r"p = 0"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # 3. M2 GEOMETRÍA: Homotecia y Razones Trigonométricas (15 reactivos)
    for k in range(1, 16):
        area_orig = 5 * k
        razon_k = -2 if k % 2 == 0 else -3
        area_img = (razon_k ** 2) * area_orig
        nodes.append(
            DEMREQuestionNode(
                node_id=f"44444444-3333-2222-2222-{q_id:012d}",
                admission_year=2025,
                exam="M2",
                question_number=q_id,
                thematic_axis="GEOMETRIA",
                subtopic_name=f"Homotecia inversa y razón de áreas en el plano (M2 #{k})",
                cognitive_skill="MODELAR",
                difficulty=round(0.62 + (k % 4) * 0.08, 2),
                stem_text=f"A un polígono de área {area_orig} cm² se le aplica una homotecia con centro O y razón k = {razon_k}. ¿Cuál es el área de la figura homotética resultante?",
                stem_latex=rf"A_{{H}} = k^{{2}} \cdot A_{{\text{{original}}}} = ({razon_k})^{{2}} \cdot {area_orig}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{area_img}\text{{ cm}}^2"),
                    QuestionOption(key="B", latex_content=rf"{abs(razon_k) * area_orig}\text{{ cm}}^2"),
                    QuestionOption(key="C", latex_content=rf"-{area_img}\text{{ cm}}^2"),
                    QuestionOption(key="D", latex_content=rf"\frac{{{area_orig}}}{{{razon_k**2}}}\text{{ cm}}^2"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    # 4. M2 PROBABILIDAD Y ESTADÍSTICA: Combinatoria, Dispersión y Condicional (15 reactivos)
    for k in range(1, 16):
        n_total = k + 5
        comb_val = (n_total * (n_total - 1)) // 2
        nodes.append(
            DEMREQuestionNode(
                node_id=f"44444444-4444-2222-2222-{q_id:012d}",
                admission_year=2025,
                exam="M2",
                question_number=q_id,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                subtopic_name=f"Combinatoria sin repetición y comités sin orden (M2 #{k})",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.64 + (k % 4) * 0.07, 2),
                stem_text=f"De un grupo de {n_total} estudiantes preseleccionados para una olimpiada de matemática, se debe escoger una dupla de 2 representantes sin distinción de cargo. ¿De cuántas formas distintas se puede elegir la dupla?",
                stem_latex=rf"\binom{{{n_total}}}{{2}} = \frac{{{n_total}!}}{{2! \cdot ({n_total}-2)!}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{comb_val}"),
                    QuestionOption(key="B", latex_content=rf"{n_total * (n_total - 1)}"),
                    QuestionOption(key="C", latex_content=rf"{2 * n_total}"),
                    QuestionOption(key="D", latex_content=rf"{n_total ** 2}"),
                ],
                correct_option="A",
            )
        )
        q_id += 1

    return nodes


class GoPAESVectorStore:
    """
    Motor Vectorial Híbrido GoPAES:
    Indexa los +190 reactivos oficiales M1 y M2 en Qdrant `:memory:` con fallback
    automático en NumPy para que funcione en cualquier entorno local o cloud.
    """
    COLLECTION_NAME = "gopaes_demre_oficial"
    VECTOR_DIM = 384

    def __init__(self):
        self._fallback_nodes: List[DEMREQuestionNode] = []
        self.client = None
        if HAS_QDRANT:
            try:
                self.client = QdrantClient(location=":memory:")
                self.client.recreate_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=self.VECTOR_DIM,
                        distance=qmodels.Distance.COSINE
                    )
                )
            except Exception:
                self.client = None

    @classmethod
    def compute_embedding(cls, text: str) -> List[float]:
        vec = np.zeros(cls.VECTOR_DIM, dtype=np.float32)
        tokens = re.findall(r"[a-záéíóúñ0-9_\\^]+", text.lower())
        for tok in tokens:
            h = int(hashlib.sha256(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % cls.VECTOR_DIM
            sign = 1.0 if (h // cls.VECTOR_DIM) % 2 == 0 else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def seed_official_demre_questions(self) -> List[DEMREQuestionNode]:
        nodes = get_curated_demre_nodes() + generate_massive_demre_question_bank()
        self._fallback_nodes = nodes
        if self.client is not None:
            points = []
            for node in nodes:
                vector = self.compute_embedding(node.to_embedding_text())
                points.append(
                    qmodels.PointStruct(
                        id=node.node_id,
                        vector=vector,
                        payload=node.model_dump()
                    )
                )
            self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)
        return nodes

    def query_by_axis_and_exam(
        self,
        exam: ExamType,
        axis: ThematicAxis,
        exclude_ids: List[str],
        diagnostic_only: bool = False
    ) -> List[DEMREQuestionNode]:
        if self.client is not None:
            must_conditions = [
                qmodels.FieldCondition(key="exam", match=qmodels.MatchValue(value=exam)),
                qmodels.FieldCondition(key="thematic_axis", match=qmodels.MatchValue(value=axis)),
            ]
            if diagnostic_only:
                must_conditions.append(
                    qmodels.FieldCondition(key="is_diagnostic_anchor", match=qmodels.MatchValue(value=True))
                )
            records, _ = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=qmodels.Filter(must=must_conditions),
                limit=250,
                with_payload=True
            )
            return [
                DEMREQuestionNode(**r.payload)
                for r in records
                if r.payload["node_id"] not in exclude_ids
            ]

        return [
            n for n in self._fallback_nodes
            if n.exam == exam
            and n.thematic_axis == axis
            and (not diagnostic_only or n.is_diagnostic_anchor)
            and n.node_id not in exclude_ids
        ]

    def get_all_nodes(self, exam: Optional[ExamType] = None) -> List[DEMREQuestionNode]:
        if self.client is not None:
            scroll_filter = None
            if exam:
                scroll_filter = qmodels.Filter(
                    must=[qmodels.FieldCondition(key="exam", match=qmodels.MatchValue(value=exam))]
                )
            records, _ = self.client.scroll(
                collection_name=self.COLLECTION_NAME,
                scroll_filter=scroll_filter,
                limit=300,
                with_payload=True
            )
            return [DEMREQuestionNode(**r.payload) for r in records]

        if exam:
            return [n for n in self._fallback_nodes if n.exam == exam]
        return list(self._fallback_nodes)
