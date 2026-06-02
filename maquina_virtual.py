# maquina_virtual.py
# Máquina Virtual del compilador Patito.
#
# Recibe los cuádruplos, la tabla de constantes y el directorio de funciones
# producidos por el GeneradorCuadruplos y los EJECUTA.
#
# La VM no vuelve a mirar el árbol ni los nombres de variables: trabaja
# exclusivamente con DIRECCIONES VIRTUALES enteras. El rango de cada dirección
# indica en qué estructura de la Memoria de Ejecución vive el dato y de qué
# tipo es, sin necesidad de tablas adicionales en tiempo de ejecución.
#
# ┌────────────┬──────────┬─────────────────┬──────────────────────────────┐
# │ Segmento   │ Tipo     │ Rango           │ Estructura en la VM           │
# ├────────────┼──────────┼─────────────────┼──────────────────────────────┤
# │ Global     │ int      │  1000 - 1999    │ mem_global  (vive todo el     │
# │ Global     │ float    │  2000 - 2999    │              programa)        │
# │ Local      │ int      │  3000 - 3999    │ marco_actual (cambia en cada  │
# │ Local      │ float    │  4000 - 4999    │              llamada/retorno) │
# │ Temporal   │ int      │  5000 - 5999    │ marco_actual                  │
# │ Temporal   │ float    │  6000 - 6999    │ marco_actual                  │
# │ Constante  │ int      │  7000 - 7999    │ mem_const   (sólo lectura)    │
# │ Constante  │ float    │  8000 - 8999    │ mem_const                     │
# │ Constante  │ string   │  9000 - 9999    │ mem_const                     │
# └────────────┴──────────┴─────────────────┴──────────────────────────────┘


class VMError(Exception):
    pass


# ─────────────────────────────────────────
# MEMORIA DE EJECUCIÓN
# ─────────────────────────────────────────

# Fronteras de segmento (deben coincidir con memoria.py / BASES)
GLOBAL_INI   = 1000
LOCAL_INI    = 3000
TEMP_INI     = 5000
CONST_INI    = 7000
CONST_FIN    = 9999


def tipo_de_direccion(dir_v):
    """
    La propia dirección codifica el tipo del dato. Cada banda de 1000
    direcciones de cada segmento alterna int / float / string, así que el
    tipo se deduce con aritmética simple, sin tablas auxiliares.
    """
    banda = (dir_v // 1000)
    if banda in (1, 3, 5, 7):   # global/local/temp/const int
        return 'int'
    if banda in (2, 4, 6, 8):   # global/local/temp/const float
        return 'float'
    if banda == 9:              # const string
        return 'string'
    raise VMError(f"Dirección fuera de rango: {dir_v}")


def _coerce(valor, tipo):
    """Ajusta el valor al tipo que implica la dirección destino."""
    if tipo == 'int':
        return int(valor)
    if tipo == 'float':
        return float(valor)
    return valor   # string


class Marco:
    """
    Marco de Activación (Activation Record).

    Estructura: un diccionario disperso  {direccion_virtual : valor}  que cubre
    los segmentos local (3000-4999) y temporal (5000-6999) de UNA invocación.
    Cada llamada a función crea su propio Marco, por eso dos funciones pueden
    reutilizar las mismas direcciones (p. ej. 3000) sin colisionar: cada una
    vive en un Marco distinto dentro de la pila de ejecución.

    Métodos de acceso:
      leer(dir)          -> valor almacenado en esa dirección local/temporal
      escribir(dir, val) -> guarda val en esa dirección local/temporal
    """
    __slots__ = ('datos', 'func')

    def __init__(self, func):
        self.datos = {}      # dirección -> valor
        self.func  = func    # nombre de la función dueña del marco

    def leer(self, dir_v):
        if dir_v not in self.datos:
            raise VMError(f"Lectura de dirección local no inicializada: {dir_v}")
        return self.datos[dir_v]

    def escribir(self, dir_v, valor):
        self.datos[dir_v] = valor


# ─────────────────────────────────────────
# MÁQUINA VIRTUAL
# ─────────────────────────────────────────

class MaquinaVirtual:
    """
    Intérprete de los cuádruplos de Patito.

    Estructuras principales de la Memoria de Ejecución:
      - mem_global   : dict  {dir: valor}  para 1000-2999 (variables globales y
                       slots de retorno de funciones). Vive todo el programa.
      - mem_const    : dict  {dir: valor}  para 7000-9999, sólo lectura, cargada
                       al inicio desde la tabla de constantes.
      - marco_actual : Marco con los segmentos local y temporal de la ejecución
                       en curso (3000-6999).
      - pila_marcos  : pila de Marcos pendientes creados por ERA y aún no
                       activados por GOSUB (soporta llamadas anidadas, p. ej.
                       f(g(x))).
      - pila_llamadas: pila de contextos de retorno (ip_retorno, marco_llamador,
                       func_llamador) que GOSUB apila y RETURN/ENDFUNC restauran.
    """

    def __init__(self, cuadruplos, constantes, directorio, nombre_programa):
        self.cuads        = cuadruplos                 # list[Cuadruplo]
        self.directorio   = directorio                 # DirectorioFunciones
        self.nombre_prog  = nombre_programa

        # ── memorias persistentes ───────────────────────
        self.mem_global   = {}
        self.mem_const    = dict(constantes)           # copia: 7000-9999

        # ── marco de la ejecución principal (main) ──────
        self.marco_actual = Marco(nombre_programa)

        # ── pilas de control ────────────────────────────
        self.pila_marcos   = []   # marcos creados por ERA, pendientes de GOSUB
        self.pila_llamadas = []   # (ip_retorno, marco_llamador, func_llamador)
        self.func_actual   = nombre_programa

        # ── salida del programa (para pruebas) ──────────
        self.salida = []

    # ── fábrica desde el generador ────────────────────────────────────────────
    @classmethod
    def desde_generador(cls, gen):
        return cls(
            cuadruplos      = gen.fila.todos(),
            constantes      = gen.memoria.tabla_constantes(),
            directorio      = gen.directorio,
            nombre_programa = gen._programa_nom,
        )

    # ── acceso unificado a memoria (enrutado por la dirección) ─────────────────
    def leer(self, dir_v):
        if dir_v is None:
            return None
        if GLOBAL_INI <= dir_v < LOCAL_INI:          # 1000-2999 global
            if dir_v not in self.mem_global:
                raise VMError(f"Lectura de global no inicializada: {dir_v}")
            return self.mem_global[dir_v]
        if LOCAL_INI <= dir_v < CONST_INI:           # 3000-6999 local/temporal
            return self.marco_actual.leer(dir_v)
        if CONST_INI <= dir_v <= CONST_FIN:          # 7000-9999 constante
            return self.mem_const[dir_v]
        raise VMError(f"Dirección inválida en lectura: {dir_v}")

    def escribir(self, dir_v, valor):
        valor = _coerce(valor, tipo_de_direccion(dir_v))
        if GLOBAL_INI <= dir_v < LOCAL_INI:
            self.mem_global[dir_v] = valor
        elif LOCAL_INI <= dir_v < CONST_INI:
            self.marco_actual.escribir(dir_v, valor)
        elif CONST_INI <= dir_v <= CONST_FIN:
            raise VMError(f"Escritura sobre constante prohibida: {dir_v}")
        else:
            raise VMError(f"Dirección inválida en escritura: {dir_v}")

    # ── ciclo principal de ejecución ──────────────────────────────────────────
    def ejecutar(self, traza=False):
        ip = 0
        while ip < len(self.cuads):
            c = self.cuads[ip]
            op = c.op
            if traza:
                print(f"   [{ip:>3}] {c}")

            # ── fin de programa ─────────────────────────
            if op == 'END':
                break

            # ── aritmética ──────────────────────────────
            elif op in ('+', '-', '*', '/'):
                a = self.leer(c.izq)
                b = self.leer(c.der)
                if   op == '+': r = a + b
                elif op == '-': r = a - b
                elif op == '*': r = a * b
                else:
                    if b == 0:
                        raise VMError("División entre cero")
                    r = a / b
                self.escribir(c.res, r)

            # ── relacionales (resultado 0/1) ────────────
            elif op in ('>', '<', '!=', '=='):
                a = self.leer(c.izq)
                b = self.leer(c.der)
                if   op == '>':  r = a >  b
                elif op == '<':  r = a <  b
                elif op == '!=': r = a != b
                else:            r = a == b
                self.escribir(c.res, 1 if r else 0)

            # ── asignación ──────────────────────────────
            elif op == '=':
                self.escribir(c.res, self.leer(c.izq))

            # ── impresión ───────────────────────────────
            elif op == 'PRINT':
                valor = self.leer(c.izq)
                self.salida.append(str(valor))
                print(valor)

            # ── saltos ──────────────────────────────────
            elif op == 'GOTO':
                ip = c.res
                continue
            elif op == 'GOTOF':
                if not self.leer(c.izq):
                    ip = c.res
                    continue

            # ── declaración / invocación de funciones ───
            elif op == 'ERA':
                # Reserva un marco nuevo para la función llamada y lo deja
                # pendiente (aún no es el marco activo). El tamaño teórico del
                # marco lo da entrada.recursos; el dict lo crea bajo demanda.
                self.pila_marcos.append(Marco(c.izq))

            elif op == 'PARAM':
                # Copia el valor del argumento (leído en el contexto del
                # llamador) a la dirección del parámetro DENTRO del marco
                # pendiente (el que está en el tope de pila_marcos).
                valor   = self.leer(c.izq)
                pdir    = c.res
                pend    = self.pila_marcos[-1]
                pend.escribir(pdir, _coerce(valor, tipo_de_direccion(pdir)))

            elif op == 'GOSUB':
                entrada = self.directorio.buscar(c.izq)
                # Guarda el contexto de retorno del llamador
                self.pila_llamadas.append(
                    (ip + 1, self.marco_actual, self.func_actual)
                )
                # Activa el marco pendiente como marco actual
                self.marco_actual = self.pila_marcos.pop()
                self.func_actual  = c.izq
                ip = entrada.inicio_cuad
                continue

            elif op == 'RETURN':
                # Deposita el valor de retorno en el slot GLOBAL de la función
                # (debe leerse ANTES de restaurar el marco del llamador) y
                # retorna el control.
                entrada = self.directorio.buscar(self.func_actual)
                valor   = self.leer(c.izq)
                self.escribir(entrada.dir_retorno, valor)
                ip = self._retornar()
                continue

            elif op == 'ENDFUNC':
                # Fin natural de una función (típicamente nula) sin 'regresa'.
                ip = self._retornar()
                continue

            elif op == 'RETVAL':
                # Del lado del llamador: copia el valor del slot global de la
                # función a un temporal del marco actual (ya restaurado).
                entrada = self.directorio.buscar(c.izq)
                valor   = self.leer(entrada.dir_retorno)
                self.escribir(c.res, valor)

            else:
                raise VMError(f"Operador desconocido en cuádruplo: {op}")

            ip += 1

        return self.salida

    # ── restauración de contexto al retornar de una función ────────────────────
    def _retornar(self):
        if not self.pila_llamadas:
            raise VMError("RETURN/ENDFUNC sin llamada activa")
        ip_ret, marco_llamador, func_llamador = self.pila_llamadas.pop()
        self.marco_actual = marco_llamador
        self.func_actual  = func_llamador
        return ip_ret

    # ── volcado de memoria (depuración) ─────────────────────────────────────────
    def imprimir_memoria(self):
        print("\n===== MEMORIA DE EJECUCIÓN (estado final) =====")
        print("  GLOBAL :", dict(sorted(self.mem_global.items())))
        print("  MARCO  :", dict(sorted(self.marco_actual.datos.items())))
        print("  CONST  :", dict(sorted(self.mem_const.items())))
        print("===============================================\n")