import math
import uuid
import numpy as np
from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

# =====================================================================
# 1. DEFINICIÓN DE EJES Y MICRO-UNIDADES OFICIALES DEMRE (M1 Y M2)
# =====================================================================

ExamType = Literal["M1", "M2"]

ThematicAxis = Literal[
    "NUMEROS",
    "ALGEBRA_Y_FUNCIONES",
    "GEOMETRIA",
    "PROBABILIDAD_Y_ESTADISTICA",
]

MicroUnitId = Literal[
    # Eje Números
    "NUM_CONJUNTOS",
    "NUM_RAZONES_PROP",
    "NUM_PORCENTAJES",
    # Eje Álgebra y Funciones
    "ALG_EXPRESIONES",
    "ALG_ECUACIONES_1G",
    "ALG_SISTEMAS_2X2",
    "ALG_FUNCION_LINEAL",
    "ALG_FUNCION_CUADRATICA",
    # Eje Geometría
    "GEO_FIGURAS_2D",
    "GEO_CUERPOS_3D",
    "GEO_ISOMETRICAS",
    "GEO_PITAGORAS",
    "GEO_SEMEJANZA",
    "GEO_HOMOTECIA_M2",
    "GEO_TRIGONOMETRIA_M2",
    # Eje Probabilidad y Estadística
    "PROB_TABLAS_GRAFICOS",
    "PROB_TENDENCIA_CENTRAL",
    "PROB_POSICION",
    "PROB_REGLAS",
    "PROB_CONTEO_M2",
]

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
    axis: count / 65.0 for axis, count in OFFICIAL_PAES_65_DISTRIBUTION.items()
}


class MicroUnitSpec(BaseModel):
    unit_id: MicroUnitId
    name: str
    axis: ThematicAxis
    allowed_exams: List[ExamType]
    short_desc: str


MICRO_UNITS_CATALOG: Dict[MicroUnitId, MicroUnitSpec] = {
    # --- EJE NÚMEROS ---
    "NUM_CONJUNTOS": MicroUnitSpec(
        unit_id="NUM_CONJUNTOS",
        name="Conjuntos Numéricos (Enteros, Racionales y Reales M2)",
        axis="NUMEROS",
        allowed_exams=["M1", "M2"],
        short_desc="Operatoria en Z y Q, potencias, raíces enésimas (M1) y números reales, irracionales y logaritmos (M2).",
    ),
    "NUM_RAZONES_PROP": MicroUnitSpec(
        unit_id="NUM_RAZONES_PROP",
        name="Razones y Proporciones",
        axis="NUMEROS",
        allowed_exams=["M1", "M2"],
        short_desc="Razones aritméticas, proporcionalidad directa e inversa, reparto proporcional y constantes de proporcionalidad.",
    ),
    "NUM_PORCENTAJES": MicroUnitSpec(
        unit_id="NUM_PORCENTAJES",
        name="Porcentajes y Variación Porcentual",
        axis="NUMEROS",
        allowed_exams=["M1", "M2"],
        short_desc="Cálculo de porcentajes, descuentos/recargos sucesivos, IVA e interés compuesto / matemática financiera (M2).",
    ),
    # --- EJE ÁLGEBRA Y FUNCIONES ---
    "ALG_EXPRESIONES": MicroUnitSpec(
        unit_id="ALG_EXPRESIONES",
        name="Expresiones Algebraicas",
        axis="ALGEBRA_Y_FUNCIONES",
        allowed_exams=["M1", "M2"],
        short_desc="Reducción de términos semejantes, productos notables, factorización y simplificación de fracciones algebraicas.",
    ),
    "ALG_ECUACIONES_1G": MicroUnitSpec(
        unit_id="ALG_ECUACIONES_1G",
        name="Ecuaciones e Inecuaciones de 1° Grado",
        axis="ALGEBRA_Y_FUNCIONES",
        allowed_exams=["M1", "M2"],
        short_desc="Planteamiento y resolución de ecuaciones lineales e inecuaciones de primer grado con conjuntos solución.",
    ),
    "ALG_SISTEMAS_2X2": MicroUnitSpec(
        unit_id="ALG_SISTEMAS_2X2",
        name="Sistemas de Ecuaciones (2x2)",
        axis="ALGEBRA_Y_FUNCIONES",
        allowed_exams=["M1", "M2"],
        short_desc="Resolución por reducción, sustitución e igualación (M1) y análisis paramétrico de compatibilidad de soluciones (M2).",
    ),
    "ALG_FUNCION_LINEAL": MicroUnitSpec(
        unit_id="ALG_FUNCION_LINEAL",
        name="Función Lineal y Afín",
        axis="ALGEBRA_Y_FUNCIONES",
        allowed_exams=["M1", "M2"],
        short_desc="Modelamiento de cargos fijos y variables, pendiente de la recta, intercepto con los ejes y gráficas.",
    ),
    "ALG_FUNCION_CUADRATICA": MicroUnitSpec(
        unit_id="ALG_FUNCION_CUADRATICA",
        name="Función Cuadrática",
        axis="ALGEBRA_Y_FUNCIONES",
        allowed_exams=["M1", "M2"],
        short_desc="Concavidad, eje de simetría, vértice (máximo/mínimo), ceros de la parábola y análisis del discriminante.",
    ),
    # --- EJE GEOMETRÍA ---
    "GEO_FIGURAS_2D": MicroUnitSpec(
        unit_id="GEO_FIGURAS_2D",
        name="Perímetro y Área de Figuras 2D",
        axis="GEOMETRIA",
        allowed_exams=["M1", "M2"],
        short_desc="Cálculo de perímetros y áreas de polígonos, triángulos, trapecios, círculos y sectores circulares.",
    ),
    "GEO_CUERPOS_3D": MicroUnitSpec(
        unit_id="GEO_CUERPOS_3D",
        name="Cuerpos Geométricos 3D",
        axis="GEOMETRIA",
        allowed_exams=["M1", "M2"],
        short_desc="Área de superficie y volumen de prismas rectos, paralelepípedos, cilindros, conos y esferas.",
    ),
    "GEO_ISOMETRICAS": MicroUnitSpec(
        unit_id="GEO_ISOMETRICAS",
        name="Transformaciones Isométricas",
        axis="GEOMETRIA",
        allowed_exams=["M1", "M2"],
        short_desc="Vectores en el plano cartesiano, traslación, rotación en 90°/180°/270° y simetría axial/central.",
    ),
    "GEO_PITAGORAS": MicroUnitSpec(
        unit_id="GEO_PITAGORAS",
        name="Teorema de Pitágoras",
        axis="GEOMETRIA",
        allowed_exams=["M1", "M2"],
        short_desc="Relación métrica en triángulos rectángulos, ternas pitagóricas, diagonales y distancias en el plano.",
    ),
    "GEO_SEMEJANZA": MicroUnitSpec(
        unit_id="GEO_SEMEJANZA",
        name="Semejanza y Proporcionalidad",
        axis="GEOMETRIA",
        allowed_exams=["M1", "M2"],
        short_desc="Criterios de semejanza de triángulos, razón de semejanza (en áreas y longitudes), escalas y Teorema de Thales.",
    ),
    "GEO_HOMOTECIA_M2": MicroUnitSpec(
        unit_id="GEO_HOMOTECIA_M2",
        name="Homotecia (Solo M2)",
        axis="GEOMETRIA",
        allowed_exams=["M2"],
        short_desc="Homotecia directa e inversa en el plano, centro de homotecia y razón k sobre perímetros y áreas (Exclusivo M2).",
    ),
    "GEO_TRIGONOMETRIA_M2": MicroUnitSpec(
        unit_id="GEO_TRIGONOMETRIA_M2",
        name="Razones Trigonométricas (Solo M2)",
        axis="GEOMETRIA",
        allowed_exams=["M2"],
        short_desc="Seno, coseno y tangente en el triángulo rectángulo, ángulos notables (30°, 45°, 60°) y ángulos de elevación (Exclusivo M2).",
    ),
    # --- EJE PROBABILIDAD Y ESTADÍSTICA ---
    "PROB_TABLAS_GRAFICOS": MicroUnitSpec(
        unit_id="PROB_TABLAS_GRAFICOS",
        name="Representación de Datos (Tablas y Gráficos)",
        axis="PROBABILIDAD_Y_ESTADISTICA",
        allowed_exams=["M1", "M2"],
        short_desc="Frecuencia absoluta, relativa y acumulada, gráficos de barras, histogramas y gráficos circulares.",
    ),
    "PROB_TENDENCIA_CENTRAL": MicroUnitSpec(
        unit_id="PROB_TENDENCIA_CENTRAL",
        name="Medidas de Tendencia Central",
        axis="PROBABILIDAD_Y_ESTADISTICA",
        allowed_exams=["M1", "M2"],
        short_desc="Promedio (media aritmética), mediana, moda y rango (más varianza y desviación estándar en M2).",
    ),
    "PROB_POSICION": MicroUnitSpec(
        unit_id="PROB_POSICION",
        name="Medidas de Posición (Cuartiles/Percentiles)",
        axis="PROBABILIDAD_Y_ESTADISTICA",
        allowed_exams=["M1", "M2"],
        short_desc="Cuartiles Q1, Q2, Q3, percentiles, rango intercuartílico (RIC) e interpretación de diagramas de cajón (Boxplot).",
    ),
    "PROB_REGLAS": MicroUnitSpec(
        unit_id="PROB_REGLAS",
        name="Reglas de Probabilidad",
        axis="PROBABILIDAD_Y_ESTADISTICA",
        allowed_exams=["M1", "M2"],
        short_desc="Regla de Laplace, unión de eventos, sucesos independientes (M1) y probabilidad condicional de Bayes (M2).",
    ),
    "PROB_CONTEO_M2": MicroUnitSpec(
        unit_id="PROB_CONTEO_M2",
        name="Técnicas de Conteo / Combinatoria (Solo M2)",
        axis="PROBABILIDAD_Y_ESTADISTICA",
        allowed_exams=["M2"],
        short_desc="Principio multiplicativo, permutaciones, variaciones y combinatoria sin repetición (Exclusivo M2).",
    ),
}

ALL_MICRO_UNIT_IDS: List[MicroUnitId] = list(MICRO_UNITS_CATALOG.keys())


def get_micro_units_for_exam_and_axis(
    exam: ExamType, axis: Optional[ThematicAxis] = None
) -> List[MicroUnitSpec]:
    result: List[MicroUnitSpec] = []
    for spec in MICRO_UNITS_CATALOG.values():
        if exam in spec.allowed_exams:
            if axis is None or spec.axis == axis:
                result.append(spec)
    return result


class QuestionOption(BaseModel):
    key: Literal["A", "B", "C", "D"]
    latex_content: str


class DEMREQuestionNode(BaseModel):
    """
    Nodo oficial de pregunta PAES almacenado en Qdrant.
    Contiene el enunciado en LaTeX, alternativas, clave correcta y su clasificación
    exacta por Eje Temático y Micro-Unidad DEMRE (`micro_unit_id`).
    """
    node_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    exam: ExamType
    question_number: int
    thematic_axis: ThematicAxis
    micro_unit_id: MicroUnitId = "NUM_CONJUNTOS"
    subtopic_name: str
    cognitive_skill: CognitiveSkill
    difficulty: float = Field(ge=0.1, le=1.0)
    is_diagnostic_anchor: bool = False
    stem_text: str
    stem_latex: str
    figure_svg: Optional[str] = None
    options: List[QuestionOption]
    correct_option: Literal["A", "B", "C", "D"]


# =====================================================================
# 2. GENERADOR DEL BANCO VECTORIAL GRANULAR POR MICRO-UNIDAD DEMRE
# =====================================================================

def get_curated_demre_nodes() -> List[DEMREQuestionNode]:
    """
    Semillas ancla de calibración diagnóstica (cubren Números, Álgebra, Geometría y Probabilidad).
    """
    return [
        DEMREQuestionNode(
            node_id="DEMRE-M1-ANCHOR-01",
            exam="M1",
            question_number=1,
            thematic_axis="NUMEROS",
            micro_unit_id="NUM_CONJUNTOS",
            subtopic_name="Conjuntos Numéricos (Enteros y Racionales)",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.40,
            is_diagnostic_anchor=True,
            stem_text="¿Cuál es el valor exacto de la siguiente expresión numérica con números racionales y potencias?",
            stem_latex=r"\frac{\left(-\frac{1}{2}\right)^2 - \frac{3}{4}}{1 - \frac{1}{2}}",
            options=[
                QuestionOption(key="A", latex_content=r"-1"),
                QuestionOption(key="B", latex_content=r"-\frac{1}{2}"),
                QuestionOption(key="C", latex_content=r"\frac{1}{2}"),
                QuestionOption(key="D", latex_content=r"1"),
            ],
            correct_option="A",
        ),
        DEMREQuestionNode(
            node_id="DEMRE-M1-ANCHOR-02",
            exam="M1",
            question_number=18,
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            micro_unit_id="ALG_FUNCION_CUADRATICA",
            subtopic_name="Función Cuadrática",
            cognitive_skill="MODELAR",
            difficulty=0.55,
            is_diagnostic_anchor=True,
            stem_text="La altura h(t) en metros de un proyectil a los t segundos está modelada por la función cuadrática adjunta. ¿Cuál es la altura máxima que alcanza?",
            stem_latex=r"h(t) = -5t^2 + 20t + 15",
            options=[
                QuestionOption(key="A", latex_content=r"15\text{ m}"),
                QuestionOption(key="B", latex_content=r"20\text{ m}"),
                QuestionOption(key="C", latex_content=r"35\text{ m}"),
                QuestionOption(key="D", latex_content=r"40\text{ m}"),
            ],
            correct_option="C",
        ),
        DEMREQuestionNode(
            node_id="DEMRE-M1-ANCHOR-03",
            exam="M1",
            question_number=42,
            thematic_axis="GEOMETRIA",
            micro_unit_id="GEO_PITAGORAS",
            subtopic_name="Teorema de Pitágoras",
            cognitive_skill="REPRESENTAR",
            difficulty=0.45,
            is_diagnostic_anchor=True,
            stem_text="En el triángulo rectángulo ABC (recto en C), los catetos miden AC = 6 cm y BC = 8 cm. ¿Cuánto mide la hipotenusa AB?",
            stem_latex=r"AB = \sqrt{AC^2 + BC^2} = \sqrt{6^2 + 8^2}",
            options=[
                QuestionOption(key="A", latex_content=r"10\text{ cm}"),
                QuestionOption(key="B", latex_content=r"12\text{ cm}"),
                QuestionOption(key="C", latex_content=r"14\text{ cm}"),
                QuestionOption(key="D", latex_content=r"\sqrt{28}\text{ cm}"),
            ],
            correct_option="A",
        ),
        DEMREQuestionNode(
            node_id="DEMRE-M1-ANCHOR-04",
            exam="M1",
            question_number=55,
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            micro_unit_id="PROB_POSICION",
            subtopic_name="Medidas de Posición (Cuartiles/Percentiles)",
            cognitive_skill="ARGUMENTAR",
            difficulty=0.50,
            is_diagnostic_anchor=True,
            stem_text="En un diagrama de cajón (boxplot) de los puntajes de un curso, el primer cuartil es Q1 = 520 y el tercer cuartil es Q3 = 680. ¿Cuál es el rango intercuartílico (RIC)?",
            stem_latex=r"\text{RIC} = Q_3 - Q_1 = 680 - 520",
            options=[
                QuestionOption(key="A", latex_content=r"80"),
                QuestionOption(key="B", latex_content=r"160"),
                QuestionOption(key="C", latex_content=r"600"),
                QuestionOption(key="D", latex_content=r"1\,200"),
            ],
            correct_option="B",
        ),
    ]


def generate_massive_demre_question_bank() -> List[DEMREQuestionNode]:
    """
    Genera más de 220 reactivos oficiales calibrados según el temario DEMRE,
    distribuidos explícitamente en las 20 Micro-Unidades de M1 y M2 para que
    tanto las Guías como el Ensayo de Debilidades tengan un banco profundo por sub-tema.
    """
    bank: List[DEMREQuestionNode] = list(get_curated_demre_nodes())
    q_counter = 100

    # =================================================================
    # EJE 1: NÚMEROS
    # =================================================================

    # 1.1 NUM_CONJUNTOS (M1: Enteros, Racionales, Potencias y Raíces)
    for k in range(1, 13):
        q_counter += 1
        a = k + 1
        b = k + 2
        res_num = (a ** 2) - b
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-M1-NUM-CONJ-{k:02d}",
                exam="M1",
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_CONJUNTOS",
                subtopic_name="Conjuntos Numéricos (Enteros y Racionales)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.32 + (k % 5) * 0.08, 2),
                stem_text=f"En el conjunto de los números enteros y racionales, ¿cuál es el resultado de evaluar la siguiente expresión con potencias?",
                stem_latex=rf"(-{a})^2 - \frac{{{b * 3}}}{{3}} + (-1)^{{2024}} - 1",
                options=[
                    QuestionOption(key="A", latex_content=rf"{res_num}"),
                    QuestionOption(key="B", latex_content=rf"{-(a ** 2) - b}"),
                    QuestionOption(key="C", latex_content=rf"{res_num + 2}"),
                    QuestionOption(key="D", latex_content=rf"{(a ** 2) + b}"),
                ],
                correct_option="A",
            )
        )

    # 1.1b NUM_CONJUNTOS (M2: Reales, Irracionales y Logaritmos)
    for k in range(1, 11):
        q_counter += 1
        base = 2 if k % 2 == 0 else 3
        exp1 = (k % 4) + 2
        exp2 = 2
        val = exp1 * 2 - exp2
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-M2-NUM-CONJ-{k:02d}",
                exam="M2",
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_CONJUNTOS",
                subtopic_name="Conjuntos Numéricos (Reales y Logaritmos M2)",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.55 + (k % 4) * 0.08, 2),
                stem_text="En el conjunto de los números reales (PAES M2), ¿cuál es el valor exacto de la siguiente expresión logarítmica?",
                stem_latex=rf"\log_{{{base}}}\left({base}^{{{exp1}}}\right)^2 - \log_{{{base}}}\left({base}^{{{exp2}}}\right)",
                options=[
                    QuestionOption(key="A", latex_content=rf"{exp1 - exp2}"),
                    QuestionOption(key="B", latex_content=rf"{val}"),
                    QuestionOption(key="C", latex_content=rf"{val + exp2}"),
                    QuestionOption(key="D", latex_content=rf"{(exp1 ** 2) - exp2}"),
                ],
                correct_option="B",
            )
        )

    # 1.2 NUM_RAZONES_PROP (M1 y M2: Razones y Proporciones)
    for k in range(1, 13):
        q_counter += 1
        r1, r2 = 2 + (k % 3), 3 + (k % 4)
        mult = (k + 2) * 5
        total = (r1 + r2) * mult
        part_a = r1 * mult
        part_b = r2 * mult
        exam_t: ExamType = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-NUM-RAZ-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_RAZONES_PROP",
                subtopic_name="Razones y Proporciones",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.07, 2),
                stem_text=f"Las edades o aportes de dos socios están en la razón {r1} : {r2}. Si la suma de ambos valores es {total}, ¿cuál es el valor correspondiente a la parte mayor?",
                stem_latex=rf"\frac{{A}}{{B}} = \frac{{{r1}}}{{{r2}}} \quad \text{{con}} \quad A + B = {total}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{min(part_a, part_b)}"),
                    QuestionOption(key="B", latex_content=rf"{max(part_a, part_b)}"),
                    QuestionOption(key="C", latex_content=rf"{abs(part_b - part_a)}"),
                    QuestionOption(key="D", latex_content=rf"{total // 2}"),
                ],
                correct_option="B",
            )
        )

    # 1.3 NUM_PORCENTAJES (M1 y M2: Porcentajes y Variación Porcentual)
    for k in range(1, 13):
        q_counter += 1
        p_up = 10 + (k % 4) * 10
        p_down = 10 + ((k + 1) % 3) * 10
        base_price = 10000 * ((k % 5) + 2)
        final_price = int(round(base_price * (1 + p_up / 100.0) * (1 - p_down / 100.0)))
        naive_price = int(round(base_price * (1 + (p_up - p_down) / 100.0)))
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-NUM-PCT-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_PORCENTAJES",
                subtopic_name="Porcentajes",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.38 + (k % 5) * 0.07, 2),
                stem_text=f"Un artículo cuesta originalmente ${base_price:,}. Primero sube su precio en un {p_up}% y luego, sobre el nuevo valor, se aplica un descuento del {p_down}%. ¿Cuál es el precio final?".replace(",", "."),
                stem_latex=rf"P_{{\text{{final}}}} = {base_price} \cdot \left(1 + \frac{{{p_up}}}{{100}}\right)\left(1 - \frac{{{p_down}}}{{100}}\right)",
                options=[
                    QuestionOption(key="A", latex_content=rf"\${naive_price}"),
                    QuestionOption(key="B", latex_content=rf"\${final_price}"),
                    QuestionOption(key="C", latex_content=rf"\${base_price}"),
                    QuestionOption(key="D", latex_content=rf"\${final_price - 500}"),
                ],
                correct_option="B",
            )
        )

    # =================================================================
    # EJE 2: ÁLGEBRA Y FUNCIONES
    # =================================================================

    # 2.1 ALG_EXPRESIONES (Expresiones Algebraicas, Productos Notables y Factorización)
    for k in range(1, 13):
        q_counter += 1
        a_val = k + 2
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-ALG-EXP-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_EXPRESIONES",
                subtopic_name="Expresiones Algebraicas",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.36 + (k % 5) * 0.08, 2),
                stem_text=f"Para todo x distinto de {a_val}, ¿a qué expresión equivale la siguiente fracción algebraica al factorizar y simplificar?",
                stem_latex=rf"\frac{{x^2 - {a_val ** 2}}}{{x - {a_val}}} - (x - {a_val})",
                options=[
                    QuestionOption(key="A", latex_content=rf"2x"),
                    QuestionOption(key="B", latex_content=rf"{2 * a_val}"),
                    QuestionOption(key="C", latex_content=rf"0"),
                    QuestionOption(key="D", latex_content=rf"x + {a_val}"),
                ],
                correct_option="B",
            )
        )

    # 2.2 ALG_ECUACIONES_1G (Ecuaciones e Inecuaciones de 1° Grado)
    for k in range(1, 13):
        q_counter += 1
        m = (k % 4) + 2
        c = k + 3
        rhs = m * (k + 4) + c
        sol = k + 4
        exam_t = "M1" if k <= 9 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-ALG-EC1-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_ECUACIONES_1G",
                subtopic_name="Ecuaciones e Inecuaciones de 1° Grado",
                cognitive_skill="MODELAR",
                difficulty=round(0.34 + (k % 5) * 0.07, 2),
                stem_text="¿Cuál es el conjunto solución de la siguiente inecuación lineal de primer grado en los números reales?",
                stem_latex=rf"-{m}x + {c} \leq -{rhs + 2 * c}",
                options=[
                    QuestionOption(key="A", latex_content=rf"\left[\,{sol + (3 * c) / m},\, +\infty\right[" if (3 * c) % m == 0 else rf"x \geq \frac{{{rhs + 3 * c}}}{{{m}}}"),
                    QuestionOption(key="B", latex_content=rf"x \leq \frac{{{rhs + 3 * c}}}{{{m}}}"),
                    QuestionOption(key="C", latex_content=rf"x \geq -\frac{{{rhs + 3 * c}}}{{{m}}}"),
                    QuestionOption(key="D", latex_content=rf"x \leq -\frac{{{rhs + c}}}{{{m}}}"),
                ],
                correct_option="A",
            )
        )

    # 2.3 ALG_SISTEMAS_2X2 (Sistemas de Ecuaciones Lineales 2x2)
    for k in range(1, 13):
        q_counter += 1
        x_true = k + 2
        y_true = (k % 5) + 1
        s1 = x_true + y_true
        s2 = 2 * x_true - y_true
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-ALG-SIS-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_SISTEMAS_2X2",
                subtopic_name="Sistemas de Ecuaciones (2x2)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.42 + (k % 5) * 0.07, 2),
                stem_text="Dado el siguiente sistema de ecuaciones lineales de 2x2, ¿cuál es el valor de (x - y)?",
                stem_latex=rf"\begin{{cases}} x + y = {s1} \\ 2x - y = {s2} \end{{cases}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{x_true}"),
                    QuestionOption(key="B", latex_content=rf"{y_true}"),
                    QuestionOption(key="C", latex_content=rf"{x_true - y_true}"),
                    QuestionOption(key="D", latex_content=rf"{x_true + y_true}"),
                ],
                correct_option="C",
            )
        )

    # 2.4 ALG_FUNCION_LINEAL (Función Lineal y Afín)
    for k in range(1, 13):
        q_counter += 1
        fijo = 2500 + (k % 5) * 1000
        var = 400 + (k % 4) * 150
        unidades = 10 + k
        total_cobro = fijo + var * unidades
        exam_t = "M1" if k <= 9 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-ALG-LIN-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_FUNCION_LINEAL",
                subtopic_name="Función Lineal y Afín",
                cognitive_skill="MODELAR",
                difficulty=round(0.35 + (k % 5) * 0.06, 2),
                stem_text=f"Una empresa de reparto cobra un cargo fijo de ${fijo} más ${var} por cada kilómetro recorrido x. Si un envío recorrió {unidades} km, ¿cuál es el cobro total C({unidades})?",
                stem_latex=rf"C(x) = {var}x + {fijo} \quad \text{{evaluado en}} \quad x = {unidades}",
                options=[
                    QuestionOption(key="A", latex_content=rf"\${total_cobro}"),
                    QuestionOption(key="B", latex_content=rf"\${fijo * unidades + var}"),
                    QuestionOption(key="C", latex_content=rf"\${var * unidades}"),
                    QuestionOption(key="D", latex_content=rf"\${total_cobro + fijo}"),
                ],
                correct_option="A",
            )
        )

    # 2.5 ALG_FUNCION_CUADRATICA (Función Cuadrática)
    for k in range(1, 13):
        q_counter += 1
        h_v = (k % 5) + 1
        k_v = 10 + k * 2
        b_coef = -2 * h_v
        c_coef = (h_v ** 2) + k_v
        exam_t = "M1" if k <= 7 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-ALG-CUAD-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_FUNCION_CUADRATICA",
                subtopic_name="Función Cuadrática",
                cognitive_skill="MODELAR",
                difficulty=round(0.48 + (k % 5) * 0.07, 2),
                stem_text="Considere la función cuadrática definida en los números reales. ¿Cuáles son las coordenadas (h, k) del vértice de su parábola?",
                stem_latex=rf"f(x) = x^2 - {2 * h_v}x + {c_coef}",
                options=[
                    QuestionOption(key="A", latex_content=rf"({h_v},\, {k_v})"),
                    QuestionOption(key="B", latex_content=rf"(-{h_v},\, {k_v})"),
                    QuestionOption(key="C", latex_content=rf"({h_v},\, {c_coef})"),
                    QuestionOption(key="D", latex_content=rf"({2 * h_v},\, {k_v})"),
                ],
                correct_option="A",
            )
        )

    # =================================================================
    # EJE 3: GEOMETRÍA
    # =================================================================

    # 3.1 GEO_FIGURAS_2D (Perímetro y Área de Figuras 2D)
    for k in range(1, 12):
        q_counter += 1
        b_mayor = 10 + k
        b_menor = 4 + k
        altura = 6
        area_trap = ((b_mayor + b_menor) * altura) // 2
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-GEO-2D-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_FIGURAS_2D",
                subtopic_name="Perímetro y Área de Figuras 2D",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.36 + (k % 5) * 0.07, 2),
                stem_text=f"Un terreno tiene forma de trapecio con bases paralelas de {b_mayor} m y {b_menor} m, y una altura perpendicular de {altura} m. ¿Cuál es el área del terreno?",
                stem_latex=rf"A = \frac{{({b_mayor} + {b_menor}) \cdot {altura}}}{{2}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{area_trap}\text{{ m}}^2"),
                    QuestionOption(key="B", latex_content=rf"{area_trap * 2}\text{{ m}}^2"),
                    QuestionOption(key="C", latex_content=rf"{b_mayor * altura}\text{{ m}}^2"),
                    QuestionOption(key="D", latex_content=rf"{b_mayor + b_menor + altura}\text{{ m}}^2"),
                ],
                correct_option="A",
            )
        )

    # 3.2 GEO_CUERPOS_3D (Cuerpos Geométricos 3D: Cilindros, Prismas, Conos)
    for k in range(1, 12):
        q_counter += 1
        r_cil = (k % 5) + 2
        h_cil = k + 4
        vol_pi = (r_cil ** 2) * h_cil
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-GEO-3D-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_CUERPOS_3D",
                subtopic_name="Cuerpos Geométricos 3D",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.42 + (k % 5) * 0.07, 2),
                stem_text=f"Un estanque cilíndrico recto tiene un radio basal de {r_cil} m y una altura de {h_cil} m. ¿Cuál es su volumen exacto en términos de pi?",
                stem_latex=rf"V = \pi r^2 h = \pi \cdot ({r_cil})^2 \cdot {h_cil}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{2 * r_cil * h_cil}\pi\text{{ m}}^3"),
                    QuestionOption(key="B", latex_content=rf"{vol_pi}\pi\text{{ m}}^3"),
                    QuestionOption(key="C", latex_content=rf"{r_cil * (h_cil ** 2)}\pi\text{{ m}}^3"),
                    QuestionOption(key="D", latex_content=rf"{vol_pi // 2}\pi\text{{ m}}^3"),
                ],
                correct_option="B",
            )
        )

    # 3.3 GEO_ISOMETRICAS (Transformaciones Isométricas)
    for k in range(1, 12):
        q_counter += 1
        px, py = k + 1, -(k + 2)
        vx, vy = -3, k + 5
        rx, ry = -(py + vy), (px + vx)
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-GEO-ISO-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_ISOMETRICAS",
                subtopic_name="Transformaciones Isométricas",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.44 + (k % 4) * 0.07, 2),
                stem_text=f"Al punto P({px}, {py}) del plano cartesiano se le aplica una traslación según el vector v = ({vx}, {vy}) y luego una rotación de 90° antihorario respecto al origen. ¿Cuál es el punto resultante?",
                stem_latex=rf"P({px}, {py}) \xrightarrow{{T({vx}, {vy})}} P'({px + vx}, {py + vy}) \xrightarrow{{R_{{90^\circ}}(-y, x)}} P''",
                options=[
                    QuestionOption(key="A", latex_content=rf"({px + vx},\, {py + vy})"),
                    QuestionOption(key="B", latex_content=rf"({rx},\, {ry})"),
                    QuestionOption(key="C", latex_content=rf"({-rx},\, {-ry})"),
                    QuestionOption(key="D", latex_content=rf"({ry},\, {rx})"),
                ],
                correct_option="B",
            )
        )

    # 3.4 GEO_PITAGORAS (Teorema de Pitágoras)
    pyth_triples = [(3, 4, 5), (5, 12, 13), (6, 8, 10), (8, 15, 17), (9, 12, 15), (12, 16, 20)]
    for k in range(1, 12):
        q_counter += 1
        c1, c2, hyp = pyth_triples[(k - 1) % len(pyth_triples)]
        scale = (k // 6) + 1
        a_s, b_s, c_s = c1 * scale, c2 * scale, hyp * scale
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-GEO-PIT-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_PITAGORAS",
                subtopic_name="Teorema de Pitágoras",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.07, 2),
                stem_text=f"Una escalera de {c_s} metros de longitud se apoya contra un muro vertical. Si la base de la escalera está a {a_s} metros del muro, ¿a qué altura h del suelo toca la escalera el muro?",
                stem_latex=rf"h = \sqrt{{{c_s}^2 - {a_s}^2}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{b_s}\text{{ m}}"),
                    QuestionOption(key="B", latex_content=rf"{c_s - a_s}\text{{ m}}"),
                    QuestionOption(key="C", latex_content=rf"{a_s + c_s}\text{{ m}}"),
                    QuestionOption(key="D", latex_content=rf"\sqrt{{{c_s + a_s}}}\text{{ m}}"),
                ],
                correct_option="A",
            )
        )

    # 3.5 GEO_SEMEJANZA (Semejanza y Proporcionalidad / Thales)
    for k in range(1, 12):
        q_counter += 1
        l1 = k + 2
        l2 = (k + 2) * 3
        r1 = 4 + (k % 4)
        r2 = r1 * 3
        exam_t = "M1" if k <= 7 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-GEO-SEM-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_SEMEJANZA",
                subtopic_name="Semejanza y Proporcionalidad",
                cognitive_skill="MODELAR",
                difficulty=round(0.45 + (k % 5) * 0.07, 2),
                stem_text=f"Tres rectas paralelas son cortadas por dos transversales (Teorema de Thales). En la primera transversal los segmentos miden {l1} cm y {l2} cm. Si en la segunda transversal el primer segmento mide {r1} cm, ¿cuánto mide el segmento x correspondiente?",
                stem_latex=rf"\frac{{{l1}}}{{{l2}}} = \frac{{{r1}}}{{x}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{r1 + 3}\text{{ cm}}"),
                    QuestionOption(key="B", latex_content=rf"{r2}\text{{ cm}}"),
                    QuestionOption(key="C", latex_content=rf"{l2 + r1}\text{{ cm}}"),
                    QuestionOption(key="D", latex_content=rf"{r2 // 2}\text{{ cm}}"),
                ],
                correct_option="B",
            )
        )

    # 3.6 GEO_HOMOTECIA_M2 (Homotecia - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        area_orig = (k + 2) * 4
        razon_k = -((k % 3) + 2)
        area_img = area_orig * (razon_k ** 2)
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-M2-GEO-HOM-{k:02d}",
                exam="M2",
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_HOMOTECIA_M2",
                subtopic_name="Homotecia (Solo M2)",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.60 + (k % 4) * 0.07, 2),
                stem_text=f"A un polígono de área {area_orig} cm² se le aplica una homotecia de centro O y razón k = {razon_k}. ¿Cuál es el área de la figura homotética resultante?",
                stem_latex=rf"A' = |k|^2 \cdot A = |{razon_k}|^2 \cdot {area_orig}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{area_orig * abs(razon_k)}\text{{ cm}}^2"),
                    QuestionOption(key="B", latex_content=rf"{area_img}\text{{ cm}}^2"),
                    QuestionOption(key="C", latex_content=rf"-{area_img}\text{{ cm}}^2"),
                    QuestionOption(key="D", latex_content=rf"{area_orig + (razon_k ** 2)}\text{{ cm}}^2"),
                ],
                correct_option="B",
            )
        )

    # 3.7 GEO_TRIGONOMETRIA_M2 (Razones Trigonométricas - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        d_base = 10 * (k + 1)
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-M2-GEO-TRIG-{k:02d}",
                exam="M2",
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_TRIGONOMETRIA_M2",
                subtopic_name="Razones Trigonométricas (Solo M2)",
                cognitive_skill="MODELAR",
                difficulty=round(0.62 + (k % 4) * 0.07, 2),
                stem_text=f"Desde un punto en el suelo situado a {d_base} m de la base de una antena vertical, el ángulo de elevación hacia la cúspide es de 60°. ¿Cuál es la altura exacta H de la antena?",
                stem_latex=rf"\tan(60^\circ) = \frac{{H}}{{{d_base}}} \quad \text{{con}} \quad \tan(60^\circ) = \sqrt{{3}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{d_base}\sqrt{{3}}\text{{ m}}"),
                    QuestionOption(key="B", latex_content=rf"\frac{{{d_base}\sqrt{{3}}}}{{3}}\text{{ m}}"),
                    QuestionOption(key="C", latex_content=rf"{d_base // 2}\text{{ m}}"),
                    QuestionOption(key="D", latex_content=rf"{d_base}\sqrt{{2}}\text{{ m}}"),
                ],
                correct_option="A",
            )
        )

    # =================================================================
    # EJE 4: PROBABILIDAD Y ESTADÍSTICA
    # =================================================================

    # 4.1 PROB_TABLAS_GRAFICOS (Representación de Datos: Tablas y Gráficos)
    for k in range(1, 12):
        q_counter += 1
        f1, f2, f3 = 10 + k * 2, 15 + k, 25 - (k % 5)
        n_tot = f1 + f2 + f3
        pct_f2 = round((f2 / n_tot) * 100, 1)
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-PROB-TAB-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_TABLAS_GRAFICOS",
                subtopic_name="Representación de Datos (Tablas y Gráficos)",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.34 + (k % 5) * 0.06, 2),
                stem_text=f"En una tabla de distribución de frecuencias de tres tramos A, B y C, las frecuencias absolutas son f_A = {f1}, f_B = {f2} y f_C = {f3}. ¿Cuál es la frecuencia acumulada F_2 hasta el segundo tramo (A + B)?",
                stem_latex=rf"F_2 = f_A + f_B = {f1} + {f2} \quad (\text{{Total }} N = {n_tot})",
                options=[
                    QuestionOption(key="A", latex_content=rf"{f2}"),
                    QuestionOption(key="B", latex_content=rf"{f1 + f2}"),
                    QuestionOption(key="C", latex_content=rf"{n_tot}"),
                    QuestionOption(key="D", latex_content=rf"{f2 + f3}"),
                ],
                correct_option="B",
            )
        )

    # 4.2 PROB_TENDENCIA_CENTRAL (Medidas de Tendencia Central)
    for k in range(1, 12):
        q_counter += 1
        target_mean = 50 + k
        v1, v2, v3 = target_mean - 4, target_mean - 1, target_mean + 2
        v4 = 4 * target_mean - (v1 + v2 + v3)
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-PROB-MTC-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_TENDENCIA_CENTRAL",
                subtopic_name="Medidas de Tendencia Central",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.38 + (k % 5) * 0.06, 2),
                stem_text=f"Un estudiante obtuvo en sus tres primeras evaluaciones los puntajes {v1}, {v2} y {v3}. ¿Qué puntaje x debe obtener en la cuarta evaluación para que su promedio aritmético exacto sea {target_mean}?",
                stem_latex=rf"\bar{{x}} = \frac{{{v1} + {v2} + {v3} + x}}{{4}} = {target_mean}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{target_mean}"),
                    QuestionOption(key="B", latex_content=rf"{v4}"),
                    QuestionOption(key="C", latex_content=rf"{v4 - 2}"),
                    QuestionOption(key="D", latex_content=rf"{v4 + 4}"),
                ],
                correct_option="B",
            )
        )

    # 4.3 PROB_POSICION (Medidas de Posición: Cuartiles y Percentiles)
    for k in range(1, 12):
        q_counter += 1
        q1_val = 20 + k * 2
        q2_val = q1_val + 8
        q3_val = q2_val + 12 + (k % 4)
        ric_val = q3_val - q1_val
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-PROB-POS-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_POSICION",
                subtopic_name="Medidas de Posición (Cuartiles/Percentiles)",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.44 + (k % 5) * 0.06, 2),
                stem_text=f"En una muestra de datos ordenados, los cuartiles son Q1 = {q1_val}, mediana Q2 = {q2_val} y tercer cuartil Q3 = {q3_val}. ¿Cuál es el Rango Intercuartílico (RIC) que concentra el 50% central de los datos?",
                stem_latex=rf"\text{{RIC}} = Q_3 - Q_1 = {q3_val} - {q1_val}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{q3_val - q2_val}"),
                    QuestionOption(key="B", latex_content=rf"{ric_val}"),
                    QuestionOption(key="C", latex_content=rf"{q2_val - q1_val}"),
                    QuestionOption(key="D", latex_content=rf"{q3_val + q1_val}"),
                ],
                correct_option="B",
            )
        )

    # 4.4 PROB_REGLAS (Reglas de Probabilidad)
    for k in range(1, 13):
        q_counter += 1
        rojas = 3 + (k % 4)
        azules = 4 + (k % 5)
        verdes = 2 + (k % 3)
        tot_b = rojas + azules + verdes
        fav = rojas + verdes
        exam_t = "M1" if k <= 8 else "M2"
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-{exam_t}-PROB-REG-{k:02d}",
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_REGLAS",
                subtopic_name="Reglas de Probabilidad",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.40 + (k % 5) * 0.07, 2),
                stem_text=f"Una urna contiene {rojas} bolitas rojas, {azules} azules y {verdes} verdes, todas de igual peso y tamaño. Al extraer una bolita al azar, ¿cuál es la probabilidad de que sea roja O verde?",
                stem_latex=rf"P(R \cup V) = P(R) + P(V) = \frac{{{rojas} + {verdes}}}{{{tot_b}}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"\frac{{{rojas * verdes}}}{{{tot_b}}}"),
                    QuestionOption(key="B", latex_content=rf"\frac{{{fav}}}{{{tot_b}}}"),
                    QuestionOption(key="C", latex_content=rf"\frac{{{azules}}}{{{tot_b}}}"),
                    QuestionOption(key="D", latex_content=rf"\frac{{{rojas}}}{{{tot_b}}} \cdot \frac{{{verdes}}}{{{tot_b}}}"),
                ],
                correct_option="B",
            )
        )

    # 4.5 PROB_CONTEO_M2 (Técnicas de Conteo / Combinatoria - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        n_cand = 6 + (k % 5)
        r_sel = 3
        comb_val = math.comb(n_cand, r_sel)
        perm_val = n_cand * (n_cand - 1) * (n_cand - 2)
        bank.append(
            DEMREQuestionNode(
                node_id=f"DEMRE-M2-PROB-COMB-{k:02d}",
                exam="M2",
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_CONTEO_M2",
                subtopic_name="Técnicas de Conteo / Combinatoria (Solo M2)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.60 + (k % 4) * 0.07, 2),
                stem_text=f"De un grupo de {n_cand} especialistas se debe elegir una comisión de {r_sel} integrantes sin distinción de cargos (no importa el orden). ¿De cuántas maneras distintas se puede formar la comisión?",
                stem_latex=rf"\binom{{{n_cand}}}{{{r_sel}}} = \frac{{{n_cand}!}}{{{r_sel}!\,({n_cand}-{r_sel})!}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{comb_val}"),
                    QuestionOption(key="B", latex_content=rf"{perm_val}"),
                    QuestionOption(key="C", latex_content=rf"{n_cand * r_sel}"),
                    QuestionOption(key="D", latex_content=rf"{n_cand ** r_sel}"),
                ],
                correct_option="A",
            )
        )

    return bank


# =====================================================================
# 3. BASE VECTORIAL QDRANT EN MEMORIA CON FILTRO POR MICRO-UNIDAD
# =====================================================================

class GoPAESVectorStore:
    """
    Almacén vectorial Qdrant en memoria (`:memory:`) con indexación tanto por
    Eje Temático (`thematic_axis`) como por Micro-Unidad DEMRE (`micro_unit_id`).
    """
    COLLECTION_NAME = "gopaes_demre_micro_units_collection"
    VECTOR_DIM = 32

    def __init__(self):
        self._memory_fallback: Dict[str, DEMREQuestionNode] = {}
        self._use_qdrant = False

        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(":memory:")
                self._init_collection()
                self._use_qdrant = True
            except Exception:
                self._use_qdrant = False

    def _init_collection(self):
        collections = [c.name for c in self.client.get_collections().collections]
        if self.COLLECTION_NAME not in collections:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=qmodels.VectorParams(
                    size=self.VECTOR_DIM,
                    distance=qmodels.Distance.COSINE,
                ),
            )

    def _compute_embedding(self, text: str) -> List[float]:
        seed = abs(hash(text)) % (2**32)
        rng = np.random.default_rng(seed)
        vec = rng.standard_normal(self.VECTOR_DIM)
        norm = np.linalg.norm(vec) or 1.0
        return (vec / norm).tolist()

    def upsert_nodes(self, nodes: List[DEMREQuestionNode]):
        for node in nodes:
            self._memory_fallback[node.node_id] = node

        if self._use_qdrant:
            points = []
            for idx, node in enumerate(nodes):
                text_repr = f"{node.exam} {node.thematic_axis} {node.micro_unit_id} {node.subtopic_name} {node.stem_text} {node.stem_latex}"
                points.append(
                    qmodels.PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, node.node_id)),
                        vector=self._compute_embedding(text_repr),
                        payload=node.model_dump(),
                    )
                )
            self.client.upsert(collection_name=self.COLLECTION_NAME, points=points)

    def seed_official_demre_questions(self) -> List[DEMREQuestionNode]:
        nodes = generate_massive_demre_question_bank()
        self.upsert_nodes(nodes)
        return nodes

    def get_all_nodes(self, exam: Optional[ExamType] = None) -> List[DEMREQuestionNode]:
        all_items = list(self._memory_fallback.values())
        if exam:
            return [n for n in all_items if n.exam == exam]
        return all_items

    def query_by_micro_unit(
        self,
        micro_unit_id: MicroUnitId,
        exam: Optional[ExamType] = None,
        exclude_ids: Optional[List[str]] = None,
    ) -> List[DEMREQuestionNode]:
        excluded = set(exclude_ids or [])
        candidates = [
            n
            for n in self._memory_fallback.values()
            if n.micro_unit_id == micro_unit_id
            and (exam is None or n.exam == exam)
            and n.node_id not in excluded
        ]
        candidates.sort(key=lambda x: (x.difficulty, x.question_number))
        return candidates

    def query_by_axis_and_exam(
        self,
        exam: ExamType,
        axis: ThematicAxis,
        exclude_ids: Optional[List[str]] = None,
        diagnostic_only: bool = False,
    ) -> List[DEMREQuestionNode]:
        excluded = set(exclude_ids or [])
        results: List[DEMREQuestionNode] = []
        for node in self._memory_fallback.values():
            if node.exam == exam and node.thematic_axis == axis and node.node_id not in excluded:
                if diagnostic_only and not node.is_diagnostic_anchor:
                    continue
                results.append(node)
        results.sort(key=lambda x: (x.difficulty, x.question_number))
        return results
