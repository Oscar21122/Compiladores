from collections import deque


# ═════════════════════════════════════════════════════════════════════════════
# PILA GENÉRICA
# ═════════════════════════════════════════════════════════════════════════════

class Pila:
    """
    Pila (LIFO) genérica usada para Operadores, Operandos y Tipos.
    """
    def __init__(self, nombre="Pila"):
        self._datos = []
        self.nombre = nombre

    def push(self, valor):
        self._datos.append(valor)

    def pop(self):
        if self.vacia():
            raise IndexError(f"[{self.nombre}] pop() sobre pila vacía")
        return self._datos.pop()

    def pop_safe(self):
        return self._datos.pop() if self._datos else None

    def tope(self):
        return self._datos[-1] if self._datos else None

    def vacia(self):
        return len(self._datos) == 0

    def __len__(self):
        return len(self._datos)

    def __repr__(self):
        return f"{self.nombre}{self._datos}"


# ═════════════════════════════════════════════════════════════════════════════
# CUÁDRUPLO
# ═════════════════════════════════════════════════════════════════════════════

class Cuadruplo:
    """
    Cuádruplo: (operador, operando_izq, operando_der, resultado)
    """
    __slots__ = ('op', 'izq', 'der', 'res')

    def __init__(self, op, izq=None, der=None, res=None):
        self.op  = op
        self.izq = izq
        self.der = der
        self.res = res

    def __repr__(self):
        izq = str(self.izq) if self.izq is not None else '_'
        der = str(self.der) if self.der is not None else '_'
        res = str(self.res) if self.res is not None else '_'
        return f"({self.op:<6} {izq:<12} {der:<12} {res})"


# ═════════════════════════════════════════════════════════════════════════════
# FILA DE CUÁDRUPLOS
# ═════════════════════════════════════════════════════════════════════════════

class FilaCuadruplos:
    """
    Fila (FIFO) de cuádruplos con numeración desde 0.
    """
    def __init__(self):
        self._lista    = []
        self._contador = 0

    def agregar(self, cuad: Cuadruplo) -> int:
        idx = self._contador
        self._lista.append(cuad)
        self._contador += 1
        return idx

    def siguiente(self) -> int:
        return self._contador

    def rellenar(self, idx: int, valor):
        """Backpatch: rellena el resultado de un cuádruplo ya generado."""
        self._lista[idx].res = valor

    def get(self, idx: int) -> Cuadruplo:
        return self._lista[idx]

    def todos(self):
        return list(self._lista)

    def imprimir(self):
        print("\n╔═══════╦══════════╦══════════════╦══════════════╦════════╗")
        print("║  Idx  ║    Op    ║    Izq       ║    Der       ║  Res   ║")
        print("╠═══════╬══════════╬══════════════╬══════════════╬════════╣")
        for i, c in enumerate(self._lista):
            izq = str(c.izq) if c.izq is not None else '_'
            der = str(c.der) if c.der is not None else '_'
            res = str(c.res) if c.res is not None else '_'
            print(f"║  {i:<4} ║ {c.op:<8} ║ {izq:<12} ║ {der:<12} ║ {res:<6} ║")
        print("╚═══════╩══════════╩══════════════╩══════════════╩════════╝")

    def __len__(self):
        return self._contador