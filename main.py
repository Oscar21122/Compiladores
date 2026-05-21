# Importa el parser ya construido y corre las 4 fases de pruebas:
#   1. Léxico        (test_lexer.txt)
#   2. Sintáctico    (test_parser.txt)
#   3+4. Semántico + Cuádruplos en un solo recorrido (test_cuadruplos.txt)

from parser_patito import parser
from semantic      import SemanticError
from generador     import GeneradorCuadruplos


def _leer_secciones(archivo):
    with open(archivo) as f:
        content = f.read()
    secciones = []
    for section in content.split("###"):
        section = section.strip()
        if not section:
            continue
        lines        = section.split("\n")
        title        = lines[0].strip()
        expect_valid = "INVALIDO" not in title.upper()
        code         = "\n".join(lines[1:]).strip()
        secciones.append((title, code, expect_valid))
    return secciones


# ── FASE 1: Léxico ────────────────────────────────────────────────────────────

def test_lexer_input(code, expect_valid=True):
    try:
        tokens = list(parser.lex(code))
        if expect_valid:
            print("✔ PASA (lexer): válido")
            print("   Tokens:", [(t.type, t.value) for t in tokens])
        else:
            print("✖ FALLA (lexer): inválido aceptado")
    except Exception as e:
        if expect_valid: print("✖ FALLA (lexer): válido rechazado —", e)
        else:            print("✔ PASA (lexer): error detectado")

def run_lexer_tests():
    print("\n================ LEXER TESTS ================")
    for title, code, expect_valid in _leer_secciones("test_lexer.txt"):
        print(f"\n🧪 {title}")
        test_lexer_input(code, expect_valid)


# ── FASE 2: Sintáctico ────────────────────────────────────────────────────────

def test_parser_input(code, expect_valid=True):
    try:
        parser.parse(code)
        if expect_valid: print("✔ PASA (parser): válido")
        else:            print("✖ FALLA (parser): inválido aceptado")
    except Exception as e:
        if expect_valid: print("✖ FALLA (parser): válido rechazado —", e)
        else:            print("✔ PASA (parser): error detectado")

def run_parser_tests():
    print("\n================ PARSER TESTS ================")
    for title, code, expect_valid in _leer_secciones("test_parser.txt"):
        print(f"\n🧪 {title}")
        test_parser_input(code, expect_valid)


# ── FASES 3+4: Semántico + Cuádruplos ────────────────────────────────────────
# GeneradorCuadruplos hace ambas fases en un solo recorrido del árbol:
# en cada nodo valida tipos/variables/funciones Y genera el cuádruplo.

def test_cuadruplos_input(code, expect_valid=True):
    try:
        tree = parser.parse(code)       # fases 1 y 2

        gen = GeneradorCuadruplos()
        gen.generar(tree)               # fases 3 y 4: un solo recorrido

        gen.directorio.imprimir()       # resultado semántico
        gen.fila.imprimir()             # cuádruplos generados

        if expect_valid: print("✔ PASA: válido")
        else:            print("✖ FALLA: inválido aceptado")

    except SemanticError as e:
        if expect_valid: print("✖ FALLA: error semántico no esperado —", e)
        else:            print("✔ PASA: error semántico detectado →", e)
    except Exception as e:
        if expect_valid: print("✖ FALLA: error no esperado —", e)
        else:            print("✔ PASA: error detectado →", e)

def run_cuadruplos_tests():
    print("\n================ SEMÁNTICO + CUÁDRUPLOS ================")
    for title, code, expect_valid in _leer_secciones("test_cuadruplos.txt"):
        print(f"\n🧪 {title}")
        test_cuadruplos_input(code, expect_valid)


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_lexer_tests()
    run_parser_tests()
    run_cuadruplos_tests()