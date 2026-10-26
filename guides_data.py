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


class InterleavedGuideExercise(BaseModel):
    exercise_id: str
    title: str
    stem_text: str
    stem_latex: str
    options: Dict[Literal["A", "B", "C", "D"], str]
    correct_option: Literal["A", "B", "C", "D"]
    step_by_step_solution: List[str]


class DEMREExhaustiveGuide(BaseModel):
    guide_id: str
    micro_unit_id: str = "NUM_CONJUNTOS"
    exam: ExamType
    thematic_axis: ThematicAxis
    unit_title: str
    short_description: str = ""
    subtopic_filter_keyword: str = ""
    demre_syllabus_reference: str
    theoretical_framework_md: str
    key_formulas: List[FormulaCard]
    resolution_recipe_title: str
    resolution_recipe_steps: List[str]
    common_demre_traps: List[str]
    interleaved_exercises: List[InterleavedGuideExercise]


# =====================================================================
# 1. LAS 4 GUÍAS MAESTRAS PAES M1 (ALINEADAS 1 A 1 CON EL DASHBOARD)
#    1) Números
#    2) Álgebra y Funciones
#    3) Geometría
#    4) Probabilidad y Estadística
# =====================================================================

PAES_M1_EXHAUSTIVE_GUIDES: Dict[ThematicAxis, List[DEMREExhaustiveGuide]] = {
    "NUMEROS": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-UNIDAD-NUMEROS",
            micro_unit_id="NUM_CONJUNTOS",
            exam="M1",
            thematic_axis="NUMEROS",
            unit_title="Unidad 1: Números (PAES M1)",
            short_description=(
                "Guía completa del Eje Números M1: Conjuntos Numéricos (Enteros y Racionales), "
                "Razones y Proporciones, Porcentajes, Potencias y Raíces Enésimas."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference=(
                "Temario Oficial DEMRE M1 • Eje Números (24,6% de la prueba: 16 de 65 preguntas)."
            ),
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Números (PAES M1)\n"
                "Esta guía integra todos los contenidos evaluados en el eje de **Números** de tu Dashboard:\n\n"
                "#### 1. Conjuntos Numéricos ($\\mathbb{Z}$ y $\\mathbb{Q}$), Potencias y Raíces\n"
                "- **Jerarquía PAPOMUDAS:** Paréntesis, Potencias y Raíces, Multiplicación y División (de izquierda a derecha), Adición y Sustracción.\n"
                "- **Transformación de Decimales a Fracción:** Todo decimal finito, periódico ($0,\\overline{a} = a/9$) o semiperiódico debe transformarse a fracción irreducible antes de operar.\n"
                "- **Potencias y Raíces:** Cuidado con el signo en $(-a)^n$ vs $-a^n$. En exponentes negativos se invierte la base: $(a/b)^{-n} = (b/a)^n$.\n\n"
                "#### 2. Razones y Proporciones\n"
                "- Si dos cantidades $A$ y $B$ están en la razón $a : b$, se modelan con la constante de proporcionalidad $k$ como $A = ak$ y $B = bk$.\n"
                "- **Proporcionalidad Directa:** Cociente constante ($y/x = k$). **Proporcionalidad Inversa:** Producto constante ($x \\cdot y = k$).\n\n"
                "#### 3. Porcentajes y Variación Porcentual\n"
                "- Un aumento del $p\\%$ equivale a multiplicar por $(1 + p/100)$ y un descuento del $d\\%$ equivale a multiplicar por $(1 - d/100)$.\n"
                "- En **variaciones porcentuales sucesivas**, se multiplican los factores individuales; nunca se suman ni restan los porcentajes directamente."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Conversión de Decimales Periódicos y Semiperiódicos",
                    latex_formula=r"0,\overline{ab} = \frac{ab}{99} \qquad;\qquad 0,c\overline{ab} = \frac{cab - c}{990}",
                    explanation="Un 9 por cada cifra bajo el período y un 0 por cada cifra del anteperíodo decimal.",
                ),
                FormulaCard(
                    title="2. Leyes de Potencias y Raíces Enésimas",
                    latex_formula=r"\left(\frac{a}{b}\right)^{-n} = \left(\frac{b}{a}\right)^n \quad;\quad a^n \cdot a^m = a^{n+m} \quad;\quad \sqrt[n]{a\cdot b} = \sqrt[n]{a}\cdot\sqrt[n]{b}",
                    explanation="Invierte la fracción para positivizar el exponente y descompón raíces buscando potencias perfectas.",
                ),
                FormulaCard(
                    title="3. Constante k en Razones y Proporciones",
                    latex_formula=r"\frac{A}{B} = \frac{a}{b} \implies A = ak \;\land\; B = bk",
                    explanation="Reemplaza A=ak y B=bk en la suma o diferencia total para hallar k inmediatamente.",
                ),
                FormulaCard(
                    title="4. Factor Multiplicativo de Porcentajes Sucesivos",
                    latex_formula=r"V_{\text{final}} = V_{\text{inicial}} \cdot \left(1 \pm \frac{p_1}{100}\right) \cdot \left(1 \pm \frac{p_2}{100}\right)",
                    explanation="Para recuperar el valor original antes de un recargo p%, divide el valor final entre (1 + p/100).",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Números",
            resolution_recipe_steps=[
                "Paso 1 (Identificar Sub-tema): ¿Es operatoria de fracciones/potencias, reparto en razón a:b, o variación porcentual?",
                "Paso 2 (Estandarizar Datos): Convierte decimales a fracción, razones a múltiplos de k, y porcentajes a factores decimales (ej. +20% -> 1,20; -15% -> 0,85).",
                "Paso 3 (Verificar Signos y Paréntesis): Revisa si los exponentes pares afectan o no al signo negativo antes de reducir.",
                "Paso 4 (Validar qué pide la pregunta): Confirma si preguntan por el valor final, el descuento realizado o una de las partes del reparto.",
            ],
            common_demre_traps=[
                "Confundir $(-3)^2 = 9$ con $-3^2 = -9$.",
                "Sumar o restar porcentajes sucesivos (ej. creer que subir 20% y bajar 20% deja el precio igual, cuando en realidad queda en $1,20 \\cdot 0,80 = 0,96$, bajando un 4%).",
                "Marcar el valor de la constante $k$ en un problema de razones sin multiplicarlo por la parte pedida.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-1",
                    title="Ejercicio Práctico 1 (Conjuntos Numéricos y Potencias)",
                    stem_text="¿Cuál es el valor exacto de la siguiente expresión con números racionales y potencias?",
                    stem_latex=r"\frac{(-2)^2 - \left(\frac{1}{2}\right)^{-1}}{1 - 0,\overline{3}}",
                    options={"A": r"3", "B": r"-3", "C": r"9", "D": r"\frac{4}{3}"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. En el numerador: $(-2)^2 = 4$ y $(1/2)^{-1} = 2$. Restando obtenemos $4 - 2 = 2$.",
                        "2. En el denominador: $0,\\overline{3} = 3/9 = 1/3$, por lo que $1 - 1/3 = 2/3$.",
                        "3. Dividimos: $$\\frac{2}{2/3} = 2 \\cdot \\frac{3}{2} = 3$$ (Alternativa A).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-2",
                    title="Ejercicio Práctico 2 (Razones y Proporciones)",
                    stem_text="Las edades de dos hermanos están en la razón 3 : 5. Si la suma de sus edades actuales es 48 años, ¿cuántos años tiene el hermano menor?",
                    stem_latex=r"\frac{E_1}{E_2} = \frac{3}{5} \quad \text{con} \quad E_1 + E_2 = 48",
                    options={"A": r"6", "B": r"18", "C": r"30", "D": r"16"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Modelamos las edades con la constante $k$: $E_1 = 3k$ y $E_2 = 5k$.",
                        "2. Sumamos: $3k + 5k = 48 \\implies 8k = 48 \\implies k = 6$.",
                        "3. La edad del hermano menor es: $$E_1 = 3 \\cdot 6 = 18\\text{ años}$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-3",
                    title="Ejercicio Práctico 3 (Porcentajes Sucesivos)",
                    stem_text="Un artículo cuesta $50.000. Primero sube su precio en un 20% y luego se le aplica un descuento del 10% sobre el nuevo precio. ¿Cuál es su precio final?",
                    stem_latex=r"P_f = 50\,000 \cdot (1 + 0,20) \cdot (1 - 0,10)",
                    options={"A": r"\$55\,000", "B": r"\$54\,000", "C": r"\$50\,000", "D": r"\$56\,000"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Tras el aumento del 20%: $50\\,000 \\cdot 1,20 = \\$60\\,000$.",
                        "2. Con el descuento del 10% sobre el nuevo valor: $$60\\,000 \\cdot 0,90 = \\$54\\,000$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    "ALGEBRA_Y_FUNCIONES": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-UNIDAD-ALGEBRA",
            micro_unit_id="ALG_FUNCION_CUADRATICA",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Unidad 2: Álgebra y Funciones (PAES M1)",
            short_description=(
                "Guía completa del Eje Álgebra y Funciones M1: Expresiones Algebraicas, Ecuaciones e Inecuaciones de 1° Grado, "
                "Sistemas de Ecuaciones (2x2), Función Lineal/Afín y Función Cuadrática."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference=(
                "Temario Oficial DEMRE M1 • Eje Álgebra y Funciones (33,8% de la prueba: 22 de 65 preguntas)."
            ),
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Álgebra y Funciones (PAES M1)\n"
                "Esta guía cubre el eje de mayor peso ponderado en la PAES M1, alineado directamente con tu barra de **Álgebra y Funciones** del Dashboard:\n\n"
                "#### 1. Expresiones Algebraicas, Productos Notables y Factorización\n"
                "- Dominio de cuadrado de binomio $(a \\pm b)^2$, suma por su diferencia $(a+b)(a-b) = a^2 - b^2$ y factorización de trinomios $x^2 + (p+q)x + pq = (x+p)(x+q)$.\n\n"
                "#### 2. Ecuaciones e Inecuaciones de 1° Grado y Sistemas $2\\times 2$\n"
                "- En inecuaciones lineales, **al multiplicar o dividir por un número negativo se invierte el sentido de la desigualdad** ($<$ pasa a $>$).\n"
                "- En sistemas de ecuaciones $2\\times 2$, el método de reducción (sumar ecuaciones para cancelar una incógnita) es el camino más directo.\n\n"
                "#### 3. Función Lineal, Función Afín y Función Cuadrática\n"
                "- **Función Afín ($f(x) = mx + n$):** $n = f(0)$ es el cargo fijo inicial y $m$ es la pendiente o cobro variable por unidad.\n"
                "- **Función Cuadrática ($f(x) = ax^2 + bx + c$):** Su vértice $V(h, k)$ entrega el punto donde ocurre el óptimo ($h = -\\frac{b}{2a}$) y el valor máximo o mínimo alcanzado ($k = f(h)$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Productos Notables Esenciales",
                    latex_formula=r"(a \pm b)^2 = a^2 \pm 2ab + b^2 \qquad;\qquad (a+b)(a-b) = a^2 - b^2",
                    explanation="Factoriza siempre antes de simplificar fracciones algebraicas.",
                ),
                FormulaCard(
                    title="2. Inversión de Desigualdad en Inecuaciones",
                    latex_formula=r"-ax \leq b \quad (a > 0) \iff x \geq -\frac{b}{a}",
                    explanation="Dividir o multiplicar por un coeficiente negativo invierte el signo de orden.",
                ),
                FormulaCard(
                    title="3. Función Afín y Pendiente de la Recta",
                    latex_formula=r"f(x) = mx + n \quad \text{con} \quad m = \frac{y_2 - y_1}{x_2 - x_1}, \;\; n = f(0)",
                    explanation="n representa el valor fijo inicial (intercepto eje Y) y m la tasa de cambio por unidad.",
                ),
                FormulaCard(
                    title="4. Vértice y Óptimo de la Función Cuadrática",
                    latex_formula=r"V(h, k) = \left(-\frac{b}{2a},\; f\left(-\frac{b}{2a}\right)\right)",
                    explanation="h = -b/(2a) indica el instante/valor x del óptimo; k = f(h) indica la altura o ganancia máxima/mínima.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Álgebra y Funciones",
            resolution_recipe_steps=[
                "Paso 1 (Traducir del Lenguaje Verbal al Algebraico): Define con claridad qué representa la incógnita $x$ (y $y$ si hay dos variables).",
                "Paso 2 (Cuidar Signos en Despejes): Si despejas una inecuación con coeficiente negativo en $x$, invierte de inmediato la desigualdad.",
                "Paso 3 (Distinguir Cargo Fijo vs Variable): En funciones lineales/afines, asocia el cobro por unidad a la pendiente $m$ y el cobro base a $n$.",
                "Paso 4 (Distinguir h vs k en Parábolas): En función cuadrática, verifica si piden dónde ocurre el máximo ($h$) o cuál es el valor máximo ($k = f(h)$).",
            ],
            common_demre_traps=[
                "Desarrollar $(a - b)^2$ como $a^2 - b^2$ olvidando el doble producto $-2ab$.",
                "En problemas de función cuadrática, marcar $h = -\\frac{b}{2a}$ cuando preguntaban por la altura máxima $k = f(h)$.",
                "En sistemas de ecuaciones $2\\times 2$, encontrar $x$ y marcar ese valor cuando la pregunta pedía $(x - y)$ o el valor de $y$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-1",
                    title="Ejercicio Práctico 1 (Expresiones Algebraicas)",
                    stem_text="Para todo x distinto de 4, ¿a qué expresión equivale la siguiente fracción algebraica?",
                    stem_latex=r"\frac{x^2 - 16}{x - 4} - (x - 4)",
                    options={"A": r"0", "B": r"8", "C": r"2x", "D": r"x + 4"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Factorizamos $x^2 - 16 = (x - 4)(x + 4)$ y simplificamos $(x - 4)$, quedando $(x + 4)$.",
                        "2. Restamos cuidando el signo del paréntesis: $$(x + 4) - (x - 4) = x + 4 - x + 4 = 8$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-2",
                    title="Ejercicio Práctico 2 (Sistemas de Ecuaciones 2x2)",
                    stem_text="En un estacionamiento hay 25 vehículos entre autos (4 ruedas) y motos (2 ruedas). Si en total se cuentan 80 ruedas, ¿cuántos autos hay?",
                    stem_latex=r"\begin{cases} A + M = 25 \\ 4A + 2M = 80 \end{cases}",
                    options={"A": r"10", "B": r"15", "C": r"12", "D": r"20"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Multiplicamos la primera ecuación por $-2$: $-2A - 2M = -50$.",
                        "2. Sumamos con la segunda ecuación: $$2A = 30 \\implies A = 15\\text{ autos}$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-3",
                    title="Ejercicio Práctico 3 (Función Cuadrática)",
                    stem_text="La altura h(t) en metros de un balón lanzado hacia arriba a los t segundos está dada por h(t) = -5t² + 30t + 5. ¿Cuál es la altura máxima que alcanza el balón?",
                    stem_latex=r"h(t) = -5t^2 + 30t + 5",
                    options={"A": r"3\text{ m}", "B": r"45\text{ m}", "C": r"50\text{ m}", "D": r"35\text{ m}"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. Calculamos el tiempo del vértice: $t_v = -\\frac{30}{2(-5)} = 3$ segundos.",
                        "2. Evaluamos la altura máxima en $t = 3$: $$h(3) = -5(3)^2 + 30(3) + 5 = -45 + 90 + 5 = 50\\text{ m}$$ (Alternativa C).",
                    ],
                ),
            ],
        ),
    ],
    "GEOMETRIA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-UNIDAD-GEOMETRIA",
            micro_unit_id="GEO_PITAGORAS",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Unidad 3: Geometría (PAES M1)",
            short_description=(
                "Guía completa del Eje Geometría M1: Perímetro y Área de Figuras 2D, Cuerpos Geométricos 3D, "
                "Teorema de Pitágoras, Transformaciones Isométricas y Semejanza / Teorema de Thales."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference=(
                "Temario Oficial DEMRE M1 • Eje Geometría (21,5% de la prueba: 14 de 65 preguntas)."
            ),
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Geometría (PAES M1)\n"
                "Esta guía reúne todos los temas del eje de **Geometría** de tu Dashboard:\n\n"
                "#### 1. Teorema de Pitágoras y Figuras 2D (Perímetro y Área)\n"
                "- En todo triángulo rectángulo de catetos $a, b$ e hipotenusa $c$ se cumple $a^2 + b^2 = c^2$. Ternas frecuentes: $(3,4,5)$, $(5,12,13)$, $(8,15,17)$.\n"
                "- El área de una región sombreada se obtiene restando $\\text{Área Exterior} - \\text{Área en Blanco}$.\n\n"
                "#### 2. Cuerpos Geométricos 3D (Prismas y Cilindros)\n"
                "- El volumen de todo prisma recto o cilindro es el área de su base por la altura: $V = A_{\\text{base}} \\cdot h$. En el cilindro: $V = \\pi r^2 h$.\n\n"
                "#### 3. Transformaciones Isométricas y Semejanza (Thales)\n"
                "- **Rotaciones antihorarias respecto al origen:** $R_{90^\\circ}(x,y) = (-y, x)$, $R_{180^\\circ}(x,y) = (-x, -y)$, $R_{270^\\circ}(x,y) = (y, -x)$.\n"
                "- **Semejanza de figuras:** Si la razón lineal entre lados homólogos es $k$, entonces la razón entre sus **áreas** es $k^2$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Teorema de Pitágoras, Diagonal del Cuadrado y Triángulo Equilátero",
                    latex_formula=r"c = \sqrt{a^2 + b^2} \quad;\quad d_{\text{cuad}} = a\sqrt{2} \quad;\quad A_{\text{equilátero}} = \frac{a^2\sqrt{3}}{4}",
                    explanation="Identifica siempre el lado opuesto al ángulo de 90° como la hipotenusa c.",
                ),
                FormulaCard(
                    title="2. Área del Trapecio, Círculo y Volumen del Cilindro",
                    latex_formula=r"A_{\text{trap}} = \frac{(B+b)\cdot h}{2} \quad;\quad A_{\odot} = \pi r^2 \quad;\quad V_{\text{cilindro}} = \pi r^2 h",
                    explanation="Si te dan el diámetro D, divídelo primero por 2 para obtener el radio r = D/2.",
                ),
                FormulaCard(
                    title="3. Traslación y Rotaciones Antihorarias respecto al Origen",
                    latex_formula=r"T_{\vec{v}}(x,y)=(x+v_x, y+v_y) \quad;\quad R_{90^\circ}(x,y)=(-y,x) \quad;\quad R_{180^\circ}(x,y)=(-x,-y)",
                    explanation="El vector traslación entre un punto inicial P y su imagen P' es v = P' - P.",
                ),
                FormulaCard(
                    title="4. Semejanza (Razón de Áreas k²) y Teorema de Thales",
                    latex_formula=r"\frac{L_1}{L_2} = k \implies \frac{A_1}{A_2} = k^2 \qquad;\qquad L_1 \parallel L_2 \implies \frac{AB}{BC} = \frac{DE}{EF}",
                    explanation="Para comparar las bases paralelas en un triángulo con Thales, usa el lado lateral completo del triángulo mayor.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Geometría",
            resolution_recipe_steps=[
                "Paso 1 (Anotar Medidas en la Figura): Si dan diámetro $D$, escribe de inmediato $r = D/2$. Si hay ángulos de $90^\\circ$, busca ternas pitagóricas.",
                "Paso 2 (Descomponer en Figuras Simples): Expresa áreas sombreadas o volúmenes compuestos como sumas/restas de figuras conocidas.",
                "Paso 3 (Cuidar el Orden en Isometrías): En transformaciones sucesivas (ej. rotar y luego trasladar), aplica cada regla coordenada a coordenada en orden.",
                "Paso 4 (Elevar al Cuadrado en Áreas Semejantes): Si te piden el área de una figura semejante, multiplica el área original por $k^2$.",
            ],
            common_demre_traps=[
                "Reemplazar el diámetro directamente en $\\pi r^2$ sin dividirlo por 2.",
                "Multiplicar el área por la razón lineal $k$ en vez de por $k^2$ en triángulos semejantes.",
                "En el Teorema de Thales con bases paralelas, no sumar el lado completo del triángulo grande.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-1",
                    title="Ejercicio Práctico 1 (Teorema de Pitágoras)",
                    stem_text="Una escalera de 13 metros se apoya en una pared vertical. Si la base de la escalera está a 5 metros del muro, ¿a qué altura llega la escalera?",
                    stem_latex=r"h = \sqrt{13^2 - 5^2}",
                    options={"A": r"8\text{ m}", "B": r"12\text{ m}", "C": r"10\text{ m}", "D": r"\sqrt{194}\text{ m}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. La escalera (13 m) es la hipotenusa y la distancia al muro (5 m) es un cateto.",
                        "2. Calculamos el cateto altura: $$h = \\sqrt{169 - 25} = \\sqrt{144} = 12\\text{ m}$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-2",
                    title="Ejercicio Práctico 2 (Transformaciones Isométricas)",
                    stem_text="Al punto A(4, -2) se le aplica una rotación de 90° antihorario respecto al origen y luego una traslación según el vector v = (-1, 3). ¿Cuáles son las coordenadas finales?",
                    stem_latex=r"A(4, -2) \xrightarrow{R_{90^\circ}} A'(2, 4) \xrightarrow{T(-1, 3)} A''",
                    options={"A": r"(1, 7)", "B": r"(3, 1)", "C": r"(-3, 7)", "D": r"(1, -1)"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Con $R_{90^\\circ}(x,y) = (-y, x)$, el punto $(4, -2)$ pasa a $A'(2, 4)$.",
                        "2. Sumamos el vector $(-1, 3)$: $$A'' = (2 - 1, 4 + 3) = (1, 7)$$ (Alternativa A).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-3",
                    title="Ejercicio Práctico 3 (Semejanza y Razón de Áreas)",
                    stem_text="Dos triángulos semejantes tienen lados homólogos en la razón 2 : 5. Si el área del triángulo menor es 12 cm², ¿cuál es el área del triángulo mayor?",
                    stem_latex=r"\frac{A_{\text{menor}}}{A_{\text{mayor}}} = \left(\frac{2}{5}\right)^2 = \frac{4}{25}",
                    options={"A": r"30\text{ cm}^2", "B": r"60\text{ cm}^2", "C": r"75\text{ cm}^2", "D": r"48\text{ cm}^2"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. La razón entre las áreas es el cuadrado de la razón lineal: $(2/5)^2 = 4/25$.",
                        "2. Despejamos el área mayor: $$A_{\\text{mayor}} = \\frac{12 \\cdot 25}{4} = 75\\text{ cm}^2$$ (Alternativa C).",
                    ],
                ),
            ],
        ),
    ],
    "PROBABILIDAD_Y_ESTADISTICA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-UNIDAD-PROBABILIDAD",
            micro_unit_id="PROB_POSICION",
            exam="M1",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Unidad 4: Probabilidad y Estadística (PAES M1)",
            short_description=(
                "Guía completa del Eje Probabilidad y Estadística M1: Tablas y Gráficos, "
                "Medidas de Tendencia Central, Medidas de Posición (Cuartiles/Boxplot) y Reglas de Probabilidad."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference=(
                "Temario Oficial DEMRE M1 • Eje Probabilidad y Estadística (20,0% de la prueba: 13 de 65 preguntas)."
            ),
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Probabilidad y Estadística (PAES M1)\n"
                "Esta guía cubre todos los contenidos asociados a tu barra de **Probabilidad y Estadística** del Dashboard:\n\n"
                "#### 1. Tablas de Frecuencia y Medidas de Tendencia Central\n"
                "- **Frecuencia absoluta ($f_i$)** vs **Frecuencia acumulada ($F_i = f_1 + \\dots + f_i$)**. El promedio para datos en tabla es $\\bar{x} = \\frac{\\sum x_i f_i}{N}$.\n"
                "- **Mediana:** Dato central tras ordenar de menor a mayor. **Moda:** Dato $x_i$ con la mayor frecuencia $f_i$.\n\n"
                "#### 2. Medidas de Posición (Cuartiles, Percentiles y Diagrama de Cajón)\n"
                "- Los cuartiles $Q_1, Q_2, Q_3$ dividen la muestra ordenada en 4 partes de **25% cada una**.\n"
                "- En un **Boxplot (Diagrama de Cajón)**, la caja central va de $Q_1$ a $Q_3$ y contiene el **50% central** de los datos ($\text{RIC} = Q_3 - Q_1$).\n\n"
                "#### 3. Reglas de Probabilidad (Laplace, Unión e Intersección)\n"
                "- **Conectivo 'O' (Unión):** $P(A \\cup B) = P(A) + P(B) - P(A \\cap B)$.\n"
                "- **Conectivo 'Y' (Intersección):** $P(A \\cap B) = P(A) \\cdot P(B)$ (ajustando el total si es extracción sin reposición)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Promedio en Tablas de Frecuencia",
                    latex_formula=r"\bar{x} = \frac{x_1 f_1 + x_2 f_2 + \dots + x_k f_k}{N} \implies \sum x_i f_i = N\cdot \bar{x}",
                    explanation="Multiplicar el promedio por la cantidad total de datos N entrega inmediatamente la suma total.",
                ),
                FormulaCard(
                    title="2. Posición de Cuartiles/Percentiles y Rango Intercuartílico (RIC)",
                    latex_formula=r"\text{Pos}(P_k) = \frac{k \cdot N}{100} \qquad;\qquad \text{RIC} = Q_3 - Q_1",
                    explanation="Entre Q1 y Q3 se concentra siempre el 50% central de los datos.",
                ),
                FormulaCard(
                    title="3. Regla de Laplace, Regla Aditiva y Multiplicativa",
                    latex_formula=r"P(A) = \frac{\text{Casos Favorables}}{\text{Casos Totales}} \quad;\quad P(A \cup B) = P(A) + P(B) - P(A \cap B)",
                    explanation="En extracciones sin reposición, reduce en 1 el denominador en la segunda extracción.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Probabilidad y Estadística",
            resolution_recipe_steps=[
                "Paso 1 (Ordenar los Datos): Si piden mediana, cuartiles o rango de una lista suelta, ordénala primero de menor a mayor.",
                "Paso 2 (Completar Frecuencia Acumulada $F_i$): En tablas, calcula la columna $F_i$ para ubicar rápidamente mediana y cuartiles.",
                "Paso 3 (Analizar el Conectivo en Probabilidades): Si pide 'evento A o evento B', suma y resta la intersección; si pide 'A y luego B', multiplica.",
            ],
            common_demre_traps=[
                "Confundir la moda con la frecuencia máxima $f_{\\max}$ (la moda es el valor del dato $x_i$, no cuántas veces se repite).",
                "Creer que un tramo más ancho del diagrama de cajón tiene más datos (todos los tramos entre cuartiles tienen exactamente el 25% de los datos).",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-1",
                    title="Ejercicio Práctico 1 (Medidas de Tendencia Central)",
                    stem_text="El promedio de 5 números es 14. Si se agrega un sexto número, el nuevo promedio de los 6 números sube a 16. ¿Cuál fue el sexto número agregado?",
                    stem_latex=r"\frac{5\cdot 14 + x_6}{6} = 16",
                    options={"A": r"15", "B": r"20", "C": r"26", "D": r"30"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. La suma inicial de los 5 números es $5 \\cdot 14 = 70$.",
                        "2. La nueva suma de los 6 números es $6 \\cdot 16 = 96$.",
                        "3. Restamos: $$x_6 = 96 - 70 = 26$$ (Alternativa C).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-2",
                    title="Ejercicio Práctico 2 (Cuartiles y Diagrama de Cajón)",
                    stem_text="En un ensayo rendido por 200 estudiantes, el primer cuartil fue Q1 = 480 puntos y el tercer cuartil fue Q3 = 640 puntos. ¿Cuántos estudiantes obtuvieron entre 480 y 640 puntos?",
                    stem_latex=r"\text{Porcentaje entre } Q_1 \text{ y } Q_3 = 75\% - 25\% = 50\%",
                    options={"A": r"50", "B": r"100", "C": r"150", "D": r"160"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Entre $Q_1$ y $Q_3$ siempre se concentra el 50% central de la muestra.",
                        "2. Calculamos el 50% de 200 estudiantes: $$0,50 \\cdot 200 = 100\\text{ estudiantes}$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-3",
                    title="Ejercicio Práctico 3 (Reglas de Probabilidad sin Reposición)",
                    stem_text="En una caja hay 4 tarjetas rojas y 6 azules. Si se extraen 2 tarjetas al azar una tras otra SIN reposición, ¿cuál es la probabilidad de que ambas sean rojas?",
                    stem_latex=r"P(R_1 \cap R_2) = \frac{4}{10} \cdot \frac{3}{9}",
                    options={"A": r"\frac{4}{25}", "B": r"\frac{2}{15}", "C": r"\frac{1}{5}", "D": r"\frac{7}{19}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Primera extracción: $4/10$. Segunda extracción sin reposición: quedan 3 rojas de 9 ($3/9$).",
                        "2. Multiplicamos: $$\\frac{4}{10} \\cdot \\frac{3}{9} = \\frac{12}{90} = \\frac{2}{15}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
}


# =====================================================================
# 2. LAS 4 GUÍAS MAESTRAS PAES M2 (ALINEADAS 1 A 1 CON EL DASHBOARD)
# =====================================================================

PAES_M2_EXHAUSTIVE_GUIDES: Dict[ThematicAxis, List[DEMREExhaustiveGuide]] = {
    "NUMEROS": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-UNIDAD-NUMEROS",
            micro_unit_id="NUM_CONJUNTOS",
            exam="M2",
            thematic_axis="NUMEROS",
            unit_title="Unidad 1: Números (PAES M2)",
            short_description=(
                "Guía completa del Eje Números M2: Números Reales e Irracionales, Racionalización, "
                "Logaritmos y Matemática Financiera (Interés Compuesto)."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Números (Reales, Logaritmos y Matemática Financiera).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Números (PAES M2)\n"
                "Además de todo el temario de Números M1, en **PAES M2** se evalúan tres pilares científicos y financieros:\n\n"
                "#### 1. Números Reales ($\\mathbb{R}$), Irracionales y Racionalización\n"
                "- Racionalizar fracciones del tipo $\\frac{A}{\\sqrt{b}}$ o $\\frac{A}{\\sqrt{a} \\pm \\sqrt{b}}$ multiplicando por su conjugado.\n\n"
                "#### 2. Logaritmos y sus Propiedades\n"
                "- Definición fundamental: $\\log_b(a) = c \\iff b^c = a$ (con $b > 0, b \\neq 1, a > 0$).\n\n"
                "#### 3. Matemática Financiera e Interés Compuesto\n"
                "- Capitalización compuesta: $C_f = C_0(1 + i)^n$, homologando siempre la tasa $i$ y el número de períodos $n$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Propiedades Operativas de Logaritmos",
                    latex_formula=r"\log_b(xy) = \log_b(x)+\log_b(y) \quad;\quad \log_b\left(\frac{x}{y}\right)=\log_b(x)-\log_b(y) \quad;\quad \log_b(x^n)=n\log_b(x)",
                    explanation="Convierte siempre las raíces en exponentes fraccionarios antes de aplicar logaritmos.",
                ),
                FormulaCard(
                    title="2. Fórmula de Interés Compuesto",
                    latex_formula=r"C_f = C_0 \cdot \left(1 + \frac{r}{100}\right)^n",
                    explanation="Si la capitalización es semestral, divide la tasa anual por 2 y multiplica los años por 2.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Números M2",
            resolution_recipe_steps=[
                "Paso 1 (Bases Primas en Logaritmos): Escribe cada número como potencia de base prima ($2, 3, 5, 10$).",
                "Paso 2 (Homologar Tasa y Tiempo): En interés compuesto, ajusta la tasa al período de capitalización antes de elevar a $n$.",
            ],
            common_demre_traps=[
                "Escribir $\\log(a + b) = \\log(a) + \\log(b)$ (falso: el logaritmo solo separa productos y cocientes).",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-NUM-1",
                    title="Ejercicio Práctico 1 (Logaritmos M2)",
                    stem_text="¿Cuál es el valor exacto de la siguiente expresión logarítmica?",
                    stem_latex=r"\log_2(32) + \log_3\left(\frac{1}{9}\right) - \log(100)",
                    options={"A": r"1", "B": r"5", "C": r"-1", "D": r"3"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Evaluamos cada término: $\\log_2(32) = 5$, $\\log_3(1/9) = -2$ y $\\log_{10}(100) = 2$.",
                        "2. Operamos: $$5 - 2 - 2 = 1$$ (Alternativa A).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M2-NUM-2",
                    title="Ejercicio Práctico 2 (Matemática Financiera M2)",
                    stem_text="Se invierten $500.000 al 12% anual de interés compuesto con capitalización semestral durante 3 años. ¿Cuál es el capital acumulado?",
                    stem_latex=r"C_f = 500\,000 \cdot (1 + i_{\text{sem}})^{n_{\text{sem}}}",
                    options={
                        "A": r"500\,000 \cdot (1,12)^3",
                        "B": r"500\,000 \cdot (1,06)^6",
                        "C": r"500\,000 \cdot (1,06)^3",
                        "D": r"500\,000 \cdot (1,12)^6",
                    },
                    correct_option="B",
                    step_by_step_solution=[
                        "1. La tasa semestral es $12\\% / 2 = 6\\% = 0,06$, y en 3 años hay $3 \\cdot 2 = 6$ semestres.",
                        "2. Por tanto: $$C_f = 500\\,000 \\cdot (1,06)^6$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    "ALGEBRA_Y_FUNCIONES": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-UNIDAD-ALGEBRA",
            micro_unit_id="ALG_SISTEMAS_2X2",
            exam="M2",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Unidad 2: Álgebra y Funciones (PAES M2)",
            short_description=(
                "Guía completa del Eje Álgebra y Funciones M2: Análisis Paramétrico de Sistemas 2x2, "
                "Discriminante en Función Cuadrática, Función Potencia, Exponencial y Logarítmica."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Álgebra y Funciones.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Álgebra y Funciones (PAES M2)\n"
                "En **PAES M2**, el eje de Álgebra y Funciones profundiza en el análisis estructural de parámetros:\n\n"
                "#### 1. Análisis de Compatibilidad en Sistemas de Ecuaciones ($2\\times 2$)\n"
                "- **Solución Única:** $\\frac{a_1}{a_2} \\neq \\frac{b_1}{b_2}$.\n"
                "- **Infinitas Soluciones:** $\\frac{a_1}{a_2} = \\frac{b_1}{b_2} = \\frac{c_1}{c_2}$.\n"
                "- **Sin Solución:** $\\frac{a_1}{a_2} = \\frac{b_1}{b_2} \\neq \\frac{c_1}{c_2}$.\n\n"
                "#### 2. Naturaleza de las Raíces en Función Cuadrática (Discriminante $\\Delta$)\n"
                "- El discriminante $\\Delta = b^2 - 4ac$ determina si la parábola corta al eje $X$ en 2 puntos ($\\Delta > 0$), es tangente en 1 punto ($\\Delta = 0$) o no corta al eje $X$ ($\\Delta < 0$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Condición de Sistemas Sin Solución vs Infinitas Soluciones",
                    latex_formula=r"\text{Sin solución: }\frac{a_1}{a_2}=\frac{b_1}{b_2}\neq\frac{c_1}{c_2} \qquad;\qquad \text{Infinitas: }\frac{a_1}{a_2}=\frac{b_1}{b_2}=\frac{c_1}{c_2}",
                    explanation="Alinea siempre las columnas x, y y término libre antes de plantear las proporciones.",
                ),
                FormulaCard(
                    title="2. Discriminante y Propiedades de Cardano-Vieta",
                    latex_formula=r"\Delta = b^2 - 4ac \qquad;\qquad x_1 + x_2 = -\frac{b}{a} \qquad;\qquad x_1 \cdot x_2 = \frac{c}{a}",
                    explanation="Tangencia al eje X equivale exactamente a imponer Delta = 0.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Álgebra y Funciones M2",
            resolution_recipe_steps=[
                "Paso 1 (Igualar Razones en Sistemas): Plantea $\\frac{a_1}{a_2} = \\frac{b_1}{b_2}$ para hallar los valores candidatos del parámetro $k$.",
                "Paso 2 (Comprobar con Términos Libres): Sustituye $k$ y verifica si $\\frac{b_1}{b_2}$ coincide o difiere de $\\frac{c_1}{c_2}$.",
                "Paso 3 (Usar el Discriminante): Si el enunciado habla de número de intersecciones de una parábola con el eje $X$, plantea el signo de $\\Delta = b^2 - 4ac$.",
            ],
            common_demre_traps=[
                "No verificar la tercera razón $\\frac{c_1}{c_2}$ al buscar un sistema sin solución.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-ALG-1",
                    title="Ejercicio Práctico 1 (Sistema 2x2 con Parámetro k)",
                    stem_text="¿Para qué valor real de k el siguiente sistema de ecuaciones NO tiene solución?",
                    stem_latex=r"\begin{cases} kx + 3y = 7 \\ 4x + 6y = 10 \end{cases}",
                    options={"A": r"k = 2", "B": r"k = 4", "C": r"k = -2", "D": r"k = 6"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Igualamos las razones de los coeficientes de $x$ e $y$: $\\frac{k}{4} = \\frac{3}{6} = \\frac{1}{2} \\implies k = 2$.",
                        "2. Verificamos que difiera de la razón de términos libres: $\\frac{1}{2} \\neq \\frac{7}{10}$. Luego, para $k = 2$ no tiene solución (Alternativa A).",
                    ],
                ),
            ],
        ),
    ],
    "GEOMETRIA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-UNIDAD-GEOMETRIA",
            micro_unit_id="GEO_HOMOTECIA_M2",
            exam="M2",
            thematic_axis="GEOMETRIA",
            unit_title="Unidad 3: Geometría (PAES M2)",
            short_description=(
                "Guía completa del Eje Geometría M2: Homotecia (directa e inversa, razón en áreas k²), "
                "Razones Trigonométricas en el Triángulo Rectángulo y Geometría Analítica."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Geometría (Homotecia y Trigonometría).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Geometría (PAES M2)\n"
                "Además de la geometría plana y espacial de M1, **PAES M2** incorpora dos temas exclusivos de alta frecuencia:\n\n"
                "#### 1. Homotecia de Centro $O$ y Razón $k$\n"
                "- Si $k > 0$, la homotecia es **directa** (mismo lado respecto al centro $O$). Si $k < 0$, es **inversa** (la imagen se invierte al otro lado de $O$).\n"
                "- Los perímetros escalan por $|k|$ y las **áreas escalan por $k^2$**.\n\n"
                "#### 2. Razones Trigonométricas en el Triángulo Rectángulo\n"
                "- $\\sin(\\alpha) = \\frac{\\text{Opuesto}}{\\text{Hipotenusa}}$, $\\cos(\\alpha) = \\frac{\\text{Adyacente}}{\\text{Hipotenusa}}$, $\\tan(\\alpha) = \\frac{\\text{Opuesto}}{\\text{Adyacente}}$.\n"
                "- Valores notables: $\\tan(30^\\circ) = \\frac{\\sqrt{3}}{3}$, $\\tan(45^\\circ) = 1$, $\\tan(60^\\circ) = \\sqrt{3}$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Escalamiento de Perímetros y Áreas bajo Homotecia",
                    latex_formula=r"P' = |k|\cdot P \qquad;\qquad A' = k^2 \cdot A",
                    explanation="Aunque la razón de homotecia k sea negativa, el área siempre se multiplica por k^2 > 0.",
                ),
                FormulaCard(
                    title="2. Razones Trigonométricas y Ángulos Notables",
                    latex_formula=r"\sin(30^\circ)=\frac{1}{2}, \quad \cos(30^\circ)=\frac{\sqrt{3}}{2}, \quad \tan(30^\circ)=\frac{\sqrt{3}}{3}, \quad \tan(60^\circ)=\sqrt{3}",
                    explanation="En problemas de alturas y sombras horizontales, usa directamente la tangente.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Geometría M2",
            resolution_recipe_steps=[
                "Paso 1 (Homotecia): Si piden razón de áreas, eleva al cuadrado la razón de homotecia $k$.",
                "Paso 2 (Trigonometría): Dibuja el triángulo rectángulo, ubica el ángulo de elevación $\\alpha$ en la horizontal y relaciona cateto opuesto (altura) con adyacente (distancia) vía $\\tan(\\alpha)$.",
            ],
            common_demre_traps=[
                "Multiplicar el área original por $|k|$ en lugar de $k^2$ en una homotecia.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-GEO-1",
                    title="Ejercicio Práctico 1 (Homotecia M2)",
                    stem_text="A un triángulo de área 15 cm² se le aplica una homotecia de razón k = -3. ¿Cuál es el área del triángulo resultante?",
                    stem_latex=r"A' = (-3)^2 \cdot 15",
                    options={"A": r"45\text{ cm}^2", "B": r"135\text{ cm}^2", "C": r"-45\text{ cm}^2", "D": r"90\text{ cm}^2"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. El factor de cambio para el área es $k^2 = (-3)^2 = 9$.",
                        "2. Multiplicamos: $$A' = 9 \\cdot 15 = 135\\text{ cm}^2$$ (Alternativa B).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M2-GEO-2",
                    title="Ejercicio Práctico 2 (Trigonometría M2)",
                    stem_text="Desde un punto en el suelo a 40 metros de la base de una torre, el ángulo de elevación hacia la cúspide es de 30°. ¿Cuál es la altura de la torre?",
                    stem_latex=r"\tan(30^\circ) = \frac{H}{40}",
                    options={"A": r"40\sqrt{3}\text{ m}", "B": r"\frac{40\sqrt{3}}{3}\text{ m}", "C": r"20\text{ m}", "D": r"20\sqrt{3}\text{ m}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Como $\\tan(30^\\circ) = \\frac{\\sqrt{3}}{3}$, planteamos $\\frac{\\sqrt{3}}{3} = \\frac{H}{40}$.",
                        "2. Despejamos: $$H = \\frac{40\\sqrt{3}}{3}\\text{ m}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    "PROBABILIDAD_Y_ESTADISTICA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-UNIDAD-PROBABILIDAD",
            micro_unit_id="PROB_CONTEO_M2",
            exam="M2",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Unidad 4: Probabilidad y Estadística (PAES M2)",
            short_description=(
                "Guía completa del Eje Probabilidad y Estadística M2: Medidas de Dispersión (Varianza y Desviación Estándar), "
                "Probabilidad Condicional y Técnicas de Conteo / Combinatoria."
            ),
            subtopic_filter_keyword="",
            demre_syllabus_reference="Temario Oficial DEMRE M2 • Eje Probabilidad y Estadística (Dispersión, Condicional y Combinatoria).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico Completo: Unidad de Probabilidad y Estadística (PAES M2)\n"
                "En **PAES M2**, el eje estadístico incorpora tres herramientas avanzadas:\n\n"
                "#### 1. Técnicas de Conteo y Combinatoria\n"
                "- **¿Importa el orden?** Si NO importa el orden (ej. elegir una comisión o grupo sin cargos), usa **Combinación** $\\binom{n}{k} = \\frac{n!}{k!(n-k)!}$. Si SÍ importa el orden (ej. podio o claves), usa **Variación** $V_k^n = \\frac{n!}{(n-k)!}$.\n\n"
                "#### 2. Probabilidad Condicional\n"
                "- $P(A \\mid B) = \\frac{P(A \\cap B)}{P(B)}$: restringe el denominador exclusivamente al subgrupo que cumple la condición $B$.\n\n"
                "#### 3. Medidas de Dispersión (Varianza $\\sigma^2$ y Desviación Estándar $\\sigma$)\n"
                "- Sumar una constante $c$ a todos los datos **no cambia** la desviación estándar; multiplicar todos los datos por $k$ multiplica la desviación estándar por $|k|$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Combinación (Sin Orden) vs Variación (Con Orden)",
                    latex_formula=r"C_k^n = \binom{n}{k} = \frac{n!}{k!(n-k)!} \qquad;\qquad V_k^n = \frac{n!}{(n-k)!}",
                    explanation="Usa Combinación siempre que elijas comités, grupos de estudio o subconjuntos.",
                ),
                FormulaCard(
                    title="2. Probabilidad Condicional y Propiedad de la Varianza",
                    latex_formula=r"P(A \mid B) = \frac{P(A \cap B)}{P(B)} = \frac{n(A \cap B)}{n(B)} \qquad;\qquad \sigma(kx + c) = |k|\cdot\sigma(x)",
                    explanation="En tablas de doble entrada, divide los casos de la celda (A y B) por el total de la fila/columna de B.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica Paso a Paso: Eje Probabilidad y Estadística M2",
            resolution_recipe_steps=[
                "Paso 1 (Combinatoria): Pregúntate si cambiar el orden de dos elegidos cambia el grupo; si es el mismo grupo, aplica $\\binom{n}{k}$.",
                "Paso 2 (Condicional): Identifica la condición 'dado que ocurrió B' y pon el total de B como nuevo denominador.",
            ],
            common_demre_traps=[
                "Usar Variación en vez de Combinación al formar comisiones sin distinción de cargos.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-PROB-1",
                    title="Ejercicio Práctico 1 (Combinatoria M2)",
                    stem_text="De un grupo de 8 estudiantes se debe escoger una delegación de 3 representantes con igual rol. ¿De cuántas formas distintas se puede elegir la delegación?",
                    stem_latex=r"\binom{8}{3} = \frac{8!}{3!\cdot 5!}",
                    options={"A": r"336", "B": r"56", "C": r"24", "D": r"512"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Como no hay cargos distintos, no importa el orden (Combinación).",
                        "2. Calculamos: $$\\binom{8}{3} = \\frac{8 \\cdot 7 \\cdot 6}{3 \\cdot 2 \\cdot 1} = 56\\text{ formas}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
}


def get_exhaustive_guides_by_exam(exam: ExamType) -> Dict[ThematicAxis, List[DEMREExhaustiveGuide]]:
    if exam == "M1":
        return PAES_M1_EXHAUSTIVE_GUIDES
    return PAES_M2_EXHAUSTIVE_GUIDES
