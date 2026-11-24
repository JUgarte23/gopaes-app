import math
import uuid
import random
import hashlib
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

def _fmt_clp(amount: int) -> str:
    """Formatea montos en pesos chilenos con separador de miles (ej: 25200 -> 25.200)."""
    return f"{amount:,}".replace(",", ".")


def _make_shuffled_options(
    node_id: str,
    correct_latex: str,
    distractor_pool: List[str],
) -> tuple[List[QuestionOption], Literal["A", "B", "C", "D"]]:
    """
    Construye 4 alternativas garantizadas sin duplicados y las baraja de forma
    determinista según `node_id` para que las claves correctas se distribuyan
    equilibradamente entre A, B, C y D.
    """
    clean_correct = correct_latex.strip()
    unique_distractors: List[str] = []
    seen = {clean_correct}
    for cand in distractor_pool:
        c = cand.strip()
        if c and c not in seen:
            seen.add(c)
            unique_distractors.append(c)
        if len(unique_distractors) == 3:
            break

    # Respaldo defensivo en caso extremo
    fallback_idx = 1
    while len(unique_distractors) < 3:
        extra = rf"{clean_correct} + {fallback_idx}"
        if extra not in seen:
            seen.add(extra)
            unique_distractors.append(extra)
        fallback_idx += 1

    items = [(clean_correct, True)] + [(d, False) for d in unique_distractors]
    seed_int = int(hashlib.sha256(node_id.encode("utf-8")).hexdigest()[:12], 16)
    rng = random.Random(seed_int)
    rng.shuffle(items)

    keys: List[Literal["A", "B", "C", "D"]] = ["A", "B", "C", "D"]
    options: List[QuestionOption] = []
    correct_key: Literal["A", "B", "C", "D"] = "A"
    for idx, (latex_val, is_correct) in enumerate(items):
        k = keys[idx]
        options.append(QuestionOption(key=k, latex_content=latex_val))
        if is_correct:
            correct_key = k

    return options, correct_key


def get_curated_demre_nodes() -> List[DEMREQuestionNode]:
    """
    Semillas ancla de calibración diagnóstica (cubren Números, Álgebra, Geometría y Probabilidad).
    """
    raw_anchors = [
        (
            "DEMRE-M1-ANCHOR-01", "M1", 1, "NUMEROS", "NUM_CONJUNTOS",
            "Conjuntos Numéricos (Enteros y Racionales)", "RESOLVER_PROBLEMAS", 0.40,
            "¿Cuál es el valor exacto de la siguiente expresión numérica con números racionales y potencias?",
            r"\frac{\left(-\frac{1}{2}\right)^2 - \frac{3}{4}}{1 - \frac{1}{2}}",
            r"-1", [r"-\frac{1}{2}", r"\frac{1}{2}", r"1"],
        ),
        (
            "DEMRE-M1-ANCHOR-02", "M1", 18, "ALGEBRA_Y_FUNCIONES", "ALG_FUNCION_CUADRATICA",
            "Función Cuadrática", "MODELAR", 0.55,
            "La altura h(t), en metros, de un proyectil a los t segundos está modelada por la función cuadrática adjunta. ¿Cuál es la altura máxima que alcanza?",
            r"h(t) = -5t^2 + 20t + 15",
            r"35\text{ m}", [r"15\text{ m}", r"20\text{ m}", r"40\text{ m}"],
        ),
        (
            "DEMRE-M1-ANCHOR-03", "M1", 42, "GEOMETRIA", "GEO_PITAGORAS",
            "Teorema de Pitágoras", "REPRESENTAR", 0.45,
            "En un triángulo rectángulo ABC, recto en C, los catetos miden AC = 6 cm y BC = 8 cm. ¿Cuánto mide la hipotenusa AB?",
            r"AC = 6\text{ cm}, \quad BC = 8\text{ cm}, \quad \angle ACB = 90^\circ",
            r"10\text{ cm}", [r"12\text{ cm}", r"14\text{ cm}", r"\sqrt{28}\text{ cm}"],
        ),
        (
            "DEMRE-M1-ANCHOR-04", "M1", 55, "PROBABILIDAD_Y_ESTADISTICA", "PROB_POSICION",
            "Medidas de Posición (Cuartiles/Percentiles)", "ARGUMENTAR", 0.50,
            "En el diagrama de cajón de los puntajes de un curso, el primer cuartil es Q1 = 520 y el tercer cuartil es Q3 = 680. ¿Cuál es el rango intercuartílico (RIC)?",
            r"Q_1 = 520, \quad Q_3 = 680",
            r"160", [r"80", r"600", r"1\,200"],
        ),
    ]

    nodes: List[DEMREQuestionNode] = []
    for (nid, exam, qnum, axis, muid, sub, skill, diff, stem, latex, corr, dists) in raw_anchors:
        opts, ckey = _make_shuffled_options(nid, corr, dists)
        nodes.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam,  # type: ignore
                question_number=qnum,
                thematic_axis=axis,  # type: ignore
                micro_unit_id=muid,  # type: ignore
                subtopic_name=sub,
                cognitive_skill=skill,  # type: ignore
                difficulty=diff,
                is_diagnostic_anchor=True,
                stem_text=stem,
                stem_latex=latex,
                options=opts,
                correct_option=ckey,
            )
        )
    return nodes


def generate_massive_demre_question_bank() -> List[DEMREQuestionNode]:
    """
    Genera 240 reactivos calibrados según el temario oficial DEMRE, distribuidos
    en las 20 Micro-Unidades de M1 y M2, con alternativas sin duplicados y claves
    correctas balanceadas equitativamente entre A, B, C y D.
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
        nid = f"DEMRE-M1-NUM-CONJ-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{res_num}",
            [rf"{-(a ** 2) - b}", rf"{res_num + 2}", rf"{(a ** 2) + b}", rf"{res_num - 2}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam="M1",
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_CONJUNTOS",
                subtopic_name="Conjuntos Numéricos (Enteros y Racionales)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.32 + (k % 5) * 0.08, 2),
                stem_text="En el conjunto de los números enteros y racionales, ¿cuál es el resultado de evaluar la siguiente expresión con potencias?",
                stem_latex=rf"(-{a})^2 - \frac{{{b * 3}}}{{3}} + (-1)^{{2024}} - 1",
                options=opts,
                correct_option=ckey,
            )
        )

    # 1.1b NUM_CONJUNTOS (M2: Reales, Irracionales y Logaritmos)
    for k in range(1, 11):
        q_counter += 1
        base = 2 if k % 2 == 0 else 3
        exp1 = (k % 4) + 3  # >= 3 para evitar colisiones con exp2 = 2
        exp2 = 2
        val = exp1 * 2 - exp2
        nid = f"DEMRE-M2-NUM-CONJ-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{val}",
            [rf"{exp1 - exp2}", rf"{val + exp2}", rf"{(exp1 ** 2) - exp2}", rf"{val + 1}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam="M2",
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_CONJUNTOS",
                subtopic_name="Conjuntos Numéricos (Reales y Logaritmos M2)",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.55 + (k % 4) * 0.08, 2),
                stem_text="En el conjunto de los números reales (PAES M2), ¿cuál es el valor exacto de la siguiente expresión logarítmica?",
                stem_latex=rf"\log_{{{base}}}\left({base}^{{{exp1}}}\right)^2 - \log_{{{base}}}\left({base}^{{{exp2}}}\right)",
                options=opts,
                correct_option=ckey,
            )
        )

    # 1.2 NUM_RAZONES_PROP (M1 y M2: Razones y Proporciones)
    ratio_pairs = [
        (2, 3), (3, 4), (2, 5), (3, 5), (4, 5), (3, 7),
        (2, 7), (5, 7), (4, 7), (5, 6), (3, 8), (5, 8),
    ]
    for k in range(1, 13):
        q_counter += 1
        r1, r2 = ratio_pairs[k - 1]
        mult = (k + 2) * 5
        total = (r1 + r2) * mult
        part_a = r1 * mult
        part_b = r2 * mult
        exam_t: ExamType = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-NUM-RAZ-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{part_b}",
            [rf"{part_a}", rf"{part_b - part_a}", rf"{total // 2}", rf"{part_b + mult}", rf"{mult}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_RAZONES_PROP",
                subtopic_name="Razones y Proporciones",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.07, 2),
                stem_text=f"Los aportes de dos socios están en la razón {r1} : {r2}. Si la suma de ambos aportes es {total}, ¿cuál es el valor correspondiente a la parte mayor?",
                stem_latex=rf"\frac{{A}}{{B}} = \frac{{{r1}}}{{{r2}}}, \qquad A + B = {total}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 1.3 NUM_PORCENTAJES (M1 y M2: Porcentajes y Variación Porcentual)
    pct_pairs = [
        (20, 10), (30, 20), (10, 20), (20, 20), (40, 25), (25, 20),
        (50, 20), (10, 10), (20, 30), (30, 10), (25, 10), (40, 10),
    ]
    for k in range(1, 13):
        q_counter += 1
        p_up, p_down = pct_pairs[k - 1]
        base_price = 10000 * ((k % 5) + 2)
        final_price = int(round(base_price * (1 + p_up / 100.0) * (1 - p_down / 100.0)))
        naive_price = int(round(base_price * (1 + (p_up - p_down) / 100.0)))
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-NUM-PCT-{k:02d}"
        base_str = _fmt_clp(base_price)
        opts, ckey = _make_shuffled_options(
            nid,
            rf"\$\,{_fmt_clp(final_price)}",
            [
                rf"\$\,{_fmt_clp(naive_price)}",
                rf"\$\,{_fmt_clp(base_price)}",
                rf"\$\,{_fmt_clp(final_price + 1000)}",
                rf"\$\,{_fmt_clp(final_price - 1000)}",
                rf"\$\,{_fmt_clp(int(base_price * (1 + p_up / 100.0)))}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="NUMEROS",
                micro_unit_id="NUM_PORCENTAJES",
                subtopic_name="Porcentajes",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.38 + (k % 5) * 0.07, 2),
                stem_text=(
                    f"Un artículo cuesta originalmente ${base_str}. Primero sube su precio en un {p_up}% "
                    f"y luego, sobre el nuevo valor, se aplica un descuento del {p_down}%. ¿Cuál es el precio final?"
                ),
                stem_latex=rf"P_0 = \$\,{base_str}, \qquad \Delta_1 = +{p_up}\%, \qquad \Delta_2 = -{p_down}\%",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-ALG-EXP-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{2 * a_val}",
            [rf"2x", rf"0", rf"x + {a_val}", rf"{a_val}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_EXPRESIONES",
                subtopic_name="Expresiones Algebraicas",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.36 + (k % 5) * 0.08, 2),
                stem_text=f"Para todo número real x distinto de {a_val}, ¿a qué expresión equivale la siguiente operación algebraica al factorizar y simplificar?",
                stem_latex=rf"\frac{{x^2 - {a_val ** 2}}}{{x - {a_val}}} - (x - {a_val})",
                options=opts,
                correct_option=ckey,
            )
        )

    # 2.2 ALG_ECUACIONES_1G (Ecuaciones e Inecuaciones de 1° Grado) — Matemáticamente exacta
    for k in range(1, 13):
        q_counter += 1
        m = (k % 4) + 2       # 2, 3, 4, 5
        sol = k + 3           # solución entera exacta >= 4
        c = k + 2             # término constante >= 3
        rhs = m * sol - c     # -m*x + c <= -rhs  <=>  -m*x <= -(rhs + c) = -m*sol  <=>  x >= sol
        exam_t = "M1" if k <= 9 else "M2"
        nid = f"DEMRE-{exam_t}-ALG-EC1-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"x \geq {sol}",
            [rf"x \leq {sol}", rf"x \geq -{sol}", rf"x \leq -{sol}", rf"x \geq {sol + 1}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_ECUACIONES_1G",
                subtopic_name="Ecuaciones e Inecuaciones de 1° Grado",
                cognitive_skill="MODELAR",
                difficulty=round(0.34 + (k % 5) * 0.07, 2),
                stem_text="¿Cuál es el conjunto solución de la siguiente inecuación lineal de primer grado en los números reales?",
                stem_latex=rf"-{m}x + {c} \leq -{rhs}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 2.3 ALG_SISTEMAS_2X2 (Sistemas de Ecuaciones Lineales 2x2)
    for k in range(1, 13):
        q_counter += 1
        x_true = k + 4
        y_true = (k % 4) + 1
        s1 = x_true + y_true
        s2 = 2 * x_true - y_true
        diff_xy = x_true - y_true
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-ALG-SIS-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{diff_xy}",
            [rf"{x_true}", rf"{y_true}", rf"{s1}", rf"{diff_xy + 2}", rf"{-diff_xy}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_SISTEMAS_2X2",
                subtopic_name="Sistemas de Ecuaciones (2x2)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.42 + (k % 5) * 0.07, 2),
                stem_text="Dado el siguiente sistema de ecuaciones lineales de 2×2, ¿cuál es el valor de (x - y)?",
                stem_latex=rf"\begin{{cases}} x + y = {s1} \\ 2x - y = {s2} \end{{cases}}",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-ALG-LIN-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"\$\,{_fmt_clp(total_cobro)}",
            [
                rf"\$\,{_fmt_clp(fijo * unidades + var)}",
                rf"\$\,{_fmt_clp(var * unidades)}",
                rf"\$\,{_fmt_clp(total_cobro + fijo)}",
                rf"\$\,{_fmt_clp(total_cobro - var)}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_FUNCION_LINEAL",
                subtopic_name="Función Lineal y Afín",
                cognitive_skill="MODELAR",
                difficulty=round(0.35 + (k % 5) * 0.06, 2),
                stem_text=(
                    f"Una empresa de reparto cobra un cargo fijo de ${_fmt_clp(fijo)} más ${_fmt_clp(var)} "
                    f"por cada kilómetro recorrido x. Si un envío recorrió {unidades} km, ¿cuál es el cobro total C({unidades})?"
                ),
                stem_latex=rf"C(x) = {var}x + {fijo}, \qquad x = {unidades}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 2.5 ALG_FUNCION_CUADRATICA (Función Cuadrática)
    for k in range(1, 13):
        q_counter += 1
        h_v = (k % 5) + 1
        k_v = 10 + k * 2
        c_coef = (h_v ** 2) + k_v
        exam_t = "M1" if k <= 7 else "M2"
        nid = f"DEMRE-{exam_t}-ALG-CUAD-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"({h_v},\, {k_v})",
            [rf"(-{h_v},\, {k_v})", rf"({h_v},\, {c_coef})", rf"({2 * h_v},\, {k_v})", rf"(-{h_v},\, {c_coef})"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                micro_unit_id="ALG_FUNCION_CUADRATICA",
                subtopic_name="Función Cuadrática",
                cognitive_skill="MODELAR",
                difficulty=round(0.48 + (k % 5) * 0.07, 2),
                stem_text="Considere la siguiente función cuadrática definida en los números reales. ¿Cuáles son las coordenadas (h, k) del vértice de su parábola?",
                stem_latex=rf"f(x) = x^2 - {2 * h_v}x + {c_coef}",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-GEO-2D-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{area_trap}\text{{ m}}^2",
            [
                rf"{area_trap * 2}\text{{ m}}^2",
                rf"{b_mayor * altura}\text{{ m}}^2",
                rf"{b_menor * altura}\text{{ m}}^2",
                rf"{b_mayor + b_menor + altura}\text{{ m}}^2",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_FIGURAS_2D",
                subtopic_name="Perímetro y Área de Figuras 2D",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.36 + (k % 5) * 0.07, 2),
                stem_text=f"Un terreno tiene forma de trapecio con bases paralelas de {b_mayor} m y {b_menor} m, y una altura perpendicular de {altura} m. ¿Cuál es el área del terreno?",
                stem_latex=rf"B = {b_mayor}\text{{ m}}, \quad b = {b_menor}\text{{ m}}, \quad h = {altura}\text{{ m}}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 3.2 GEO_CUERPOS_3D (Cuerpos Geométricos 3D: Cilindros)
    for k in range(1, 12):
        q_counter += 1
        r_cil = (k % 4) + 3  # 3, 4, 5, 6 (evita r=2 donde 2*r*h == r^2*h)
        h_cil = k + 5
        vol_pi = (r_cil ** 2) * h_cil
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-GEO-3D-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{vol_pi}\pi\text{{ m}}^3",
            [
                rf"{2 * r_cil * h_cil}\pi\text{{ m}}^3",
                rf"{r_cil * (h_cil ** 2)}\pi\text{{ m}}^3",
                rf"{r_cil * h_cil}\pi\text{{ m}}^3",
                rf"{vol_pi + r_cil * h_cil}\pi\text{{ m}}^3",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_CUERPOS_3D",
                subtopic_name="Cuerpos Geométricos 3D",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.42 + (k % 5) * 0.07, 2),
                stem_text=f"Un estanque cilíndrico recto tiene un radio basal de {r_cil} m y una altura de {h_cil} m. ¿Cuál es su volumen exacto en términos de π?",
                stem_latex=rf"r = {r_cil}\text{{ m}}, \qquad h = {h_cil}\text{{ m}}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 3.3 GEO_ISOMETRICAS (Transformaciones Isométricas)
    for k in range(1, 12):
        q_counter += 1
        px, py = k + 2, -(k + 1)
        vx, vy = -2, k + 5
        tx, ty = px + vx, py + vy
        rx, ry = -ty, tx
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-GEO-ISO-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"({rx},\, {ry})",
            [
                rf"({tx},\, {ty})",
                rf"({-rx},\, {-ry})",
                rf"({ry},\, {rx})",
                rf"({ty},\, {-tx})",
                rf"({-tx},\, {ty})",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_ISOMETRICAS",
                subtopic_name="Transformaciones Isométricas",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.44 + (k % 4) * 0.07, 2),
                stem_text=(
                    f"Al punto P({px}, {py}) del plano cartesiano se le aplica una traslación según el vector "
                    f"v = ({vx}, {vy}) y luego una rotación de 90° en sentido antihorario respecto al origen. ¿Cuál es el punto resultante?"
                ),
                stem_latex=rf"P({px}, {py}) \xrightarrow{{T({vx}, {vy})}} P' \xrightarrow{{R_{{90^\circ}}}} P''",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-GEO-PIT-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{b_s}\text{{ m}}",
            [
                rf"{c_s - a_s}\text{{ m}}",
                rf"{a_s + c_s}\text{{ m}}",
                rf"\sqrt{{{c_s + a_s}}}\text{{ m}}",
                rf"{b_s + 2}\text{{ m}}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_PITAGORAS",
                subtopic_name="Teorema de Pitágoras",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.07, 2),
                stem_text=(
                    f"Una escalera de {c_s} metros de longitud se apoya contra un muro vertical. "
                    f"Si la base de la escalera está a {a_s} metros del muro, ¿a qué altura h del suelo toca la escalera el muro?"
                ),
                stem_latex=rf"\text{{Hipotenusa}} = {c_s}\text{{ m}}, \qquad \text{{Base}} = {a_s}\text{{ m}}",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-GEO-SEM-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{r2}\text{{ cm}}",
            [
                rf"{r1 + 3}\text{{ cm}}",
                rf"{r2 + 4}\text{{ cm}}",
                rf"{r1 * 2}\text{{ cm}}",
                rf"{r2 - 3}\text{{ cm}}",
                rf"{l2 + r1}\text{{ cm}}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_SEMEJANZA",
                subtopic_name="Semejanza y Proporcionalidad",
                cognitive_skill="MODELAR",
                difficulty=round(0.45 + (k % 5) * 0.07, 2),
                stem_text=(
                    f"Tres rectas paralelas son cortadas por dos transversales (Teorema de Thales). "
                    f"En la primera transversal los segmentos miden {l1} cm y {l2} cm. "
                    f"Si en la segunda transversal el primer segmento mide {r1} cm, ¿cuánto mide el segmento x correspondiente?"
                ),
                stem_latex=rf"\frac{{{l1}}}{{{l2}}} = \frac{{{r1}}}{{x}}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 3.6 GEO_HOMOTECIA_M2 (Homotecia - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        area_orig = (k + 2) * 4
        razon_k = -((k % 3) + 2)
        area_img = area_orig * (razon_k ** 2)
        nid = f"DEMRE-M2-GEO-HOM-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{area_img}\text{{ cm}}^2",
            [
                rf"{area_orig * abs(razon_k)}\text{{ cm}}^2",
                rf"-{area_img}\text{{ cm}}^2",
                rf"{area_orig + (razon_k ** 2)}\text{{ cm}}^2",
                rf"{area_img // 2}\text{{ cm}}^2",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam="M2",
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_HOMOTECIA_M2",
                subtopic_name="Homotecia (Solo M2)",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.60 + (k % 4) * 0.07, 2),
                stem_text=f"A un polígono de área {area_orig} cm² se le aplica una homotecia de centro O y razón k = {razon_k}. ¿Cuál es el área de la figura homotética resultante?",
                stem_latex=rf"A = {area_orig}\text{{ cm}}^2, \qquad k = {razon_k}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 3.7 GEO_TRIGONOMETRIA_M2 (Razones Trigonométricas - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        d_base = 10 * (k + 1)
        nid = f"DEMRE-M2-GEO-TRIG-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{d_base}\sqrt{{3}}\text{{ m}}",
            [
                rf"\frac{{{d_base}\sqrt{{3}}}}{{3}}\text{{ m}}",
                rf"{d_base // 2}\text{{ m}}",
                rf"{d_base}\sqrt{{2}}\text{{ m}}",
                rf"{d_base}\text{{ m}}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam="M2",
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                micro_unit_id="GEO_TRIGONOMETRIA_M2",
                subtopic_name="Razones Trigonométricas (Solo M2)",
                cognitive_skill="MODELAR",
                difficulty=round(0.62 + (k % 4) * 0.07, 2),
                stem_text=f"Desde un punto en el suelo situado a {d_base} m de la base de una antena vertical, el ángulo de elevación hacia la cúspide es de 60°. ¿Cuál es la altura exacta H de la antena?",
                stem_latex=rf"d = {d_base}\text{{ m}}, \qquad \alpha = 60^\circ",
                options=opts,
                correct_option=ckey,
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
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-PROB-TAB-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{f1 + f2}",
            [rf"{f2}", rf"{n_tot}", rf"{f2 + f3}", rf"{f1 + f3}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_TABLAS_GRAFICOS",
                subtopic_name="Representación de Datos (Tablas y Gráficos)",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.34 + (k % 5) * 0.06, 2),
                stem_text=(
                    f"En una tabla de distribución de frecuencias de tres tramos A, B y C, las frecuencias absolutas "
                    f"son f_A = {f1}, f_B = {f2} y f_C = {f3}. ¿Cuál es la frecuencia acumulada F₂ hasta el segundo tramo?"
                ),
                stem_latex=rf"f_A = {f1}, \quad f_B = {f2}, \quad f_C = {f3}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 4.2 PROB_TENDENCIA_CENTRAL (Medidas de Tendencia Central)
    for k in range(1, 12):
        q_counter += 1
        target_mean = 50 + k
        v1, v2, v3 = target_mean - 4, target_mean - 1, target_mean + 2
        v4 = 4 * target_mean - (v1 + v2 + v3)
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-PROB-MTC-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{v4}",
            [rf"{target_mean}", rf"{v4 - 2}", rf"{v4 + 4}", rf"{v4 - 4}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_TENDENCIA_CENTRAL",
                subtopic_name="Medidas de Tendencia Central",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.38 + (k % 5) * 0.06, 2),
                stem_text=(
                    f"Un estudiante obtuvo en sus tres primeras evaluaciones los puntajes {v1}, {v2} y {v3}. "
                    f"¿Qué puntaje x debe obtener en la cuarta evaluación para que su promedio aritmético exacto sea {target_mean}?"
                ),
                stem_latex=rf"\bar{{x}} = \frac{{{v1} + {v2} + {v3} + x}}{{4}} = {target_mean}",
                options=opts,
                correct_option=ckey,
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
        nid = f"DEMRE-{exam_t}-PROB-POS-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{ric_val}",
            [rf"{q3_val - q2_val}", rf"{q2_val - q1_val}", rf"{q3_val + q1_val}", rf"{ric_val + 4}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_POSICION",
                subtopic_name="Medidas de Posición (Cuartiles/Percentiles)",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.44 + (k % 5) * 0.06, 2),
                stem_text=(
                    f"En una muestra de datos ordenados, los cuartiles son Q₁ = {q1_val}, mediana Q₂ = {q2_val} "
                    f"y tercer cuartil Q₃ = {q3_val}. ¿Cuál es el Rango Intercuartílico (RIC)?"
                ),
                stem_latex=rf"Q_1 = {q1_val}, \quad Q_2 = {q2_val}, \quad Q_3 = {q3_val}",
                options=opts,
                correct_option=ckey,
            )
        )

    # 4.4 PROB_REGLAS (Reglas de Probabilidad)
    for k in range(1, 13):
        q_counter += 1
        rojas = 3 + (k % 4)
        azules = 5 + (k % 5)
        verdes = 2 + (k % 3)
        tot_b = rojas + azules + verdes
        fav = rojas + verdes
        exam_t = "M1" if k <= 8 else "M2"
        nid = f"DEMRE-{exam_t}-PROB-REG-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"\frac{{{fav}}}{{{tot_b}}}",
            [
                rf"\frac{{{azules}}}{{{tot_b}}}",
                rf"\frac{{{rojas}}}{{{tot_b}}} \cdot \frac{{{verdes}}}{{{tot_b}}}",
                rf"\frac{{{rojas}}}{{{tot_b}}}",
                rf"\frac{{{verdes}}}{{{tot_b}}}",
                rf"\frac{{{abs(fav - 1)}}}{{{tot_b}}}",
            ],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam=exam_t,
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_REGLAS",
                subtopic_name="Reglas de Probabilidad",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.40 + (k % 5) * 0.07, 2),
                stem_text=(
                    f"Una urna contiene {rojas} bolitas rojas, {azules} azules y {verdes} verdes, todas de igual peso y tamaño. "
                    "Al extraer una bolita al azar, ¿cuál es la probabilidad de que sea roja o verde?"
                ),
                stem_latex=rf"R = {rojas}, \quad A = {azules}, \quad V = {verdes} \quad (N = {tot_b})",
                options=opts,
                correct_option=ckey,
            )
        )

    # 4.5 PROB_CONTEO_M2 (Técnicas de Conteo / Combinatoria - Exclusivo M2)
    for k in range(1, 11):
        q_counter += 1
        n_cand = 6 + (k % 5)
        r_sel = 3
        comb_val = math.comb(n_cand, r_sel)
        perm_val = n_cand * (n_cand - 1) * (n_cand - 2)
        nid = f"DEMRE-M2-PROB-COMB-{k:02d}"
        opts, ckey = _make_shuffled_options(
            nid,
            rf"{comb_val}",
            [rf"{perm_val}", rf"{n_cand * r_sel}", rf"{n_cand ** r_sel}", rf"{comb_val + r_sel}"],
        )
        bank.append(
            DEMREQuestionNode(
                node_id=nid,
                exam="M2",
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                micro_unit_id="PROB_CONTEO_M2",
                subtopic_name="Técnicas de Conteo / Combinatoria (Solo M2)",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.60 + (k % 4) * 0.07, 2),
                stem_text=(
                    f"De un grupo de {n_cand} especialistas se debe elegir una comisión de {r_sel} integrantes "
                    "sin distinción de cargos (no importa el orden). ¿De cuántas maneras distintas se puede formar la comisión?"
                ),
                stem_latex=rf"n = {n_cand}\text{{ especialistas}}, \qquad k = {r_sel}\text{{ integrantes}}",
                options=opts,
                correct_option=ckey,
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
