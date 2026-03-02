"""Exceptions Classes

Used for Exceptions generated throughout cable systems program
"""


class InvalidInput(Exception):
    """Invalid Input

    This Exception indicates an invalid or missing input.
    """
    pass


class SolverException(Exception):
    """Invalid Input

    This Exception indicates an invalid or missing input.
    """
    pass


class LoadException(Exception):
    """Error Loading CabSys object

    This Exception indicates a problem loading a CabSys object.
    """
    pass


class IEC60287Exception(Exception):
    """Error during IEC 60287 calculation

    This Exception indicates an error during an IEC 60287 calculation.
    """
    pass


class IEC60853Exception(Exception):
    """Error during IEC 60287 calculation

    This Exception indicates an error during an IEC 60287 calculation.
    """
    pass