import unittest
from structures import Stack, Queue, Dictionary

# ─────────────────────────────────────────
#  Tests: Stack
# ─────────────────────────────────────────
class TestStack(unittest.TestCase):

    def setUp(self):
        self.s = Stack()

    # TC-S1: Stack recién creado está vacío
    def test_s1_empty_on_creation(self):
        self.assertTrue(self.s.is_empty())
        self.assertEqual(self.s.size(), 0)

    # TC-S2: push agrega elementos y size crece
    def test_s2_push_increases_size(self):
        self.s.push(1)
        self.s.push(2)
        self.assertEqual(self.s.size(), 2)
        self.assertFalse(self.s.is_empty())

    # TC-S3: pop devuelve LIFO (último en entrar, primero en salir)
    def test_s3_pop_lifo_order(self):
        for v in [1, 2, 3]:
            self.s.push(v)
        self.assertEqual(self.s.pop(), 3)
        self.assertEqual(self.s.pop(), 2)
        self.assertEqual(self.s.pop(), 1)

    # TC-S4: peek no elimina el tope
    def test_s4_peek_no_removal(self):
        self.s.push(99)
        self.assertEqual(self.s.peek(), 99)
        self.assertEqual(self.s.size(), 1)   # sigue ahí

    # TC-S5: pop / peek en stack vacío lanza IndexError
    def test_s5_pop_empty_raises(self):
        with self.assertRaises(IndexError):
            self.s.pop()

    def test_s5b_peek_empty_raises(self):
        with self.assertRaises(IndexError):
            self.s.peek()

    # TC-S6: clear vacía el stack
    def test_s6_clear(self):
        self.s.push(1)
        self.s.push(2)
        self.s.clear()
        self.assertTrue(self.s.is_empty())

    # TC-S7: acepta tipos mixtos
    def test_s7_mixed_types(self):
        self.s.push("hola")
        self.s.push(3.14)
        self.s.push([1, 2])
        self.assertEqual(self.s.size(), 3)


# ─────────────────────────────────────────
#  Tests: Queue
# ─────────────────────────────────────────
class TestQueue(unittest.TestCase):

    def setUp(self):
        self.q = Queue()

    # TC-Q1: Queue recién creada está vacía
    def test_q1_empty_on_creation(self):
        self.assertTrue(self.q.is_empty())
        self.assertEqual(self.q.size(), 0)

    # TC-Q2: enqueue agrega elementos
    def test_q2_enqueue_increases_size(self):
        self.q.enqueue("x")
        self.q.enqueue("y")
        self.assertEqual(self.q.size(), 2)

    # TC-Q3: dequeue devuelve FIFO (primero en entrar, primero en salir)
    def test_q3_dequeue_fifo_order(self):
        for v in ["a", "b", "c"]:
            self.q.enqueue(v)
        self.assertEqual(self.q.dequeue(), "a")
        self.assertEqual(self.q.dequeue(), "b")
        self.assertEqual(self.q.dequeue(), "c")

    # TC-Q4: front no elimina el frente
    def test_q4_front_no_removal(self):
        self.q.enqueue(7)
        self.assertEqual(self.q.front(), 7)
        self.assertEqual(self.q.size(), 1)

    # TC-Q5: dequeue / front en queue vacía lanza IndexError
    def test_q5_dequeue_empty_raises(self):
        with self.assertRaises(IndexError):
            self.q.dequeue()

    def test_q5b_front_empty_raises(self):
        with self.assertRaises(IndexError):
            self.q.front()

    # TC-Q6: clear vacía la queue
    def test_q6_clear(self):
        self.q.enqueue(1)
        self.q.clear()
        self.assertTrue(self.q.is_empty())


# ─────────────────────────────────────────
#  Tests: Dictionary
# ─────────────────────────────────────────
class TestDictionary(unittest.TestCase):

    def setUp(self):
        self.d = Dictionary()

    # TC-D1: Dictionary recién creado está vacío
    def test_d1_empty_on_creation(self):
        self.assertTrue(self.d.is_empty())
        self.assertEqual(self.d.size(), 0)

    # TC-D2: put y get básicos
    def test_d2_put_and_get(self):
        self.d.put("nombre", "Ana")
        self.assertEqual(self.d.get("nombre"), "Ana")

    # TC-D3: put actualiza valor existente
    def test_d3_put_updates_value(self):
        self.d.put("x", 1)
        self.d.put("x", 99)
        self.assertEqual(self.d.get("x"), 99)
        self.assertEqual(self.d.size(), 1)

    # TC-D4: get con default para clave inexistente
    def test_d4_get_default(self):
        self.assertIsNone(self.d.get("no_existe"))
        self.assertEqual(self.d.get("no_existe", "fallback"), "fallback")

    # TC-D5: contains detecta presencia/ausencia
    def test_d5_contains(self):
        self.d.put("a", 1)
        self.assertTrue(self.d.contains("a"))
        self.assertFalse(self.d.contains("z"))

    # TC-D6: remove elimina la clave
    def test_d6_remove(self):
        self.d.put("k", "v")
        self.d.remove("k")
        self.assertFalse(self.d.contains("k"))

    # TC-D7: remove en clave inexistente lanza KeyError
    def test_d7_remove_missing_raises(self):
        with self.assertRaises(KeyError):
            self.d.remove("ghost")

    # TC-D8: keys / values / items reflejan el estado actual
    def test_d8_keys_values_items(self):
        self.d.put("a", 1)
        self.d.put("b", 2)
        self.assertEqual(self.d.keys(), ["a", "b"])
        self.assertEqual(self.d.values(), [1, 2])
        self.assertEqual(self.d.items(), [("a", 1), ("b", 2)])

    # TC-D9: orden de inserción se preserva
    def test_d9_insertion_order(self):
        for k in ["z", "m", "a"]:
            self.d.put(k, k)
        self.assertEqual(self.d.keys(), ["z", "m", "a"])

    # TC-D10: clear vacía el diccionario
    def test_d10_clear(self):
        self.d.put("x", 1)
        self.d.clear()
        self.assertTrue(self.d.is_empty())


if __name__ == "__main__":
    unittest.main(verbosity=2)