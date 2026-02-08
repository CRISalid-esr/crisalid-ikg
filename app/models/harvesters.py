from enum import Enum


class Harvester(str, Enum):
    """
    Enum for harvesters.
    """
    # pylint: disable=duplicate-code
    HAL = "hal"
    SCANR = "scanr"
    IDREF = "idref"
    OPENALEX = "openalex"
    SCOPUS = "scopus"
