from pydantic import BaseModel, HttpUrl

class user_response(BaseModel):
    id : int
    name : str 
    email : str
    profile_link : str