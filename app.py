import os
import re
import json
import uuid
import math
import hashlib
import datetime
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Literal
import numpy as np
import pandas as pd
import streamlit as st
from pydantic import BaseModel, Field

# Carga segura de python-dotenv (no falla si no está instalado en el entorno cloud)
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    def load_dotenv(*args, **kwargs):
        return False

# Carga segura de Qdrant (con fallback automático a búsqueda vectorial Coseno en NumPy si no está instalado)
try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as qmodels
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False


# =====================================================================
# 1. MODELOS CURRICULARES DEMRE, GUÍAS POR MATERIA Y VECTOR STORE
# =====================================================================

ExamType = Literal["M1", "M2"]
ThematicAxis = Literal[
    "NUMEROS",
    "ALGEBRA_Y_FUNCIONES",
    "GEOMETRIA",
    "PROBABILIDAD_Y_ESTADISTICA"
]
CognitiveSkill = Literal[
    "RESOLVER_PROBLEMAS",
    "MODELAR",
    "REPRESENTAR",
    "ARGUMENTAR"
]
ResponseState = Literal["CORRECT", "INCORRECT", "OMITTED"]
SelectionMode = Literal["ADAPTIVE", "GENERAL_STANDARD", "OFFICIAL_65"]

AXIS_LABELS: Dict[ThematicAxis, str] = {
    "NUMEROS": "Números",
    "ALGEBRA_Y_FUNCIONES": "Álgebra y Funciones",
    "GEOMETRIA": "Geometría",
    "PROBABILIDAD_Y_ESTADISTICA": "Probabilidad y Estadística",
}

ALL_AXES: List[ThematicAxis] = [
    "NUMEROS",
    "ALGEBRA_Y_FUNCIONES",
    "GEOMETRIA",
    "PROBABILIDAD_Y_ESTADISTICA",
]

OFFICIAL_SECONDS_PER_QUESTION: Dict[ExamType, int] = {
    "M1": 130,
    "M2": 150,
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


class FormulaCard(BaseModel):
    title: str
    latex_formula: str
    explanation: str


class DEMREStudyGuide(BaseModel):
    axis: ThematicAxis
    exam_scope: str
    title: str
    summary_markdown: str
    key_formulas: List[FormulaCard]
    common_demre_traps: List[str]


def get_official_study_guides() -> Dict[ThematicAxis, List[DEMREStudyGuide]]:
    return {
        "NUMEROS": [
            DEMREStudyGuide(
                axis="NUMEROS",
                exam_scope="M1 y M2",
                title="Potencias, Raíces Enésimas y Porcentajes",
                summary_markdown=(
                    "El eje de **Números** evalúa la operatoria en $\\mathbb{Z}$ y $\\mathbb{Q}$, "
                    "las propiedades de potencias de base racional y exponente entero, la descomposición "
                    "de raíces enésimas y la resolución de problemas de variaciones porcentuales sucesivas."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Potencia con Exponente Negativo",
                        latex_formula=r"\left(\frac{a}{b}\right)^{-n} = \left(\frac{b}{a}\right)^{n} = \frac{b^{n}}{a^{n}}, \quad (a, b \neq 0)",
                        explanation="Un exponente negativo invierte la fracción base; NO cambia el signo positivo/negativo de la base."
                    ),
                    FormulaCard(
                        title="Multiplicación y División de Potencias de Igual Base",
                        latex_formula=r"a^{n} \cdot a^{m} = a^{n+m} \quad ; \quad \frac{a^{n}}{a^{m}} = a^{n-m}",
                        explanation="Se conserva la base común y se suman o restan algebraicamente los exponentes."
                    ),
                    FormulaCard(
                        title="Descomposición de Raíces y Variación Porcentual Sucesiva",
                        latex_formula=r"\sqrt{a^{2} \cdot b} = |a|\sqrt{b} \quad ; \quad P_{\text{final}} = P_{0} \cdot \left(1 \pm \frac{r_1}{100}\right)\left(1 \pm \frac{r_2}{100}\right)",
                        explanation="Subir un porcentaje r% y luego bajar el mismo r% nunca vuelve al valor original: siempre resulta en una disminución neta."
                    ),
                ],
                common_demre_traps=[
                    "Confundir $(-a)^2 = a^2$ con $-a^2 = -(a^2)$ cuando el signo menos no está dentro del paréntesis.",
                    "Sumar raíces sumando directamente las cantidades subradicales: $\\sqrt{a} + \\sqrt{b} \\neq \\sqrt{a+b}$.",
                    "Asumir que un aumento del 20% seguido de un descuento del 20% deja el precio sin variación (en realidad queda en $0,96P$)."
                ]
            ),
            DEMREStudyGuide(
                axis="NUMEROS",
                exam_scope="Exclusivo M2",
                title="Logaritmos y Matemática Financiera (M2)",
                summary_markdown=(
                    "En la prueba electiva **M2**, se incorpora la relación entre potencias, raíces y **logaritmos**, "
                    "junto con problemas de cambio de base y aplicaciones de crecimiento exponencial."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Definición Fundamental del Logaritmo",
                        latex_formula=r"\log_{b}(a) = c \iff b^{c} = a \quad (b > 0, b \neq 1, a > 0)",
                        explanation="El logaritmo es el exponente c al que se debe elevar la base b para obtener el argumento a."
                    ),
                    FormulaCard(
                        title="Logaritmo de un Producto, Cociente y Potencia",
                        latex_formula=r"\log_{b}(x \cdot y) = \log_{b}(x) + \log_{b}(y) \quad ; \quad \log_{b}\left(\frac{x}{y}\right) = \log_{b}(x) - \log_{b}(y) \quad ; \quad \log_{b}(x^{k}) = k \cdot \log_{b}(x)",
                        explanation="Los exponentes del argumento bajan multiplicando al logaritmo."
                    ),
                ],
                common_demre_traps=[
                    "Reemplazar $\\log_b(x + y)$ por $\\log_b(x) + \\log_b(y)$ (no existe propiedad para el logaritmo de una suma).",
                    "Olvidar que $\\log_b(1) = 0$ y $\\log_b(b) = 1$ para cualquier base válida."
                ]
            )
        ],
        "ALGEBRA_Y_FUNCIONES": [
            DEMREStudyGuide(
                axis="ALGEBRA_Y_FUNCIONES",
                exam_scope="M1 y M2",
                title="Productos Notables, Sistemas 2x2, Inecuaciones y Función Cuadrática",
                summary_markdown=(
                    "Representa el eje de mayor peso en la PAES (**33,8% en M1**). Abarca factorización, "
                    "proporcionalidad directa e inversa, ecuaciones e inecuaciones lineales, sistemas $2 \\times 2$, "
                    "función lineal/afín y el análisis completo de la **función cuadrática**."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Productos Notables Esenciales",
                        latex_formula=r"(a \pm b)^{2} = a^{2} \pm 2ab + b^{2} \quad ; \quad (a + b)(a - b) = a^{2} - b^{2}",
                        explanation="El cuadrado de binomio siempre genera el doble producto central (2ab)."
                    ),
                    FormulaCard(
                        title="Vértice y Eje de Simetría de la Función Cuadrática",
                        latex_formula=r"f(x) = ax^{2} + bx + c \implies x_{v} = -\frac{b}{2a}, \quad V = \left(-\frac{b}{2a}, f\left(-\frac{b}{2a}\right)\right)",
                        explanation="La coordenada x_v indica dónde ocurre el extremo; la coordenada y_v = f(x_v) indica cuál es el valor mínimo (si a > 0) o máximo (si a < 0)."
                    ),
                    FormulaCard(
                        title="Fórmula General y Discriminante (M2)",
                        latex_formula=r"x = \frac{-b \pm \sqrt{b^{2} - 4ac}}{2a} \quad ; \quad \Delta = b^{2} - 4ac",
                        explanation="Si Δ > 0 corta al eje X en 2 puntos; si Δ = 0 es tangente en 1 punto; si Δ < 0 no corta al eje X."
                    ),
                ],
                common_demre_traps=[
                    "Responder el valor de $x_v = -b/(2a)$ cuando el problema pide el valor mínimo o máximo alcanzado por la función $f(x_v)$.",
                    "Olvidar invertir el signo de la desigualdad ($\\geq$ a $\\leq$) al multiplicar o dividir una inecuación por un número negativo.",
                    "En sistemas $2 \\times 2$, despejar $x$ y marcar esa alternativa cuando el enunciado pedía el valor de $(x + y)$ o $(2x - y)$."
                ]
            )
        ],
        "GEOMETRIA": [
            DEMREStudyGuide(
                axis="GEOMETRIA",
                exam_scope="M1 y M2",
                title="Teorema de Pitágoras, Áreas, Volúmenes, Vectores y Transformaciones Isométricas",
                summary_markdown=(
                    "Evalúa la resolución de problemas geométricos en 2D y 3D: triángulos, cuadriláteros, "
                    "círculos, cilindros, conos, prismas, operatoria con vectores en el plano cartesiano "
                    "y transformaciones isométricas (traslación, rotación y reflexión) además de Homotecia en M2."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Teorema de Pitágoras y Diagonal del Cuadrado",
                        latex_formula=r"c^{2} = a^{2} + b^{2} \quad ; \quad d_{\text{cuadrado}} = a\sqrt{2} \quad ; \quad h_{\text{triángulo equilátero}} = \frac{a\sqrt{3}}{2}",
                        explanation="Permite hallar lados desconocidos en triángulos rectángulos y diagonales de forma directa."
                    ),
                    FormulaCard(
                        title="Área y Perímetro del Círculo / Volumen del Cilindro y Cono",
                        latex_formula=r"A_{\odot} = \pi r^{2}, \quad P_{\odot} = 2\pi r \quad ; \quad V_{\text{cilindro}} = \pi r^{2} h, \quad V_{\text{cono}} = \frac{1}{3}\pi r^{2} h",
                        explanation="Si el radio se multiplica por un factor k, el área basal y el volumen se multiplican por k²."
                    ),
                    FormulaCard(
                        title="Traslación y Rotación en 90° respecto al Origen",
                        latex_formula=r"P(x, y) + \vec{v}(v_x, v_y) = P'(x + v_x, y + v_y) \quad ; \quad R_{(0,0)}^{90^\circ}(x, y) = (-y, x)",
                        explanation="El vector de traslación se despeja siempre como Punto Final menos Punto Inicial: v = P' - P."
                    ),
                ],
                common_demre_traps=[
                    "Usar el diámetro directamente en la fórmula $\\pi r^2$ sin dividirlo por 2 para obtener el radio.",
                    "Calcular el vector traslación restando $P_{\\text{inicial}} - P_{\\text{final}}$ en vez de $P_{\\text{final}} - P_{\\text{inicial}}$.",
                    "En variaciones de volumen del cilindro, olvidar que duplicar el radio cuadruplica el volumen ($2^2 = 4$)."
                ]
            )
        ],
        "PROBABILIDAD_Y_ESTADISTICA": [
            DEMREStudyGuide(
                axis="PROBABILIDAD_Y_ESTADISTICA",
                exam_scope="M1 y M2",
                title="Tablas de Frecuencia, Medidas de Tendencia Central, Cuartiles y Probabilidad",
                summary_markdown=(
                    "Comprende la interpretación de gráficos estadísticos, cálculo de promedio, mediana, moda, "
                    "rango, cuartiles y diagramas de cajón (Boxplot), junto con las reglas aditiva y multiplicativa "
                    "de probabilidades (con y sin reposición)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Media Aritmética (Promedio) y Suma Acumulada",
                        latex_formula=r"\bar{x} = \frac{\sum_{i=1}^{n} x_{i}}{n} \iff \sum_{i=1}^{n} x_{i} = n \cdot \bar{x}",
                        explanation="Multiplicar el promedio por la cantidad de datos permite conocer de inmediato la suma total de los elementos."
                    ),
                    FormulaCard(
                        title="Regla de Laplace y Eventos Complementarios",
                        latex_formula=r"P(A) = \frac{\text{Casos Favorables}}{\text{Casos Totales}} \quad ; \quad P(A^{c}) = 1 - P(A)",
                        explanation="Válida cuando todos los resultados del espacio muestral son equiprobables."
                    ),
                    FormulaCard(
                        title="Regla Aditiva y Multiplicativa (Sin Reposición)",
                        latex_formula=r"P(A \cup B) = P(A) + P(B) - P(A \cap B) \quad ; \quad P(A \cap B) = P(A) \cdot P(B \mid A)",
                        explanation="En extracciones sin reposición, tanto los casos favorables como el total de la urna disminuyen en la segunda extracción."
                    ),
                ],
                common_demre_traps=[
                    "Olvidar descontar 1 unidad del denominador total en la segunda extracción cuando el problema dice explícitamente 'SIN reposición'.",
                    "Calcular la mediana sin haber ordenado previamente los datos de menor a mayor.",
                    "Confundir frecuencia absoluta ($f_i$) con frecuencia acumulada ($F_i$) al leer tablas estadísticas del DEMRE."
                ]
            )
        ],
    }


def get_curated_demre_nodes() -> List[DEMREQuestionNode]:
    return [
        DEMREQuestionNode(
            node_id="11111111-1111-1111-1111-000000000001",
            admission_year=2025,
            exam="M1",
            question_number=1,
            thematic_axis="NUMEROS",
            subtopic_name="Potencias y operatoria en números racionales",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.45,
            is_diagnostic_anchor=True,
            stem_text="¿Cuál es el valor numérico de la siguiente expresión con potencias de exponente negativo?",
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
            subtopic_name="Teorema de Pitágoras y perímetro de figuras planas",
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
            subtopic_name="Propiedades de raíces cuadradas",
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
            subtopic_name="Inecuaciones lineales con una incógnita",
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
            subtopic_name="Volumen de cilindros y variación de parámetros",
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
            subtopic_name="Medidas de tendencia central y promedio",
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
            subtopic_name="Propiedades de logaritmos (Exclusivo M2)",
            cognitive_skill="RESOLVER_PROBLEMAS",
            difficulty=0.72,
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


def generate_full_65_exam_pool() -> List[DEMREQuestionNode]:
    extra_nodes: List[DEMREQuestionNode] = []
    q_counter = 13

    for k in range(1, 18):
        a = k + 1
        b = k + 3
        extra_nodes.append(
            DEMREQuestionNode(
                node_id=f"22222222-1111-1111-1111-{q_counter:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_counter,
                thematic_axis="NUMEROS",
                subtopic_name=f"Operatoria de potencias de igual base (Ítem #{k})",
                cognitive_skill="RESOLVER_PROBLEMAS",
                difficulty=round(0.35 + (k % 5) * 0.1, 2),
                stem_text="Al simplificar la siguiente expresión de potencias de base entera, ¿qué resultado se obtiene?",
                stem_latex=rf"\frac{{3^{{{a+2}}} \cdot 3^{{{b}}}}}{{3^{{{a+b}}}}}",
                options=[
                    QuestionOption(key="A", latex_content=r"9"),
                    QuestionOption(key="B", latex_content=r"3"),
                    QuestionOption(key="C", latex_content=r"27"),
                    QuestionOption(key="D", latex_content=rf"3^{{{a}}}"),
                ],
                correct_option="A",
            )
        )
        q_counter += 1

    for k in range(1, 24):
        m = k + 2
        n = 2 * k + 1
        val_x = 3
        rhs = m * val_x + n
        extra_nodes.append(
            DEMREQuestionNode(
                node_id=f"22222222-2222-1111-1111-{q_counter:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_counter,
                thematic_axis="ALGEBRA_Y_FUNCIONES",
                subtopic_name=f"Ecuaciones lineales y modelamiento (Ítem #{k})",
                cognitive_skill="MODELAR",
                difficulty=round(0.40 + (k % 5) * 0.1, 2),
                stem_text="¿Cuál es el valor de la incógnita x en la siguiente ecuación de primer grado?",
                stem_latex=rf"{m}x + {n} = {rhs}",
                options=[
                    QuestionOption(key="A", latex_content=r"2"),
                    QuestionOption(key="B", latex_content=r"3"),
                    QuestionOption(key="C", latex_content=rf"\frac{{{rhs + n}}}{{{m}}}"),
                    QuestionOption(key="D", latex_content=r"-3"),
                ],
                correct_option="B",
            )
        )
        q_counter += 1

    for k in range(1, 16):
        lado = k + 2
        area = lado * lado
        perim = 4 * lado
        extra_nodes.append(
            DEMREQuestionNode(
                node_id=f"22222222-3333-1111-1111-{q_counter:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_counter,
                thematic_axis="GEOMETRIA",
                subtopic_name=f"Perímetro y diagonal de polígonos (Ítem #{k})",
                cognitive_skill="REPRESENTAR",
                difficulty=round(0.42 + (k % 5) * 0.1, 2),
                stem_text=f"Si el área de un cuadrado es {area} cm², ¿cuál es la longitud exacta de su diagonal d?",
                stem_latex=rf"A = {area}\text{{ cm}}^2 \quad \Longrightarrow \quad d = a\sqrt{{2}}",
                options=[
                    QuestionOption(key="A", latex_content=rf"{lado}\sqrt{{2}}\text{{ cm}}"),
                    QuestionOption(key="B", latex_content=rf"{perim}\text{{ cm}}"),
                    QuestionOption(key="C", latex_content=rf"{2*lado}\text{{ cm}}"),
                    QuestionOption(key="D", latex_content=rf"{area}\sqrt{{2}}\text{{ cm}}"),
                ],
                correct_option="A",
            )
        )
        q_counter += 1

    for k in range(1, 15):
        fav = k + 1
        tot = 3 * (k + 1)
        extra_nodes.append(
            DEMREQuestionNode(
                node_id=f"22222222-4444-1111-1111-{q_counter:012d}",
                admission_year=2025,
                exam="M1",
                question_number=q_counter,
                thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
                subtopic_name=f"Regla de Laplace y eventos equiprobables (Ítem #{k})",
                cognitive_skill="ARGUMENTAR",
                difficulty=round(0.38 + (k % 5) * 0.1, 2),
                stem_text=f"En una caja hay {tot} tarjetas numeradas del 1 al {tot}. Si exactamente {fav} de ellas son premiadas, ¿cuál es la probabilidad de extraer al azar una tarjeta NO premiada?",
                stem_latex=rf"P(\text{{No premiada}}) = 1 - \frac{{{fav}}}{{{tot}}}",
                options=[
                    QuestionOption(key="A", latex_content=r"\frac{1}{3}"),
                    QuestionOption(key="B", latex_content=r"\frac{2}{3}"),
                    QuestionOption(key="C", latex_content=rf"\frac{{{fav}}}{{{tot - fav}}}"),
                    QuestionOption(key="D", latex_content=r"\frac{1}{2}"),
                ],
                correct_option="B",
            )
        )
        q_counter += 1

    return extra_nodes


class GoPAESVectorStore:
    """
    Motor Vectorial Híbrido GoPAES:
    Usa Qdrant `:memory:` cuando está disponible y cuenta con respaldo en memoria
    basado en NumPy para garantizar cero fallos de importación en cualquier servidor.
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
        nodes = get_curated_demre_nodes() + generate_full_65_exam_pool()
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
                limit=120,
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
                limit=200,
                with_payload=True
            )
            return [DEMREQuestionNode(**r.payload) for r in records]

        if exam:
            return [n for n in self._fallback_nodes if n.exam == exam]
        return list(self._fallback_nodes)


# =====================================================================
# 2. SISTEMA DE PERFILES PERSISTENTES, MOTOR ADAPTATIVO Y COACH LLM
# =====================================================================

class AxisMasteryState(BaseModel):
    axis: ThematicAxis
    mastery_score: float = 0.50
    knowledge_gap_index: float = 0.0
    conceptual_error_index: float = 0.0
    correct_count: int = 0
    incorrect_count: int = 0
    omitted_count: int = 0
    total_seen: int = 0

    @property
    def net_accuracy(self) -> float:
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
    STORAGE_PATH = Path("./storage/gopaes_profiles.json")

    @classmethod
    def _ensure_storage(cls) -> Dict[str, dict]:
        try:
            cls.STORAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
            if not cls.STORAGE_PATH.exists():
                cls.STORAGE_PATH.write_text("{}", encoding="utf-8")
                return {}
            return json.loads(cls.STORAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return st.session_state.get("_memory_profiles", {})

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
        st.session_state["_memory_profiles"] = data
        try:
            cls.STORAGE_PATH.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
        except Exception:
            pass


class GoPAESAdaptiveEngine:
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

        for axis, st_ax in self.axes_state.items():
            deficit = 1.0 - st_ax.mastery_score
            priority = (
                (deficit * 0.50)
                + (st_ax.conceptual_error_index * 0.35)
                + (st_ax.knowledge_gap_index * 0.30)
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
        st_ax = self.axes_state[axis]
        old_m = st_ax.mastery_score
        st_ax.total_seen += 1

        expected_p = 1.0 / (1.0 + math.exp(-3.5 * (old_m - question.difficulty)))
        base_lr = 0.16

        if selected_option is None or selected_option == "OMIT":
            state: ResponseState = "OMITTED"
            st_ax.omitted_count += 1
            st_ax.knowledge_gap_index = min(1.0, round(st_ax.knowledge_gap_index + 0.25, 3))
            delta = - (base_lr * 0.45) * expected_p
            reason = (
                "🏳️ OMISIÓN ('Dejar en blanco'): Se registra Vacío de Conocimiento (+0.25 Gap) "
                "sin castigar tu Precisión Neta."
            )
        elif selected_option == question.correct_option:
            state = "CORRECT"
            st_ax.correct_count += 1
            st_ax.knowledge_gap_index = max(0.0, round(st_ax.knowledge_gap_index - 0.15, 3))
            st_ax.conceptual_error_index = max(0.0, round(st_ax.conceptual_error_index - 0.15, 3))
            delta = base_lr * (1.15 - expected_p)
            reason = "✅ RESPUESTA CORRECTA: Sube el dominio del eje en tu perfil GoPAES."
        else:
            state = "INCORRECT"
            st_ax.incorrect_count += 1
            st_ax.conceptual_error_index = min(1.0, round(st_ax.conceptual_error_index + 0.35, 3))
            delta = - (base_lr * 1.25) * expected_p
            reason = (
                f"❌ ERROR CONCEPTUAL (Marcaste {selected_option}): Penalización en dominio "
                "y alerta de distractor (+0.35 Error Index)."
            )

        new_m = max(0.08, min(0.98, round(old_m + delta, 4)))
        st_ax.mastery_score = new_m

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

    def build_exam_question_queue(
        self,
        vector_store: GoPAESVectorStore,
        exam: ExamType,
        num_questions: int,
        mode: SelectionMode,
        asked_ids: List[str],
        focus_axis: Optional[ThematicAxis] = None
    ) -> List[DEMREQuestionNode]:
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


class GoPAESLLMCoach:
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
        secret_gemini = None
        secret_openai = None
        secret_provider = None
        try:
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
                return "openai", manual_clean, "Ingresada en barra lateral (OpenAI)"
            if manual_clean.startswith("AIza"):
                return "gemini", manual_clean, "Ingresada en barra lateral (Gemini)"
            return provider, manual_clean, "Ingresada en barra lateral"

        if provider == "gemini":
            if secret_gemini:
                return "gemini", secret_gemini, "Streamlit Secrets (GEMINI_API_KEY)"
            if env_gemini:
                return "gemini", env_gemini, "Archivo .env (GEMINI_API_KEY)"
            if secret_openai or env_openai:
                return "openai", (secret_openai or env_openai), "Fallback a OPENAI_API_KEY"
        else:
            if secret_openai:
                return "openai", secret_openai, "Streamlit Secrets (OPENAI_API_KEY)"
            if env_openai:
                return "openai", env_openai, "Archivo .env (OPENAI_API_KEY)"
            if secret_gemini or env_gemini:
                return "gemini", (secret_gemini or env_gemini), "Fallback a GEMINI_API_KEY"

        return provider, None, "Sin clave configurada"

    @classmethod
    def validate_key_format(cls, provider: str, api_key: Optional[str]) -> Tuple[bool, str]:
        if not api_key:
            return False, "No se detectó API Key. Pégala arriba o en Settings -> Secrets."

        if provider == "gemini":
            if api_key.startswith("AQ."):
                return (
                    False,
                    "La clave ingresada comienza con `AQ.` (token OAuth), no es una API Key de Gemini. "
                    "Crea una clave gratuita que empiece con **`AIzaSy...`** en https://aistudio.google.com/apikey"
                )
            if not api_key.startswith("AIza"):
                return (
                    False,
                    f"El formato `{api_key[:6]}...` no corresponde a Google AI Studio (`AIzaSy...`)."
                )
        elif provider == "openai":
            if not api_key.startswith("sk-"):
                return (
                    False,
                    f"El formato `{api_key[:6]}...` no corresponde a OpenAI (`sk-...`)."
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

        if provider == "gemini":
            ok, text_or_err, used_model = cls._call_gemini_rest(
                api_key=api_key,  # type: ignore
                system_prompt="Responde en 1 línea.",
                user_prompt="Di 'Conexión GoPAES exitosa'."
            )
            if ok:
                return True, f"✅ Conectado con **{used_model}** ({source})."
            return False, f"❌ Error Gemini: {text_or_err}"
        else:
            ok, text_or_err = cls._call_openai_rest(
                api_key=api_key,  # type: ignore
                system_prompt="Responde en 1 línea.",
                user_prompt="Di 'Conexión GoPAES exitosa'."
            )
            if ok:
                return True, f"✅ Conectado con **gpt-4o-mini** ({source})."
            return False, f"❌ Error OpenAI: {text_or_err}"

    @classmethod
    def _call_gemini_rest(
        cls, api_key: str, system_prompt: str, user_prompt: str
    ) -> Tuple[bool, str, str]:
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
                "El estudiante decidió DEJAR EN BLANCO (Omitir) la pregunta para no adivinar al azar."
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
                f"1. **Diagnóstico del Error Conceptual**: Deduce y explica qué error algebraico o conceptual llevó al alumno a obtener el distractor {selected_option}) (${chosen_latex}$).\n"
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
