from typing import List, Any, Coroutine

from fastapi import FastAPI, HTTPException

from app.models.llm_response_model import QuizResponse
from app.models.processing_models import QuizResults
from app.models.translate_video_metadata import CourseWrapper
from app.schema.video_schema import VideoRequestSchema
from app.service.course_service import generate_quiz, get_paragraph, simplify_paragraph_v1
from app.service.translate_service import translate_video, translate_course_meta_data

app = FastAPI(root_path="/aicourseprocessing")


# List[QuizResults]

@app.post("/process_video")
async def process_video(process_video_request: VideoRequestSchema) -> QuizResponse:
    try:
        quiz = await generate_quiz(process_video_request)
        return quiz
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate_video/{language}")
async def translate_script(process_video_request: List[QuizResults], language: str) -> List[QuizResults]:
    try:
        paragraph_list = await translate_video(process_video_request, language)
        return paragraph_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate_course_meta/{language}")
async def translate_course_meta(process_video_request: CourseWrapper, language: str) -> CourseWrapper:
    try:
        paragraph_list = await translate_course_meta_data(process_video_request, language)
        return paragraph_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
