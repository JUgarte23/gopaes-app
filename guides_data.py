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
                unit_title="Unidad 1: Conjunto de los Enteros (ℤ), Racionales (ℚ) y Porcentajes",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Números (Operatoria, Prioridad y Variación Porcentual)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "En la **PAES M1**, el eje de Números evalúa la comprensión profunda de la jerarquía de operaciones "
                    "en $\\mathbb{Z}$ y $\\mathbb{Q}$, la transformación entre decimales (finitos, periódicos y semiperiódicos) "
                    "y fracciones irreductibles, además del modelamiento de **variaciones porcentuales sucesivas**.\n\n"
                    "1. **Jerarquía PAPOMUDAS**: Paréntesis (desde el más interno al más externo), Potencias, Multiplicación y "
                    "División (de izquierda a derecha), y finalmente Adición y Sustracción.\n"
                    "2. **Signos en Potencias**: Una potencia de base negativa conserva el signo negativo únicamente si el paréntesis "
                    "abarca al signo y el exponente es impar: $(-a)^{2k+1} < 0$. Si no hay paréntesis, $-a^n = -(a^n)$ siempre es negativo.\n"
                    "3. **Variaciones Porcentuales Sucesivas**: Un aumento del $a\\%$ equivale al factor multiplicativo $\\left(1 + \\frac{a}{100}\\right)$, "
                    "mientras que un descuento del $b\\%$ equivale al factor $\\left(1 - \\frac{b}{100}\\right)$."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Transformación de Decimal Periódico y Semiperiódico a Fracción",
                        latex_formula=r"0,\overline{ab} = \frac{ab}{99} \quad ; \quad 0,c\overline{ab} = \frac{cab - c}{990}",
                        explanation="Se escribe el número completo sin coma menos la parte no periódica, dividido por tantos 9 como cifras tenga el período y tantos 0 como cifras tenga el anteperíodo."
                    ),
                    FormulaCard(
                        title="Factor Multiplicativo de Porcentajes Sucesivos",
                        latex_formula=r"V_{\text{final}} = V_{\text{inicial}} \cdot \left(1 \pm \frac{p_1}{100}\right) \cdot \left(1 \pm \frac{p_2}{100}\right)",
                        explanation="Permite encadenar aumentos y descuentos de IVA, liquidaciones o reajustes en un solo paso."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Problemas de Porcentajes y Racionales",
                resolution_recipe_steps=[
                    "Paso 1 (Estandarización): Convierte todos los números decimales periódicos o mixtos a fracción irreductible antes de operar.",
                    "Paso 2 (Identificación de la Base 100%): Define claramente cuál es la cantidad referente sobre la cual se calcula cada porcentaje.",
                    "Paso 3 (Traducción a Factor Decimal): Sustituye cada 'aumento del X%' por (1 + X/100) y cada 'descuento del Y%' por (1 - Y/100).",
                    "Paso 4 (Simplificación Cruzada): Antes de multiplicar numeradores grandes, simplifica factores comunes entre numerador y denominador.",
                    "Paso 5 (Verificación de Magnitud): Comprueba si el resultado final debe ser mayor o menor que la cantidad original."
                ],
                common_demre_traps=[
                    "Sumar o restar porcentajes aplicados sobre bases distintas (ej. subir 20% y bajar 20% NO da 0%, sino un descuento neto del 4%).",
                    "Evaluar $-3^2 = 9$ en lugar de $-3^2 = -(3^2) = -9$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-01A",
                        title="Ejercicio Intercalado 1: Operatoria Racional con Decimales Periódicos",
                        stem_text="¿Cuál es el valor exacto de la siguiente expresión numérica?",
                        stem_latex=r"0,\overline{3} + \frac{1}{2} : \frac{3}{4}",
                        options={
                            "A": r"1",
                            "B": r"\frac{10}{9}",
                            "C": r"\frac{5}{6}",
                            "D": r"\frac{7}{6}",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Convertimos el decimal periódico a fracción: $0,\overline{3} = \frac{3}{9} = \frac{1}{3}$.",
                            r"2. Por prioridad de operaciones, resolvemos primero la división de fracciones invirtiendo el divisor: $\frac{1}{2} : \frac{3}{4} = \frac{1}{2} \cdot \frac{4}{3} = \frac{2}{3}$.",
                            r"3. Sumamos ambos términos de igual denominador: $\frac{1}{3} + \frac{2}{3} = \frac{3}{3} = 1$."
                        ]
                    ),
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-01B",
                        title="Ejercicio Intercalado 2: Variación Porcentual Encadenada",
                        stem_text="En una tienda, una chaqueta de $40.000 sube su precio en un 25% por cambio de temporada y luego, en una venta nocturna, se le aplica una rebaja del 20% sobre el nuevo precio. ¿Cuál es el precio final?",
                        stem_latex=r"P_f = 40.000 \cdot \left(1 + \frac{25}{100}\right) \cdot \left(1 - \frac{20}{100}\right)",
                        options={
                            "A": r"\$40.000",
                            "B": r"\$42.000",
                            "C": r"\$38.000",
                            "D": r"\$45.000",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Expresamos los factores en fracción: $1,25 = \frac{5}{4}$ y $0,80 = \frac{4}{5}$.",
                            r"2. Multiplicamos los factores sucesivos: $\frac{5}{4} \cdot \frac{4}{5} = 1$.",
                            r"3. Por lo tanto, el precio final es exactamente $40.000 \cdot 1 = \$40.000$."
                        ]
                    ),
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-NUM-02",
                exam="M1",
                axis="NUMEROS",
                unit_title="Unidad 2: Potencias de Exponente Entero y Raíces Enésimas",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Números (Propiedades de Potencias y Raíces)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "Las preguntas de potencias y raíces en M1 buscan medir tu capacidad de **reescribir bases compuestas "
                    "en factores primos** ($4 = 2^2, 8 = 2^3, 9 = 3^2, 27 = 3^3$) y extraer factores de raíces enésimas.\n\n"
                    "- **Suma de potencias de igual base**: Cuando aparece $2^{10} + 2^{10} + 2^{10}$, NO se suman los exponentes; "
                    "se factoriza por el término común: $3 \\cdot 2^{10}$.\n"
                    "- **Operatoria con raíces**: Solo se pueden sumar o restar raíces que tengan simultáneamente el mismo índice "
                    "y la misma cantidad subradical."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Potencia de una Potencia y Exponente Negativo",
                        latex_formula=r"\left(a^{n}\right)^{m} = a^{n \cdot m} \quad ; \quad \left(\frac{a}{b}\right)^{-n} = \left(\frac{b}{a}\right)^{n}",
                        explanation="Al elevar una potencia a otro exponente, los exponentes se multiplican."
                    ),
                    FormulaCard(
                        title="Extracción de Factores y Racionalización Simple",
                        latex_formula=r"\sqrt[n]{a^{n} \cdot b} = a\sqrt[n]{b} \quad ; \quad \frac{c}{\sqrt{b}} = \frac{c\sqrt{b}}{b}",
                        explanation="Descompón siempre la cantidad subradical buscando cuadrados o cubos perfectos."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Reducción de Potencias y Raíces",
                resolution_recipe_steps=[
                    "Paso 1 (Descomposición Prima): Reescribe todas las bases numéricas como potencias de números primos (2, 3, 5, 7).",
                    "Paso 2 (Eliminación de Exponentes Negativos): Invierte las bases fraccionarias que tengan exponente negativo.",
                    "Paso 3 (Factor Común en Sumas): Si hay sumas o restas de potencias, factoriza por la potencia de menor exponente.",
                    "Paso 4 (Reducción de Raíces): Descompón cada raíz grande (ej. √75 = √(25·3) = 5√3) antes de sumar o dividir."
                ],
                common_demre_traps=[
                    "Aplicar propiedad de multiplicación de potencias en una suma: $2^3 + 2^4 \\neq 2^7$.",
                    "Creer que $\\sqrt{a^2 + b^2} = a + b$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-NUM-02A",
                        title="Ejercicio Intercalado: Factorización de Potencias de Igual Base",
                        stem_text="¿A cuánto equivale la suma de cuatro términos iguales a 4¹⁵?",
                        stem_latex=r"4^{15} + 4^{15} + 4^{15} + 4^{15}",
                        options={
                            "A": r"4^{16}",
                            "B": r"16^{15}",
                            "C": r"4^{60}",
                            "D": r"16^{60}",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Agrupamos los 4 términos idénticos como una multiplicación: $4 \cdot 4^{15}$.",
                            r"2. Aplicamos producto de potencias de igual base ($4^1 \cdot 4^{15}$): se conserva la base 4 y se suman los exponentes $1 + 15 = 16$.",
                            r"3. Resultado final: $4^{16}$ (o equivalentemente $2^{32}$)."
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
                unit_title="Unidad 1: Productos Notables, Factorización, Ecuaciones, Inecuaciones y Sistemas 2x2",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Álgebra y Funciones (Expresiones Algebraicas y Sistemas)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "El eje de **Álgebra y Funciones** representa un tercio completo de la prueba M1. "
                    "Domina la traducción de lenguaje natural a lenguaje algebraico, el despeje de ecuaciones e inecuaciones "
                    "de primer grado y la resolución de **sistemas de ecuaciones lineales $2 \\times 2$** mediante reducción o sustitución.\n\n"
                    "- **Sentido de las Desigualdades**: En toda inecuación lineal, al multiplicar o dividir ambos lados por un "
                    "número negativo, el signo de orden se invierte obligatoriamente ($<$ pasa a $>$, y $\\leq$ pasa a $\\geq$)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Cuadrado de Binomio y Suma por su Diferencia",
                        latex_formula=r"(x \pm y)^{2} = x^{2} \pm 2xy + y^{2} \quad ; \quad (x + y)(x - y) = x^{2} - y^{2}",
                        explanation="Fundamental para simplificar fracciones algebraicas y desarrollar áreas de figuras compuestas."
                    ),
                    FormulaCard(
                        title="Trinomio Ordenado de la Forma x² + bx + c",
                        latex_formula=r"x^{2} + (p + q)x + (p \cdot q) = (x + p)(x + q)",
                        explanation="Busca dos números p y q que multiplicados den el término libre c y sumados den el coeficiente lineal b."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Sistemas de Ecuaciones 2x2 y Problemas Verbales",
                resolution_recipe_steps=[
                    "Paso 1 (Definición de Incógnitas): Asigna letras explícitas con unidades (ej. x = cantidad de monedas de $100, y = cantidad de monedas de $500).",
                    "Paso 2 (Ecuación de Cantidad vs Ecuación de Valor): Plantea la primera ecuación con el total de objetos (x + y = N) y la segunda con el monto total (100x + 500y = M).",
                    "Paso 3 (Método de Reducción): Multiplica una ecuación para igualar coeficientes con signo opuesto y suma verticalmente.",
                    "Paso 4 (Lectura de la Pregunta Final): Antes de marcar la alternativa, verifica si el DEMRE pregunta por x, por y, o por una combinación como (x + y) o la diferencia |x - y|."
                ],
                common_demre_traps=[
                    "Desarrollar $(x - 3)^2$ como $x^2 - 9$ olvidando el término central $-6x$.",
                    "No invertir la desigualdad al despejar $-2x \\geq 10 \\implies x \\leq -5$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-ALG-01A",
                        title="Ejercicio Intercalado: Modelamiento con Sistemas 2x2",
                        stem_text="En un estacionamiento hay 35 vehículos entre autos (4 ruedas) y motos (2 ruedas). Si en total se cuentan 110 ruedas, ¿cuántos autos hay en el estacionamiento?",
                        stem_latex=r"\begin{cases} A + M = 35 \\ 4A + 2M = 110 \end{cases}",
                        options={
                            "A": r"15",
                            "B": r"20",
                            "C": r"25",
                            "D": r"18",
                        },
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Multiplicamos la primera ecuación por $-2$ para eliminar $M$: $-2A - 2M = -70$.",
                            r"2. Sumamos con la segunda ecuación: $(4A - 2A) + (2M - 2M) = 110 - 70 \implies 2A = 40$.",
                            r"3. Despejamos $A$: $A = \frac{40}{2} = 20\text{ autos}$ (y $15\text{ motos}$)."
                        ]
                    )
                ]
            ),
            DEMREExhaustiveGuide(
                guide_id="M1-ALG-02",
                exam="M1",
                axis="ALGEBRA_Y_FUNCIONES",
                unit_title="Unidad 2: Función Lineal, Afín y Función Cuadrática",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Álgebra y Funciones (Modelos Funcionales y Parábolas)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "- **Función Lineal ($f(x) = mx$)**: Su gráfica es una recta que pasa por el origen $(0,0)$ y modela relaciones de proporcionalidad directa.\n"
                    "- **Función Afín ($f(x) = mx + n$)**: Tiene pendiente $m$ (cargo variable por unidad) y coeficiente de posición $n$ (cargo fijo inicial en $x = 0$).\n"
                    "- **Función Cuadrática ($f(x) = ax^2 + bx + c, a \\neq 0$)**: Su gráfica es una parábola. Si $a > 0$ abre hacia arriba (tiene mínimo); si $a < 0$ abre hacia abajo (tiene máximo)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Pendiente e Intersección de la Función Afín",
                        latex_formula=r"f(x) = mx + n \quad ; \quad m = \frac{y_2 - y_1}{x_2 - x_1} \quad ; \quad \text{Corte Eje Y: } (0, n)",
                        explanation="n representa siempre el valor inicial cuando la variable independiente x vale cero."
                    ),
                    FormulaCard(
                        title="Coordenadas del Vértice de la Parábola",
                        latex_formula=r"x_{v} = -\frac{b}{2a} \quad ; \quad y_{v} = f(x_{v}) = c - \frac{b^{2}}{4a}",
                        explanation="En problemas de proyectiles o ganancias máximas: x_v es el tiempo o cantidad que optimiza la función, e y_v es la altura o ganancia máxima alcanzada."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Optimización con Función Cuadrática",
                resolution_recipe_steps=[
                    "Paso 1 (Identificación de Coeficientes): Ordena la función en la forma estándar f(x) = ax² + bx + c e identifica a, b y c con sus signos.",
                    "Paso 2 (Distinción de la Pregunta): Lee si piden 'en qué instante/cantidad ocurre el máximo' (piden x_v) o 'cuál es el valor máximo/mínimo alcanzado' (piden y_v = f(x_v)).",
                    "Paso 3 (Cálculo del Eje de Simetría): Calcula x_v = -b / (2a).",
                    "Paso 4 (Evaluación del Extremo): Si piden el valor máximo o mínimo, reemplaza el valor de x_v dentro de la función original f(x)."
                ],
                common_demre_traps=[
                    "Marcar el valor de $x_v$ cuando la pregunta pedía la altura máxima $y_v = f(x_v)$.",
                    "Confundir el corte con el eje Y $(0, c)$ con el vértice de la parábola."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-ALG-02A",
                        title="Ejercicio Intercalado: Altura Máxima de una Parábola",
                        stem_text="La altura h(t), en metros, que alcanza un balón lanzado verticalmente a los t segundos está modelada por la función indicada. ¿Cuál es la altura máxima que alcanza el balón?",
                        stem_latex=r"h(t) = 12t - 2t^{2}",
                        options={
                            "A": r"3\text{ m}",
                            "B": r"18\text{ m}",
                            "C": r"12\text{ m}",
                            "D": r"36\text{ m}",
                        },
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Ordenamos la función cuadrática: $h(t) = -2t^2 + 12t + 0$, identificando $a = -2$, $b = 12$, $c = 0$.",
                            r"2. Calculamos el instante en que alcanza su altura máxima: $t_v = -\frac{12}{2(-2)} = \frac{-12}{-4} = 3\text{ segundos}$.",
                            r"3. Evaluamos $h(3)$ para obtener la altura máxima: $h(3) = 12(3) - 2(3)^2 = 36 - 18 = 18\text{ metros}$."
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
                unit_title="Unidad 1: Teorema de Pitágoras, Áreas, Perímetros, Cilindros, Conos y Transformaciones Isométricas",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Geometría (Figuras 2D, Cuerpos 3D y Vectores)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "En **Geometría M1**, las preguntas combinan el **Teorema de Pitágoras** (incluyendo los tríos pitagóricos clásicos "
                    "$3-4-5$, $5-12-13$, $6-8-10$, $8-15-17$), el cálculo de áreas sombreadas por resta de superficies, "
                    "el volumen de prismas, cilindros y conos, y las **transformaciones isométricas en el plano cartesiano** (traslación, reflexión y rotación)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Tríos Pitagóricos y Triángulo Equilátero de Lado a",
                        latex_formula=r"a^{2} + b^{2} = c^{2} \quad ; \quad h_{\triangle\text{eq}} = \frac{a\sqrt{3}}{2}, \quad A_{\triangle\text{eq}} = \frac{a^{2}\sqrt{3}}{4}",
                        explanation="Memorizar los tríos (3,4,5) y (5,12,13) ahorra más de 1 minuto por pregunta en la PAES."
                    ),
                    FormulaCard(
                        title="Volumen y Área Total de Cilindros y Conos",
                        latex_formula=r"V_{\text{cilindro}} = \pi r^{2} h \quad ; \quad V_{\text{cono}} = \frac{1}{3}\pi r^{2} h \quad ; \quad g = \sqrt{r^{2} + h^{2}}",
                        explanation="El volumen de un cono es exactamente la tercera parte del volumen de un cilindro de igual radio y altura."
                    ),
                    FormulaCard(
                        title="Rotaciones respecto al Origen (0,0) en Sentido Antihorario",
                        latex_formula=r"R_{90^\circ}(x, y) = (-y, x) \quad ; \quad R_{180^\circ}(x, y) = (-x, -y) \quad ; \quad R_{270^\circ}(x, y) = (y, -x)",
                        explanation="Una rotación de 270° antihoraria equivale exactamente a una rotación de 90° en sentido horario."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Problemas de Geometría y Vectores",
                resolution_recipe_steps=[
                    "Paso 1 (Trazado Auxiliar): Si la figura es un trapecio o polígono compuesto, traza alturas perpendiculares para formar rectángulos y triángulos rectángulos.",
                    "Paso 2 (Verificación Radio vs Diámetro): Subraya en el enunciado si el dato entregado es el radio (r) o el diámetro (d = 2r).",
                    "Paso 3 (Cálculo en función de π): No reemplaces π por 3,14 a menos que el enunciado lo pida explícitamente; deja el resultado expresado en términos de π.",
                    "Paso 4 (Despeje Vectorial): En traslaciones P + v = P', despeja siempre v = P' - P restando coordenada a coordenada."
                ],
                common_demre_traps=[
                    "Olvidar dividir por 3 al calcular el volumen de un cono.",
                    "Aplicar la fórmula de rotación en torno al origen cuando el centro de rotación es otro punto $C(h, k)$ distinto de $(0,0)$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-GEO-01A",
                        title="Ejercicio Intercalado: Rotación + Traslación en el Plano Cartesiano",
                        stem_text="Al punto A(2, -5) se le aplica una rotación de 90° en sentido antihorario respecto al origen y luego una traslación según el vector v = (-3, 1). ¿Cuáles son las coordenadas finales?",
                        stem_latex=r"A(2, -5) \xrightarrow{R_{90^\circ}} A'(-(-5), 2) = (5, 2) \xrightarrow{+\vec{v}(-3, 1)} A''",
                        options={
                            "A": r"(2, 3)",
                            "B": r"(-8, 3)",
                            "C": r"(2, -4)",
                            "D": r"(-1, -4)",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Aplicamos la rotación antihoraria de $90^\circ$ sobre $(x, y) = (2, -5)$: $R_{90^\circ}(2, -5) = (-(-5), 2) = (5, 2)$.",
                            r"2. Sumamos el vector de traslación $\vec{v} = (-3, 1)$: $(5 + (-3), 2 + 1) = (2, 3)$."
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
                unit_title="Unidad 1: Medidas de Tendencia Central, Cuartiles, Boxplot y Reglas de Probabilidad",
                demre_syllabus_reference="Temario Oficial DEMRE M1 • Eje Probabilidad y Estadística (Estadística Descriptiva y Laplace)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M1)\n"
                    "- **Medidas de Tendencia Central**: Media aritmética ($\\bar{x}$), Mediana (dato central tras ordenar de menor a mayor) y Moda (dato con mayor frecuencia absoluta).\n"
                    "- **Medidas de Posición (Cuartiles $Q_1, Q_2, Q_3$ y Percentiles)**: Dividen la muestra ordenada en 4 partes del $25\\%$ cada una o 100 partes del $1\\%$. El **Rango Intercuartílico** es $RIC = Q_3 - Q_1$.\n"
                    "- **Probabilidad Clásica**: Regla aditiva (unión de sucesos \"O\") y regla multiplicativa (intersección de sucesos \"Y\", distinguiendo con y sin reposición)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Promedio Ponderado para Datos en Tabla de Frecuencias",
                        latex_formula=r"\bar{x} = \frac{x_1 \cdot f_1 + x_2 \cdot f_2 + \dots + x_k \cdot f_k}{f_1 + f_2 + \dots + f_k}",
                        explanation="Cada valor de la variable se multiplica por su frecuencia absoluta y se divide por el total de datos N."
                    ),
                    FormulaCard(
                        title="Regla Aditiva General de Probabilidades",
                        latex_formula=r"P(A \cup B) = P(A) + P(B) - P(A \cap B)",
                        explanation="Si los eventos A y B no son mutuamente excluyentes, debes restar la intersección para no contar dos veces los casos comunes."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE para Tablas de Frecuencia y Probabilidad",
                resolution_recipe_steps=[
                    "Paso 1 (Columna de Frecuencia Acumulada F_i): Agrega siempre al costado de la tabla la frecuencia acumulada para ubicar rápidamente la mediana y los cuartiles.",
                    "Paso 2 (Posición de Cuartiles): Calcula la posición aproximada de Q_k como k·N/4 y busca el primer intervalo cuya frecuencia acumulada F_i supere o iguale dicho valor.",
                    "Paso 3 (Árbol de Probabilidades): En extracciones sucesivas, dibuja un diagrama de árbol actualizando los numeradores y denominadores si es SIN reposición."
                ],
                common_demre_traps=[
                    "Sumar $P(A) + P(B)$ olvidando restar $P(A \\cap B)$ cuando ambos eventos pueden ocurrir al mismo tiempo (ej. sacar una carta que sea 'Corazón' O 'Rey').",
                    "Confundir la posición de la mediana ($N/2$) con el valor de la variable en esa posición."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M1-PROB-01A",
                        title="Ejercicio Intercalado: Regla Aditiva con Intersección No Vacía",
                        stem_text="Al lanzar un dado común de 6 caras, ¿cuál es la probabilidad de obtener un número par O un número mayor que 4?",
                        stem_latex=r"P(\text{Par} \cup \text{Mayor que 4}) = P(\{2,4,6\}) + P(\{5,6\}) - P(\{6\})",
                        options={
                            "A": r"\frac{5}{6}",
                            "B": r"\frac{2}{3}",
                            "C": r"\frac{1}{2}",
                            "D": r"\frac{1}{6}",
                        },
                        correct_option="B",
                        step_by_step_solution=[
                            r"1. Definimos los casos favorables del evento A (Par): $\{2, 4, 6\} \implies P(A) = \frac{3}{6}$.",
                            r"2. Definimos los casos del evento B (Mayor que 4): $\{5, 6\} \implies P(B) = \frac{2}{6}$.",
                            r"3. El número 6 está en ambos eventos ($A \cap B = \{6\}$), por lo que restamos su repetición: $P(A \cup B) = \frac{3}{6} + \frac{2}{6} - \frac{1}{6} = \frac{4}{6} = \frac{2}{3}$."
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
                unit_title="Unidad Exclusiva M2: Números Reales (ℝ), Logaritmos y Matemática Financiera",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Números (Propiedades de Logaritmos, Cambio de Base e Interés Compuesto)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "La **PAES M2** profundiza en la estructura algebraica de los **Números Reales ($\\mathbb{R}$)**, "
                    "la operatoria avanzada con **logaritmos** y el modelamiento de situaciones financieras (interés compuesto, "
                    "depreciación, AFP e inflación).\n\n"
                    "1. **Restricción de Existencia del Logaritmo**: En $\\log_b(x)$, la base debe cumplir $b > 0, b \\neq 1$ "
                    "y el argumento debe ser estrictamente positivo ($x > 0$).\n"
                    "2. **Cambio de Base**: Permite pasar cualquier logaritmo a una base conveniente común (usualmente base 10 o base prima)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Propiedades Algebraicas y Cambio de Base en Logaritmos",
                        latex_formula=r"\log_{b}\left(\frac{x^{n}}{y^{m}}\right) = n\log_{b}(x) - m\log_{b}(y) \quad ; \quad \log_{b}(a) = \frac{\log_{c}(a)}{\log_{c}(b)}",
                        explanation="El cambio de base es clave cuando el problema entrega como dato logaritmos en bases distintas."
                    ),
                    FormulaCard(
                        title="Capital Final en Régimen de Interés Compuesto",
                        latex_formula=r"C_{f} = C_{0} \cdot \left(1 + i\right)^{n}",
                        explanation="Donde C_0 es el capital inicial, i es la tasa de interés por período expresada en decimal (o fracción) y n es el número total de períodos de capitalización."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Ecuaciones y Reducciones Logarítmicas",
                resolution_recipe_steps=[
                    "Paso 1 (Transformación de Raíces a Exponentes Fraccionarios): Sustituye toda raíz enésima por exponente fraccionario: √x = x^(1/2).",
                    "Paso 2 (Expansión Lineal): Aplica logaritmo de un producto (suma) y cociente (resta) para separar todas las variables.",
                    "Paso 3 (Bajada de Exponentes): Pasa cada exponente multiplicando delante de su respectivo logaritmo.",
                    "Paso 4 (Descomposición Prima de Constantes): Expresa números como 8, 27, 0,25 en forma de potencia prima (2³, 3³, 2⁻²) para evaluarlos exactamente."
                ],
                common_demre_traps=[
                    "En interés compuesto con capitalización trimestral o mensual, olvidar ajustar tanto la tasa anual como el número de períodos al mismo intervalo de tiempo.",
                    "Simplificar $\\frac{\\log(a)}{\\log(b)}$ como $\\log(a - b)$ (en realidad equivale a $\\log_b(a)$)."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-NUM-01A",
                        title="Ejercicio Intercalado M2: Cambio de Base y Potencias Fraccionarias",
                        stem_text="¿Cuál es el valor numérico exacto de la siguiente expresión logarítmica?",
                        stem_latex=r"\log_{4}(32) - \log_{3}\left(\frac{1}{27}\right)",
                        options={
                            "A": r"\frac{11}{2}",
                            "B": r"-\frac{1}{2}",
                            "C": r"5",
                            "D": r"\frac{7}{2}",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Expresamos ambos términos en base prima: $\log_{2^2}(2^5) = \frac{5}{2}$.",
                            r"2. Para el segundo término: $\frac{1}{27} = 3^{-3} \implies \log_3(3^{-3}) = -3$.",
                            r"3. Restamos respetando signos: $\frac{5}{2} - (-3) = \frac{5}{2} + 3 = \frac{11}{2}$."
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
                unit_title="Unidad Exclusiva M2: Análisis de Sistemas 2x2 (Compatibilidad), Discriminante y Función Potencia",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Álgebra y Funciones (Sistemas Paramétricos y Naturaleza de Raíces)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "En **M2**, no solo se pide resolver un sistema $2 \\times 2$, sino **determinar para qué valor de un parámetro $k$** "
                    "el sistema tiene **solución única**, **infinitas soluciones** o **ninguna solución**.\n\n"
                    "Asimismo, en ecuaciones cuadráticas $ax^2 + bx + c = 0$, se evalúa el uso del **discriminante ($\\Delta = b^2 - 4ac$)** "
                    "y las **propiedades de Cardano-Vieta** para la suma y producto de las raíces."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Criterio de Proporcionalidad en Sistemas Lineales 2x2",
                        latex_formula=r"\text{Solución Única: } \frac{a_1}{a_2} \neq \frac{b_1}{b_2} \quad ; \quad \text{Infinitas: } \frac{a_1}{a_2} = \frac{b_1}{b_2} = \frac{c_1}{c_2} \quad ; \quad \text{Sin Solución: } \frac{a_1}{a_2} = \frac{b_1}{b_2} \neq \frac{c_1}{c_2}",
                        explanation="Permite hallar inmediatamente parámetros desconocidos comparando las razones entre coeficientes."
                    ),
                    FormulaCard(
                        title="Propiedades de las Raíces de la Ecuación Cuadrática (Cardano-Vieta)",
                        latex_formula=r"x_1 + x_2 = -\frac{b}{a} \quad ; \quad x_1 \cdot x_2 = \frac{c}{a} \quad ; \quad \Delta = b^{2} - 4ac",
                        explanation="Si piden (1/x_1 + 1/x_2), basta con sumar las fracciones como (x_1 + x_2)/(x_1 · x_2) = -b/c sin calcular cada raíz por separado."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Sistemas con Parámetro k",
                resolution_recipe_steps=[
                    "Paso 1 (Alineación Estándar): Ordena ambas ecuaciones en la forma a·x + b·y = c.",
                    "Paso 2 (Planteamiento de Razones): Escribe la proporción entre los coeficientes de x y los coeficientes de y: a₁/a₂ = b₁/b₂.",
                    "Paso 3 (Resolución Cruzada): Despeja los valores candidatos del parámetro k.",
                    "Paso 4 (Verificación en c₁/c₂): Reemplaza cada valor de k en la razón de los términos libres para distinguir entre rectas paralelas (sin solución) y rectas coincidentes (infinitas soluciones)."
                ],
                common_demre_traps=[
                    "En problemas donde $\\frac{a_1}{a_2} = \\frac{b_1}{b_2}$ arroja dos soluciones para $k$ (ej. $k = \\pm 3$), olvidar comprobar cuál de las dos hace que $\\frac{b_1}{b_2} \\neq \\frac{c_1}{c_2}$."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-ALG-01A",
                        title="Ejercicio Intercalado M2: Sistema Paramétrico Sin Solución",
                        stem_text="¿Para qué valor real de k el siguiente sistema de ecuaciones lineales NO tiene solución?",
                        stem_latex=r"\begin{cases} kx + 3y = 7 \\ 4x + 6y = 10 \end{cases}",
                        options={
                            "A": r"k = 2",
                            "B": r"k = -2",
                            "C": r"k = 6",
                            "D": r"k = \frac{21}{5}",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Para que el sistema no tenga solución, debe cumplirse $\frac{k}{4} = \frac{3}{6} \neq \frac{7}{10}$.",
                            r"2. De la primera igualdad despejamos $k$: $\frac{k}{4} = \frac{1}{2} \implies k = 2$.",
                            r"3. Verificamos que $\frac{1}{2} \neq \frac{7}{10}$ se cumple, por lo que para $k = 2$ las rectas son paralelas no coincidentes."
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
                unit_title="Unidad Exclusiva M2: Homotecia, Razones Trigonométricas y Relaciones Métricas",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Geometría (Homotecia Vectorial y Trigonometría en Triángulo Rectángulo)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "En **Geometría M2** destacan dos grandes bloques exclusivos:\n"
                    "1. **Homotecia de centro $O$ y razón $k \\neq 0$**: Si $k > 0$ es una homotecia directa (la figura imagen queda al mismo lado del centro $O$); "
                    "si $k < 0$ es una homotecia inversa (la figura se invierte al otro lado de $O$). Los perímetros varían en factor $|k|$ y las áreas en factor $k^2$.\n"
                    "2. **Trigonometría en el Triángulo Rectángulo**: Razones seno, coseno y tangente de ángulos agudos y ángulos notables ($30^\\circ, 45^\\circ, 60^\\circ$)."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Razón de Homotecia en Longitudes, Perímetros y Áreas",
                        latex_formula=r"\frac{\overline{OA'}}{\overline{OA}} = |k| \quad ; \quad \frac{P_{\text{imagen}}}{P_{\text{original}}} = |k| \quad ; \quad \frac{A_{\text{imagen}}}{A_{\text{original}}} = k^{2}",
                        explanation="El área de la figura homotética siempre se multiplica por el cuadrado de la razón de homotecia."
                    ),
                    FormulaCard(
                        title="Razones Trigonométricas e Identidad Pitagórica",
                        latex_formula=r"\sin(\alpha) = \frac{\text{Cat. Opuesto}}{\text{Hipotenusa}}, \quad \cos(\alpha) = \frac{\text{Cat. Adyacente}}{\text{Hipotenusa}}, \quad \tan(\alpha) = \frac{\text{Cat. Opuesto}}{\text{Cat. Adyacente}}",
                        explanation="En ángulos notables: sen(30°) = cos(60°) = 1/2, sen(45°) = cos(45°) = √2/2, sen(60°) = cos(30°) = √3/2 y tan(45°) = 1."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Homotecia y Trigonometría",
                resolution_recipe_steps=[
                    "Paso 1 (Signo de la Homotecia): Si el centro O está ENTRE el punto original A y su imagen A', la razón k es obligatoriamente NEGATIVA.",
                    "Paso 2 (Relación de Área): Si el problema da la razón entre las áreas (A'/A = 9), extrae raíz cuadrada (|k| = 3) y asígnale el signo según la posición de la figura.",
                    "Paso 3 (Ángulos de Elevación y Depresión): En trigonometría, dibuja el triángulo rectángulo identificando qué cateto está frente al ángulo (opuesto) y cuál pegado al ángulo (adyacente)."
                ],
                common_demre_traps=[
                    "Confundir la distancia $\\overline{AA'}$ con la distancia desde el centro de homotecia $\\overline{OA'}$ (especialmente cuando $k < 0$, donde $\\overline{AA'} = \\overline{OA} + \\overline{OA'}$).",
                    "Usar $|k|$ en lugar de $k^2$ al calcular el área de un polígono homotético."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-GEO-01A",
                        title="Ejercicio Intercalado M2: Variación de Área bajo Homotecia Inversa",
                        stem_text="A un triángulo ABC de área 12 cm² se le aplica una homotecia de razón k = -3. ¿Cuál es el área del triángulo imagen A'B'C'?",
                        stem_latex=r"A_{\text{imagen}} = k^{2} \cdot A_{\text{original}} = (-3)^{2} \cdot 12",
                        options={
                            "A": r"108\text{ cm}^{2}",
                            "B": r"36\text{ cm}^{2}",
                            "C": r"-36\text{ cm}^{2}",
                            "D": r"4\text{ cm}^{2}",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Sabemos que la razón entre áreas homotéticas es $k^2 = (-3)^2 = 9$.",
                            r"2. Multiplicamos el área original por 9: $A_{\text{imagen}} = 9 \cdot 12 = 108\text{ cm}^2$ (un área geométrica siempre es positiva)."
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
                unit_title="Unidad Exclusiva M2:Medidas de Dispersión, Combinatoria, Probabilidad Condicional y Binomial",
                demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Probabilidad y Estadística (Varianza, Desviación Estándar, Combinatoria y Condicional)",
                theoretical_framework_md=(
                    "### Marco Teórico Oficial DEMRE (M2)\n"
                    "En **M2** se evalúan cuatro temas avanzados de probabilidad y estadística:\n"
                    "1. **Medidas de Dispersión (Varianza $\\sigma^2$ y Desviación Estándar $\\sigma$)**: Miden qué tan homogéneos o dispersos están los datos respecto a su media. Si todos los datos son iguales, $\\sigma = 0$.\n"
                    "2. **Técnicas de Conteo (Permutación, Variación y Combinación)**: Saber distinguir si **importa el orden** (Variación/Permutación) o **NO importa el orden** (Combinatoria $\\binom{n}{k}$).\n"
                    "3. **Probabilidad Condicional y Modelo Binomial**: $P(A \\mid B) = \\frac{P(A \\cap B)}{P(B)}$."
                ),
                key_formulas=[
                    FormulaCard(
                        title="Varianza, Desviación Estándar y Propiedades ante Transformaciones",
                        latex_formula=r"\sigma^{2} = \frac{\sum_{i=1}^{n} (x_i - \bar{x})^{2}}{n} \quad ; \quad \sigma(aX + b) = |a| \cdot \sigma(X)",
                        explanation="Sumar una constante b a todos los datos de una muestra NO altera su desviación estándar ni su varianza."
                    ),
                    FormulaCard(
                        title="Combinatoria, Variación sin Repetición y Distribución Binomial",
                        latex_formula=r"C_{k}^{n} = \binom{n}{k} = \frac{n!}{k!(n - k)!} \quad ; \quad P(X = k) = \binom{n}{k} p^{k} (1 - p)^{n - k}",
                        explanation="Usa Combinatoria para formar comisiones o grupos sin cargos jerárquicos; usa Variación cuando hay cargos distintos (ej. Presidente, Secretario y Tesorero)."
                    ),
                ],
                resolution_recipe_title="Receta Algorítmica DEMRE M2 para Distinguir Técnicas de Conteo",
                resolution_recipe_steps=[
                    "Paso 1 (Prueba del Intercambio): Imagina que eliges a Juan y Pedro. Si cambiar el orden a Pedro y Juan genera el MISMO resultado (ej. un comité de 2 personas), NO importa el orden -> usa Combinación C(n,k).",
                    "Paso 2 (Orden Relevante): Si cambiar el orden genera un resultado DISTINTO (ej. una clave numérica o podio 1° y 2° lugar), SÍ importa el orden -> usa Principio Multiplicativo o Variación V(n,k).",
                    "Paso 3 (Probabilidad Condicional): Cuando el enunciado dice 'Sabiendo que ocurrió B, ¿cuál es la probabilidad de A?', restringe tu denominador únicamente al total de casos del evento conocido B."
                ],
                common_demre_traps=[
                    "Creer que si a todos los puntajes de un curso se les suman 15 puntos de bonificación, la desviación estándar también aumenta en 15 (la desviación estándar se mantiene exactamente igual).",
                    "Usar permutación $n!$ en lugar de combinación $\\binom{n}{k}$ al elegir un subgrupo sin orden."
                ],
                interleaved_exercises=[
                    InterleavedExercise(
                        exercise_id="EX-M2-PROB-01A",
                        title="Ejercicio Intercalado M2: Combinatoria vs Variación",
                        stem_text="De un grupo de 8 científicos se debe escoger una comisión de 3 integrantes sin distinción de cargo. ¿De cuántas maneras distintas se puede formar dicha comisión?",
                        stem_latex=r"\binom{8}{3} = \frac{8!}{3! \cdot (8 - 3)!}",
                        options={
                            "A": r"56",
                            "B": r"336",
                            "C": r"24",
                            "D": r"512",
                        },
                        correct_option="A",
                        step_by_step_solution=[
                            r"1. Como no hay distinción de cargo, no importa el orden en que sean elegidos (Combinación).",
                            r"2. Desarrollamos el número combinatorio: $\binom{8}{3} = \frac{8 \cdot 7 \cdot 6}{3 \cdot 2 \cdot 1}$.",
                            r"3. Simplificamos $3 \cdot 2 \cdot 1 = 6$ con el $6$ del numerador: queda $8 \cdot 7 = 56\text{ comisiones distintas}$."
                        ]
                    )
                ]
            ),
        ],
    }
