# memoria.py
# Administrador de Memoria Virtual del compilador Patito.
#
# Traduce variables, constantes y temporales a DIRECCIONES VIRTUALES.
# El espacio de direcciones se divide en SEGMENTOS (global, local, temporal,
# constante) y cada segmento en TIPOS (int, float). Cada combinación
# (segmento, tipo) tiene un rango contiguo de 1000 direcciones.
#
# ┌────────────┬──────────┬─────────────────┐
# │ Segmento   │ Tipo     │ Rango           │
# ├────────────┼──────────┼─────────────────┤
# │ Global     │ int      │  1000 - 1999    │
# │ Global     │ float    │  2000 - 2999    │
# │ Local      │ int      │  3000 - 3999    │
# │ Local      │ float    │  4000 - 4999    │
# │ Temporal   │ int      │  5000 - 5999    │
# │ Temporal   │ float    │  6000 - 6999    │
# │ Constante  │ int      │  7000 - 7999    │
# │ Constante  │ float    │  8000 - 8999    │
# │ Constante  │ string   │  9000 - 9999    │
# └────────────┴──────────┴─────────────────┘


# ─────────────────────────────────────────
# BASES DE CADA SEGMENTO / TIPO
# ─────────────────────────────────────────

BASES = {
    ('global',   'int'):    1000,
    ('global',   'float'):  2000,
    ('local',    'int'):    3000,
    ('local',    'float'):  4000,
    ('temporal', 'int'):    5000,
    ('temporal', 'float'):  6000,
    ('constante','int'):    7000,
    ('constante','float'):  8000,
    ('constante','string'): 9000,
}

LIMITE_SEGMENTO = 1000   # direcciones disponibles por (segmento, tipo)


class MemoriaError(Exception):
    pass


class SegmentoMemoria:
    """
    Administra un único par (segmento, tipo): entrega la siguiente dirección
    libre dentro de su rango y verifica que no se desborde.
    """
    def __init__(self, base, limite=LIMITE_SEGMENTO):
        self.base     = base
        self.limite   = limite
        self.contador = 0

    def siguiente(self):
        if self.contador >= self.limite:
            raise MemoriaError(
                f"Segmento desbordado en base {self.base} (límite {self.limite})"
            )
        dir_virtual = self.base + self.contador
        self.contador += 1
        return dir_virtual

    def reiniciar(self):
        """Libera el segmento (usado al salir de un ámbito local)."""
        self.contador = 0


# ─────────────────────────────────────────
# ADMINISTRADOR PRINCIPAL
# ─────────────────────────────────────────

class MemoriaVirtual:
    """
    Punto único de asignación de direcciones virtuales.

    - asignar_variable(segmento, tipo) → dirección para una variable declarada.
    - nuevo_temporal(tipo)             → dirección para un temporal generado.
    - asignar_constante(valor, tipo)   → dirección para una constante
                                         (reutiliza la misma dirección si la
                                         constante ya apareció antes).
    - reiniciar_locales()              → recicla segmentos locales y temporales
                                         al terminar una función.
    """

    def __init__(self):
        # un SegmentoMemoria por cada (segmento, tipo)
        self._segmentos = {
            clave: SegmentoMemoria(base) for clave, base in BASES.items()
        }
        # tabla de constantes ya vistas: (valor, tipo) → dirección
        self._consts = {}

    # ── variables ────────────────────────────────────────────────────────────
    def asignar_variable(self, segmento, tipo):
        return self._segmentos[(segmento, tipo)].siguiente()

    # ── temporales ───────────────────────────────────────────────────────────
    def nuevo_temporal(self, tipo):
        return self._segmentos[('temporal', tipo)].siguiente()

    # ── constantes ───────────────────────────────────────────────────────────
    def asignar_constante(self, valor, tipo):
        clave = (str(valor), tipo)
        if clave in self._consts:
            return self._consts[clave]          # reutiliza dirección existente
        dir_virtual = self._segmentos[('constante', tipo)].siguiente()
        self._consts[clave] = dir_virtual
        return dir_virtual

    # ── reciclaje de ámbito local ────────────────────────────────────────────
    def reiniciar_locales(self):
        self._segmentos[('local', 'int')].reiniciar()
        self._segmentos[('local', 'float')].reiniciar()
        self._segmentos[('temporal', 'int')].reiniciar()
        self._segmentos[('temporal', 'float')].reiniciar()

    # ── tabla de constantes (depuración / cuádruplo final) ────────────────────
    def imprimir_constantes(self):
        print("\n===== TABLA DE CONSTANTES =====")
        for (val, tipo), dir_v in sorted(self._consts.items(), key=lambda x: x[1]):
            print(f"  {dir_v:<6} <- {val}  ({tipo})")
        print("===============================\n")