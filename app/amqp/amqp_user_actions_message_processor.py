# file: app/amqp/amqp_user_actions_message_processor.py

from loguru import logger
from pydantic import ValidationError

from app.amqp.amqp_message_processor import AMQPMessageProcessor
from app.models.change import Change
from app.services.changes.change_service import ChangeService
from app.services.people.people_service import PeopleService


class AMQPUserActionsMessageProcessor(AMQPMessageProcessor):
    """
    Workers to process messages about user actions from AMQP interface
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.change_service = ChangeService()

    async def _process_message(self, key: str, payload: str):
        json_payload = await self._read_message_json(payload)
        logger.debug(f"Processing user action message: {json_payload}")

        self._check_keys(json_payload, {
            #"id": None,
            "actionType": None,
            "parameters": None,
            "path": None,
            "personUid": None,
            "targetType": None,
            "targetUid": None,
            "timestamp": None,
            "application": None,  # make sure 'clientApp' is present to build the UID
        })
        if await self._check_registration_need(json_payload):
            await self._process_registered_change(json_payload)
        else:
            await self._process_unregistered_change(json_payload)

    async def _check_registration_need(self, json_payload: str):
        if json_payload["actionType"] in ["ADD", "REMOVE", "UPDATE"]:
            if json_payload["targetType"] == "DOCUMENT":
                return True
        else:
            return False

    async def _process_registered_change(self, json_payload: str):
        try:
            change = Change.model_validate(json_payload)
        except ValidationError as e:
            raise ValueError(f"Failed to build Change object: {e}") from e
        # exceptions are handled in the base class
        await self.change_service.create_and_apply_change(change)

    async def _process_unregistered_change(self, json_payload: str):
        """
        Method handling different cases of unregistered changes
        """
        if json_payload["actionType"] == "FETCH":
            if json_payload["targetType"] != "HARVESTING":
                raise ValueError("Target type must be 'HARVESTING' for FETCH action type.")
            if not json_payload["targetUid"] or not isinstance(json_payload["targetUid"], str):
                raise ValueError("Target UID is required for "
                                 "FETCH action type and should be a string.")
            harvesters = json_payload.get("parameters", {}).get("platforms")
            if not isinstance(harvesters, list) or not harvesters:
                logger.error(
                    f"Invalid or empty harvesters in parameters: {json_payload.get('parameters')}")
                harvesters = None
            service = PeopleService()
            await service.signal_publications_to_be_updated(json_payload["targetUid"],
                                                            harvesters=harvesters)
            logger.debug(f"Publications fetched for person {json_payload['targetUid']}.")
            return

        if json_payload["actionType"] == "ADD":
            if json_payload["targetType"] != "PERSON":
                raise ValueError("Target type must be 'PERSON' for unregistered ADD action type.")
            if not json_payload["targetUid"] or not isinstance(json_payload["targetUid"], str):
                raise ValueError("Target UID is required for person-related"
                                 "ADD action type and should be a string.")

            received_orcid = None
            received_identifier = json_payload.get("parameters", {}).get("identifiers", {})
            if received_identifier.get("type", "") == "ORCID":
                received_orcid = received_identifier.get("value")


            service = PeopleService()
            person = await service.get_person(json_payload["targetUid"])
            existing_orcid = None
            authenticated_orcid = False

            for identifier in person.identifiers:
                if identifier.type.value == "orcid":
                    existing_orcid = identifier.value
                    if identifier.authenticated:
                        authenticated_orcid = True

            if existing_orcid != received_orcid:
                # return message of non-corresponding orcid to merge
                pass
            elif existing_orcid == received_orcid and authenticated_orcid:
                # return  of nothing to do ?
                pass

            # in other cases, update the person

            logger.debug(f"Identifier added for person {json_payload['targetUid']}.")
            return
