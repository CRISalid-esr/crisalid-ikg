"""
Organization unit model hierarchy for research structures.
"""
from datetime import date
from typing import Optional, Union, Annotated
from typing import Literal as TypingLiteral

from pydantic import BaseModel, Field, model_validator, field_validator, TypeAdapter

from app.models.agent_identifiers import OrganizationIdentifier
from app.models.agents import Agent
from app.models.identifier_types import OrganizationIdentifierType
from app.models.literal import Literal
from app.models.organization_types import (
    GenericOrganizationType,
    MissionType,
    NationalOrganizationType,
    OrgMembershipPosition,
    ALLOWED_NATIONAL_TYPES_BY_GENERIC_TYPE,
)
from app.models.structured_physical_address import StructuredPhysicalAddress
from app.models.text_literal import TextLiteral


class ElectronicalAddress(BaseModel):
    uri: str


class OrgInclusion(BaseModel):
    """Reified PART_OF relationship (strong inclusion)."""
    target: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class OrgMembership(BaseModel):
    """Reified MEMBER_OF relationship (weak membership/supervision)."""
    target: str
    position: Optional[OrgMembershipPosition] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class OrganizationBase(Agent[OrganizationIdentifierType]):
    """
    Base class for all research organization structures.
    All concrete subtypes share the OrganizationUnit label in Neo4j.
    """
    uid: Optional[str] = None
    generic_type: GenericOrganizationType
    national_type: Optional[NationalOrganizationType] = None
    local_types: list[Literal] = Field(default_factory=list)
    short_labels: list[Literal] = Field(default_factory=list)
    long_labels: list[Literal] = Field(default_factory=list)
    descriptions: list[TextLiteral] = Field(default_factory=list)
    identifiers: list[OrganizationIdentifier] = Field(default_factory=list)
    addresses: list[StructuredPhysicalAddress] = Field(default_factory=list)
    electronical_addresses: list[ElectronicalAddress] = Field(default_factory=list)
    memberships: list[OrgMembership] = Field(default_factory=list)
    parents: list[OrgInclusion] = Field(default_factory=list)

    @model_validator(mode='before')
    @classmethod
    def _normalize_input(cls, data):
        if not isinstance(data, dict):
            return data

        # Rename 'type' → 'national_type' (incoming AMQP field name)
        if 'type' in data and 'national_type' not in data:
            data['national_type'] = data.pop('type')

        # Parse contacts → addresses + electronical_addresses
        contacts = data.pop('contacts', None) or []
        addresses = list(data.get('addresses') or [])
        electronical_addresses = list(data.get('electronical_addresses') or [])

        for contact in contacts:
            fmt = contact.get('format')
            value = contact.get('value') or {}
            if fmt == 'structured_physical_address':
                addr: dict = {}
                for field_name in ('street', 'city', 'zip_code', 'country', 'state_or_province'):
                    raw = value.get(field_name)
                    if raw:
                        addr[field_name] = [{'value': raw, 'language': 'und'}]
                if addr:
                    addresses.append(addr)
            elif fmt == 'website_address':
                uri = value.get('uri')
                if uri:
                    electronical_addresses.append({'uri': uri})

        data['addresses'] = addresses
        data['electronical_addresses'] = electronical_addresses

        # Parse relationships → memberships + parents
        relationships = data.pop('relationships', None) or []
        memberships = list(data.get('memberships') or [])
        parents = list(data.get('parents') or [])

        for rel in relationships:
            rel_type = rel.get('type')
            target = rel.get('target')
            start_date = rel.get('start_date')
            end_date = rel.get('end_date')
            subtype = rel.get('subtype')
            if not target:
                continue
            if rel_type == 'member_of':
                membership: dict = {
                    'target': target,
                    'start_date': start_date,
                    'end_date': end_date,
                }
                if subtype:
                    membership['position'] = subtype
                memberships.append(membership)
            elif rel_type == 'part_of':
                parents.append({
                    'target': target,
                    'start_date': start_date,
                    'end_date': end_date,
                })

        data['memberships'] = memberships
        data['parents'] = parents
        return data

    @model_validator(mode='after')
    def _validate_type_constraints(self):
        if not self.national_type and not self.local_types and not self.long_labels:
            raise ValueError(
                "Either national_type, at least one local_type, or at least one long_label is required"
            )
        if self.national_type is not None:
            allowed = ALLOWED_NATIONAL_TYPES_BY_GENERIC_TYPE.get(self.generic_type, set())
            if self.national_type not in allowed:
                raise ValueError(
                    f"national_type {self.national_type!r} is not allowed "
                    f"for generic_type {self.generic_type!r}"
                )
        return self

    @field_validator('identifiers', mode='after')
    @classmethod
    def _validate_identifiers(cls, identifiers):
        return cls._deduplicate_identifiers(identifiers)


# ── Non-unit concrete classes ──────────────────────────────────────────────────

class Institution(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.INSTITUTION] = (
        GenericOrganizationType.INSTITUTION
    )


class InstitutionSubdivision(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.INSTITUTION_SUBDIVISION] = (
        GenericOrganizationType.INSTITUTION_SUBDIVISION
    )


class UnitSubdivision(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.UNIT_SUBDIVISION] = (
        GenericOrganizationType.UNIT_SUBDIVISION
    )


class Team(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.TEAM] = (
        GenericOrganizationType.TEAM
    )


# ── Unit classes (discriminated by main_mission) ───────────────────────────────

class UnitBase(OrganizationBase):
    generic_type: TypingLiteral[GenericOrganizationType.UNIT] = (
        GenericOrganizationType.UNIT
    )
    main_mission: MissionType
    secondary_missions: list[MissionType] = Field(default_factory=list)


class ResearchUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.RESEARCH] = MissionType.RESEARCH


class SupportUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.SCIENTIFIC_SERVICES] = (
        MissionType.SCIENTIFIC_SERVICES
    )


class AdministrativeUnit(UnitBase):
    main_mission: TypingLiteral[MissionType.ADMINISTRATIVE_SERVICES] = (
        MissionType.ADMINISTRATIVE_SERVICES
    )


# ── Type aliases and adapters ──────────────────────────────────────────────────

Unit = Annotated[
    Union[ResearchUnit, SupportUnit, AdministrativeUnit],
    Field(discriminator='main_mission'),
]

NonUnitOrganizationUnit = Annotated[
    Union[Institution, InstitutionSubdivision, UnitSubdivision, Team],
    Field(discriminator='generic_type'),
]

OrganizationUnit = Union[NonUnitOrganizationUnit, Unit]

# Instantiate once to avoid repeated schema-building overhead
unitAdapter: TypeAdapter = TypeAdapter(Unit)
nonUnitAdapter: TypeAdapter = TypeAdapter(NonUnitOrganizationUnit)
