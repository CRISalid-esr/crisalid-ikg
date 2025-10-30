from app.models.book import ScholarlyPublication


class Presentation(ScholarlyPublication):
    """
    Presentation model
    """
    type: str = "Presentation"
