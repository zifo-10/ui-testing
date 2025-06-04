from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.llm_response_model import QuizMetaData
from app.schema.video_schema import MetaDataSchema


class ProcessedParagraph(BaseModel):
    objective: List[MetaDataSchema] = Field(..., description="Objective of the video")
    skills: List[MetaDataSchema] = Field(..., description="Skills related to the video")
    language: str = Field(..., description="Language of the video")
    paragraph: str = Field(..., description="Paragraph text")
    paragraph_level: MetaDataSchema = Field(..., description="Level of the paragraph")


class SimplifyResults(ProcessedParagraph):
    simplify1: str = Field(..., description="Basic explanation")
    simplify2: str = Field(..., description="More simplified explanation")
    simplify3: str = Field(..., description="Child-friendly explanation")


class QuizResults(SimplifyResults):
    quiz: List[QuizMetaData]


class TranslateP1Response(ProcessedParagraph):
    simplify1_id: str
    simplify1: str = Field(..., description="Basic explanation")
    simplify1_first_word: str = Field(..., description="First word of the simplification")
    simplify1_last_word: str = Field(..., description="Last word of the simplification")


class TranslateP2Response(BaseModel):
    simplify2_id: str
    simplify2: str = Field(..., description="More simplified explanation")
    simplify2_first_word: str = Field(..., description="First word of the simplification")
    simplify2_last_word: str = Field(..., description="Last word of the simplification")
    simplify3_id: str
    simplify3: str = Field(..., description="Child-friendly explanation")
    simplify3_first_word: str = Field(..., description="First word of the simplification")
    simplify3_last_word: str = Field(..., description="Last word of the simplification")
