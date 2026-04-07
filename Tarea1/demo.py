from structures import Stack, Queue, Dictionary

SEP = "─" * 45

def demo_stack():
    print(SEP)
    print("  STACK (LIFO)")
    print(SEP)
    s = Stack()

    for val in [10, 20, 30, 40]:
        s.push(val)
        print(f"  push({val})  →  {s}")

    print(f"\n  peek()  →  {s.peek()}  (sin eliminar)")
    print(f"  pop()   →  {s.pop()}")
    print(f"  pop()   →  {s.pop()}")
    print(f"  estado  →  {s}  | tamaño: {s.size()}")

    s.clear()
    print(f"  clear() →  vacía: {s.is_empty()}")
    print()

def demo_queue():
    print(SEP)
    print("  QUEUE (FIFO)")
    print(SEP)
    q = Queue()

    for val in ["A", "B", "C", "D"]:
        q.enqueue(val)
        print(f"  enqueue('{val}')  →  {q}")

    print(f"\n  front()    →  '{q.front()}'  (sin eliminar)")
    print(f"  dequeue()  →  '{q.dequeue()}'")
    print(f"  dequeue()  →  '{q.dequeue()}'")
    print(f"  estado     →  {q}  | tamaño: {q.size()}")

    q.clear()
    print(f"  clear()    →  vacía: {q.is_empty()}")
    print()

def demo_dictionary():
    print(SEP)
    print("  DICTIONARY / HASH TABLE")
    print(SEP)
    d = Dictionary()

    datos = [("nombre", "Ana"), ("edad", 25), ("ciudad", "Monterrey"), ("rol", "dev")]
    for k, v in datos:
        d.put(k, v)
        print(f"  put('{k}', {v!r})")

    print(f"\n  estado     →  {d}")
    print(f"  get('edad')       →  {d.get('edad')}")
    print(f"  get('x', 'N/A')   →  {d.get('x', 'N/A')}")
    print(f"  contains('rol')   →  {d.contains('rol')}")

    d.put("edad", 26)          # actualizar
    print(f"\n  put('edad', 26)  [actualizar]  →  {d.get('edad')}")

    d.remove("ciudad")
    print(f"  remove('ciudad') →  keys: {d.keys()}")
    print(f"  items()  →  {d.items()}")
    print(f"  tamaño   →  {d.size()}")

    d.clear()
    print(f"  clear()  →  vacía: {d.is_empty()}")
    print()

if __name__ == "__main__":
    print("\n" + SEP)
    print("  DEMO — Estructuras de Datos en Python")
    print(SEP + "\n")
    demo_stack()
    demo_queue()
    demo_dictionary()
    print("  ✓ Demo completado sin errores.")