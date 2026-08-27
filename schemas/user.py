from pydantic import BaseModel

class user_response(BaseModel):
    id : int
    name : str 
    email : str
    profile_link : str


class auth_token(BaseModel):
    token : str