from app.models.scholarly_publication import ScholarlyPublication


class Article(ScholarlyPublication):
    """
    Article model
    """
    type: str = "Article"
