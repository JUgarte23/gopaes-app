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
    interleaved_exercises: List[InterleavedGuideGuideExercise] if False else List[InterleavedGuideExercise]


# =====================================================================
# 1. CATÁLOGO GRANULAR DE MICRO-UNIDADES PAES M1 (16 SUB-TEMAS DEMRE)
# =====================================================================

PAES_M1_EXHAUSTIVE_GUIDES: Dict[ThematicAxis, List[DEMREExhaustiveGuide]] = {
    # -----------------------------------------------------------------
    # EJE 1: NÚMEROS (M1)
    # -----------------------------------------------------------------
    "NUMEROS": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-NUM-CONJ",
            micro_unit_id="NUM_CONJUNTOS",
            exam="M1",
            thematic_axis="NUMEROS",
            unit_title="Conjuntos Numéricos (Enteros y Racionales)",
            short_description="Operatoria en Z y Q, jerarquía PAPOMUDAS, transformación de decimales periódicos y propiedades de potencias y raíces.",
            subtopic_filter_keyword="conjuntos",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Números: Conjuntos de los números enteros y racionales, potencias y raíces enésimas.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Enteros ($\\mathbb{Z}$), Racionales ($\\mathbb{Q}$), Potencias y Raíces\n"
                "En **PAES M1**, el eje de Conjuntos Numéricos evalúa la precisión al operar signos, fracciones compuestas y potencias:\n\n"
                "- **Jerarquía de Operaciones (PAPOMUDAS):** Paréntesis (de adentro hacia afuera), Potencias/Raíces, Multiplicación/División (de izquierda a derecha) y Adición/Sustracción.\n"
                "- **Decimales Infinitos en $\\mathbb{Q}$:** Todo decimal finito, periódico o semiperiódico puede escribirse como fracción de enteros.\n"
                "- **Potencias de Exponente Negativo:** Invertir la base racional cambia el signo del exponente."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Signo en Potencias de Base Negativa",
                    latex_formula=r"(-a)^n \neq -a^n \quad \text{para } n \text{ par}; \quad (-3)^2 = 9 \;\;\text{vs.}\;\; -3^2 = -9",
                    explanation="El exponente solo afecta al signo negativo si éste está dentro del paréntesis.",
                ),
                FormulaCard(
                    title="2. Conversión de Decimal Periódico y Semiperiódico",
                    latex_formula=r"0,\overline{ab} = \frac{ab}{99} \qquad \text{y} \qquad 0,c\overline{ab} = \frac{cab - c}{990}",
                    explanation="Un 9 por cada cifra bajo el período y un 0 por cada cifra del anteperíodo decimal.",
                ),
                FormulaCard(
                    title="3. Potencia con Exponente Entero Negativo",
                    latex_formula=r"\left(\frac{a}{b}\right)^{-n} = \left(\frac{b}{a}\right)^n = \frac{b^n}{a^n} \quad (a, b \neq 0)",
                    explanation="Invierte numerador y denominador antes de elevar a la potencia positiva.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Operatoria Racional y Potencias",
            resolution_recipe_steps=[
                "Paso 1 (Todo a Fracción): Convierte cualquier decimal periódico o finito a fracción irreducible antes de operar.",
                "Paso 2 (Blindaje de Signos): Evalúa primero $(-a)^n$ identificando si el signo está dentro del paréntesis.",
                "Paso 3 (Exponentes Negativos): Invierte las bases con exponente negativo.",
                "Paso 4 (Reducción Final): Resuelve la división principal multiplicando la fracción superior por el recíproco de la inferior.",
            ],
            common_demre_traps=[
                "Confundir $-4^2 = -16$ con $(-4)^2 = 16$.",
                "Convertir $0,3\\overline{3}$ como $3/10$ en vez de $3/9 = 1/3$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-CONJ-1",
                    title="Ejercicio Práctico 1: Fracciones y Potencias con Signo",
                    stem_text="¿Cuál es el valor exacto de la siguiente expresión numérica?",
                    stem_latex=r"\frac{(-2)^2 - \left(\frac{1}{2}\right)^{-1}}{1 - 0,\overline{3}}",
                    options={"A": r"3", "B": r"-3", "C": r"9", "D": r"\frac{4}{3}"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Evaluamos las potencias del numerador: $(-2)^2 = 4$ y $(1/2)^{-1} = 2$. Por tanto, el numerador vale $4 - 2 = 2$.",
                        "2. En el denominador convertimos el decimal periódico: $0,\\overline{3} = \\frac{3}{9} = \\frac{1}{3}$, luego $1 - \\frac{1}{3} = \\frac{2}{3}$.",
                        "3. Dividimos numerador entre denominador: $$\\frac{2}{\\frac{2}{3}} = 2 \\cdot \\frac{3}{2} = 3$$ (Alternativa A).",
                    ],
                ),
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-CONJ-2",
                    title="Ejercicio Práctico 2: Raíces y Descomposición",
                    stem_text="¿Cuál es el valor simplificado de la siguiente suma de raíces cuadradas?",
                    stem_latex=r"\sqrt{75} - \sqrt{12} + \sqrt{27}",
                    options={"A": r"6\sqrt{3}", "B": r"4\sqrt{3}", "C": r"\sqrt{90}", "D": r"9\sqrt{3}"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Descomponemos cada cantidad subradical buscando cuadrados perfectos: $\\sqrt{75} = \\sqrt{25 \\cdot 3} = 5\\sqrt{3}$.",
                        "2. De igual forma, $\\sqrt{12} = \\sqrt{4 \\cdot 3} = 2\\sqrt{3}$ y $\\sqrt{27} = \\sqrt{9 \\cdot 3} = 3\\sqrt{3}$.",
                        "3. Agrupamos términos semejantes: $$(5 - 2 + 3)\\sqrt{3} = 6\\sqrt{3}$$ (Alternativa A).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-NUM-RAZ",
            micro_unit_id="NUM_RAZONES_PROP",
            exam="M1",
            thematic_axis="NUMEROS",
            unit_title="Razones y Proporciones",
            short_description="Razón geométrica, constante k de reparto proporcional, proporcionalidad directa e inversa.",
            subtopic_filter_keyword="razones",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Números: Problemas de razones y proporciones en diversos contextos.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Razones y Proporcionalidad\n"
                "Una **razón** entre dos cantidades $a$ y $b$ es el cociente $\\frac{a}{b}$ (se lee '$a$ es a $b$'). La igualdad entre dos razones forma una **proporción**:\n\n"
                "- **Constante de Reparto ($k$):** Si dos cantidades están en la razón $a : b$, podemos escribirlas inmediatamente como $A = a\\cdot k$ y $B = b\\cdot k$.\n"
                "- **Proporcionalidad Directa:** Al aumentar una variable, la otra aumenta en la misma razón ($\\frac{y}{x} = k$).\n"
                "- **Proporcionalidad Inversa:** Al aumentar una variable (ej. cantidad de trabajadores), la otra disminuye en la misma proporción ($x \\cdot y = k$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Parametrización por Constante de Razón k",
                    latex_formula=r"\frac{A}{B} = \frac{a}{b} \implies A = ak \;\land\; B = bk",
                    explanation="Sustituye A y B en el dato total del enunciado para despejar k en un solo paso.",
                ),
                FormulaCard(
                    title="2. Proporcionalidad Directa vs. Inversa",
                    latex_formula=r"\text{Directa: } \frac{y_1}{x_1} = \frac{y_2}{x_2} \qquad \text{Inversa: } x_1 \cdot y_1 = x_2 \cdot y_2",
                    explanation="En problemas de obreros vs. tiempo de entrega, usa siempre el producto constante (inversa).",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Problemas de Razones y Proporciones",
            resolution_recipe_steps=[
                "Paso 1 (Asignar k): Si el problema dice que las partes están en razón $m : n$, escribe $m k$ y $n k$.",
                "Paso 2 (Plantear Ecuación del Total o Diferencia): Suma o resta los múltiplos de $k$ e iguala al total dado.",
                "Paso 3 (Responder lo pedido): Una vez hallado $k$, multiplícalo por el coeficiente de la parte que pregunta el DEMRE.",
            ],
            common_demre_traps=[
                "Entregar el valor de la constante $k$ como respuesta final en lugar de multiplicar por la parte pedida.",
                "Aplicar regla de tres directa en problemas de velocidad-tiempo o trabajadores-días (que son inversamente proporcionales).",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-RAZ-1",
                    title="Ejercicio Práctico 1: Reparto Proporcional",
                    stem_text="Las edades de dos hermanos están en la razón 3 : 5. Si la suma de sus edades actuales es 48 años, ¿cuántos años tiene el hermano menor?",
                    stem_latex=r"\frac{E_1}{E_2} = \frac{3}{5} \quad \text{con} \quad E_1 + E_2 = 48",
                    options={"A": r"6", "B": r"18", "C": r"30", "D": r"16"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Expresamos las edades mediante la constante $k$: $E_1 = 3k$ (menor) y $E_2 = 5k$ (mayor).",
                        "2. Usamos el dato de la suma: $3k + 5k = 48 \\implies 8k = 48 \\implies k = 6$.",
                        "3. Calculamos la edad del hermano menor: $$E_1 = 3 \\cdot 6 = 18\\text{ años}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-NUM-PCT",
            micro_unit_id="NUM_PORCENTAJES",
            exam="M1",
            thematic_axis="NUMEROS",
            unit_title="Porcentajes",
            short_description="Factores multiplicativos, variaciones porcentuales sucesivas, cálculo del valor original antes de IVA/descuento.",
            subtopic_filter_keyword="porcentaje",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Números: Concepto y cálculo de porcentaje y problemas aplicados.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Porcentajes y Variación Multiplicativa\n"
                "El porcentaje $p\\%$ equivale al operador racional $\\frac{p}{100}$. Para resolver ejercicios PAES en segundos:\n\n"
                "- **Aumento del $p\\%$:** Multiplica la cantidad por $\\left(1 + \\frac{p}{100}\\right)$.\n"
                "- **Descuento del $d\\%$:** Multiplica la cantidad por $\\left(1 - \\frac{d}{100}\\right)$.\n"
                "- **Variaciones Sucesivas:** Se multiplican los factores individuales; **jamás** se suman ni restan los porcentajes directamente."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Variación Porcentual Sucesiva",
                    latex_formula=r"V_{\text{final}} = V_{\text{inicial}} \cdot \left(1 \pm \frac{p_1}{100}\right) \cdot \left(1 \pm \frac{p_2}{100}\right)",
                    explanation="Subir un 20% y luego bajar un 20% equivale a multiplicar por 1,20 * 0,80 = 0,96 (baja un 4%).",
                ),
                FormulaCard(
                    title="2. Variación Porcentual Relativa",
                    latex_formula=r"\%\Delta = \frac{V_{\text{final}} - V_{\text{inicial}}}{V_{\text{inicial}}} \cdot 100\%",
                    explanation="Siempre se divide por el valor inicial (referencia del 100%).",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Problemas de Porcentajes",
            resolution_recipe_steps=[
                "Paso 1 (Identificar el 100%): Define cuál es el valor base inicial antes del cambio.",
                "Paso 2 (Traducir a Factor Decimal): Convierte cada aumento o descuento en su factor $(1 \\pm p/100)$.",
                "Paso 3 (Operar o Despejar): Multiplica los factores si buscas el valor final, o divide por el factor si buscas el precio original.",
            ],
            common_demre_traps=[
                "Creer que un aumento del 30% seguido de un descuento del 30% deja el precio igual (en realidad disminuye un 9%).",
                "Para quitar un 20% de recargo, restar el 20% del precio final en vez de dividir entre $1,20$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-NUM-PCT-1",
                    title="Ejercicio Práctico: Cambio Porcentual Sucesivo",
                    stem_text="Un producto cuesta $50.000. Primero se le aplica un aumento del 20% y luego un descuento del 10% sobre el nuevo precio. ¿Cuál es el precio final?",
                    stem_latex=r"P_f = 50\,000 \cdot (1 + 0,20) \cdot (1 - 0,10)",
                    options={"A": r"\$55\,000", "B": r"\$54\,000", "C": r"\$50\,000", "D": r"\$56\,000"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Tras el aumento del 20%, el precio pasa a ser $50\\,000 \\cdot 1,20 = \\$60\\,000$.",
                        "2. Aplicamos el descuento del 10% sobre los $\\$60\\,000$: $$60\\,000 \\cdot 0,90 = \\$54\\,000$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    # -----------------------------------------------------------------
    # EJE 2: ÁLGEBRA Y FUNCIONES (M1)
    # -----------------------------------------------------------------
    "ALGEBRA_Y_FUNCIONES": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-ALG-EXP",
            micro_unit_id="ALG_EXPRESIONES",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Expresiones Algebraicas",
            short_description="Productos notables (cuadrado de binomio, suma por su diferencia), factorización de trinomios y simplificación.",
            subtopic_filter_keyword="expresiones",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Álgebra: Productos notables, factorizaciones y reducción de expresiones algebraicas.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Productos Notables y Factorización\n"
                "El dominio de las identidades algebraicas permite simplificar expresiones y modelar áreas geométricas sin desarrollar multiplicaciones extensas."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Cuadrado de Binomio y Suma por su Diferencia",
                    latex_formula=r"(a \pm b)^2 = a^2 \pm 2ab + b^2 \qquad \text{y} \qquad (a+b)(a-b) = a^2 - b^2",
                    explanation="Recuerda siempre incluir el doble producto central 2ab en el cuadrado de binomio.",
                ),
                FormulaCard(
                    title="2. Factorización de Trinomio Mónico",
                    latex_formula=r"x^2 + (p+q)x + (p\cdot q) = (x+p)(x+q)",
                    explanation="Busca dos números que multiplicados den el término libre y sumados den el coeficiente de x.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Simplificación Algebraica",
            resolution_recipe_steps=[
                "Paso 1 (Factor Común): Extrae primero cualquier factor numérico o literal común a todos los términos.",
                "Paso 2 (Reconocer Patrón): Si hay 2 términos con resta de cuadrados usa $(a+b)(a-b)$; si hay 3 términos usa trinomio.",
                "Paso 3 (Cancelar Factores): Simplifica únicamente factores completos multiplicativos, nunca sumandos sueltos.",
            ],
            common_demre_traps=[
                "Escribir $(x - 5)^2 = x^2 - 25$ olvidando el término central $-10x$ y el signo positivo de $+25$.",
                "Simplificar la $x^2$ en $\\frac{x^2 - 9}{x^2}$ sin factorizar.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-EXP-1",
                    title="Ejercicio Práctico: Factorización y Simplificación",
                    stem_text="Para todo x distinto de 4, ¿a qué expresión equivale la siguiente fracción algebraica?",
                    stem_latex=r"\frac{x^2 - 16}{x - 4} - (x - 4)",
                    options={"A": r"0", "B": r"8", "C": r"2x", "D": r"x + 4"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Factorizamos el numerador por suma por su diferencia: $x^2 - 16 = (x - 4)(x + 4)$.",
                        "2. Simplificamos el factor $(x - 4)$: la fracción queda como $(x + 4)$.",
                        "3. Restamos cuidando el paréntesis: $$(x + 4) - (x - 4) = x + 4 - x + 4 = 8$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-ALG-EC1",
            micro_unit_id="ALG_ECUACIONES_1G",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Ecuaciones e Inecuaciones de 1° Grado",
            short_description="Planteo verbal de ecuaciones lineales, despeje con coeficientes fraccionarios e inversión de desigualdad en inecuaciones.",
            subtopic_filter_keyword="inecuación",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Álgebra: Ecuaciones e inecuaciones lineales de primer grado.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Ecuaciones e Inecuaciones Lineales\n"
                "Las ecuaciones lineales tienen una única solución real ($ax + b = c$), mientras que las inecuaciones entregan un intervalo de soluciones. "
                "La regla de oro en inecuaciones es **invertir el sentido de la desigualdad** al multiplicar o dividir por un número negativo."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Inversión de Desigualdad por Factor Negativo",
                    latex_formula=r"-ax \leq b \quad (a > 0) \iff x \geq -\frac{b}{a}",
                    explanation="Al dividir entre -a, el símbolo <= cambia obligatoriamente a >=.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Resolución de Inecuaciones",
            resolution_recipe_steps=[
                "Paso 1 (Eliminar Denominadores): Multiplica toda la ecuación o inecuación por el MCM positivo de los denominadores.",
                "Paso 2 (Agrupar la Incógnita): Deja los términos con $x$ a un lado y las constantes al otro.",
                "Paso 3 (Verificar Signo del Coeficiente): Si el número que multiplica a $x$ es negativo, invierte el signo de desigualdad al despejar.",
            ],
            common_demre_traps=[
                "Dividir por un número negativo en una inecuación sin invertir el signo $<$ o $\\leq$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-EC1-1",
                    title="Ejercicio Práctico: Inecuación de 1° Grado",
                    stem_text="¿Cuál es el conjunto solución de la siguiente inecuación lineal?",
                    stem_latex=r"7 - 3x < 19",
                    options={"A": r"x > -4", "B": r"x < -4", "C": r"x > 4", "D": r"x < -\frac{26}{3}"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Restamos 7 en ambos miembros: $-3x < 12$.",
                        "2. Dividimos entre $-3$ invirtiendo el sentido de la desigualdad: $$x > \\frac{12}{-3} \\implies x > -4$$ (Alternativa A).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-ALG-SIS",
            micro_unit_id="ALG_SISTEMAS_2X2",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Sistemas de Ecuaciones (2x2)",
            short_description="Modelamiento con dos incógnitas, método de reducción (eliminación), sustitución e interpretación geométrica de rectas.",
            subtopic_filter_keyword="sistemas",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Álgebra: Sistemas de ecuaciones lineales (2x2).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Sistemas Lineales $2 \\times 2$\n"
                "Un sistema de dos ecuaciones lineales con dos incógnitas representa dos rectas en el plano cartesiano. Su solución $(x, y)$ es el punto de intersección entre ambas rectas."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Estructura Estándar del Sistema 2x2",
                    latex_formula=r"\begin{cases} a_1 x + b_1 y = c_1 \\ a_2 x + b_2 y = c_2 \end{cases}",
                    explanation="Ordena siempre las columnas x, y y término libre antes de aplicar reducción.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Método de Reducción Rápida",
            resolution_recipe_steps=[
                "Paso 1 (Definir Variables): Identifica claramente qué representa $x$ (ej. cantidad) y qué representa $y$.",
                "Paso 2 (Igualar Coeficientes Opuestos): Multiplica una ecuación para que una variable tenga signos opuestos ($+by$ y $-by$).",
                "Paso 3 (Sumar y Sustituir): Suma verticalmente para despejar la primera incógnita y reemplaza en la ecuación más simple.",
            ],
            common_demre_traps=[
                "Encontrar el valor de $x$ y marcarlo inmediatamente cuando la pregunta pedía $(x + y)$ o el valor de $y$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-SIS-1",
                    title="Ejercicio Práctico: Sistema 2x2 Aplicado",
                    stem_text="En un estacionamiento hay 25 vehículos entre autos (4 ruedas) y motos (2 ruedas). Si en total se cuentan 80 ruedas, ¿cuántos autos hay?",
                    stem_latex=r"\begin{cases} A + M = 25 \\ 4A + 2M = 80 \end{cases}",
                    options={"A": r"10", "B": r"15", "C": r"12", "D": r"20"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Multiplicamos la primera ecuación por $-2$: $-2A - 2M = -50$.",
                        "2. Sumamos con la segunda ecuación: $(4A - 2A) = 80 - 50 \\implies 2A = 30 \\implies A = 15$ autos (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-ALG-LIN",
            micro_unit_id="ALG_FUNCION_LINEAL",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Función Lineal y Afín",
            short_description="Modelamiento de cargo fijo (coeficiente de posición n) y costo variable (pendiente m), gráficas e intersección con ejes.",
            subtopic_filter_keyword="lineal",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Álgebra y Funciones: Función lineal y afín.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Función Lineal y Función Afín\n"
                "- **Función Lineal ($f(x) = mx$):** Pasa por el origen $(0,0)$ y modela proporcionalidad directa.\n"
                "- **Función Afín ($f(x) = mx + n$):** Tiene pendiente $m$ (tasa de cambio por unidad) y coeficiente de posición $n$ (valor inicial cuando $x=0$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Ecuación de la Función Afín y Pendiente",
                    latex_formula=r"f(x) = mx + n \quad \text{con} \quad m = \frac{y_2 - y_1}{x_2 - x_1}, \;\; n = f(0)",
                    explanation="En problemas tarifarios, n es el cargo fijo base y m es el cobro por unidad consumida.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Modelamiento con Función Afín",
            resolution_recipe_steps=[
                "Paso 1 (Identificar el Cargo Fijo $n$): Es el monto que se paga aunque el consumo $x$ sea cero.",
                "Paso 2 (Identificar la Pendiente $m$): Es la variación por cada unidad adicional de $x$.",
                "Paso 3 (Evaluar o Igualar): Sustituye en $x$ si te dan las unidades, o iguala $f(x)$ al monto total si te piden despejar $x$.",
            ],
            common_demre_traps=[
                "Intercambiar el cargo fijo $n$ con la pendiente $m$, escribiendo $f(x) = nx + m$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-LIN-1",
                    title="Ejercicio Práctico: Modelamiento Tarifario",
                    stem_text="Un técnico cobra $15.000 por la visita a domicilio más $12.000 por cada hora de trabajo h. Si en una reparación cobró en total $51.000, ¿cuántas horas trabajó?",
                    stem_latex=r"C(h) = 12\,000h + 15\,000 = 51\,000",
                    options={"A": r"2\text{ horas}", "B": r"3\text{ horas}", "C": r"4\text{ horas}", "D": r"3,5\text{ horas}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Restamos el cargo fijo de visita: $12\\,000h = 51\\,000 - 15\\,000 = 36\\,000$.",
                        "2. Despejamos $h$: $$h = \\frac{36\\,000}{12\\,000} = 3\\text{ horas}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-ALG-CUAD",
            micro_unit_id="ALG_FUNCION_CUADRATICA",
            exam="M1",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Función Cuadrática",
            short_description="Parábola, concavidad, eje de simetría, coordenadas del vértice (máximo o mínimo) e intersecciones con los ejes.",
            subtopic_filter_keyword="cuadrática",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Álgebra y Funciones: Ecuación y función cuadrática.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Función Cuadrática y Optimización en Parábolas\n"
                "Dada $f(x) = ax^2 + bx + c$ ($a \\neq 0$):\n\n"
                "- Si $a > 0$, la parábola abre hacia arriba ($\\cup$) y su vértice es un **mínimo**.\n"
                "- Si $a < 0$, la parábola abre hacia abajo ($\\cap$) y su vértice es un **máximo**.\n"
                "- **Distinción crítica DEMRE:** $h = -\\frac{b}{2a}$ indica **cuándo** ocurre el óptimo; $k = f(h)$ indica **cuál es** el valor máximo o mínimo."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Coordenadas del Vértice V(h, k)",
                    latex_formula=r"V(h, k) = \left(-\frac{b}{2a},\; f\left(-\frac{b}{2a}\right)\right)",
                    explanation="Calcula primero h = -b/(2a) y luego reemplaza ese número en f(x) para obtener k.",
                ),
                FormulaCard(
                    title="2. Intersecciones con los Ejes",
                    latex_formula=r"\text{Eje } Y: (0, c) \qquad \text{Eje } X: x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}",
                    explanation="Los ceros o raíces de la parábola se obtienen resolviendo f(x) = 0.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Problemas de Función Cuadrática",
            resolution_recipe_steps=[
                "Paso 1 (Extraer Coeficientes): Anota con signo $a$, $b$ y $c$ desde $f(x) = ax^2 + bx + c$.",
                "Paso 2 (Leer la Pregunta): ¿Pide el tiempo/valor $x$ donde ocurre el máximo ($h$), el valor máximo alcanzado ($k$), o cuándo toca el suelo ($f(x)=0$)?",
                "Paso 3 (Calcular): Halla $h = -b/(2a)$ y, si piden el valor máximo/mínimo, evalúa $k = f(h)$.",
            ],
            common_demre_traps=[
                "Marcar $h = -\\frac{b}{2a}$ cuando el problema pregunta por la altura máxima o ganancia máxima $k = f(h)$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-ALG-CUAD-1",
                    title="Ejercicio Práctico: Altura Máxima de una Parábola",
                    stem_text="La trayectoria de un balón lanzado hacia arriba está dada por h(t) = -5t² + 30t + 5, donde h es la altura en metros y t el tiempo en segundos. ¿Cuál es la altura máxima que alcanza el balón?",
                    stem_latex=r"h(t) = -5t^2 + 30t + 5",
                    options={"A": r"3\text{ m}", "B": r"45\text{ m}", "C": r"50\text{ m}", "D": r"35\text{ m}"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. Identificamos $a = -5$, $b = 30$, $c = 5$. El instante de altura máxima es $t_v = -\\frac{30}{2(-5)} = 3$ segundos.",
                        "2. Evaluamos $h(3)$ para obtener la altura máxima: $$h(3) = -5(3)^2 + 30(3) + 5 = -45 + 90 + 5 = 50\\text{ m}$$ (Alternativa C).",
                    ],
                ),
            ],
        ),
    ],
    # -----------------------------------------------------------------
    # EJE 3: GEOMETRÍA (M1)
    # -----------------------------------------------------------------
    "GEOMETRIA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-GEO-2D",
            micro_unit_id="GEO_FIGURAS_2D",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Perímetro y Área de Figuras 2D",
            short_description="Áreas y perímetros de triángulos, paralelogramos, trapecios, círculos, sectores circulares y regiones sombreadas.",
            subtopic_filter_keyword="trapecio",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Geometría: Perímetro y áreas de triángulos, paralelogramos, trapecios y círculos.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Figuras Planas y Regiones Sombreadas\n"
                "Para calcular el área de una **región sombreada**, la estrategia estándar del DEMRE es restar el área de la figura exterior menos el área de las figuras interiores en blanco."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Área del Trapecio y del Triángulo Equilátero",
                    latex_formula=r"A_{\text{trapecio}} = \frac{(B + b)\cdot h}{2} \qquad A_{\text{equilátero}} = \frac{a^2\sqrt{3}}{4}",
                    explanation="En el trapecio, B y b son los lados paralelos (bases) y h la distancia perpendicular entre ellos.",
                ),
                FormulaCard(
                    title="2. Círculo y Circunferencia",
                    latex_formula=r"A_{\odot} = \pi r^2 \qquad P_{\odot} = 2\pi r",
                    explanation="Si el enunciado da el diámetro D, divide primero entre 2 para obtener el radio r = D/2.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Cálculo de Áreas y Perímetros 2D",
            resolution_recipe_steps=[
                "Paso 1 (Radio vs Diámetro): Si hay círculos o semicírculos, anota de inmediato $r = D/2$.",
                "Paso 2 (Descomponer Región): Expresa el área pedida como suma o resta de figuras elementales conocidas.",
                "Paso 3 (Cuidar el Perímetro): El perímetro de una figura compuesta es solo su borde exterior (no sumes líneas interiores).",
            ],
            common_demre_traps=[
                "Usar el diámetro completo en $\\pi r^2$ sin dividirlo por 2.",
                "En el perímetro de un semicírculo de radio $r$, escribir solo $\\pi r$ olvidando sumar el diámetro recto $+2r$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-2D-1",
                    title="Ejercicio Práctico: Área de Región Compuesta",
                    stem_text="En un cuadrado de lado 10 cm se inscribe un círculo que toca los cuatro lados del cuadrado. ¿Cuál es el área de la región del cuadrado que queda fuera del círculo?",
                    stem_latex=r"A_{\text{sombreada}} = A_{\text{cuadrado}} - A_{\text{círculo}}",
                    options={"A": r"100 - 100\pi\text{ cm}^2", "B": r"100 - 25\pi\text{ cm}^2", "C": r"100 - 10\pi\text{ cm}^2", "D": r"40 - 25\pi\text{ cm}^2"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. El área del cuadrado de lado 10 cm es $10^2 = 100\\text{ cm}^2$.",
                        "2. El diámetro del círculo inscrito mide 10 cm, por lo que su radio es $r = 5$ cm y su área es $\\pi(5)^2 = 25\\pi\\text{ cm}^2$.",
                        "3. Restamos ambas áreas: $$100 - 25\\pi\\text{ cm}^2$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-GEO-3D",
            micro_unit_id="GEO_CUERPOS_3D",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Cuerpos Geométricos 3D",
            short_description="Área de superficie total y volumen de prismas rectos, paralelepípedos, cubos, cilindros y conos.",
            subtopic_filter_keyword="cilíndrico",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Geometría: Área y volumen de prismas rectos y cilindros.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Prismas Rectos y Cilindros\n"
                "Todo prisma recto o cilindro tiene un volumen igual al **área de su base multiplicada por su altura**: $V = A_{\\text{basal}} \\cdot h$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Volumen y Área Total del Cilindro Recto",
                    latex_formula=r"V_{\text{cil}} = \pi r^2 h \qquad A_{\text{total}} = 2\pi r^2 + 2\pi r h",
                    explanation="Si el cilindro es abierto por arriba (ej. un vaso), cuenta solo una base pi*r^2.",
                ),
                FormulaCard(
                    title="2. Paralelepípedo Recto (Caja Rectangular)",
                    latex_formula=r"V = a\cdot b\cdot c \qquad A_{\text{total}} = 2(ab + bc + ac)",
                    explanation="Sus caras son 3 pares de rectángulos congruentes.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Problemas de Cuerpos 3D",
            resolution_recipe_steps=[
                "Paso 1 (Identificar Base y Altura): Determina qué figura 2D forma la base (círculo, triángulo, rectángulo).",
                "Paso 2 (Calcular Área Basal): Halla $A_{\\text{base}}$ con la fórmula 2D correspondiente.",
                "Paso 3 (Multiplicar por Altura): Calcula $V = A_{\\text{base}} \\cdot h$ verificando que todas las medidas estén en la misma unidad.",
            ],
            common_demre_traps=[
                "Confundir el efecto de duplicar el radio de un cilindro: como el radio está al cuadrado ($r^2$), duplicar el radio **cuadruplica** el volumen.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-3D-1",
                    title="Ejercicio Práctico: Volumen de un Cilindro",
                    stem_text="Un recipiente cilíndrico tiene un diámetro basal de 8 cm y una altura de 10 cm. ¿Cuál es su capacidad total en cm³?",
                    stem_latex=r"V = \pi r^2 h \quad \text{con } r = 4\text{ cm}, \; h = 10\text{ cm}",
                    options={"A": r"80\pi\text{ cm}^3", "B": r"160\pi\text{ cm}^3", "C": r"640\pi\text{ cm}^3", "D": r"40\pi\text{ cm}^3"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Como el diámetro es 8 cm, el radio basal es $r = 4$ cm.",
                        "2. Aplicamos la fórmula del volumen: $$V = \\pi \\cdot 4^2 \\cdot 10 = 160\\pi\\text{ cm}^3$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-GEO-ISO",
            micro_unit_id="GEO_ISOMETRICAS",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Transformaciones Isométricas",
            short_description="Vectores en el plano, traslación, rotación respecto al origen (90°, 180°, 270°) y reflexión axial/central.",
            subtopic_filter_keyword="isométrica",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Geometría: Puntos y vectores en el plano y transformaciones isométricas.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Transformaciones Isométricas\n"
                "Las transformaciones isométricas conservan la forma y el tamaño de las figuras (la figura resultante siempre es **congruente** a la original)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Traslación y Rotaciones Antihorarias respecto al Origen (0,0)",
                    latex_formula=r"T_{\vec{v}}(x,y) = (x+v_x, y+v_y) \quad;\quad R_{90^\circ}(x,y)=(-y,x), \;\; R_{180^\circ}(x,y)=(-x,-y), \;\; R_{270^\circ}(x,y)=(y,-x)",
                    explanation="Una rotación horaria de 90° equivale exactamente a una rotación antihoraria de 270°.",
                ),
                FormulaCard(
                    title="2. Simetrías respecto a los Ejes Coordenados",
                    latex_formula=r"\text{Eje } X: (x, -y) \qquad \text{Eje } Y: (-x, y)",
                    explanation="Al reflejar respecto a un eje, se conserva la coordenada de ese eje y cambia de signo la otra.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Transformaciones en el Plano",
            resolution_recipe_steps=[
                "Paso 1 (Orden Secuencial): Aplica cada transformación en el orden exacto en que aparece en el enunciado.",
                "Paso 2 (Sentido de Giro): Si no se especifica sentido en una rotación, es positiva (antihoraria).",
                "Paso 3 (Despeje de Vector): Si te dan $P$ y $P'$, el vector traslación es $\\vec{v} = P' - P$.",
            ],
            common_demre_traps=[
                "Calcular el vector traslación restando $\\text{Inicial} - \\text{Final}$ en vez de $\\text{Final} - \\text{Inicial}$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-ISO-1",
                    title="Ejercicio Práctico: Rotación y Traslación",
                    stem_text="Al punto A(4, -2) se le aplica una rotación de 90° antihorario respecto al origen y luego una traslación según el vector v = (-1, 3). ¿Cuáles son las coordenadas finales?",
                    stem_latex=r"A(4, -2) \xrightarrow{R_{90^\circ}} A'(2, 4) \xrightarrow{T(-1, 3)} A''",
                    options={"A": r"(1, 7)", "B": r"(3, 1)", "C": r"(-3, 7)", "D": r"(1, -1)"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Aplicamos $R_{90^\\circ}(x,y) = (-y, x)$ sobre $(4, -2)$: obtenemos $A' = (-(-2), 4) = (2, 4)$.",
                        "2. Sumamos el vector $\\vec{v} = (-1, 3)$: $$A'' = (2 - 1, 4 + 3) = (1, 7)$$ (Alternativa A).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-GEO-PIT",
            micro_unit_id="GEO_PITAGORAS",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Teorema de Pitágoras",
            short_description="Relación entre catetos e hipotenusa, ternas pitagóricas clásicas, diagonal de cuadrados/rectángulos y altura de triángulos.",
            subtopic_filter_keyword="pitágoras",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Geometría: Teorema de Pitágoras y sus aplicaciones.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Teorema de Pitágoras y Ternas Clásicas\n"
                "En todo triángulo rectángulo, la suma de los cuadrados de los catetos es igual al cuadrado de la hipotenusa. Memorizar las **ternas pitagóricas** ($3-4-5$, $5-12-13$, $8-15-17$) ahorra valiosos minutos en el ensayo."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Teorema de Pitágoras y Despeje de Cateto",
                    latex_formula=r"a^2 + b^2 = c^2 \implies c = \sqrt{a^2 + b^2} \quad\land\quad a = \sqrt{c^2 - b^2}",
                    explanation="La hipotenusa c es siempre el lado mayor opuesto al ángulo de 90°.",
                ),
                FormulaCard(
                    title="2. Diagonal del Cuadrado y Altura del Triángulo Equilátero",
                    latex_formula=r"d_{\text{cuadrado}} = a\sqrt{2} \qquad h_{\text{equilátero}} = \frac{a\sqrt{3}}{2}",
                    explanation="Consecuencias directas de aplicar Pitágoras en figuras regulares de lado a.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Resolución con Pitágoras",
            resolution_recipe_steps=[
                "Paso 1 (Ubicar el Ángulo Recto): Identifica cuál lado se opone a los $90^\\circ$; ésa es la hipotenusa $c$.",
                "Paso 2 (Buscar Múltiplo de Terna): Revisa si los lados son múltiplos de $(3,4,5)$ o $(5,12,13)$.",
                "Paso 3 (Despejar): Suma cuadrados si buscas la hipotenusa; resta cuadrados si buscas un cateto.",
            ],
            common_demre_traps=[
                "Sumar los cuadrados cuando el lado desconocido es un cateto (ej. la altura de un muro donde se apoya una escalera).",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-PIT-1",
                    title="Ejercicio Práctico: Escalera Apoyada en un Muro",
                    stem_text="Una escalera de 13 metros se apoya en una pared vertical. Si el pie de la escalera está a 5 metros de la base de la pared, ¿a qué altura llega la escalera?",
                    stem_latex=r"h = \sqrt{13^2 - 5^2}",
                    options={"A": r"8\text{ m}", "B": r"12\text{ m}", "C": r"\sqrt{194}\text{ m}", "D": r"10\text{ m}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. La escalera (13 m) es la hipotenusa y la distancia al muro (5 m) es un cateto.",
                        "2. Por la terna $(5, 12, 13)$ o calculando: $$h = \\sqrt{169 - 25} = \\sqrt{144} = 12\\text{ m}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-GEO-SEM",
            micro_unit_id="GEO_SEMEJANZA",
            exam="M1",
            thematic_axis="GEOMETRIA",
            unit_title="Semejanza y Proporcionalidad",
            short_description="Semejanza de triángulos, razón lineal k vs razón de áreas k², planos a escala y Teorema de Thales.",
            subtopic_filter_keyword="semejanza",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Geometría: Semejanza, proporcionalidad, escalas y Teorema de Thales.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Semejanza de Figuras y Teorema de Thales\n"
                "Dos figuras son semejantes si tienen la misma forma (ángulos interiores iguales) y sus lados homólogos son proporcionales con razón $k$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Teorema de Thales en Paralelas y Triángulos",
                    latex_formula=r"L_1 \parallel L_2 \implies \frac{AB}{BC} = \frac{DE}{EF} \qquad \text{y en conos de sombra: } \frac{\text{pequeño}}{\text{grande}} = \frac{\text{base}_1}{\text{base}_2}",
                    explanation="Para comparar las bases paralelas, debes usar siempre el lado lateral completo del triángulo grande.",
                ),
                FormulaCard(
                    title="2. Razón de Perímetros (k) vs. Razón de Áreas (k²)",
                    latex_formula=r"\frac{P_1}{P_2} = k \implies \frac{A_1}{A_2} = k^2",
                    explanation="Si los lados de dos triángulos semejantes están en razón 1:3, sus áreas están en razón 1:9.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Semejanza y Thales",
            resolution_recipe_steps=[
                "Paso 1 (Verificar si involucra Bases Paralelas): Si la incógnita está en las rectas paralelas, plantea $\\text{Triángulo Pequeño} / \\text{Triángulo Grande Completo}$.",
                "Paso 2 (Longitud vs Área): Si piden razón de áreas, eleva al cuadrado la razón lineal $k$.",
            ],
            common_demre_traps=[
                "En el Teorema de Thales con bases paralelas, dividir por el tramo inferior en vez de sumar el lado completo del triángulo mayor.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-GEO-SEM-1",
                    title="Ejercicio Práctico: Razón de Áreas en Semejanza",
                    stem_text="Dos triángulos semejantes tienen perímetros que están en la razón 2 : 5. Si el área del triángulo menor es 12 cm², ¿cuál es el área del triángulo mayor?",
                    stem_latex=r"\frac{A_{\text{menor}}}{A_{\text{mayor}}} = \left(\frac{2}{5}\right)^2 = \frac{4}{25}",
                    options={"A": r"30\text{ cm}^2", "B": r"60\text{ cm}^2", "C": r"75\text{ cm}^2", "D": r"48\text{ cm}^2"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. La razón de semejanza lineal es $k = \\frac{2}{5}$, por lo que la razón entre sus áreas es $k^2 = \\frac{4}{25}$.",
                        "2. Planteamos la proporción: $$\\frac{12}{A_{\\text{mayor}}} = \\frac{4}{25} \\implies A_{\\text{mayor}} = \\frac{12 \\cdot 25}{4} = 75\\text{ cm}^2$$ (Alternativa C).",
                    ],
                ),
            ],
        ),
    ],
    # -----------------------------------------------------------------
    # EJE 4: PROBABILIDAD Y ESTADÍSTICA (M1)
    # -----------------------------------------------------------------
    "PROBABILIDAD_Y_ESTADISTICA": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-PROB-TAB",
            micro_unit_id="PROB_TABLAS_GRAFICOS",
            exam="M1",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Representación de Datos (Tablas y Gráficos)",
            short_description="Frecuencia absoluta (f), acumulada (F), relativa (h) y porcentual en tablas de datos e histogramas.",
            subtopic_filter_keyword="frecuencia",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Probabilidad y Estadística: Tablas de frecuencia y gráficos estadísticos.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Tablas de Frecuencia y Gráficos\n"
                "- **Frecuencia Absoluta ($f_i$):** Cantidad de datos en la categoría $i$. La suma de todas las $f_i$ es el tamaño total de la muestra $N$.\n"
                "- **Frecuencia Acumulada ($F_i$):** Suma de las frecuencias absolutas desde el primer dato hasta la fila $i$ ($F_i = f_1 + f_2 + \\dots + f_i$).\n"
                "- **Frecuencia Relativa ($h_i$):** Cociente $h_i = \\frac{f_i}{N}$ (la suma total siempre es $1$ o $100\\%$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Relaciones entre Frecuencias de una Tabla",
                    latex_formula=r"F_i = F_{i-1} + f_i \qquad;\qquad h_i = \frac{f_i}{N} \qquad;\qquad \%_i = h_i \cdot 100\%",
                    explanation="La última frecuencia acumulada F_k siempre coincide con el total de datos N.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Completar e Interpretar Tablas DEMRE",
            resolution_recipe_steps=[
                "Paso 1 (Hallar el Total $N$): Suma la columna $f_i$ o mira el último valor de la columna acumulada $F_i$.",
                "Paso 2 (Rellenar Celdas Faltantes): Usa $f_i = F_i - F_{i-1}$ y $f_i = h_i \\cdot N$.",
                "Paso 3 (Distinguir Exacto vs Acumulado): 'Tienen 3 hermanos' lee $f_i$; 'tienen a lo más 3 hermanos' lee $F_i$.",
            ],
            common_demre_traps=[
                "Confundir la columna de frecuencia absoluta $f_i$ con la acumulada $F_i$ cuando el enunciado dice 'a lo más' o 'como máximo'.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-TAB-1",
                    title="Ejercicio Práctico: Frecuencia Acumulada y Relativa",
                    stem_text="En una encuesta a 80 personas sobre la cantidad de mascotas (0, 1 o 2), 20 personas tienen 0 mascotas y la frecuencia acumulada hasta 1 mascota es 56. ¿Cuántas personas tienen exactamente 1 mascota?",
                    stem_latex=r"F_2 = f_1 + f_2 \implies 56 = 20 + f_2",
                    options={"A": r"24", "B": r"36", "C": r"56", "D": r"44"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Sabemos que la frecuencia acumulada hasta la segunda fila es $F_2 = f_1 + f_2 = 56$.",
                        "2. Como $f_1 = 20$, despejamos: $$f_2 = 56 - 20 = 36\\text{ personas}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-PROB-MTC",
            micro_unit_id="PROB_TENDENCIA_CENTRAL",
            exam="M1",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Medidas de Tendencia Central",
            short_description="Media aritmética (promedio ponderado y en tablas), mediana de datos ordenados, moda y rango.",
            subtopic_filter_keyword="promedio",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Probabilidad y Estadística: Medidas de tendencia central y rango.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Promedio, Mediana y Moda\n"
                "- **Media Aritmética ($\\bar{x}$):** Suma total de los valores dividida por $N$. En tablas: $\\bar{x} = \\frac{\\sum x_i f_i}{N}$.\n"
                "- **Mediana ($Me$):** Valor central de los datos **ordenados de menor a mayor**.\n"
                "- **Moda ($Mo$):** El valor $x_i$ que posee la **mayor frecuencia absoluta $f_i$**."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Promedio en Datos Agrupados por Frecuencia",
                    latex_formula=r"\bar{x} = \frac{x_1 f_1 + x_2 f_2 + \dots + x_k f_k}{N} \implies \sum x_i f_i = N \cdot \bar{x}",
                    explanation="Multiplicar el promedio por la cantidad de datos N entrega inmediatamente la suma total de los datos.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Cálculo de Mediana y Promedio",
            resolution_recipe_steps=[
                "Paso 1 (Ordenar): Antes de buscar la mediana o el rango, verifica que los datos estén ordenados de menor a mayor.",
                "Paso 2 (Ubicar Posición en Tabla): Para la mediana en tabla, calcula $N/2$ y busca la primera frecuencia acumulada $F_i$ que supere ese valor.",
            ],
            common_demre_traps=[
                "Marcar como moda la frecuencia más alta ($f_{\\max}$) en lugar del dato $x_i$ que se repite esa cantidad de veces.",
                "Calcular la mediana sin ordenar previamente la lista de números.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-MTC-1",
                    title="Ejercicio Práctico: Despeje a partir del Promedio",
                    stem_text="El promedio de 5 números es 14. Si se agrega un sexto número, el nuevo promedio de los 6 números sube a 16. ¿Cuál fue el sexto número agregado?",
                    stem_latex=r"\frac{S_5 + x_6}{6} = 16 \quad \text{con} \quad S_5 = 5 \cdot 14",
                    options={"A": r"15", "B": r"20", "C": r"26", "D": r"30"},
                    correct_option="C",
                    step_by_step_solution=[
                        "1. La suma de los primeros 5 números es $S_5 = 5 \\cdot 14 = 70$.",
                        "2. La suma de los 6 números debe ser $S_6 = 6 \\cdot 16 = 96$.",
                        "3. El sexto número agregado es: $$x_6 = 96 - 70 = 26$$ (Alternativa C).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-PROB-POS",
            micro_unit_id="PROB_POSICION",
            exam="M1",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Medidas de Posición (Cuartiles/Percentiles)",
            short_description="Cálculo de cuartiles Q1, Q2, Q3, percentiles, rango intercuartílico (RIC) y lectura de diagramas de cajón (Boxplot).",
            subtopic_filter_keyword="cuartil",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Probabilidad y Estadística: Medidas de posición (cuartiles, percentiles y diagramas de cajón).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Cuartiles, Percentiles y Diagrama de Cajón\n"
                "Los **cuartiles** dividen la muestra ordenada en 4 tramos con un **25% de los datos en cada tramo**:\n"
                "- $Q_1$ ($P_{25}$): Acumula el 25% inferior.\n"
                "- $Q_2$ ($P_{50}$): Coincide exactamente con la **Mediana**.\n"
                "- $Q_3$ ($P_{75}$): Acumula el 75% inferior (y deja el 25% superior sobre él).\n"
                "- **Caja del Boxplot:** Va desde $Q_1$ hasta $Q_3$ y encierra el **50% central** de los datos."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Posición del Percentil k y Rango Intercuartílico (RIC)",
                    latex_formula=r"\text{Pos}(P_k) = \frac{k \cdot N}{100} \qquad \text{y} \qquad \text{RIC} = Q_3 - Q_1",
                    explanation="El ancho de un tramo del boxplot indica dispersión en ese 25%, NO mayor cantidad de datos.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Lectura de Boxplot y Cuartiles",
            resolution_recipe_steps=[
                "Paso 1 (Identificar los 5 Números del Boxplot): Extremo izquierdo = Mínimo; borde izquierdo de la caja = $Q_1$; línea interior = $Q_2$; borde derecho = $Q_3$; extremo derecho = Máximo.",
                "Paso 2 (Regla del 25%): Recuerda que entre Mín y $Q_1$, entre $Q_1$ y $Q_2$, entre $Q_2$ y $Q_3$, y entre $Q_3$ y Máx hay siempre la misma proporción de datos (25%).",
            ],
            common_demre_traps=[
                "Afirmar que hay más datos entre $Q_2$ y $Q_3$ que entre $Q_1$ y $Q_2$ solo porque esa mitad de la caja se ve más ancha.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-POS-1",
                    title="Ejercicio Práctico: Interpretación de Cuartiles",
                    stem_text="En una prueba rendida por 200 estudiantes, el primer cuartil fue Q1 = 480 puntos y el tercer cuartil fue Q3 = 640 puntos. ¿Cuántos estudiantes obtuvieron entre 480 y 640 puntos?",
                    stem_latex=r"\text{Entre } Q_1 \text{ y } Q_3 \text{ se concentra el } 50\% \text{ de } N = 200",
                    options={"A": r"50", "B": r"100", "C": r"150", "D": r"160"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Entre el primer cuartil $Q_1$ (25%) y el tercer cuartil $Q_3$ (75%) se ubica el $75\\% - 25\\% = 50\\%$ central de los datos.",
                        "2. El 50% de 200 estudiantes es: $$0,50 \\cdot 200 = 100\\text{ estudiantes}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M1-PROB-REG",
            micro_unit_id="PROB_REGLAS",
            exam="M1",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Reglas de Probabilidad",
            short_description="Regla de Laplace, probabilidad de la unión (conectivo 'O' e intersección) y regla multiplicativa (conectivo 'Y').",
            subtopic_filter_keyword="probabilidad",
            demre_syllabus_reference="Temario DEMRE M1 • Eje Probabilidad y Estadística: Reglas aditiva y multiplicativa de probabilidad.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico: Regla de Laplace, Unión e Intersección\n"
                "- **Conectivo 'O' (Unión $A \\cup B$):** Se suman las probabilidades y se resta una vez la intersección para no contar doble.\n"
                "- **Conectivo 'Y' (Intersección $A \\cap B$):** Se multiplican las probabilidades (cuidando si el experimento es con o sin reposición)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Regla Aditiva (Unión) y Multiplicativa",
                    latex_formula=r"P(A \cup B) = P(A) + P(B) - P(A \cap B) \qquad;\qquad P(A \cap B) = P(A)\cdot P(B)",
                    explanation="Al sacar elementos sin reposición, disminuye en 1 el denominador en la segunda extracción.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica: Cálculo de Probabilidades",
            resolution_recipe_steps=[
                "Paso 1 (Detectar Conectivo): Si dice 'A o B', usa suma menos intersección; si dice 'A y luego B', multiplica.",
                "Paso 2 (Con o Sin Reposición): Si hay extracciones sucesivas sin devolver el objeto, reduce el total $N$ en 1 en el segundo factor.",
            ],
            common_demre_traps=[
                "Sumar $P(A) + P(B)$ sin restar $P(A \\cap B)$ cuando ambos eventos pueden ocurrir simultáneamente (ej. sacar una carta que sea par O corazón).",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M1-PROB-REG-1",
                    title="Ejercicio Práctico: Extracción Sucesiva Sin Reposición",
                    stem_text="En una caja hay 4 tarjetas rojas y 6 azules. Si se extraen 2 tarjetas al azar una tras otra SIN reposición, ¿cuál es la probabilidad de que ambas sean rojas?",
                    stem_latex=r"P(R_1 \cap R_2) = \frac{4}{10} \cdot \frac{3}{9}",
                    options={"A": r"\frac{4}{25}", "B": r"\frac{2}{15}", "C": r"\frac{1}{5}", "D": r"\frac{7}{19}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. En la primera extracción hay 4 rojas de 10 tarjetas: $P(R_1) = \\frac{4}{10}$.",
                        "2. Sin reposición, quedan 3 rojas de un total de 9 tarjetas: $P(R_2 | R_1) = \\frac{3}{9}$.",
                        "3. Multiplicamos y simplificamos: $$\\frac{4}{10} \\cdot \\frac{3}{9} = \\frac{12}{90} = \\frac{2}{15}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
}


# =====================================================================
# 2. CATÁLOGO GRANULAR DE MICRO-UNIDADES PAES M2 (INCLUYE UNIDADES EXCLUSIVAS M2)
# =====================================================================

PAES_M2_EXHAUSTIVE_GUIDES: Dict[ThematicAxis, List[DEMREExhaustiveGuide]] = {
    "NUMEROS": [
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-NUM-CONJ",
            micro_unit_id="NUM_CONJUNTOS",
            exam="M2",
            thematic_axis="NUMEROS",
            unit_title="Conjuntos Numéricos (Reales, Irracionales y Logaritmos M2)",
            short_description="Números reales e irracionales, racionalización de denominadores y propiedades de logaritmos.",
            subtopic_filter_keyword="logaritmo",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Números: Conjunto de los números reales y logaritmos.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Números Reales ($\\mathbb{R}$) y Logaritmos\n"
                "En **PAES M2** se incorpora el conjunto de los irracionales ($\\mathbb{I}$) y el operador logarítmico $\\log_b(a) = c \\iff b^c = a$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Definición y Propiedades de Logaritmos",
                    latex_formula=r"\log_b(x\cdot y) = \log_b(x) + \log_b(y) \quad;\quad \log_b\left(\frac{x}{y}\right) = \log_b(x) - \log_b(y) \quad;\quad \log_b(x^n) = n\log_b(x)",
                    explanation="Convierte raíces en exponentes fraccionarios antes de bajar el exponente.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Reducción de Logaritmos",
            resolution_recipe_steps=[
                "Paso 1 (Bases Primas): Expresa cada argumento como potencia de números primos ($2, 3, 5, 10$).",
                "Paso 2 (Descomponer): Aplica las leyes de producto, cociente y exponente para separar en logaritmos simples.",
            ],
            common_demre_traps=[
                "Confundir $\\log(a + b)$ con $\\log(a) + \\log(b)$: no existe propiedad para el logaritmo de una suma.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-NUM-CONJ-1",
                    title="Ejercicio Práctico M2: Expresión Logarítmica",
                    stem_text="¿Cuál es el valor numérico exacto de la siguiente expresión en los números reales?",
                    stem_latex=r"\log_2(32) + \log_3\left(\frac{1}{9}\right) - \log(100)",
                    options={"A": r"1", "B": r"5", "C": r"-1", "D": r"3"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Calculamos cada término: $\\log_2(32) = \\log_2(2^5) = 5$; $\\log_3(1/9) = \\log_3(3^{-2}) = -2$; $\\log_{10}(100) = 2$.",
                        "2. Operamos: $$5 + (-2) - 2 = 1$$ (Alternativa A).",
                    ],
                ),
            ],
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["NUMEROS"][1].model_copy(
            update={"guide_id": "GUIDE-M2-NUM-RAZ", "exam": "M2"}
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-NUM-PCT",
            micro_unit_id="NUM_PORCENTAJES",
            exam="M2",
            thematic_axis="NUMEROS",
            unit_title="Porcentajes y Matemática Financiera (M2)",
            short_description="Variaciones porcentuales avanzadas, interés compuesto, capitalización sub-anual, créditos y depreciación.",
            subtopic_filter_keyword="porcentaje",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Números: Matemática financiera e interés compuesto.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Porcentajes Aplicados e Interés Compuesto\n"
                "En **PAES M2**, los porcentajes se extienden a procesos exponenciales de capitalización financiera: $C_f = C_0(1 + i)^n$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Capital Final con Interés Compuesto",
                    latex_formula=r"C_f = C_0 \cdot \left(1 + \frac{r}{100}\right)^n",
                    explanation="La tasa r y el número de períodos n deben estar expresados en la misma unidad temporal.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Matemática Financiera",
            resolution_recipe_steps=[
                "Paso 1 (Homologar Período): Si la capitalización es trimestral, divide la tasa anual entre 4 y multiplica los años por 4.",
                "Paso 2 (Sustituir en Modelo Exponencial): Plantea $C_0(1 + i)^n$.",
            ],
            common_demre_traps=[
                "Multiplicar la tasa por el número de años ($C_0(1 + n\\cdot i)$) como si fuera interés simple.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-NUM-PCT-1",
                    title="Ejercicio Práctico M2: Capitalización Compuesta",
                    stem_text="Se invierten $500.000 a una tasa de interés compuesto anual del 12%, capitalizable semestralmente durante 3 años. ¿Qué expresión representa el capital final?",
                    stem_latex=r"C_f = 500\,000 \cdot (1 + i_{\text{sem}})^{n_{\text{sem}}}",
                    options={
                        "A": r"500\,000 \cdot (1,12)^3",
                        "B": r"500\,000 \cdot (1,06)^6",
                        "C": r"500\,000 \cdot (1,06)^3",
                        "D": r"500\,000 \cdot (1,12)^6",
                    },
                    correct_option="B",
                    step_by_step_solution=[
                        "1. La tasa semestral es la mitad de la anual: $12\\% / 2 = 6\\% = 0,06$.",
                        "2. En 3 años hay $3 \\cdot 2 = 6$ semestres: $$C_f = 500\\,000 \\cdot (1,06)^6$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    "ALGEBRA_Y_FUNCIONES": [
        PAES_M1_EXHAUSTIVE_GUIDES["ALGEBRA_Y_FUNCIONES"][0].model_copy(
            update={"guide_id": "GUIDE-M2-ALG-EXP", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["ALGEBRA_Y_FUNCIONES"][1].model_copy(
            update={"guide_id": "GUIDE-M2-ALG-EC1", "exam": "M2"}
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-ALG-SIS",
            micro_unit_id="ALG_SISTEMAS_2X2",
            exam="M2",
            thematic_axis="ALGEBRA_Y_FUNCIONES",
            unit_title="Sistemas de Ecuaciones (2x2) y Análisis Paramétrico M2",
            short_description="Resolución de sistemas 2x2 y criterios de solución única, infinitas soluciones o sin solución según parámetro k.",
            subtopic_filter_keyword="sistemas",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Álgebra: Análisis de compatibilidad de sistemas 2x2.",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Compatibilidad de Sistemas Lineales $2\\times 2$\n"
                "En **PAES M2** se evalúa determinar para qué valor de un parámetro $k$ el sistema tiene solución única, infinitas soluciones o ninguna solución."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Proporción de Coeficientes en Sistemas 2x2",
                    latex_formula=r"\text{Única: }\frac{a_1}{a_2}\neq\frac{b_1}{b_2} \quad;\quad \text{Infinitas: }\frac{a_1}{a_2}=\frac{b_1}{b_2}=\frac{c_1}{c_2} \quad;\quad \text{Sin solución: }\frac{a_1}{a_2}=\frac{b_1}{b_2}\neq\frac{c_1}{c_2}",
                    explanation="Compara siempre las razones de los coeficientes de x, de y y de los términos libres.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Sistemas con Parámetro k",
            resolution_recipe_steps=[
                "Paso 1 (Alinear el Sistema): Asegúrate de que ambas ecuaciones estén en la forma $ax + by = c$.",
                "Paso 2 (Igualar Razones): Plantea $\\frac{a_1}{a_2} = \\frac{b_1}{b_2}$ y despeja $k$.",
                "Paso 3 (Verificar con $c_1/c_2$): Comprueba si para ese $k$ la tercera razón es igual (infinitas) o distinta (vacía).",
            ],
            common_demre_traps=[
                "Olvidar verificar la tercera razón $c_1/c_2$, marcando un valor de $k$ que genera infinitas soluciones cuando pedían 'sin solución'.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-ALG-SIS-1",
                    title="Ejercicio Práctico M2: Sistema sin Solución",
                    stem_text="¿Para qué valor real de k el siguiente sistema de ecuaciones NO tiene solución?",
                    stem_latex=r"\begin{cases} kx + 3y = 7 \\ 4x + 6y = 10 \end{cases}",
                    options={"A": r"k = 2", "B": r"k = 4", "C": r"k = -2", "D": r"k = 6"},
                    correct_option="A",
                    step_by_step_solution=[
                        "1. Planteamos la igualdad de razones en $x$ e $y$: $\\frac{k}{4} = \\frac{3}{6} = \\frac{1}{2} \\implies k = 2$.",
                        "2. Verificamos que difiera de los términos libres: $\\frac{1}{2} \\neq \\frac{7}{10}$. Por tanto, con $k = 2$ las rectas son paralelas sin solución (Alternativa A).",
                    ],
                ),
            ],
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["ALGEBRA_Y_FUNCIONES"][3].model_copy(
            update={"guide_id": "GUIDE-M2-ALG-LIN", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["ALGEBRA_Y_FUNCIONES"][4].model_copy(
            update={"guide_id": "GUIDE-M2-ALG-CUAD", "exam": "M2"}
        ),
    ],
    "GEOMETRIA": [
        PAES_M1_EXHAUSTIVE_GUIDES["GEOMETRIA"][0].model_copy(
            update={"guide_id": "GUIDE-M2-GEO-2D", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["GEOMETRIA"][1].model_copy(
            update={"guide_id": "GUIDE-M2-GEO-3D", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["GEOMETRIA"][2].model_copy(
            update={"guide_id": "GUIDE-M2-GEO-ISO", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["GEOMETRIA"][3].model_copy(
            update={"guide_id": "GUIDE-M2-GEO-PIT", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["GEOMETRIA"][4].model_copy(
            update={"guide_id": "GUIDE-M2-GEO-SEM", "exam": "M2"}
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-GEO-HOM",
            micro_unit_id="GEO_HOMOTECIA_M2",
            exam="M2",
            thematic_axis="GEOMETRIA",
            unit_title="Homotecia (Solo M2)",
            short_description="Homotecia vectorial en el plano, clasificación según razón k (directa/inversa) y efecto sobre perímetros (|k|) y áreas (k²).",
            subtopic_filter_keyword="homotecia",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Geometría: Homotecia de figuras planas (Exclusivo M2).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Homotecia de Centro $O$ y Razón $k$\n"
                "Una homotecia $H(O, k)$ transforma cada punto $P$ en $P'$ tal que $\\overrightarrow{OP'} = k \\cdot \\overrightarrow{OP}$:\n"
                "- Si $k > 0$: **Homotecia Directa** (ambas figuras al mismo lado del centro $O$).\n"
                "- Si $k < 0$: **Homotecia Inversa** (el centro $O$ queda entre la figura original y su imagen, girada en $180^\\circ$)."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Efecto de la Razón de Homotecia k en Perímetros y Áreas",
                    latex_formula=r"P_{\text{imagen}} = |k| \cdot P_{\text{original}} \qquad\text{y}\qquad A_{\text{imagen}} = k^2 \cdot A_{\text{original}}",
                    explanation="Las longitudes y áreas son siempre positivas; por eso se usa valor absoluto |k| y k^2.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Problemas de Homotecia",
            resolution_recipe_steps=[
                "Paso 1 (Signo de $k$): Si la figura se invierte al otro lado del centro $O$, entonces $k < 0$.",
                "Paso 2 (Escalamiento): Multiplica por $|k|$ para segmentos/perímetros y por $k^2$ para áreas.",
            ],
            common_demre_traps=[
                "Multiplicar el área original por $|k|$ en lugar de por $k^2$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-GEO-HOM-1",
                    title="Ejercicio Práctico M2: Homotecia y Razón de Áreas",
                    stem_text="A un triángulo de área 15 cm² se le aplica una homotecia de razón k = -3. ¿Cuál es el área del triángulo homotético resultante?",
                    stem_latex=r"A' = (-3)^2 \cdot 15",
                    options={"A": r"45\text{ cm}^2", "B": r"135\text{ cm}^2", "C": r"-45\text{ cm}^2", "D": r"90\text{ cm}^2"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. En toda homotecia de razón $k$, la razón entre el área imagen y el área original es $k^2 = (-3)^2 = 9$.",
                        "2. Multiplicamos: $$A' = 9 \\cdot 15 = 135\\text{ cm}^2$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-GEO-TRIG",
            micro_unit_id="GEO_TRIGONOMETRIA_M2",
            exam="M2",
            thematic_axis="GEOMETRIA",
            unit_title="Razones Trigonométricas (Solo M2)",
            short_description="Seno, coseno y tangente en triángulos rectángulos, valores en ángulos notables (30°, 45°, 60°) y ángulos de elevación/depresión.",
            subtopic_filter_keyword="elevación",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Geometría: Razones trigonométricas en el triángulo rectángulo (Exclusivo M2).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Trigonometría en el Triángulo Rectángulo\n"
                "Mediante la regla mnemotécnica **SOH-CAH-TOA** relacionamos los ángulos agudos de un triángulo rectángulo con las razones de sus lados."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Razones Trigonométricas y Identidad Pitagórica",
                    latex_formula=r"\sin(\alpha)=\frac{\text{Opuesto}}{\text{Hipotenusa}}, \quad \cos(\alpha)=\frac{\text{Adyacente}}{\text{Hipotenusa}}, \quad \tan(\alpha)=\frac{\text{Opuesto}}{\text{Adyacente}}",
                    explanation="En problemas de sombras y alturas sin usar la hipotenusa, la razón directa es siempre la tangente.",
                ),
                FormulaCard(
                    title="2. Ángulos Notables (30°, 45°, 60°)",
                    latex_formula=r"\sin(30^\circ)=\frac{1}{2}, \;\; \cos(30^\circ)=\frac{\sqrt{3}}{2}, \;\; \tan(30^\circ)=\frac{\sqrt{3}}{3}, \;\; \tan(45^\circ)=1, \;\; \tan(60^\circ)=\sqrt{3}",
                    explanation="Valores exactos exigidos sin calculadora en PAES M2.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Problemas de Ángulo de Elevación",
            resolution_recipe_steps=[
                "Paso 1 (Dibujar Triángulo Rectángulo): La altura vertical es el cateto opuesto al ángulo de elevación y la distancia en el suelo es el cateto adyacente.",
                "Paso 2 (Elegir Razón): Si relacionas altura y distancia horizontal, plantea $\\tan(\\alpha) = \\text{Altura}/\\text{Distancia}$.",
            ],
            common_demre_traps=[
                "Intercambiar $\\tan(30^\\circ) = \\frac{\\sqrt{3}}{3}$ con $\\tan(60^\\circ) = \\sqrt{3}$.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-GEO-TRIG-1",
                    title="Ejercicio Práctico M2: Altura de una Torre",
                    stem_text="Desde un punto en el suelo a 40 metros de la base de una torre, el ángulo de elevación hacia su extremo superior es de 30°. ¿Cuál es la altura exacta de la torre?",
                    stem_latex=r"\tan(30^\circ) = \frac{H}{40}",
                    options={"A": r"40\sqrt{3}\text{ m}", "B": r"\frac{40\sqrt{3}}{3}\text{ m}", "C": r"20\text{ m}", "D": r"20\sqrt{3}\text{ m}"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Planteamos la tangente de $30^\\circ$: $\\tan(30^\\circ) = \\frac{H}{40}$.",
                        "2. Como $\\tan(30^\\circ) = \\frac{\\sqrt{3}}{3}$, despejamos: $$H = \\frac{40\\sqrt{3}}{3}\\text{ m}$$ (Alternativa B).",
                    ],
                ),
            ],
        ),
    ],
    "PROBABILIDAD_Y_ESTADISTICA": [
        PAES_M1_EXHAUSTIVE_GUIDES["PROBABILIDAD_Y_ESTADISTICA"][0].model_copy(
            update={"guide_id": "GUIDE-M2-PROB-TAB", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["PROBABILIDAD_Y_ESTADISTICA"][1].model_copy(
            update={"guide_id": "GUIDE-M2-PROB-MTC", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["PROBABILIDAD_Y_ESTADISTICA"][2].model_copy(
            update={"guide_id": "GUIDE-M2-PROB-POS", "exam": "M2"}
        ),
        PAES_M1_EXHAUSTIVE_GUIDES["PROBABILIDAD_Y_ESTADISTICA"][3].model_copy(
            update={"guide_id": "GUIDE-M2-PROB-REG", "exam": "M2"}
        ),
        DEMREExhaustiveGuide(
            guide_id="GUIDE-M2-PROB-COMB",
            micro_unit_id="PROB_CONTEO_M2",
            exam="M2",
            thematic_axis="PROBABILIDAD_Y_ESTADISTICA",
            unit_title="Técnicas de Conteo / Combinatoria (Solo M2)",
            short_description="Principio multiplicativo, permutaciones (P_n = n!), variaciones (importa el orden) y combinaciones (no importa el orden).",
            subtopic_filter_keyword="combinatoria",
            demre_syllabus_reference="Temario DEMRE M2 • Eje Probabilidad y Estadística: Permutación y combinatoria (Exclusivo M2).",
            theoretical_framework_md=(
                "### 📖 Marco Teórico M2: Permutaciones, Variaciones y Combinatoria\n"
                "La pregunta decisiva en todo problema de conteo de **PAES M2** es: **¿Importa el orden en que se eligen los elementos?**\n\n"
                "- **NO importa el orden** (ej. elegir un comité de 3 personas, un grupo de estudio, o diagonales): usa **Combinación** $\\binom{n}{k}$.\n"
                "- **SÍ importa el orden** (ej. podio 1°/2°/3° lugar, claves o códigos, cargos de Presidente/Tesorero): usa **Variación** $V_k^n$."
            ),
            key_formulas=[
                FormulaCard(
                    title="1. Combinación (Sin orden) vs. Variación (Con orden)",
                    latex_formula=r"C_k^n = \binom{n}{k} = \frac{n!}{k!\,(n-k)!} \qquad;\qquad V_k^n = \frac{n!}{(n-k)!}",
                    explanation="En la combinación se divide por k! para eliminar las permutaciones repetidas del mismo grupo.",
                ),
            ],
            resolution_recipe_title="Receta Algorítmica M2: Árbol de Decisión de Combinatoria",
            resolution_recipe_steps=[
                "Paso 1 (Probar Intercambio): Si eliges a {Ana, Bruno} y lo cambias a {Bruno, Ana}, ¿es el mismo resultado? Si es el mismo, usa Combinación $\\binom{n}{k}$.",
                "Paso 2 (Simplificar Factoriales): Desarrolla el factorial mayor hasta cancelar $(n-k)!$ antes de multiplicar.",
            ],
            common_demre_traps=[
                "Usar Variación $n!/(n-k)!$ cuando el problema pide formar una comisión sin cargos diferenciados.",
            ],
            interleaved_exercises=[
                InterleavedGuideExercise(
                    exercise_id="EX-M2-PROB-COMB-1",
                    title="Ejercicio Práctico M2: Formación de Comité",
                    stem_text="De un grupo de 8 estudiantes se debe escoger una delegación de 3 representantes para asistir a un congreso (todos con igual rol). ¿De cuántas formas distintas se puede elegir la delegación?",
                    stem_latex=r"\binom{8}{3} = \frac{8!}{3!\cdot 5!}",
                    options={"A": r"336", "B": r"56", "C": r"24", "D": r"512"},
                    correct_option="B",
                    step_by_step_solution=[
                        "1. Como todos los representantes tienen el mismo rol, NO importa el orden (Combinación).",
                        "2. Calculamos: $$\\binom{8}{3} = \\frac{8 \\cdot 7 \\cdot 6}{3 \\cdot 2 \\cdot 1} = 8 \\cdot 7 = 56\\text{ formas}$$ (Alternativa B).",
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
