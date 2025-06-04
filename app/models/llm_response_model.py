import uuid
from typing import List, Literal

from pydantic import BaseModel, Field, model_validator

from app.schema.video_schema import MetaDataSchema


class ParagraphMetaData(BaseModel):
    paragraph: str = Field(..., description="Paragraph text")
    related_objectives: MetaDataSchema = Field(..., description="List of objectives related to the paragraph")
    related_skills: MetaDataSchema = Field(..., description="List of skills related to the paragraph")
    paragraph_level: MetaDataSchema = Field(..., description="Level of the paragraph")


class ParagraphResponse(BaseModel):
    paragraph: List[ParagraphMetaData] = Field(..., description="List of paragraphs in the video")


class SimplifyResponse(BaseModel):
    simplify1: str = Field(..., description="Basic explanation")
    simplify2: str = Field(..., description="More simplified explanation")
    simplify3: str = Field(..., description="Child-friendly explanation")


class AlternativeQuestion(BaseModel):
    question: str = Field(..., description="Alternative question")
    question_type: Literal['multiple_choice', 'true_false'] = Field(
        ...,
        description="Type of the alternative question: multiple_choice or true_false")
    post_assessment: bool = Field(..., description="Indicates if the question is a post-assessment")
    options: List[str] = Field(..., description="List of answer options [A, B, C, D] or [True, False]")
    correct_answer: str = Field(..., description="Correct answer")


class QuizMetaData(BaseModel):
    question: str = Field(..., description="Quiz question")
    question_type: Literal['multiple_choice', 'true_false'] = Field(
        ...,
        description="Type of the alternative question: multiple_choice or true_false")
    post_assessment: bool = Field(..., description="Indicates if the question is a post-assessment")
    question_level: str = Field(..., description="Quiz question level from 1 to 6")
    options: List[str] = Field(..., description="List of quiz responses")
    correct_answer: str = Field(..., description="Correct answer")
    related_skills: List[MetaDataSchema] = Field(..., description="List of skills related to the quiz")
    related_objectives: List[MetaDataSchema] = Field(..., description="List of objectives related to the quiz")
    alternative_questions: bool = Field(
        False, description="Indicates that if the question is an alternative question or not")


class QuizResponse(BaseModel):
    quiz: List[QuizMetaData] = Field(..., description="Generated quiz for the paragraph")
