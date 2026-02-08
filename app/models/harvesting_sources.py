from enum import Enum


class HarvestingSource(str, Enum):
    """
    Enum for harvesters.
    """
    HAL = "hal"
    SCANR = "scanr"
    IDREF = "idref"
    OPENALEX = "openalex"
    SCOPUS = "scopus"
    SUDOC = "sudoc"
    SCIENCEPLUS = "scienceplus"
    OPENEDITION = "openedition"
    PERSEE = "persee"
