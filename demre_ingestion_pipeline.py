import os
import re
import uuid
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Literal
import numpy as np
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


# =====================================================================
# 1. ESQUEMA PURO DEL NODO PREGUNTA GOPAES (SOLO DATOS EXTRAÍDOS DEL PDF)
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

AXIS_LABELS: Dict[ThematicAxis, str] = {
    "NUMEROS": "Números",
    "ALGEBRA_Y_FUNCIONES": "Álgebra y Funciones",
    "GEOMETRIA": "Geometría",
    "PROBABILIDAD_Y_ESTADISTICA": "Probabilidad y Estadística",
}

# Proporción oficial de preguntas por eje en la PAES de 65 preguntas (DEMRE):
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
    """
    Nodo atómico almacenado en Qdrant.
    Contiene exclusivamente los datos extraídos del cuadernillo y pauta oficial DEMRE:
    enunciado, alternativas en LaTeX, clave correcta y metadatos curriculares.
    """
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
# 2. MODELO DE GUÍAS DE ESTUDIO OFICIALES POR MATERIA (MÓDULO DE GUÍAS)
# =====================================================================

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
    """
    Retorna el catálogo de Guías por Materia alineadas al Temario Oficial DEMRE (M1 y M2).
    """
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


# =====================================================================
# 3. BASE DE DATOS VECTORIAL GOPAES EN MEMORIA (QDRANT)
# =====================================================================

class GoPAESVectorStore:
    """
    Gestiona la colección vectorial oficial de GoPAES en Qdrant `:memory:`.
    """
    COLLECTION_NAME = "gopaes_demre_oficial"
    VECTOR_DIM = 384

    def __init__(self):
        self.client = QdrantClient(location=":memory:")
        self._init_collection()

    def _init_collection(self):
        self.client.recreate_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=qmodels.VectorParams(
                size=self.VECTOR_DIM,
                distance=qmodels.Distance.COSINE
            )
        )

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

        results = []
        for r in records:
            node = DEMREQuestionNode(**r.payload)
            if node.node_id not in exclude_ids:
                results.append(node)
        return results

    def get_all_nodes(self, exam: Optional[ExamType] = None) -> List[DEMREQuestionNode]:
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


# =====================================================================
# 4. BANCO DE PREGUNTAS LIMPIO (SOLO ENUNCIADO + OPCIONES + CLAVE PAUTA)
# =====================================================================

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
