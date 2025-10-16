import warnings

warnings.filterwarnings(
    "ignore",
    message="Core Pydantic V1 functionality isn't compatible with Python 3.14 or greater.",
    category=UserWarning,
)

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, AfterValidator, BeforeValidator, Field, EmailStr
from typing import Annotated

app = FastAPI()

def validate_name(name: str, info):
    # strip spaces
    name = name.strip()
    if not name.isalpha():
        raise HTTPException(status_code=422, detail="Name must contain only alphabetic characters")
    return name

ValidatedName = Annotated[str, BeforeValidator(validate_name)]

class Person(BaseModel):
    id: int
    firstname: ValidatedName
    lastname: ValidatedName
    email: EmailStr | None 
    favorite_anime: str | None = None
    model_config = {"validate_assignment": True}

_people = [
    Person(id=0, firstname="John", lastname="Doe", email="matt@aresayoo.com"),
    Person(id=1, firstname="Matt", lastname="A", email=None),
    Person(id=2, firstname="Joe", lastname="Blow", email=None)
]
_free_ids: set[int] = set()

def get_next_id() -> int:
    if _free_ids:
        return min(_free_ids)
    elif _people:
        return max(person.id for person in _people) + 1
    return 0

@app.get("/")
def read_root():
    return {"message": "RESTfulAPI is running!"}

@app.get("/api/v1/people",response_model=list[Person])
def get_people():
    return _people

@app.get("/api/v1/people/{person_id}",response_model=Person)
def get_person(person_id: int):
    for person in _people:
        if person.id == person_id:
            return person
    raise HTTPException(status_code=404, detail="Person not found")

@app.post("/api/v1/people",response_model=Person,status_code=201)
def create_person(firstname: str, lastname: str, email: str = None, favorite_anime: str = None):
    new_person = Person(id = get_next_id(), firstname=firstname, lastname=lastname, email=email, favorite_anime=favorite_anime)
    _people.append(new_person)
    return new_person

@app.put("/api/v1/people/{person_id}",response_model=Person)
def update_person(person_id: int, firstname: str = None, lastname: str = None, email: str = None, favorite_anime: str = None):
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

@app.delete("/api/v1/people/{person_id}")
def delete_person(person_id: int):
    for person in _people:
        if person.id == person_id:
            _people.remove(person)
            _free_ids.add(person.id)
            return person
    raise HTTPException(status_code=404, detail="Person not found")
