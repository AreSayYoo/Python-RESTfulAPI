import warnings
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, BeforeValidator, EmailStr

warnings.filterwarnings(
    "ignore",
    message=
    "Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
    category=UserWarning,
)

app = FastAPI()


def validate_name(name: str) -> str:
    """Return name to ensure it contains only alphabetic characters.

    Args:
        name (str): The name to validate.

    Returns:
        str: The validated name.

    Raises:
        HTTPException: If the name contains non-alphabetic characters.

    """
    # strip spaces
    name = name.strip()
    if not name.isalpha():
        raise HTTPException(
            status_code=422,
            detail="Name must contain only alphabetic characters",
        )
    return name


ValidatedName = Annotated[str, BeforeValidator(validate_name)]


class Person(BaseModel):
    """Represents a person in the system.
    
    Attributes:
        id (int): The unique identifier for the person.
        firstname (ValidatedName): The first name of the person.
        lastname (ValidatedName): The last name of the person.
        email (EmailStr | None): The email address of the person.
        favorite_anime (str | None): The person's favorite anime.

    """

    id: int
    firstname: ValidatedName
    lastname: ValidatedName
    email: EmailStr | None
    favorite_anime: str | None = None
    model_config = {"validate_assignment": True}


_people = [
    Person(id=0, firstname="John", lastname="Doe", email="matt@aresayoo.com"),
    Person(id=1, firstname="Matt", lastname="A", email=None),
    Person(id=2, firstname="Joe", lastname="Blow", email=None),
]
_free_ids: set[int] = set()


def get_next_id() -> int:
    """Return the next available ID for a new person.
    
    Returns:
        int: The next available ID.

    """
    if _free_ids:
        return min(_free_ids)
    if _people:
        return max(person.id for person in _people) + 1
    return 0


@app.get("/")
def read_root() -> dict[str, str]:
    """Root endpoint to verify the API is live.
    
    Returns:
        dict[str, str]: A message indicating the API is running.
    
    """
    return {"message": "RESTfulAPI is running!"}


@app.get("/api/v1/people", response_model=list[Person])
def get_people(
    favorite_anime: str | None = None,
    has_email: bool | None = Query(default=None),
    has_favorite_anime: bool | None = Query(default=None),
) -> list[Person]:
    """Return a list of people, optionally filtered by query parameters.
    
    Args:
        favorite_anime (str | None): Filter by favorite anime.
        has_email (bool | None): Filter by presence of email.
        has_favorite_anime (bool | None): Filter by presence of favorite anime.

    Returns:
        list[Person]: A list of people matching the filters (if any)

    """
    people = _people

    filters = {
        "favorite_anime": favorite_anime,
    }

    for field, value in filters.items():
        if value:
            # if we are filtering and remove case-sensitive check
            people = [
                p
                for p in people
                if getattr(p, field, None)
                and value.lower() == getattr(p, field).lower()
            ]

    if has_email is True:
        people = [p for p in people if p.email]
    elif has_email is False:
        people = [p for p in people if not p.email]
    if has_favorite_anime is True:
        people = [p for p in people if p.favorite_anime]
    elif has_favorite_anime is False:
        people = [p for p in people if not p.favorite_anime]

    return people


@app.get("/api/v1/people/{person_id}", response_model=Person)
def get_person(person_id: int) -> Person:
    """Return a person by their ID.
    
    Args:
        person_id (int): The ID of the person to retrieve.

    Returns:
        Person: The person with the specified ID.

    Raises:
        HTTPException: If the person is not found.
        
    """
    for person in _people:
        if person.id == person_id:
            return person
    raise HTTPException(status_code=404, detail="Person not found")


@app.post("/api/v1/people", response_model=Person, status_code=201)
def create_person(
    firstname: str,
    lastname: str,
    email: str | None = None,
    favorite_anime: str | None = None,
) -> Person:
    """Create a new person and add them to the system.
    
    Args:
        firstname (str): The first name of the person.
        lastname (str): The last name of the person.
        email (str | None): The email address of the person.
        favorite_anime (str | None): The person's favorite anime.
    
    Returns:
        Person: The newly created person.

    """
    new_person = Person(
        id=get_next_id(),
        firstname=firstname,
        lastname=lastname,
        email=email,
        favorite_anime=favorite_anime,
    )
    _people.append(new_person)
    return new_person


@app.put("/api/v1/people/{person_id}", response_model=Person)
def update_person(
    person_id: int,
    firstname: str | None = None,
    lastname: str | None = None,
    email: str | None = None,
    favorite_anime: str | None = None,
) -> Person:
    """Update an existing person's details.
    
    Args:
        person_id (int): The ID of the person to update.
        firstname (str | None): The new first name of the person.
        lastname (str | None): The new last name of the person.
        email (str | None): The new email address of the person.
        favorite_anime (str | None): The new favorite anime of the person.
    
    Returns:
        Person: The updated person.

    Raises:
        HTTPException: If the person is not found.

    """
    for person in _people:
        if person.id == person_id:
            if firstname:
                person.firstname = firstname
            if lastname:
                person.lastname = lastname
            if email:
                person.email = email
            if favorite_anime:
                person.favorite_anime = favorite_anime
            return person
    raise HTTPException(status_code=404, detail="Person not found")


@app.delete("/api/v1/people/{person_id}", response_model=Person)
def delete_person(person_id: int) -> Person:
    """Delete a person from the system by their ID.
    
    Args:
        person_id (int): The ID of the person to delete.
    
    Returns:
        Person: The deleted person.

    Raises:
        HTTPException: If the person is not found.
    
    """
    for person in _people:
        if person.id == person_id:
            _people.remove(person)
            _free_ids.add(person.id)
            return person
    raise HTTPException(status_code=404, detail="Person not found")
