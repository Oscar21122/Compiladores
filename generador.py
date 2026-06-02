from lark import Token, Tree
from semantic import (
    SemanticError,
    tipo_resultado,
    DirectorioFunciones,
)
from cuadruplos import Pila, Cuadruplo, FilaCuadruplos
from memoria    import MemoriaVirtual


def es_token(nodo, tipo):
    return isinstance(nodo, Token) and nodo.type == tipo

def es_arbol(nodo, regla):
    return isinstance(nodo, Tree) and nodo.data == regla


class GeneradorCuadruplos:
    """
    Punto único de generación: valida semántica y emite código intermedio
    con direcciones virtuales en un solo recorrido del árbol.
    """

    def __init__(self):
        # ── estructuras semánticas ──────────────────────
        self.directorio     = DirectorioFunciones()
        self._ambito_actual = None     # EntradaFuncion activa
        self._programa_nom  = None     # nombre del ámbito global

        # ── pilas de traducción ─────────────────────────
        self.pila_ops       = Pila("P_Ops")
        self.pila_operandos = Pila("P_Operandos")
        self.pila_tipos     = Pila("P_Tipos")

        # ── fila de cuádruplos ──────────────────────────
        self.fila = FilaCuadruplos()

        # ── memoria virtual ─────────────────────────────
        self.memoria = MemoriaVirtual()

    # ── helpers ──────────────────────────────────────────────────────────────

    def _scope(self):
        """Devuelve 'global' o 'local' según el ámbito actual."""
        return 'global' if self._ambito_actual.nombre == self._programa_nom else 'local'

    def _nuevo_temporal(self, tipo):
        """PN: pide al MemoriaVirtual una nueva dirección de temporal."""
        return self.memoria.nuevo_temporal(tipo)

    def _ambito_global(self):
        return self.directorio.buscar(self._programa_nom)

    def _buscar_variable(self, nombre):
        """Busca primero en el ámbito actual, luego en el global."""
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
    # Registra el programa como ámbito global. Si hay funciones declaradas,
    # se emite un GOTO inicial (cuádruplo 0) que las salta y aterriza en el main.
    # Al final del cuerpo se emite un cuádruplo END.

    def _programa(self, nodo):
        nombre_prog = str(nodo.children[1])
        self._programa_nom = nombre_prog
        self.directorio.agregar(nombre_prog, 'nula')
        self._ambito_actual = self.directorio.buscar(nombre_prog)

        # GOTO inicial que saltará al main (será relleno con backpatch)
        idx_goto_main = self.fila.agregar(Cuadruplo('GOTO', None, None, None))

        # 1) declaraciones de variables globales
        for hijo in nodo.children:
            if es_arbol(hijo, 'vars'):
                self._vars(hijo)

        # 2) funciones (su código vive antes del main; el GOTO inicial lo salta)
        for hijo in nodo.children:
            if es_arbol(hijo, 'funcs'):
                self._funcs(hijo)

        # Backpatch: el GOTO inicial apunta al primer cuádruplo del main
        self.fila.rellenar(idx_goto_main, self.fila.siguiente())

        # 3) cuerpo principal (main)
        for hijo in nodo.children:
            if es_arbol(hijo, 'cuerpo'):
                self._cuerpo(hijo)

        # Marca final
        self.fila.agregar(Cuadruplo('END', None, None, None))

    # ── PN-2: vars / decl_var ────────────────────────────────────────────────
    # Por cada id declarado: pide una dirección al MemoriaVirtual según el
    # ámbito actual (global o local) y el tipo, y registra la variable con
    # esa dirección en la tabla del ámbito.

    def _vars(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'decl_var'):
                self._decl_var(hijo)

    def _decl_var(self, nodo):
        tipo_nodo = next(h for h in nodo.children if es_arbol(h, 'tipo'))
        tipo      = self._tipo(tipo_nodo)
        scope     = self._scope()
        for hijo in nodo.children:
            if es_token(hijo, 'ID'):
                direccion = self.memoria.asignar_variable(scope, tipo)
                self._ambito_actual.tabla_vars.agregar(str(hijo), tipo, direccion)

    # ── PN-3/4/5: funcs / func / params ─────────────────────────────────────

    def _funcs(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'func'):
                self._func(hijo)

    def _func(self, nodo):
        primer      = nodo.children[0]
        tipo_ret    = self._tipo(primer) if es_arbol(primer, 'tipo') else 'nula'
        nombre_func = str(nodo.children[1])

        # PN-3: registra función, guarda dirección de inicio y cambia ámbito
        entrada_func = self.directorio.agregar(nombre_func, tipo_ret)
        entrada_func.inicio_cuad = self.fila.siguiente()

        # Slot GLOBAL de retorno: la función deja aquí su valor de retorno para
        # que RETVAL lo recoja del lado del llamador. Vive en el segmento global
        # para sobrevivir al cierre del marco de activación de la función.
        if tipo_ret != 'nula':
            entrada_func.dir_retorno = self.memoria.asignar_variable('global', tipo_ret)

        ambito_previo       = self._ambito_actual
        self._ambito_actual = entrada_func

        for hijo in nodo.children:
            if   es_arbol(hijo, 'params'): self._params(hijo)    # PN-4
            elif es_arbol(hijo, 'vars'):   self._vars(hijo)
            elif es_arbol(hijo, 'cuerpo'): self._cuerpo(hijo)

        # PN-5: marca fin de la función, registra el tamaño de su marco de
        # activación (recursos) y libera direcciones locales/temporales.
        self.fila.agregar(Cuadruplo('ENDFUNC', None, None, nombre_func))
        entrada_func.recursos = self.memoria.recursos_locales()
        self._ambito_actual = ambito_previo
        self.memoria.reiniciar_locales()

    def _params(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'param'):
                self._param(hijo)

    def _param(self, nodo):
        # PN-4: cada parámetro recibe dirección local del segmento correspondiente
        nombre    = str(nodo.children[0])
        tipo      = self._tipo(nodo.children[2])
        direccion = self.memoria.asignar_variable('local', tipo)
        self._ambito_actual.agregar_param(nombre, tipo, direccion)

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
        elif es_arbol(hijo, 'regresa'):   self._regresa(hijo)

    # ── PN-8: asigna ─────────────────────────────────────────────────────────
    # PN-8a (antes de la expresión): obtiene la dirección de la variable destino.
    # PN-8b (después): valida compatibilidad y genera (=, dir_expr, _, dir_var).

    def _asigna(self, nodo):
        nombre_var = str(nodo.children[0])
        var        = self._buscar_variable(nombre_var)

        tipo_exp = self._expresion(nodo.children[2])
        tipo_resultado('=', var.tipo, tipo_exp)

        dir_res = self.pila_operandos.pop()
        self.pila_tipos.pop()
        self.fila.agregar(Cuadruplo('=', dir_res, None, var.direccion))

    # ── PN-7: expresion / exp / termino ───────────────────────────────────────
    # PN-7a: cuando aparece un operador se apila en pila_ops.
    # PN-7b: al terminar el operando derecho, si el operador en el tope
    #        pertenece al nivel de precedencia actual, se genera el cuádruplo.

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
    # Para un id: busca la variable, recupera su dirección y la apila.
    # Para una cte: pide a MemoriaVirtual la dirección de la constante.
    # Para negación unaria de id: emite mult por la cte -1, deja un temporal.

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
            var    = self._buscar_variable(nombre)
            tipo   = var.tipo
            if signo == '-':
                dir_menos1 = self.memoria.asignar_constante('-1', 'int')
                tmp        = self._nuevo_temporal(tipo)
                self.fila.agregar(Cuadruplo('*', var.direccion, dir_menos1, tmp))
                self.pila_operandos.push(tmp)
            else:
                self.pila_operandos.push(var.direccion)
            self.pila_tipos.push(tipo)
            return tipo

        if es_arbol(operando, 'cte'):
            token     = operando.children[0]
            valor     = ('-' if signo == '-' else '') + str(token)
            tipo      = 'float' if token.type == 'CTE_FLOT' else 'int'
            direccion = self.memoria.asignar_constante(valor, tipo)
            self.pila_operandos.push(direccion)
            self.pila_tipos.push(tipo)
            return tipo

        return 'int'

    # ── _generar_si_aplica ────────────────────────────────────────────────────
    # Punto neurálgico central: si el operador en el tope de pila_ops es de la
    # precedencia actual, desapila operandos, consulta el cubo semántico, pide
    # una dirección temporal y emite el cuádruplo. Tras esto el resultado
    # (la dirección del temporal) queda en el tope de pila_operandos.

    def _generar_si_aplica(self, ops_permitidos, tipo_izq, tipo_der):
        if self.pila_ops.vacia() or self.pila_ops.tope() not in ops_permitidos:
            return tipo_izq

        op       = self.pila_ops.pop()
        tipo_res = tipo_resultado(op, tipo_izq, tipo_der)

        der = self.pila_operandos.pop(); self.pila_tipos.pop()
        izq = self.pila_operandos.pop(); self.pila_tipos.pop()
        tmp = self._nuevo_temporal(tipo_res)
        self.fila.agregar(Cuadruplo(op, izq, der, tmp))
        self.pila_operandos.push(tmp)
        self.pila_tipos.push(tipo_res)
        return tipo_res

    # ── PN-cond: condicion ────────────────────────────────────────────────────
    # PN-cond-1: tras la expresión se desapila la dirección del resultado
    #            booleano y se emite GOTOF con destino pendiente.
    # PN-cond-2: al llegar a 'sino' se emite GOTO pendiente y se hace
    #            backpatch del GOTOF al inicio del bloque sino.
    # PN-cond-3: al cerrar la condición se hace backpatch del GOTO/GOTOF
    #            al cuádruplo siguiente al condicional.

    def _condicion(self, nodo):
        hijos = [h for h in nodo.children if isinstance(h, Tree)]

        self._expresion(hijos[0])
        cond = self.pila_operandos.pop(); self.pila_tipos.pop()
        idx_gotof = self.fila.agregar(Cuadruplo('GOTOF', cond, None, None))

        self._cuerpo(hijos[1])

        if len(hijos) == 3:
            idx_goto = self.fila.agregar(Cuadruplo('GOTO', None, None, None))
            self.fila.rellenar(idx_gotof, self.fila.siguiente())
            self._cuerpo(hijos[2])
            self.fila.rellenar(idx_goto, self.fila.siguiente())
        else:
            self.fila.rellenar(idx_gotof, self.fila.siguiente())

    # ── PN-ciclo: ciclo ───────────────────────────────────────────────────────
    # PN-ci1: guarda el índice antes de la condición (destino del salto atrás).
    # PN-ci2: tras la expresión emite GOTOF con destino pendiente.
    # PN-ci3: al cerrar el cuerpo emite GOTO al inicio y backpatch del GOTOF
    #         al cuádruplo siguiente (salida del ciclo).

    def _ciclo(self, nodo):
        hijos = [h for h in nodo.children if isinstance(h, Tree)]

        inicio = self.fila.siguiente()

        self._expresion(hijos[0])
        cond = self.pila_operandos.pop(); self.pila_tipos.pop()
        idx_gotof = self.fila.agregar(Cuadruplo('GOTOF', cond, None, None))

        self._cuerpo(hijos[1])

        self.fila.agregar(Cuadruplo('GOTO', None, None, inicio))
        self.fila.rellenar(idx_gotof, self.fila.siguiente())

    # ── imprime ───────────────────────────────────────────────────────────────
    # Por cada imprimible: si es expresión se desapila la dirección del
    # resultado y se emite PRINT con esa dirección; si es letrero se pide
    # una dirección de constante string y se emite PRINT con ella.

    def _imprime(self, nodo):
        for hijo in nodo.children:
            if es_arbol(hijo, 'imprimible'):
                sub = hijo.children[0]
                if es_arbol(sub, 'expresion'):
                    self._expresion(sub)
                    val = self.pila_operandos.pop(); self.pila_tipos.pop()
                    self.fila.agregar(Cuadruplo('PRINT', val, None, None))
                elif es_token(sub, 'LETRERO'):
                    direccion = self.memoria.asignar_constante(str(sub), 'string')
                    self.fila.agregar(Cuadruplo('PRINT', direccion, None, None))

    # ── PN-llam: llamada ──────────────────────────────────────────────────────
    # PN-L1: verifica existencia, valida aridad y emite ERA.
    # PN-L2: por cada argumento emite PARAM con la dirección del valor y la
    #        dirección del parámetro destino (el i-ésimo en la función).
    # PN-L3: emite GOSUB; si la función no es nula, emite RETVAL en un temporal
    #        y deja ese temporal en pila_operandos para que la llamada pueda
    #        usarse dentro de una expresión.

    def _llamada(self, nodo):
        nombre = str(nodo.children[0])

        if not self.directorio.existe(nombre):
            raise SemanticError(f"Función no declarada: '{nombre}'")

        entrada = self.directorio.buscar(nombre)
        args    = [h for h in nodo.children if es_arbol(h, 'expresion')]

        if len(args) != len(entrada.params):
            raise SemanticError(
                f"Aridad incorrecta en '{nombre}': "
                f"esperados {len(entrada.params)}, recibidos {len(args)}"
            )

        self.fila.agregar(Cuadruplo('ERA', nombre, None, None))

        for i, arg in enumerate(args):
            self._expresion(arg)
            val = self.pila_operandos.pop(); self.pila_tipos.pop()
            param_nombre, _param_tipo = entrada.params[i]
            param_dir = entrada.tabla_vars.buscar(param_nombre).direccion
            self.fila.agregar(Cuadruplo('PARAM', val, None, param_dir))

        self.fila.agregar(Cuadruplo('GOSUB', nombre, None, None))

        if entrada.tipo_retorno != 'nula':
            tmp = self._nuevo_temporal(entrada.tipo_retorno)
            self.fila.agregar(Cuadruplo('RETVAL', nombre, None, tmp))
            self.pila_operandos.push(tmp)
            self.pila_tipos.push(entrada.tipo_retorno)

        return entrada.tipo_retorno

    # ── PN-R: regresa ─────────────────────────────────────────────────────────
    # Punto neurálgico del estatuto `regresa expresion;`.
    #
    # Validaciones semánticas (tres):
    #   1. El ámbito actual debe ser una función, no el programa principal.
    #   2. La función debe tener un tipo de retorno distinto de 'nula'.
    #   3. El tipo de la expresión debe ser compatible con el tipo de retorno
    #      (se reusa la regla del cubo semántico para '=': float aceptado en int
    #      es error, int aceptado en float convierte implícitamente).
    #
    # Generación:
    #   Emite (RETURN, dir_valor, _, _). El operando izquierdo es la dirección
    #   virtual del resultado de la expresión (variable, temporal o constante).
    #   La VM, al ejecutar este cuádruplo, deposita el valor en el slot de
    #   retorno de la función (que la instrucción RETVAL del lado del llamador
    #   leerá después de GOSUB) y pone fin al marco de activación actual.

    def _regresa(self, nodo):
        # Validación 1: estamos dentro de una función, no en el main
        if self._ambito_actual.nombre == self._programa_nom:
            raise SemanticError(
                "'regresa' sólo puede usarse dentro de una función"
            )
        # Validación 2: la función no es nula
        if self._ambito_actual.tipo_retorno == 'nula':
            raise SemanticError(
                f"La función nula '{self._ambito_actual.nombre}' no puede "
                f"regresar un valor"
            )

        # Evaluar la expresión y obtener su tipo
        expr_nodo = next(h for h in nodo.children if es_arbol(h, 'expresion'))
        tipo_expr = self._expresion(expr_nodo)

        # Validación 3: compatibilidad de tipos (cubo semántico, operador '=')
        tipo_resultado('=', self._ambito_actual.tipo_retorno, tipo_expr)

        # Generar cuádruplo RETURN con la dirección del valor de retorno
        dir_valor = self.pila_operandos.pop()
        self.pila_tipos.pop()
        self.fila.agregar(Cuadruplo('RETURN', dir_valor, None, None))