
# ─────────────────────────────────────────
#  STACK  (LIFO)
# ─────────────────────────────────────────
class Stack:
    """Pila LIFO implementada sobre una lista de Python."""

    def __init__(self):
        self._data = []

    def push(self, item):
        """Agrega un elemento al tope."""
        self._data.append(item)

    def pop(self):
        """Elimina y devuelve el elemento del tope. Lanza IndexError si está vacía."""
        if self.is_empty():
            raise IndexError("pop en stack vacío")
        return self._data.pop()

    def peek(self):
        """Devuelve el elemento del tope sin eliminarlo."""
        if self.is_empty():
            raise IndexError("peek en stack vacío")
        return self._data[-1]

    def is_empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)

    def clear(self):
        self._data.clear()

    def __repr__(self):
        return f"Stack(top → {self._data[::-1]})"


# ─────────────────────────────────────────
#  QUEUE  (FIFO)
# ─────────────────────────────────────────
from collections import deque

class Queue:
    """Cola FIFO implementada sobre collections.deque (O(1) en ambos extremos)."""

    def __init__(self):
        self._data = deque()

    def enqueue(self, item):
        """Agrega un elemento al final."""
        self._data.append(item)

    def dequeue(self):
        """Elimina y devuelve el elemento del frente. Lanza IndexError si está vacía."""
        if self.is_empty():
            raise IndexError("dequeue en queue vacía")
        return self._data.popleft()

    def front(self):
        """Devuelve el elemento del frente sin eliminarlo."""
        if self.is_empty():
            raise IndexError("front en queue vacía")
        return self._data[0]

    def is_empty(self):
        return len(self._data) == 0

    def size(self):
        return len(self._data)

    def clear(self):
        self._data.clear()

    def __repr__(self):
        return f"Queue(front → {list(self._data)})"


# ─────────────────────────────────────────
#  DICTIONARY / HASH TABLE  (orden inserción)
# ─────────────────────────────────────────
class Dictionary:
    """
    Tabla hash ordenada por inserción.
    Internamente usa el dict nativo de Python 3.7+ (orden garantizado).
    """

    def __init__(self):
        self._data = {}

    def put(self, key, value):
        """Inserta o actualiza una clave."""
        self._data[key] = value

    def get(self, key, default=None):
        """Devuelve el valor de la clave, o default si no existe."""
        return self._data.get(key, default)

    def remove(self, key):
        """Elimina la clave. Lanza KeyError si no existe."""
        if key not in self._data:
            raise KeyError(f"clave '{key}' no encontrada")
        del self._data[key]

    def contains(self, key):
        return key in self._data

    def keys(self):
        return list(self._data.keys())

    def values(self):
        return list(self._data.values())

    def items(self):
        return list(self._data.items())

    def size(self):
        return len(self._data)

    def is_empty(self):
        return len(self._data) == 0

    def clear(self):
        self._data.clear()

    def __repr__(self):
        return f"Dictionary({self._data})"