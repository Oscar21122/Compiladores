from lark import Token, Tree
from semantic import (
    SemanticError,       # excepción para errores semánticos
    tipo_resultado,      # consulta el cubo semántico internamente
    DirectorioFunciones, # registra funciones y sus ámbitos
)
from cuadruplos import Pila, Cuadruplo, FilaCuadruplos


def es_token(nodo, tipo):
    return isinstance(nodo, Token) and nodo.type == tipo

def es_arbol(nodo, regla):
    return isinstance(nodo, Tree) and nodo.data == regla


class GeneradorCuadruplos:
    """
    Recorre el árbol sintáctico una sola vez.
    En cada nodo: valida tipos/variables/funciones Y genera cuádruplos.
    """

    def __init__(self):
        # ── estructuras semánticas ──────────────────────
        self.directorio    = DirectorioFunciones()
        self._ambito_actual = None   # EntradaFuncion activa

        # ── pilas de traducción ─────────────────────────
        self.pila_ops       = Pila("P_Ops")
        self.pila_operandos = Pila("P_Operandos")
        self.pila_tipos     = Pila("P_Tipos")

        # ── fila de cuádruplos ──────────────────────────
        self.fila = FilaCuadruplos()

        # ── contador de temporales ──────────────────────
        self._tmp_count = 0

    # ── helpers ──────────────────────────────────────────────────────────────

    def _nuevo_tmp(self):
        self._tmp_count += 1
        return f"t{self._tmp_count}"

    def _ambito_global(self):
        nombre = list(self.directorio._directorio.keys())[0]
        return self.directorio._directorio[nombre]

    def _buscar_variable(self, nombre):
        """Busca primero en ámbito local, luego en global. Igual que semantic.py."""
        if self._ambito_actual.tabla_vars.existe(nombre):
            return self._ambito_actual.tabla_vars.buscar(nombre)
        global_vars = self._ambito_global().tabla_vars
        if global_vars.existe(nombre):
            return global_vars.buscar(nombre)
        raise SemanticError(f"Variable no declarada: '{nombre}'")

    def _tipo(self, nodo):
        token = nodo.children[0]
        return 'int' if token.type == 'ENTERO' else 'float'

    # ── punto de entrada ─────────────────────────────────────────────────────

    def generar(self, tree):
        self._programa(tree.children[0])

    # ── PN-1: programa ───────────────────────────────────────────────────────
    # Registra el programa en el directorio y establece el ámbito global.

    def _programa(self, nodo):
        nombre_prog = str(nodo.children[1])
        self.directorio.agregar(nombre_prog, 'nula')        # semántico
        self._ambito_actual = self.directorio.buscar(nombre_prog)

        for hijo in nodo.children:
            if   es_arbol(hijo, 'vars'):   self._vars(hijo)
            elif es_arbol(hijo, 'funcs'):  self._funcs(hijo)
            elif es_arbol(hijo, 'cuerpo'): self._cuerpo(hijo)

    # ── PN-2: vars / decl_var ────────────────────────────────────────────────
    # Registra cada variable con su tipo en la tabla del ámbito actual.
    # Solo semántico — no genera cuádruplos.

    def _vars(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'decl_var'):
                self._decl_var(hijo)

    def _decl_var(self, nodo):
        tipo_nodo = next(h for h in nodo.children if es_arbol(h, 'tipo'))
        tipo      = self._tipo(tipo_nodo)
        for hijo in nodo.children:
            if es_token(hijo, 'ID'):
                self._ambito_actual.tabla_vars.agregar(str(hijo), tipo)  # semántico

    # ── PN-3/4/5: funcs / func / params ─────────────────────────────────────
    # PN-3: registra función y cambia ámbito.
    # PN-4: registra parámetros en la tabla local.
    # PN-5: restaura ámbito y genera ENDFUNC.

    def _funcs(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'func'):
                self._func(hijo)

    def _func(self, nodo):
        primer = nodo.children[0]
        tipo_ret = self._tipo(primer) if es_arbol(primer, 'tipo') else 'nula'
        nombre_func = str(nodo.children[1])

        self.directorio.agregar(nombre_func, tipo_ret)      # PN-3 semántico
        ambito_previo      = self._ambito_actual
        self._ambito_actual = self.directorio.buscar(nombre_func)

        for hijo in nodo.children:
            if   es_arbol(hijo, 'params'): self._params(hijo)   # PN-4
            elif es_arbol(hijo, 'vars'):   self._vars(hijo)
            elif es_arbol(hijo, 'cuerpo'): self._cuerpo(hijo)

        self.fila.agregar(Cuadruplo('ENDFUNC', None, None, nombre_func))  # PN-5 generación
        self._ambito_actual = ambito_previo                                # PN-5 semántico

    def _params(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'param'):
                self._param(hijo)

    def _param(self, nodo):
        nombre = str(nodo.children[0])
        tipo   = self._tipo(nodo.children[2])
        self._ambito_actual.agregar_param(nombre, tipo)     # PN-4 semántico

    # ── cuerpo / estatuto ────────────────────────────────────────────────────

    def _cuerpo(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'estatuto'):
                self._estatuto(hijo)

    def _estatuto(self, nodo):
        hijo = nodo.children[0]
        if   es_arbol(hijo, 'asigna'):    self._asigna(hijo)
        elif es_arbol(hijo, 'condicion'): self._condicion(hijo)
        elif es_arbol(hijo, 'ciclo'):     self._ciclo(hijo)
        elif es_arbol(hijo, 'imprime'):   self._imprime(hijo)
        elif es_arbol(hijo, 'llamada'):   self._llamada(hijo)

    # ── PN-8: asigna ─────────────────────────────────────────────────────────
    # Semántico: verifica que el tipo de la expresión sea compatible con la variable.
    # Generación: produce cuádruplo (=, resultado_expr, _, variable_destino).

    def _asigna(self, nodo):
        nombre_var = str(nodo.children[0])
        tipo_var   = self._buscar_variable(nombre_var).tipo  # semántico: existe?

        tipo_exp = self._expresion(nodo.children[2])         # semántico: tipo resultado
        tipo_resultado('=', tipo_var, tipo_exp)              # semántico: compatible?

        res_op = self.pila_operandos.pop()                   # generación
        self.pila_tipos.pop()
        self.fila.agregar(Cuadruplo('=', res_op, None, nombre_var))

    # ── PN-7: expresion ───────────────────────────────────────────────────────
    # Semántico: devuelve el tipo resultante de la expresión.
    # Generación: deja el resultado en el tope de pila_operandos.

    def _expresion(self, nodo):
        hijos = nodo.children
        tipo  = self._exp(hijos[0])
        if len(hijos) == 3:
            op = str(hijos[1])
            self.pila_ops.push(op)
            tipo_der = self._exp(hijos[2])
            tipo     = self._generar_si_aplica({'>', '<', '!=', '=='}, tipo, tipo_der)
        return tipo

    def _exp(self, nodo):
        hijos     = nodo.children
        tipo_acum = self._termino(hijos[0])
        i = 1
        while i < len(hijos):
            op = str(hijos[i])
            self.pila_ops.push(op)
            tipo_der  = self._termino(hijos[i + 1])
            tipo_acum = self._generar_si_aplica({'+', '-'}, tipo_acum, tipo_der)
            i += 2
        return tipo_acum

    def _termino(self, nodo):
        hijos     = nodo.children
        tipo_acum = self._factor(hijos[0])
        i = 1
        while i < len(hijos):
            op = str(hijos[i])
            self.pila_ops.push(op)
            tipo_der  = self._factor(hijos[i + 1])
            tipo_acum = self._generar_si_aplica({'*', '/'}, tipo_acum, tipo_der)
            i += 2
        return tipo_acum

    # ── PN-9: factor ──────────────────────────────────────────────────────────
    # Semántico: busca la variable y obtiene su tipo (o lee el tipo de la constante).
    # Generación: apila el operando y su tipo en las pilas.

    def _factor(self, nodo):
        hijos = nodo.children

        if es_token(hijos[0], 'LPAREN'):
            return self._expresion(hijos[1])

        if es_arbol(hijos[0], 'llamada'):
            return self._llamada(hijos[0])

        signo = None
        idx   = 0
        if es_token(hijos[0], 'OP_SUMA'):
            signo = str(hijos[0])
            idx   = 1

        operando = hijos[idx]

        if es_token(operando, 'ID'):
            nombre = str(operando)
            tipo   = self._buscar_variable(nombre).tipo      # semántico: existe + tipo
            if signo == '-':
                tmp = self._nuevo_tmp()
                self.fila.agregar(Cuadruplo('*', nombre, '-1', tmp))
                self.pila_operandos.push(tmp)
            else:
                self.pila_operandos.push(nombre)             # generación
            self.pila_tipos.push(tipo)
            return tipo

        if es_arbol(operando, 'cte'):
            token = operando.children[0]
            valor = ('-' if signo == '-' else '') + str(token)
            tipo  = 'float' if token.type == 'CTE_FLOT' else 'int'
            self.pila_operandos.push(valor)                  # generación
            self.pila_tipos.push(tipo)
            return tipo

        return 'int'

    # ── _generar_si_aplica ────────────────────────────────────────────────────
    # Punto neurálgico central: cuando el operador en el tope de pila_ops
    # pertenece al nivel de precedencia actual:
    #   Semántico: consulta el cubo semántico para obtener el tipo resultado.
    #   Generación: desapila operandos, crea temporal, genera cuádruplo.

    def _generar_si_aplica(self, ops_permitidos, tipo_izq, tipo_der):
        if self.pila_ops.vacia() or self.pila_ops.tope() not in ops_permitidos:
            return tipo_izq

        op       = self.pila_ops.pop()
        tipo_res = tipo_resultado(op, tipo_izq, tipo_der)   # semántico

        der = self.pila_operandos.pop(); self.pila_tipos.pop()
        izq = self.pila_operandos.pop(); self.pila_tipos.pop()
        tmp = self._nuevo_tmp()
        self.fila.agregar(Cuadruplo(op, izq, der, tmp))     # generación
        self.pila_operandos.push(tmp)
        self.pila_tipos.push(tipo_res)
        return tipo_res

    # ── PN-cond: condicion ────────────────────────────────────────────────────
    # Semántico: evalúa la expresión condicional (tipo).
    # Generación: GOTOF con backpatch, GOTO con backpatch para sino.

    def _condicion(self, nodo):
        hijos = [h for h in nodo.children if isinstance(h, Tree)]

        self._expresion(hijos[0])                                        # PN-cond-1
        cond = self.pila_operandos.pop(); self.pila_tipos.pop()
        idx_gotof = self.fila.agregar(Cuadruplo('GOTOF', cond, None, None))

        self._cuerpo(hijos[1])

        if len(hijos) == 3:                                              # PN-cond-2
            idx_goto = self.fila.agregar(Cuadruplo('GOTO', None, None, None))
            self.fila.rellenar(idx_gotof, self.fila.siguiente())
            self._cuerpo(hijos[2])
            self.fila.rellenar(idx_goto, self.fila.siguiente())          # PN-cond-3
        else:
            self.fila.rellenar(idx_gotof, self.fila.siguiente())         # PN-cond-3

    # ── PN-ciclo: ciclo ───────────────────────────────────────────────────────
    # Semántico: evalúa la expresión de control.
    # Generación: guarda dirección de retorno, GOTOF, GOTO de vuelta.

    def _ciclo(self, nodo):
        hijos = [h for h in nodo.children if isinstance(h, Tree)]

        inicio = self.fila.siguiente()                                   # PN-ciclo-1

        self._expresion(hijos[0])                                        # PN-ciclo-2
        cond = self.pila_operandos.pop(); self.pila_tipos.pop()
        idx_gotof = self.fila.agregar(Cuadruplo('GOTOF', cond, None, None))

        self._cuerpo(hijos[1])

        self.fila.agregar(Cuadruplo('GOTO', None, None, inicio))         # PN-ciclo-3
        self.fila.rellenar(idx_gotof, self.fila.siguiente())

    # ── imprime ───────────────────────────────────────────────────────────────
    # Generación: PRINT por cada imprimible.

    def _imprime(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'imprimible'):
                sub = hijo.children[0]
                if es_arbol(sub, 'expresion'):
                    self._expresion(sub)
                    val = self.pila_operandos.pop(); self.pila_tipos.pop()
                    self.fila.agregar(Cuadruplo('PRINT', val, None, None))
                elif es_token(sub, 'LETRERO'):
                    self.fila.agregar(Cuadruplo('PRINT', str(sub), None, None))

    # ── PN-llam: llamada ──────────────────────────────────────────────────────
    # Semántico: verifica existencia de función y aridad.
    # Generación: ERA, PARAM por argumento, GOSUB, RETVAL si tiene retorno.

    def _llamada(self, nodo):
        nombre = str(nodo.children[0])

        if not self.directorio.existe(nombre):                           # semántico
            raise SemanticError(f"Función no declarada: '{nombre}'")

        entrada = self.directorio.buscar(nombre)
        args    = [h for h in nodo.children if es_arbol(h, 'expresion')]

        if len(args) != len(entrada.params):                             # semántico
            raise SemanticError(
                f"Aridad incorrecta en '{nombre}': "
                f"esperados {len(entrada.params)}, recibidos {len(args)}"
            )

        self.fila.agregar(Cuadruplo('ERA', nombre, None, None))          # generación

        for i, arg in enumerate(args):
            self._expresion(arg)
            val = self.pila_operandos.pop(); self.pila_tipos.pop()
            self.fila.agregar(Cuadruplo('PARAM', val, None, f"param{i+1}"))

        self.fila.agregar(Cuadruplo('GOSUB', nombre, None, None))

        if entrada.tipo_retorno != 'nula':
            tmp = self._nuevo_tmp()
            self.fila.agregar(Cuadruplo('RETVAL', nombre, None, tmp))
            self.pila_operandos.push(tmp)
            self.pila_tipos.push(entrada.tipo_retorno)

        return entrada.tipo_retorno