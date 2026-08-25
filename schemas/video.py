from pydantic import BaseModel, HttpUrl, Field

class video_link(BaseModel):
    url : HttpUrl = Field("Url is required.")


class query(BaseModel):
    query : str = Field("query is required.")