# semantic.py
# Estructuras de datos y cubo semántico del compilador Patito.
# AnalizadorSemantico fue eliminado: su lógica vive en generador.py
# como recorrido único que valida y genera cuádruplos al mismo tiempo.

# ─────────────────────────────────────────
# CUBO SEMÁNTICO
# ─────────────────────────────────────────

CUBO_SEMANTICO = {
    '+':  { 'int':   { 'int': 'int',   'float': 'float' },
            'float': { 'int': 'float', 'float': 'float' } },
    '-':  { 'int':   { 'int': 'int',   'float': 'float' },
            'float': { 'int': 'float', 'float': 'float' } },
    '*':  { 'int':   { 'int': 'int',   'float': 'float' },
            'float': { 'int': 'float', 'float': 'float' } },
    '/':  { 'int':   { 'int': 'int',   'float': 'float' },
            'float': { 'int': 'float', 'float': 'float' } },
    '>':  { 'int':   { 'int': 'int',   'float': 'int'   },
            'float': { 'int': 'int',   'float': 'int'   } },
    '<':  { 'int':   { 'int': 'int',   'float': 'int'   },
            'float': { 'int': 'int',   'float': 'int'   } },
    '!=': { 'int':   { 'int': 'int',   'float': 'int'   },
            'float': { 'int': 'int',   'float': 'int'   } },
    '==': { 'int':   { 'int': 'int',   'float': 'int'   },
            'float': { 'int': 'int',   'float': 'int'   } },
    '=':  { 'int':   { 'int': 'int',   'float': 'error' },
            'float': { 'int': 'float', 'float': 'float' } },
}


class SemanticError(Exception):
    pass


def tipo_resultado(op, tipo_izq, tipo_der):
    resultado = CUBO_SEMANTICO.get(op, {}).get(tipo_izq, {}).get(tipo_der, 'error')
    if resultado == 'error':
        raise SemanticError(f"Operación inválida: {tipo_izq} {op} {tipo_der}")
    return resultado


# ─────────────────────────────────────────
# TABLA DE VARIABLES
# ─────────────────────────────────────────

class EntradaVariable:
    def __init__(self, nombre, tipo):
        self.nombre = nombre
        self.tipo   = tipo

    def __repr__(self):
        return f"Var({self.nombre}: {self.tipo})"


class TablaVariables:
    def __init__(self):
        self._tabla = {}

    def agregar(self, nombre, tipo):
        if nombre in self._tabla:
            raise SemanticError(f"Variable doblemente declarada: '{nombre}'")
        self._tabla[nombre] = EntradaVariable(nombre, tipo)

    def buscar(self, nombre):
        if nombre not in self._tabla:
            raise SemanticError(f"Variable no declarada: '{nombre}'")
        return self._tabla[nombre]

    def existe(self, nombre):
        return nombre in self._tabla

    def __repr__(self):
        return f"TablaVariables({list(self._tabla.values())})"


# ─────────────────────────────────────────
# DIRECTORIO DE FUNCIONES
# ─────────────────────────────────────────

class EntradaFuncion:
    def __init__(self, nombre, tipo_retorno):
        self.nombre       = nombre
        self.tipo_retorno = tipo_retorno
        self.params       = []
        self.tabla_vars   = TablaVariables()

    def agregar_param(self, nombre, tipo):
        self.params.append((nombre, tipo))
        self.tabla_vars.agregar(nombre, tipo)

    def __repr__(self):
        return (f"Func({self.nombre} -> {self.tipo_retorno} | "
                f"params={self.params} | vars={self.tabla_vars})")


class DirectorioFunciones:
    def __init__(self):
        self._directorio = {}

    def agregar(self, nombre, tipo_retorno):
        if nombre in self._directorio:
            raise SemanticError(f"Función doblemente declarada: '{nombre}'")
        entrada = EntradaFuncion(nombre, tipo_retorno)
        self._directorio[nombre] = entrada
        return entrada

    def buscar(self, nombre):
        if nombre not in self._directorio:
            raise SemanticError(f"Función no declarada: '{nombre}'")
        return self._directorio[nombre]

    def existe(self, nombre):
        return nombre in self._directorio

    def imprimir(self):
        print("\n===== DIRECTORIO DE FUNCIONES =====")
        for nombre, entrada in self._directorio.items():
            print(f"\n  [{nombre}]")
            print(f"    retorno : {entrada.tipo_retorno}")
            print(f"    params  : {entrada.params}")
            print(f"    vars    : {list(entrada.tabla_vars._tabla.values())}")
        print("===================================\n")