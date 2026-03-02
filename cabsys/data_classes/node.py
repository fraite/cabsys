import typing

from cabsys.quantity.quantity_store import QuantityStore, QFloat, QStr, QBool, QInt, QuantityBase


class NoEarthMat:
    pass


class Node(QuantityStore):
    """A node between cable sections.

    A node is a point (or area) that contains connections between installation sections. A node may have a local earth
    mat"""

    name: typing.Optional[str]
    resistance: QFloat

    def __init__(self, **kwargs):
        super().__init__()

        self.name = None
        self.resistance = QFloat(None, unit='ohm', description='earth mat resistance', source=None,
                                 options=None, symbol='R_E')

        super().post_init(**kwargs)
