from pydantic import BaseModel, Field
from typing import List, Optional


class Video(BaseModel):
    id: str
    name: str
    description: Optional[str] = Field(None, description="A brief description of the video content")


class Chapter(BaseModel):
    id: str
    name: str
    description: Optional[str] = Field(None, description="A summary of what the chapter covers")
    videos: List[Video]


class Course(BaseModel):
    id: str
    name: str
    description: str
    chapters: List[Chapter]


class CourseWrapper(BaseModel):
    course: Course
