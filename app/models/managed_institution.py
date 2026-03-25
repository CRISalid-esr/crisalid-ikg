"""
Internal institution model
"""
from app.models.institution import Institution

class ManagedInstitution(Institution):
    """
    Internal institution API model
    """
    external = False
