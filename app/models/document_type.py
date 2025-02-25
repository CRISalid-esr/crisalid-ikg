from enum import Enum

from loguru import logger
from pydantic import BaseModel

from app.utils.semantic_web.rdf_suffixes import RDF_SUFFIXES


class DocumentTypeEnum(str, Enum):
    """
    Enum for document types
    """
    ARTICLE = "Article"
    AUDIOVISUAL_DOCUMENT = "Audiovisual Document"
    BLOG_POST = "Blog Post"
    BOOK = "Book"
    BOOK_REVIEW = "Book Review"
    CHAPTER = "Chapter"
    CONFERENCE_OUTPUT = "Conference Output"
    CONFERENCE_PAPER = "Conference Paper"
    CONFERENCE_POSTER = "Conference Poster"
    DATA_MANAGEMENT_PLAN = "Data Management Plan"
    DATA_PAPER = "Data Paper"
    DATASET = "Dataset"
    DICTIONARY = "Reference Book"
    DOCUMENT = "Document"
    DRAWING = "Still Image"
    EDITORIAL = "Editorial"
    ERRATUM = "Erratum"
    GRANT = "Grant"
    GRAPHICS = "Still Image"
    IMAGE = "Image"
    ILLUSTRATION = "Still Image"
    LECTURE = "Lecture"
    LETTER = "Letter"
    MANUAL = "Manual"
    MAP = "Map"
    MASTER_THESIS = "Master Thesis"
    METADATA_DOCUMENT = "Metadata Document"
    NOTE = "Note"
    OTHER = "Other"
    PARATEXT = "Metadata Document"
    PATENT = "Patent"
    PEER_REVIEW = "Peer review"
    PHOTOGRAPHY = "Still Image"
    PREPRINT = "Preprint"
    PROCEEDINGS = "Proceedings"
    REFERENCE_ENTRY = "Document"
    REPORT = "Report"
    RESEARCH_REPORT = "Research Report"
    REVIEW = "Review Paper"
    REVIEW_ARTICLE = "Review Article"
    SOFTWARE = "Software"
    STANDARD = "Standard"
    STILL_IMAGE = "Still Image"
    TECHNICAL_REPORT = "Technical Report"
    THESIS = "Thesis"
    WORKING_PAPER = "Working Paper"
    UNKNOWN = "Unknown"

    @classmethod
    def from_uri(cls, uri: str):
        """
        Get the enum value from a vocabulary term URI
        :param uri: URI of the vocabulary term
        :return: Enum value
        """
        mapping = {
            f"{RDF_SUFFIXES['BIBO']}Article": cls.ARTICLE,
            f"{RDF_SUFFIXES['BIBO']}AudioVisualDocument": cls.AUDIOVISUAL_DOCUMENT,
            f"{RDF_SUFFIXES['COAR']}c_6947": cls.BLOG_POST,
            f"{RDF_SUFFIXES['BIBO']}Book": cls.BOOK,
            f"{RDF_SUFFIXES['SPAR']}BookReview": cls.BOOK_REVIEW,
            f"{RDF_SUFFIXES['BIBO']}Chapter": cls.CHAPTER,
            f"{RDF_SUFFIXES['COAR']}c_c94f": cls.CONFERENCE_OUTPUT,
            f"{RDF_SUFFIXES['SPAR']}ConferencePaper": cls.CONFERENCE_PAPER,
            f"{RDF_SUFFIXES['SPAR']}ConferencePoster": cls.CONFERENCE_POSTER,
            f"{RDF_SUFFIXES['SPAR']}DataMangementPlan": cls.DATA_MANAGEMENT_PLAN,
            f"{RDF_SUFFIXES['COAR']}c_beb9": cls.DATA_PAPER,
            f"{RDF_SUFFIXES['SPAR']}Dataset": cls.DATASET,
            f"{RDF_SUFFIXES['SPAR']}ReferenceBook": cls.DICTIONARY,
            f"{RDF_SUFFIXES['BIBO']}Document": cls.DOCUMENT,
            f"{RDF_SUFFIXES['SPAR']}StillImage": cls.STILL_IMAGE,
            f"{RDF_SUFFIXES['SPAR']}Editorial": cls.EDITORIAL,
            f"{RDF_SUFFIXES['SPAR']}Erratum": cls.ERRATUM,
            f"{RDF_SUFFIXES['CERIF']}Grant": cls.GRANT,
            f"{RDF_SUFFIXES['BIBO']}Image": cls.IMAGE,
            f"{RDF_SUFFIXES['BIBO']}Letter": cls.LETTER,
            f"{RDF_SUFFIXES['BIBO']}Manual": cls.MANUAL,
            f"{RDF_SUFFIXES['BIBO']}Map": cls.MAP,
            f"{RDF_SUFFIXES['COAR_VOC']}resource_types/c_bdcc/": cls.MASTER_THESIS,
            f"{RDF_SUFFIXES['SPAR']}MetadataDocument": cls.METADATA_DOCUMENT,
            f"{RDF_SUFFIXES['BIBO']}Note": cls.NOTE,
            f"{RDF_SUFFIXES['COAR']}c_1843": cls.OTHER,
            f"{RDF_SUFFIXES['COAR']}H9BQ-739P": cls.PEER_REVIEW,
            f"{RDF_SUFFIXES['SPAR']}Preprint": cls.PREPRINT,
            f"{RDF_SUFFIXES['BIBO']}Proceedings": cls.PROCEEDINGS,
            f"{RDF_SUFFIXES['SPAR']}Report": cls.REPORT,
            f"{RDF_SUFFIXES['COAR']}c_18ws": cls.RESEARCH_REPORT,
            f"{RDF_SUFFIXES['SPAR']}ReviewArticle": cls.REVIEW_ARTICLE,
            f"{RDF_SUFFIXES['SPAR']}ReviewPaper": cls.REVIEW,
            f"{RDF_SUFFIXES['COAR']}c_5ce6": cls.SOFTWARE,
            f"{RDF_SUFFIXES['BIBO']}Standard": cls.STANDARD,
            f"{RDF_SUFFIXES['BIBO']}Thesis": cls.THESIS,
            f"{RDF_SUFFIXES['SPAR']}TechnicalReport": cls.TECHNICAL_REPORT,
            f"{RDF_SUFFIXES['SPAR']}WorkingPaper": cls.WORKING_PAPER,
            f"{RDF_SUFFIXES['FRBR']}Work": cls.DOCUMENT,
            f"{RDF_SUFFIXES['RDA']}C10001": cls.DOCUMENT,
            "http://data.crisalid.org/ref/document_types/unknown": cls.UNKNOWN,
        }
        return mapping.get(uri, None)


class DocumentType(BaseModel):
    """
    Document Type model
    """
    uri: str
    label: str

    def to_enum(self) -> DocumentTypeEnum:
        """
        Get the enum value from the URI

        :return: the enum value
        """
        enum_value = DocumentTypeEnum.from_uri(self.uri)
        if not enum_value:
            logger.error(f"Unsupported document type URI: {self.uri}")
            return DocumentTypeEnum.UNKNOWN
        return enum_value
