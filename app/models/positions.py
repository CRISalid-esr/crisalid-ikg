# file: app/models/positions.py
from typing import Dict, ClassVar, Optional

from pydantic import BaseModel


class Position(BaseModel):
    """
    Position model with predefined HCERES position codes and labels.
    """
    code: Optional[str] = None
    title: Optional[str] = None

    # Hardcoded list of positions
    POSITION_CODES: ClassVar[Dict[str, str]] = {
        "PR": "Professeur",
        "DIR": "Directeur d'études",
        "Phys": "Physicien",
        "Astro": "Astronome",
        "PUPH": "Professeurs des universités-Praticiens hospitaliers",
        "PR_AutMin": "Professeur des établissements dépendant d'autres ministères",
        "ATER": "Attaché temporaire d'enseignement et de recherche",
        "MCF": "Maître de conférences",
        "Phys_adj": "Physicien adjoint",
        "Astro_adj": "Astronome adjoint",
        "MCUPH": "Maître de conférences des universités-Praticiens hospitaliers",
        "MC_AutMin": "Maître de conférences ou Maître assistant des établissements "
                     "dépendant d'autres ministères",
        "PREM": "Professeur émérite",
        "MCFEM": "Maître de conférences émérites",
        "CCA": "Chef de clinique assistant",
        "AHU": "Attaché hospitalier universitaire",
        "PHU": "Praticien hospitalier universitaire",
        "ECC": "Enseignant-chercheur contractuel (dont contrats LRU)",
        "PAST": "Enseignant-chercheur associé (MC, PR à temps partiel ou temps plein)",
        "Autre_EC": "Autre statut",
        "ChPJ": "Chaire de professeur junior",
        "DR": "Directeur de recherche  et assimilés",
        "CR": "Chargé de recherche  et assimilés",
        "CBIB": "Conservateur des bibliothèques",
        "CPAT": "Conservateur du patrimoine",
        "DREM": "Directeur de recherche émérite",
        "CJC": "Contrat jeune chercheur (CDD 3 / 5 ans,  ATIP-Avenir)",
        "C_contractuel": "Chercheur contractuel",
        "Post-doc": "Post-doctorant",
        "Invité": "Visiteur étranger : professeur invité et chercheur associé, "
                  "ayant séjourné au moins 3 mois au sein de l'unité",
        "Docteur": "Docteur en médecine, pharmacie, etc.",
        "Autre_Ch": "autre statut",
        "PRAG": "Professeur agrégé",
        "PCAP": "Professeur certifié",
        "IR": "Ingénieur de recherche ou assimilé",
        "IE": "Ingénieur d'études ou assimilé",
        "AI": "Assistant ingénieur ou assimilé",
        "TECH": "Technicien de recherche ou assimilé",
        "AJT": "Adjoints et agents techniques de recherche, adjoints et agents administratifs",
        "BIB": "Bibliothécaire d'état",
        "BIBAS": "Bibliothécaire assistant spécialisé",
        "ASBIB": "Assistant des bibliothèques",
        "MABIB": "Magasinier et magasinier principal des bibliothèques",
        "PH": "Praticien hospitalier",
        "AJH": "Adjoint administratif, technique, ouvrier, agent de service hospitaliers",
        "ASPM": "Aide-soignant, auxiliaire de puériculture, aide médico-psychologique",
        "SEC": "Secrétaire hospitalier",
        "TEC": "Technicien hospitalier",
        "INF": "Infirmier",
        "SF": "Sage-femme",
        "ARC": "Attaché de recherche clinique",
        "CS": "Cadre de santé",
        "Igh": "Ingénieur hospitalier",
        "CP": "Chef de projet (en milieu hospitalier)",
        "PATP": "Personnel associé à temps partiel",
        "CDD": "Contrat à durée déterminée (catégorie non précisée)",
        "CDDA": "Contrat à durée déterminée (catégorie A)",
        "CDDB": "Contrat à durée déterminée (catégorie B)",
        "CDDC": "Contrat à durée déterminée (catégorie C)",
        "Autre_AP": "Autre statut",
        "Stag": "Stagiaire BTS, M1 ou M2 présent au moins 3 mois dans l'unité",
    }

    @classmethod
    def from_code(cls, code: str) -> "Position":
        """Creates a Position object based on the code."""
        if code not in cls.POSITION_CODES:
            raise ValueError(f"Unknown position code: {code}")
        return cls(code=code, title=cls.POSITION_CODES[code])
