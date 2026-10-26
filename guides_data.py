from typing import List, Dict, Literal
from pydantic import BaseModel

ExamType = Literal["M1", "M2"]
ThematicAxis = Literal[
    "NUMEROS",
    "ALGEBRA_Y_FUNCIONES",
    "GEOMETRIA",
    "PROBABILIDAD_Y_ESTADISTICA",
]


class FormulaCard(BaseModel):
    title: str
    latex_formula: str
    explanation: str


class InterleavedExercise(BaseModel):
    exercise_id: str
    title: str
    stem_text: str
    stem_latex: str
    options: Dict[str, str]
    correct_option: str
    step_by_step_solution: List[str]


class DEMREExhaustiveGuide(BaseModel):
    guide_id: str
    exam: ExamType
    axis: ThematicAxis
    unit_title: str
    short_description: str
    subtopic_filter_keyword: str
    demre_syllabus_reference: str
    theoretical_framework_md: str
    key_formulas: List[FormulaCard]
    resolution_recipe_title: str
    resolution_recipe_steps: List[str]
    common_demre_traps: List[str]
    interleaved_exercises: List[InterleavedExercise]


def get_exhaustive_guides_by_exam(exam: ExamType) -> Dict[ThematicAxis, List[DEMREExhaustiveGuide]]:
    """
    Retorna el catálogo exhaustivo de Guías por Materia separando estrictamente
    el currículo oficial PAES M1 (Obligatoria) del currículo PAES M2 (Electiva Científica).
    Cada Eje contiene múltiples Guías (Unidades) seleccionables desde un Menú Intermedio.
    """
    if exam == "M1":
        return _get_m1_guides()
    return _get_m2_guides()


# =====================================================================
# CATÁLOGO EXHAUSTIVO PAES M1 (COMPETENCIA MATEMÁTICA 1 - OBLIGATORIA)
# =====================================================================
def _get_m1_guides() -> Dict[ThematicAxis, List[DEMREExhaustiveGuide]]:
    return {
        "NUMEROS": [
            DEMREExhaustiveGuide(
                guide_id="M1-NUM-01",
                exam="M1",
                axis="NUMEROS",
                unit_title="Guía 1: Números Enteros (ℤ) y Racionales (ℚ)",
                short_description="Jerarquía de operaciones PAPOMUDAS, transformación de decimales periódicos/semiperiódicos y operatoria fraccionaria.",
                subtopic_filter_keyword="racional",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Números • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "En la **PAES M1**, esta unidad evalúa el dominio de la jerarquía de las operaciones en $\\mathbb{Z}$ y $\\mathbb{Q}$, "
                    "la equivalencia entre números decimales (finitos, periódicos y semiperiódicos) y fracciones irreductibles, "
                    "así como problemas de orden y ubicación en la recta numérica.\n\n"
                    "1. **Jerarquía PAPOMUDAS**: Paréntesis (de adentro hacia afuera), Potencias, Multiplicación y División "
                    "(de izquierda a derecha según aparezcan) y finalmente Adición y Sustracción.\n"
                    "2. **Inverso Aditivo vs. Inverso Multiplicativo (Recíproco)**: El inverso aditivo (opuesto) de $a$ es $-a$ (suman $0$). "
                    "El inverso multiplicativo (recíproco) de $\\frac{a}{b}$ (con $a,b \\neq 0$) es $\\frac{b}{a}$ (su producto es $1$)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Transformación de Decimal Periódico y Semiperiódico a Fracción",
                        latex_formula=r"0,\overline{ab} = \frac{ab}{99} \quad ; \quad 0,c\overline{ab} = \frac{cab - c}{990}",
                        explanation="Se escribe el número completo sin coma menos la parte no periódica, dividido por tantos 9 como cifras tenga el período y tantos 0 como cifras tenga el anteperíodo."
                    ),
                    FormulaCard(
                        title="División de Fracciones y Fracciones Compuestas",
                        latex_formula=r"\frac{a}{b} : \frac{c}{d} = \frac{\frac{a}{b}}{\frac{c}{d}} = \frac{a \cdot d}{b \cdot c} \quad (b, c, d \neq 0)",
                        explanation="Dividir por una fracción equivale a multiplicar por su inverso multiplicativo (recíproco)."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Operatoria en ℤ y ℚ",
                resolution_recipe_steps=[
                    "Paso 1 (Estandarización a Fracción): Convierte todos los decimales periódicos, semiperiódicos o números mixtos a fracción irreductible antes de operar.",
                    "Paso 2 (Resolución de Paréntesis Internos): Calcula el mínimo común múltiplo (m.c.m.) dentro de cada paréntesis.",
                    "Paso 3 (Inversión de Divisiones): Transforma cada división (:) en multiplicación (·) invirtiendo la fracción derecha.",
                    "Paso 4 (Simplificación Cruzada): Simplifica numeradores con denominadores antes de multiplicar para evitar números grandes."
                ],
                common_demre_traps=[
                    "Confundir el 'inverso aditivo' (cambiar signo) con el 'inverso multiplicativo' (invertir la fracción).",
                    "Transformar $1,\\overline{3}$ como $\\frac{13}{90}$ en lugar de $\\frac{13 - 1}{9} = \\frac{12}{9} = \\frac{4}{3}$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-01A",
                        title="Ejemplo Guiado: Operatoria Racional con Decimales Periódicos",
                        stem_text="¿Cuál es el valor exacto de la siguiente expresión numérica?",
                        stem_latex=r"0,\overline{3} + \frac{1}{2} : \frac{3}{4}",
                        options={"A": r"1", "B": r"\frac{10}{9}", "C": r"\frac{5}{6}", "D": r"\frac{7}{6}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Convertimos el decimal periódico a fracción: $0,\overline{3} = \frac{3}{9} = \frac{1}{3}$.",
                            r"2. Resolvemos primero la división: $\frac{1}{2} : \frac{3}{4} = \frac{1}{2} \cdot \frac{4}{3} = \frac{2}{3}$.",
                            r"3. Sumamos: $\frac{1}{3} + \frac{2}{3} = 1$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-NUM-02",
                exam="M1",
                axis="NUMEROS",
                unit_title="Guía 2: Porcentajes y Variaciones Porcentuales Sucesivas",
                short_description="Cálculo de porcentajes, descuentos e incrementos encadenados, IVA y problemas de variación porcentual.",
                subtopic_filter_keyword="porcent",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Números • Unidad 2",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "El DEMRE incluye entre 4 y 6 preguntas de **Porcentajes** en cada prueba M1. La clave para resolverlas "
                    "con rapidez es utilizar **factores multiplicativos decimales o fraccionarios** en lugar de hacer múltiples reglas de tres.\n\n"
                    "- **Aumento porcentual del $p\\%$**: Se multiplica el valor inicial por $\\left(1 + \\frac{p}{100}\\right)$.\n"
                    "- **Descuento porcentual del $q\\%$**: Se multiplica el valor inicial por $\\left(1 - \\frac{q}{100}\\right)$."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Factor Multiplicativo de Variaciones Porcentuales Sucesivas",
                        latex_formula=r"V_{\text{final}} = V_{\text{inicial}} \cdot \left(1 \pm \frac{p_1}{100}\right) \cdot \left(1 \pm \frac{p_2}{100}\right)",
                        explanation="Permite encadenar cualquier cantidad de alzas y rebajas sucesivas en una sola multiplicación."
                    ),
                    FormulaCard(
                        title="Porcentaje de Variación Neta",
                        latex_formula=r"\%\Delta = \left(\frac{V_{\text{final}} - V_{\text{inicial}}}{V_{\text{inicial}}}\right) \cdot 100\%",
                        explanation="Siempre se divide el cambio absoluto por el valor original (la base 100%)."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Problemas de Porcentajes",
                resolution_recipe_steps=[
                    "Paso 1 (Identificación del 100%): Reconoce cuál es el valor inicial sobre el que se aplica el cambio.",
                    "Paso 2 (Conversión a Factor): Si sube 25% escribe 1,25 (o 5/4); si baja 20% escribe 0,80 (o 4/5).",
                    "Paso 3 (Multiplicación Encadenada): Multiplica todos los factores sucesivos por la cantidad inicial.",
                    "Paso 4 (Despeje Inverso): Si te dan el precio final con IVA (119%) y piden el precio sin IVA, divide por 1,19 (nunca restes el 19% del precio final)."
                ],
                common_demre_traps=[
                    "Creer que subir un 20% y luego bajar un 20% deja el precio igual (en realidad $1,20 \\cdot 0,80 = 0,96$, es decir, baja un 4%)."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-02A",
                        title="Ejemplo Guiado: Rebaja sobre Alza de Temporada",
                        stem_text="Una chaqueta de $40.000 sube un 25% y luego se le aplica un 20% de descuento sobre el nuevo precio. ¿Cuál es su precio final?",
                        stem_latex=r"P_f = 40.000 \cdot \frac{5}{4} \cdot \frac{4}{5}",
                        options={"A": r"\$40.000", "B": r"\$42.000", "C": r"\$38.000", "D": r"\$45.000"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Expresamos +25% como $\frac{5}{4}$ y -20% como $\frac{4}{5}$.",
                            r"2. Multiplicamos: $40.000 \cdot \frac{5}{4} \cdot \frac{4}{5} = \$40.000$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-NUM-03",
                exam="M1",
                axis="NUMEROS",
                unit_title="Guía 3: Potencias de Exponente Entero y Raíces Enésimas",
                short_description="Propiedades de potencias, factorización de sumas de potencias de igual base y descomposición de raíces.",
                subtopic_filter_keyword="potencia",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Números • Unidad 3",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Las preguntas de potencias y raíces evalúan la habilidad de **expresar números compuestos en bases primas** "
                    "($4=2^2, 8=2^3, 9=3^2, 27=3^3$) y descomponer cantidades subradicales.\n\n"
                    "- **Suma de potencias**: En $3^x + 3^x + 3^x = 3 \\cdot 3^x = 3^{x+1}$ se factoriza, no se usa regla de multiplicación directa."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Exponente Negativo y Potencia de una Potencia",
                        latex_formula=r"\left(\frac{a}{b}\right)^{-n} = \left(\frac{b}{a}\right)^{n} \quad ; \quad \left(a^{n}\right)^{m} = a^{n \cdot m}",
                        explanation="El signo negativo en el exponente invierte la fracción base."
                    ),
                    FormulaCard(
                        title="Descomposición de Raíces Enésimas",
                        latex_formula=r"\sqrt[n]{a^{n} \cdot b} = a\sqrt[n]{b} \quad (a, b > 0)",
                        explanation="Permite reducir raíces como √75 = 5√3 y √27 = 3√3 para poder sumarlas o restarlas."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Potencias y Raíces",
                resolution_recipe_steps=[
                    "Paso 1 (Bases Primas): Lleva todas las bases a números primos (2, 3, 5, 7).",
                    "Paso 2 (Exponentes Negativos): Invierte las fracciones con exponente negativo.",
                    "Paso 3 (Factor Común): En sumas o restas de potencias, factoriza por la potencia de menor exponente.",
                    "Paso 4 (Cuadrados Perfectos): En raíces, busca el mayor cuadrado perfecto que divida a la cantidad subradical."
                ],
                common_demre_traps=[
                    "Evaluar $(-2)^4 = -16$ en vez de $+16$, o evaluar $-2^4 = +16$ en vez de $-16$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-03A",
                        title="Ejemplo Guiado: Suma de Potencias Idénticas",
                        stem_text="¿A cuánto equivale la suma de cuatro términos iguales a 4¹⁵?",
                        stem_latex=r"4^{15} + 4^{15} + 4^{15} + 4^{15}",
                        options={"A": r"4^{16}", "B": r"16^{15}", "C": r"4^{60}", "D": r"16^{60}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Factorizamos los 4 sumandos iguales: $4 \cdot 4^{15} = 4^1 \cdot 4^{15}$.",
                            r"2. Conservamos la base y sumamos exponentes: $4^{1+15} = 4^{16}$."
                        ]
                    )
                ]
            ),
        ],
        "ALGEBRA_Y_FUNCIONES": [
            DEMREExhaustiveGuide(
                guide_id="M1-ALG-01",
                exam="M1",
                axis="ALGEBRA_Y_FUNCIONES",
                unit_title="Guía 1: Productos Notables, Factorización y Ecuaciones/Inecuaciones Lineales",
                short_description="Cuadrado de binomio, suma por su diferencia, despeje de ecuaciones de primer grado e inecuaciones.",
                subtopic_filter_keyword="ecuac",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Álgebra y Funciones • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Aborda la manipulación simbólica de expresiones algebraicas, simplificación mediante productos notables "
                    "y resolución de ecuaciones e inecuaciones de primer grado con una incógnita."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Cuadrado de Binomio y Suma por su Diferencia",
                        latex_formula=r"(a \pm b)^{2} = a^{2} \pm 2ab + b^{2} \quad ; \quad (a + b)(a - b) = a^{2} - b^{2}",
                        explanation="Indispensables para reducir expresiones y modelar áreas de rectángulos y cuadrados."
                    ),
                    FormulaCard(
                        title="Inversión de Orden en Inecuaciones Lineales",
                        latex_formula=r"-ax \geq b \quad (a > 0) \implies x \leq -\frac{b}{a}",
                        explanation="Al multiplicar o dividir por un número negativo, se invierte el sentido de la desigualdad."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Ecuaciones e Inecuaciones",
                resolution_recipe_steps=[
                    "Paso 1 (Eliminación de Denominadores): Multiplica toda la ecuación o inecuación por el m.c.m. de los denominadores.",
                    "Paso 2 (Expansión Cuidadosa): Desarrolla paréntesis vigilando los signos menos delante de binomios.",
                    "Paso 3 (Agrupación): Deja los términos con x en el lado donde su coeficiente quede positivo para evitar errores de signo."
                ],
                common_demre_traps=[
                    "Olvidar cambiar el signo del segundo término al restar un binomio: $5 - (2x - 3) = 5 - 2x + 3$, no $5 - 2x - 3$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-ALG-01A",
                        title="Ejemplo Guiado: Inecuación con Coeficiente Negativo",
                        stem_text="¿Cuál es el conjunto solución de la inecuación 4 - 3x ≥ 19?",
                        stem_latex=r"4 - 3x \geq 19",
                        options={"A": r"x \geq -5", "B": r"x \leq -5", "C": r"x \leq 5", "D": r"x \geq 5"},
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Restamos 4 en ambos lados: $-3x \geq 15$.",
                            r"2. Dividimos por $-3$ invirtiendo la desigualdad: $x \leq -5$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-ALG-02",
                exam="M1",
                axis="ALGEBRA_Y_FUNCIONES",
                unit_title="Guía 2: Sistemas de Ecuaciones Lineales 2x2 y Función Lineal/Afín",
                short_description="Método de reducción y sustitución en sistemas 2x2, modelamiento de tarifas con función afín y proporcionalidad.",
                subtopic_filter_keyword="sistema",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Álgebra y Funciones • Unidad 2",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Los sistemas de ecuaciones lineales $2 \\times 2$ modelan situaciones donde existen dos incógnitas y dos condiciones simultáneas "
                    "(por ejemplo, cantidad total de entradas y recaudación total en dinero). Geométricamente, la solución $(x, y)$ "
                    "representa el **punto de intersección** entre las dos rectas en el plano cartesiano."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Estructura de un Sistema 2x2 y Función Afín",
                        latex_formula=r"\begin{cases} a_1 x + b_1 y = c_1 \\ a_2 x + b_2 y = c_2 \end{cases} \quad ; \quad f(x) = mx + n",
                        explanation="En problemas de cobros: n es el cargo fijo inicial y m es el cobro por cada unidad consumida."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Sistemas 2x2",
                resolution_recipe_steps=[
                    "Paso 1 (Definición de Variables): Escribe explícitamente qué representa x y qué representa y.",
                    "Paso 2 (Método de Reducción): Multiplica una o ambas ecuaciones para que una incógnita quede con coeficientes opuestos (+k y -k).",
                    "Paso 3 (Suma Vertical): Suma ambas ecuaciones para despejar la primera incógnita en un paso.",
                    "Paso 4 (Verificación de lo Pedido): Comprueba si piden x, y, o una expresión como (x + y)."
                ],
                common_demre_traps=[
                    "Despejar correctamente $x$ y marcar ese valor cuando la pregunta pedía el valor de $y$ o la suma $x + y$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-ALG-02A",
                        title="Ejemplo Guiado: Sistema 2x2 por Reducción",
                        stem_text="En un estacionamiento hay 35 vehículos entre autos (4 ruedas) y motos (2 ruedas). Si en total hay 110 ruedas, ¿cuántos autos hay?",
                        stem_latex=r"\begin{cases} A + M = 35 \\ 4A + 2M = 110 \end{cases}",
                        options={"A": r"15", "B": r"20", "C": r"25", "D": r"18"},
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Multiplicamos la primera ecuación por $-2$: $-2A - 2M = -70$.",
                            r"2. Sumamos con la segunda ecuación: $2A = 40 \implies A = 20\text{ autos}$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-ALG-03",
                exam="M1",
                axis="ALGEBRA_Y_FUNCIONES",
                unit_title="Guía 3: Función Cuadrática, Parábola, Vértice y Ceros",
                short_description="Concavidad, eje de simetría, cálculo de máximos/mínimos en el vértice e intersecciones con los ejes.",
                subtopic_filter_keyword="cuadrática",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Álgebra y Funciones • Unidad 3",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "La función cuadrática $f(x) = ax^2 + bx + c$ ($a \\neq 0$) modela trayectorias de proyectiles, áreas máximas "
                    "y ganancias o costos. Su gráfica es una parábola simétrica respecto a la recta vertical $x = -\\frac{b}{2a}$."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Abscisa y Ordenada del Vértice de la Parábola",
                        latex_formula=r"x_{v} = -\frac{b}{2a} \quad ; \quad y_{v} = f(x_{v}) \quad ; \quad \text{Corte Eje Y: } (0, c)",
                        explanation="x_v indica DÓNDE o CUÁNDO ocurre el extremo; y_v = f(x_v) indica CUÁL es el valor máximo o mínimo."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Función Cuadrática",
                resolution_recipe_steps=[
                    "Paso 1 (Orden Estándar): Ordena la función como f(x) = ax² + bx + c e identifica a, b y c con sus signos.",
                    "Paso 2 (Lectura de la Pregunta): Distingue si piden la abscisa del vértice (x_v) o el valor extremo de la función (y_v).",
                    "Paso 3 (Evaluación): Calcula x_v = -b/(2a) y, si piden el máximo/mínimo, evalúa f(x_v)."
                ],
                common_demre_traps=[
                    "Marcar el valor de $x_v = -b/(2a)$ cuando el enunciado pregunta '¿cuál es la altura máxima o el valor mínimo que alcanza la función?'."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-ALG-03A",
                        title="Ejemplo Guiado: Altura Máxima de un Proyectil",
                        stem_text="La altura h(t) en metros a los t segundos está dada por h(t) = 12t - 2t². ¿Cuál es la altura máxima alcanzada?",
                        stem_latex=r"h(t) = -2t^{2} + 12t",
                        options={"A": r"3\text{ m}", "B": r"18\text{ m}", "C": r"12\text{ m}", "D": r"36\text{ m}"},
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Calculamos $t_v = -\frac{12}{2(-2)} = 3\text{ s}$.",
                            r"2. Evaluamos $h(3) = 12(3) - 2(3)^2 = 36 - 18 = 18\text{ m}$."
                        ]
                    )
                ]
            ),
        ],
        "GEOMETRIA": [
            DEMREExhaustiveGuide(
                guide_id="M1-GEO-01",
                exam="M1",
                axis="GEOMETRIA",
                unit_title="Guía 1: Teorema de Pitágoras, Perímetros y Áreas de Figuras Planas",
                short_description="Tríos pitagóricos, diagonal del cuadrado, altura del triángulo equilátero y áreas de círculos y polígonos.",
                subtopic_filter_keyword="pitágoras",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Geometría • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Comprende la aplicación del Teorema de Pitágoras en triángulos rectángulos y su uso para deducir "
                    "diagonales de rectángulos/cuadrados y alturas de triángulos equiláteros o trapecios isósceles."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Teorema de Pitágoras, Diagonal del Cuadrado y Triángulo Equilátero",
                        latex_formula=r"a^{2} + b^{2} = c^{2} \quad ; \quad d_{\text{cuadrado}} = a\sqrt{2} \quad ; \quad h_{\triangle\text{eq}} = \frac{a\sqrt{3}}{2}, \quad A_{\triangle\text{eq}} = \frac{a^{2}\sqrt{3}}{4}",
                        explanation="Reconocer los tríos pitagóricos (3,4,5), (6,8,10) y (5,12,13) permite resolver sin calculadora en segundos."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Figuras Planas",
                resolution_recipe_steps=[
                    "Paso 1 (Descomposición): Divide figuras irregulares o trapecios trazando alturas para formar triángulos rectángulos.",
                    "Paso 2 (Áreas Sombreadas): Calcula siempre como Área Mayor menos Área Blanca no sombreada."
                ],
                common_demre_traps=[
                    "Usar el diámetro en vez del radio al aplicar $A = \\pi r^2$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-GEO-01A",
                        title="Ejemplo Guiado: Diagonal de un Cuadrado a partir de su Área",
                        stem_text="Si el área de un cuadrado es 36 cm², ¿cuál es la longitud de su diagonal?",
                        stem_latex=r"A = a^{2} = 36 \implies d = a\sqrt{2}",
                        options={"A": r"6\sqrt{2}\text{ cm}", "B": r"12\text{ cm}", "C": r"18\sqrt{2}\text{ cm}", "D": r"6\text{ cm}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Del área $a^2 = 36$ obtenemos el lado $a = 6\text{ cm}$.",
                            r"2. La diagonal mide $d = 6\sqrt{2}\text{ cm}$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-GEO-02",
                exam="M1",
                axis="GEOMETRIA",
                unit_title="Guía 2: Cuerpos Geométricos (Cilindros, Conos y Prismas) y Transformaciones Isométricas",
                short_description="Volumen de cilindros y conos, vectores, traslación, reflexión y rotaciones en 90°, 180° y 270°.",
                subtopic_filter_keyword="rotación",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Geometría • Unidad 2",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Integra el cálculo de áreas de superficie y volúmenes de prismas rectos, cilindros y conos, "
                    "junto con la operatoria de vectores en $\\mathbb{R}^2$ y transformaciones isométricas."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Volumen del Cilindro y del Cono / Rotaciones en el Plano",
                        latex_formula=r"V_{\text{cil}} = \pi r^{2} h, \quad V_{\text{cono}} = \frac{1}{3}\pi r^{2} h \quad ; \quad R_{(0,0)}^{90^\circ}(x, y) = (-y, x)",
                        explanation="En traslaciones P + v = P', el vector traslación es v = P' - P."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Isometrías y Volúmenes",
                resolution_recipe_steps=[
                    "Paso 1 (Sentido de Rotación): En el plano cartesiano, el sentido positivo estándar es ANTIHORARIO.",
                    "Paso 2 (Centro de Rotación distinto del origen): Si el centro es C, resta C al punto P, rota respecto al origen y vuelve a sumar C."
                ],
                common_demre_traps=[
                    "Restar $P - P'$ en lugar de $P' - P$ al buscar el vector de traslación."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-GEO-02A",
                        title="Ejemplo Guiado: Rotación + Traslación",
                        stem_text="Al punto A(2, -5) se le aplica una rotación de 90° antihoraria respecto al origen y luego una traslación v = (-3, 1). ¿Qué punto resulta?",
                        stem_latex=r"R_{90^\circ}(2, -5) + (-3, 1)",
                        options={"A": r"(2, 3)", "B": r"(-8, 3)", "C": r"(2, -4)", "D": r"(-1, -4)"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. $R_{90^\circ}(2, -5) = (5, 2)$.",
                            r"2. Sumamos $(-3, 1)$: $(5 - 3, 2 + 1) = (2, 3)$."
                        ]
                    )
                ]
            ),
        ],
        "PROBABILIDAD_Y_ESTADISTICA": [
            DEMREExhaustiveGuide(
                guide_id="M1-PROB-01",
                exam="M1",
                axis="PROBABILIDAD_Y_ESTADISTICA",
                unit_title="Guía 1: Estadística Descriptiva, Medidas de Tendencia Central, Cuartiles y Boxplot",
                short_description="Promedio en tablas de frecuencia, mediana, moda, cuartiles Q1, Q2, Q3 y rango intercuartílico.",
                subtopic_filter_keyword="cuartil",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Probabilidad y Estadística • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Cubre la lectura de tablas de frecuencias absolutas y acumuladas, histogramas, cálculo de media, mediana y moda, "
                    "así como cuartiles, percentiles y diagramas de cajón (*Boxplot*)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Media Ponderada y Rango Intercuartílico (RIC)",
                        latex_formula=r"\bar{x} = \frac{\sum x_i \cdot f_i}{N} \quad ; \quad \text{RIC} = Q_{3} - Q_{1}",
                        explanation="Entre Q1 y Q3 se concentra siempre el 50% central de los datos de la muestra."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Tablas y Cuartiles",
                resolution_recipe_steps=[
                    "Paso 1 (Ordenamiento): Si los datos están sueltos, ordénalos de menor a mayor antes de buscar la mediana o cuartiles.",
                    "Paso 2 (Columna Acumulada F_i): En tablas, construye siempre la columna de frecuencia acumulada para ubicar dónde caen N/4, N/2 y 3N/4."
                ],
                common_demre_traps=[
                    "Calcular la mediana tomando el valor del medio sin haber ordenado la lista de menor a mayor."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-PROB-01A",
                        title="Ejemplo Guiado: Cálculo de Rango Intercuartílico",
                        stem_text="En un diagrama de cajón, el primer cuartil es 18 y el tercer cuartil es 42. ¿Cuál es el rango intercuartílico?",
                        stem_latex=r"\text{RIC} = Q_3 - Q_1 = 42 - 18",
                        options={"A": r"24", "B": r"30", "C": r"60", "D": r"12"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Restamos $Q_3 - Q_1 = 42 - 18 = 24$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-PROB-02",
                exam="M1",
                axis="PROBABILIDAD_Y_ESTADISTICA",
                unit_title="Guía 2: Regla de Laplace y Reglas Aditiva y Multiplicativa de Probabilidad",
                short_description="Probabilidad clásica, eventos mutuamente excluyentes, intersección e independencia con y sin reposición.",
                subtopic_filter_keyword="probabilidad",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Probabilidad y Estadística • Unidad 2",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Evalúa la regla de Laplace y la traducción del conectivo **'O' (Unión / Regla Aditiva)** "
                    "y del conectivo **'Y' (Intersección / Regla Multiplicativa)** en experimentos con y sin reposición."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Regla Aditiva y Regla Multiplicativa Sin Reposición",
                        latex_formula=r"P(A \cup B) = P(A) + P(B) - P(A \cap B) \quad ; \quad P(A \cap B) = P(A) \cdot P(B \mid A)",
                        explanation="En extracciones sin reposición, recuerda disminuir en 1 tanto los casos favorables (si se repite el color) como el total de la urna."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Probabilidades",
                resolution_recipe_steps=[
                    "Paso 1 (Identificar Conectivo): Si pide 'A o B', suma las probabilidades y resta la intersección; si pide 'A y luego B', multiplícalas.",
                    "Paso 2 (Chequeo de Reposición): Lee con atención si dice 'con reposición' (denominador constante) o 'sin reposición' (denominador decrece en 1)."
                ],
                common_demre_traps=[
                    "No restar $P(A \\cap B)$ cuando los eventos tienen elementos en común."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-PROB-02A",
                        title="Ejemplo Guiado: Regla Aditiva en Lanzamiento de Dado",
                        stem_text="Al lanzar un dado de 6 caras, ¿cuál es la probabilidad de obtener un número par O mayor que 4?",
                        stem_latex=r"P(\{2,4,6\} \cup \{5,6\})",
                        options={"A": r"\frac{5}{6}", "B": r"\frac{2}{3}", "C": r"\frac{1}{2}", "D": r"\frac{1}{6}"},
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. $P(\text{Par}) = \frac{3}{6}$, $P(>4) = \frac{2}{6}$ y $P(\{6\}) = \frac{1}{6}$.",
                            r"2. $P(A \cup B) = \frac{3 + 2 - 1}{6} = \frac{4}{6} = \frac{2}{3}$."
                        ]
                    )
                ]
            ),
        ],
    }


# =====================================================================
# CATÁLOGO EXHAUSTIVO PAES M2 (COMPETENCIA MATEMÁTICA 2 - ELECTIVA)
# =====================================================================
def _get_m2_guides() -> Dict[ThematicAxis, List[DEMREExhaustiveGuide]]:
    return {
        "NUMEROS": [
            DEMREExhaustiveGuide(
                guide_id="M2-NUM-01",
                exam="M2",
                axis="NUMEROS",
                unit_title="Guía 1 M2: Propiedades de Logaritmos y Cambio de Base",
                short_description="Definición exponencial-logarítmica, logaritmo de productos, cocientes, potencias y cambio de base.",
                subtopic_filter_keyword="logaritmo",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Números • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "En **PAES M2**, los logaritmos evalúan tu capacidad de traducir entre lenguaje exponencial y logarítmico "
                    "y descomponer expresiones algebraicas o numéricas mediante propiedades."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Propiedades Algebraicas y Cambio de Base",
                        latex_formula=r"\log_{b}\left(\frac{x^{n}}{y^{m}}\right) = n\log_{b}(x) - m\log_{b}(y) \quad ; \quad \log_{b}(a) = \frac{\log_{c}(a)}{\log_{c}(b)}",
                        explanation="Transforma siempre las raíces en exponentes fraccionarios antes de aplicar logaritmos."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Logaritmos",
                resolution_recipe_steps=[
                    "Paso 1 (Raíces a Exponentes): Escribe √x como x^(1/2).",
                    "Paso 2 (Separación): Separa productos en sumas y divisiones en restas de logaritmos.",
                    "Paso 3 (Bajada de Exponentes): Pasa cada exponente multiplicando al frente del logaritmo."
                ],
                common_demre_traps=[
                    "Confundir $\\log_b(x + y)$ con $\\log_b(x) + \\log_b(y)$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-NUM-01A",
                        title="Ejemplo Guiado M2: Reducción Logarítmica",
                        stem_text="¿Cuál es el valor numérico exacto de la expresión?",
                        stem_latex=r"\log_{4}(32) - \log_{3}\left(\frac{1}{27}\right)",
                        options={"A": r"\frac{11}{2}", "B": r"-\frac{1}{2}", "C": r"5", "D": r"\frac{7}{2}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. $\log_{4}(32) = \frac{5}{2}$ y $\log_{3}(3^{-3}) = -3$.",
                            r"2. $\frac{5}{2} - (-3) = \frac{11}{2}$."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M2-NUM-02",
                exam="M2",
                axis="NUMEROS",
                unit_title="Guía 2 M2: Matemática Financiera, Interés Compuesto y Crecimiento Exponencial",
                short_description="Modelos de capitalización compuesta, periodos trimestrales/mensuales, inflación y depreciación.",
                subtopic_filter_keyword="logaritmo",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Números • Unidad 2",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "Evalúa el modelamiento de ahorros, créditos e inversiones bajo régimen de **interés compuesto**, "
                    "donde los intereses generados en cada período se suman al capital para generar nuevos intereses."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Fórmula General de Interés Compuesto",
                        latex_formula=r"C_{f} = C_{0} \cdot \left(1 + \frac{i}{m}\right)^{m \cdot t}",
                        explanation="Si la tasa anual i se capitaliza m veces al año durante t años, la tasa por período es i/m y el total de períodos es m·t."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Matemática Financiera",
                resolution_recipe_steps=[
                    "Paso 1 (Sincronización de Unidad Temporal): Verifica que la tasa de interés y el tiempo estén en la misma unidad (ej. ambos en meses o ambos en trimestres).",
                    "Paso 2 (Expresión sin Calcular Potencias Grandes): En la PAES las alternativas suelen dejar la potencia expresada; enfócate en plantear correctamente la base y el exponente."
                ],
                common_demre_traps=[
                    "Dejar el exponente en años cuando la capitalización es mensual (en 2 años hay 24 períodos mensuales)."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-NUM-02A",
                        title="Ejemplo Guiado M2: Capitalización Trimestral",
                        stem_text="Un capital de $C se invierte a una tasa del 2% trimestral compuesto durante 3 años. ¿Qué expresión representa el capital final?",
                        stem_latex=r"C_f = C \cdot (1 + 0,02)^{n}",
                        options={"A": r"C \cdot (1,02)^{12}", "B": r"C \cdot (1,02)^{3}", "C": r"C \cdot (1,2)^{12}", "D": r"C \cdot (1,02)^{9}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Cada año tiene 4 trimestres, por lo que en 3 años hay $3 \cdot 4 = 12$ trimestres.",
                            r"2. La tasa del 2% es $0,02$, resultando $C \cdot (1,02)^{12}$."
                        ]
                    )
                ]
            ),
        ],
        "ALGEBRA_Y_FUNCIONES": [
            DEMREExhaustiveGuide(
                guide_id="M2-ALG-01",
                exam="M2",
                axis="ALGEBRA_Y_FUNCIONES",
                unit_title="Guía 1 M2: Análisis de Sistemas Lineales Paramétricos y Naturaleza de Raíces (Δ)",
                short_description="Criterio de solución única, infinitas o sin solución en sistemas 2x2 con parámetro k, y discriminante cuadrático.",
                subtopic_filter_keyword="parámetro",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Álgebra y Funciones • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "En **M2**, los problemas de sistemas $2 \\times 2$ exigen analizar la proporcionalidad de los coeficientes "
                    "para determinar la existencia y unicidad de soluciones según un parámetro real $p$ o $k$."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Criterio de Compatibilidad en Sistemas 2x2 y Discriminante",
                        latex_formula=r"\text{Sin solución: } \frac{a_1}{a_2} = \frac{b_1}{b_2} \neq \frac{c_1}{c_2} \quad ; \quad \Delta = b^{2} - 4ac",
                        explanation="Si Δ > 0 hay dos soluciones reales distintas; si Δ = 0 hay una única solución real doble; si Δ < 0 no hay soluciones reales."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Sistemas con Parámetro",
                resolution_recipe_steps=[
                    "Paso 1 (Alineación): Ordena el sistema dejando x e y a la izquierda y las constantes a la derecha.",
                    "Paso 2 (Igualdad de Pendientes): Plantea a₁/a₂ = b₁/b₂ y despeja el parámetro.",
                    "Paso 3 (Chequeo de Términos Libres): Verifica si la razón coincide o difiere de c₁/c₂."
                ],
                common_demre_traps=[
                    "No verificar si para el valor hallado de $k$ las rectas resultan coincidentes en vez de paralelas disjuntas."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-ALG-01A",
                        title="Ejemplo Guiado M2: Sistema Incompatibe (Sin Solución)",
                        stem_text="¿Para qué valor de k el sistema NO tiene solución?",
                        stem_latex=r"\begin{cases} kx + 3y = 7 \\ 4x + 6y = 10 \end{cases}",
                        options={"A": r"k = 2", "B": r"k = -2", "C": r"k = 6", "D": r"k = 4"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Planteamos $\frac{k}{4} = \frac{3}{6} \implies k = 2$.",
                            r"2. Como $\frac{1}{2} \neq \frac{7}{10}$, para $k = 2$ no tiene solución."
                        ]
                    )
                ]
            ),
        ],
        "GEOMETRIA": [
            DEMREExhaustiveGuide(
                guide_id="M2-GEO-01",
                exam="M2",
                axis="GEOMETRIA",
                unit_title="Guía 1 M2: Homotecia Directa e Inversa y Razones Trigonométricas",
                short_description="Razón de homotecia en perímetros y áreas (k²), seno, coseno, tangente y ángulos de elevación.",
                subtopic_filter_keyword="homotecia",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Geometría • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "Abarca las propiedades vectoriales y métricas de la **Homotecia** de centro $O$ y razón $k$, "
                    "y la **Trigonometría en el triángulo rectángulo**."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Efecto de la Homotecia en Perímetros y Áreas / Trigonometría",
                        latex_formula=r"\frac{P'}{P} = |k|, \quad \frac{A'}{A} = k^{2} \quad ; \quad \sin(\alpha) = \frac{\text{Op}}{\text{Hip}}, \quad \cos(\alpha) = \frac{\text{Ady}}{\text{Hip}}, \quad \tan(\alpha) = \frac{\text{Op}}{\text{Ady}}",
                        explanation="Si k < 0 la figura se invierte al otro lado del centro O, pero su área se multiplica igualmente por k² > 0."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Homotecia",
                resolution_recipe_steps=[
                    "Paso 1 (Signo de k): Si el centro O está entre la figura original y la imagen, k es negativo.",
                    "Paso 2 (Escala de Área): Eleva siempre la razón k al cuadrado cuando te pidan comparar áreas."
                ],
                common_demre_traps=[
                    "Multiplicar el área original por $|k|$ en lugar de $k^2$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-GEO-01A",
                        title="Ejemplo Guiado M2: Área de un Triángulo Homotético",
                        stem_text="A un triángulo de área 12 cm² se le aplica una homotecia de razón k = -3. ¿Cuál es el área del triángulo imagen?",
                        stem_latex=r"A' = (-3)^{2} \cdot 12",
                        options={"A": r"108\text{ cm}^{2}", "B": r"36\text{ cm}^{2}", "C": r"-36\text{ cm}^{2}", "D": r"4\text{ cm}^{2}"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. $A' = k^2 \cdot A = 9 \cdot 12 = 108\text{ cm}^2$."
                        ]
                    )
                ]
            ),
        ],
        "PROBABILIDAD_Y_ESTADISTICA": [
            DEMREExhaustiveGuide(
                guide_id="M2-PROB-01",
                exam="M2",
                axis="PROBABILIDAD_Y_ESTADISTICA",
                unit_title="Guía 1 M2: Combinatoria, Desviación Estándar, Probabilidad Condicional y Binomial",
                short_description="Permutaciones, variaciones y combinaciones, varianza y desviación estándar, y modelo binomial.",
                subtopic_filter_keyword="combinatoria",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Probabilidad y Estadística • Unidad 1",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "Integra las medidas de dispersión (**varianza y desviación estándar**), las técnicas de conteo "
                    "(**permutación, variación y combinación**), la **probabilidad condicional** y la **distribución binomial**."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Combinatoria sin Repetición, Probabilidad Condicional y Binomial",
                        latex_formula=r"\binom{n}{k} = \frac{n!}{k!(n-k)!} \quad ; \quad P(A \mid B) = \frac{P(A \cap B)}{P(B)} \quad ; \quad P(X = k) = \binom{n}{k}p^{k}(1-p)^{n-k}",
                        explanation="Usa Combinatoria cuando el orden de selección NO importa (comisiones, grupos de trabajo)."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Combinatoria y Dispersión",
                resolution_recipe_steps=[
                    "Paso 1 (¿Importa el orden?): Si elegir {A, B} es igual que {B, A}, aplica Combinación C(n, k).",
                    "Paso 2 (Propiedad de la Desviación Estándar): Si sumas una misma constante a todos los datos, la desviación estándar NO cambia; si multiplicas todos los datos por k, la desviación estándar se multiplica por |k|."
                ],
                common_demre_traps=[
                    "Usar variación $n!/(n-k)!$ cuando el problema pide formar un comité sin cargos jerárquicos."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-PROB-01A",
                        title="Ejemplo Guiado M2: Selección de Comisión por Combinatoria",
                        stem_text="De 8 científicos se debe escoger una comisión de 3 sin distinción de cargo. ¿De cuántas maneras puede hacerse?",
                        stem_latex=r"\binom{8}{3} = \frac{8 \cdot 7 \cdot 6}{3 \cdot 2 \cdot 1}",
                        options={"A": r"56", "B": r"336", "C": r"24", "D": r"512"},
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. $\binom{8}{3} = \frac{8 \cdot 7 \cdot 6}{6} = 56$."
                        ]
                    )
                ]
            ),
        ],
    }
