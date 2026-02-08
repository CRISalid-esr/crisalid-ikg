from enum import Enum


class Harvester(str, Enum):
    """
    Enum for harvesters.
    """
    HAL = "hal"
    SCANR = "scanr"
    IDREF = "idref"
    OPENALEX = "openalex"
    SCOPUS = "scopus"
