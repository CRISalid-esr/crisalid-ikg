"""
External institution model
"""
from app.models.institution import Institution

class ExternalInstitution(Institution):
    """
    External institution API model
    """
    external = True
