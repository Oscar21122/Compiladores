# Compilador Patito

Compilador completo para el lenguaje **Patito**, desarrollado como proyecto del curso de Desarrollo de Aplicaciones Avanzadas de Ciencias Computacionales (Tec de Monterrey).

## ¿Qué es Patito?

Patito es un lenguaje de programación didáctico de tipo imperativo que soporta variables enteras y flotantes, expresiones aritméticas y relacionales, condicionales, ciclos, funciones con y sin retorno, parámetros y recursión.

## Fases del compilador

| Fase | Descripción | Archivos |
|---|---|---|
| 1. Scanner | Análisis léxico — reconoce tokens del lenguaje | `grammar.lark`, `parser_patito.py` |
| 2. Parser | Análisis sintáctico LALR — valida la estructura del programa | `grammar.lark`, `parser_patito.py` |
| 3. Semántica | Verificación de tipos y tabla de variables/funciones | `semantic.py` |
| 4. Generación | Código intermedio (cuádruplos) con direcciones virtuales | `generador.py`, `cuadruplos.py`, `memoria.py` |
| 5. Ejecución | Máquina virtual que interpreta los cuádruplos | `maquina_virtual.py` |

## Requisitos

- Python 3.8 o superior
- Librería `lark` (parser LALR)

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

Esto corre las 5 fases de pruebas en orden:
1. **Léxico** — sobre `test_lexer.txt`
2. **Sintáctico** — sobre `test_parser.txt`
3. **Semántico + Cuádruplos** — sobre `test_cuadruplos.txt`
4. **Máquina Virtual** — sobre `test_vm.txt`

## Estructura de archivos

```
Patito/
├── grammar.lark          # Gramática del lenguaje
├── parser_patito.py      # Instancia del parser LALR
├── semantic.py           # Cubo semántico, tablas de variables y funciones
├── cuadruplos.py         # Estructuras de pilas y fila de cuádruplos
├── memoria.py            # Administrador de memoria virtual
├── generador.py          # Generador de código intermedio
├── maquina_virtual.py    # Máquina virtual de ejecución
├── main.py               # Pipeline principal de pruebas
├── test_lexer.txt        # Casos de prueba léxicos
├── test_parser.txt       # Casos de prueba sintácticos
├── test_cuadruplos.txt   # Casos de prueba semánticos y de cuádruplos
├── test_vm.txt           # Casos de prueba de ejecución (factorial, fibonacci, etc.)
└── requirements.txt      # Dependencias
```

## Ejemplo de programa válido en Patito

```
programa ejemplo;
vars r: entero;

entero factorial(n: entero) {
    {
        si (n < 2) {
            regresa 1;
        } sino {
            regresa n * factorial(n - 1);
        };
    }
};

inicio {
    r = factorial(5);
    escribe("5! =", r);
}
fin
```

Salida esperada:
```
5! =
120
```

## Elementos del lenguaje

- **Tipos:** `entero`, `flotante`
- **Operadores aritméticos:** `+`, `-`, `*`, `/`
- **Operadores relacionales:** `>`, `<`, `!=`, `==`
- **Condicional:** `si (...) { } sino { };`
- **Ciclo:** `mientras (...) haz { };`
- **Salida:** `escribe(...);`
- **Funciones:** con tipo de retorno (`entero`, `flotante`) o sin retorno (`nula`)
- **Retorno de valor:** `regresa expresion;`
