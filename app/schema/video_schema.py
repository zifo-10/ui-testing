from typing import List, Optional

from pydantic import BaseModel, Field


class MetaDataSchema(BaseModel):
    name: str = Field(..., description="The name of the skill or objective")


class VideoRequestSchema(BaseModel):
    video: str = Field(..., description="Video URL or path to the video file")
    objective: List[MetaDataSchema] = Field(..., description="List of objectives associated with the video")
    skills: List[MetaDataSchema] = Field(..., description="List of skills associated with the video")
    language: Optional[str] = Field('English', description="Language of the video")
