from app.models.people import Person


class PeopleService:
    """
    Service to handle operations on people data
    """

    def __init__(self):
        # temporary stub
        pass

    def create_person(self, person_data: Person):
        """
        Create a person in the graph database from a Pydantic Person object
        :param person_data: Pydantic Person object
        :return:
        """
