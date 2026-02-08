from enum import Enum


class HarvestingSource(str, Enum):
    """
    Enum for harvesting sources. Harvesting sources are not the same as harvester, as
    a harvester (e.g. IdRef) can harvest secondary sources (e.g. HAL, OpenAlex, etc.).
    For sources models, sources identifiers are unique only at the source level
    """
    # pylint: disable=duplicate-code
    HAL = "hal"
    SCANR = "scanr"
    IDREF = "idref"
    OPENALEX = "openalex"
    SCOPUS = "scopus"
    SUDOC = "sudoc"
    SCIENCEPLUS = "scienceplus"
    OPENEDITION = "openedition"
    PERSEE = "persee"
