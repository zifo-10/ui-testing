import asyncio
from typing import List
from app.models.processing_models import QuizResults
from app.models.translate_video_metadata import CourseWrapper, Course
from app.service.course_service import llm_client


async def translate_video(video: List[QuizResults], language: str) -> List[QuizResults]:
    """
    Translate the video content to a different language.
    """

    async def translate_single_item(video_item: QuizResults) -> QuizResults:
        try:
            # Run both synchronous translation calls in separate threads concurrently
            quiz_future = asyncio.to_thread(llm_client.translate_quiz, str(video_item.quiz), language)
            content_data = video_item.model_dump(exclude={'quiz'})
            content_future = asyncio.to_thread(llm_client.translate_content, content_data, language)

            translated_quiz, translated_content = await asyncio.gather(quiz_future, content_future)

            return QuizResults(
                video_id=video_item.video_id,
                objective=translated_content.objective,
                language=language,
                paragraph_id=video_item.paragraph_id,
                paragraph=translated_content.paragraph,
                paragraph_level=video_item.paragraph_level,
                start_word=translated_content.start_word,
                end_word=translated_content.end_word,
                skills=translated_content.skills,
                simplify1_id=video_item.simplify1_id,
                simplify1=translated_content.simplify1,
                simplify1_first_word=translated_content.simplify1_first_word,
                simplify1_last_word=translated_content.simplify1_last_word,
                simplify2_id=video_item.simplify2_id,
                simplify2=translated_content.simplify2,
                simplify2_first_word=translated_content.simplify2_first_word,
                simplify2_last_word=translated_content.simplify2_last_word,
                simplify3_id=video_item.simplify3_id,
                simplify3=translated_content.simplify3,
                simplify3_first_word=translated_content.simplify3_first_word,
                simplify3_last_word=translated_content.simplify3_last_word,
                quiz=translated_quiz.quiz
            )

        except Exception as e:
            raise e

    return await asyncio.gather(*(translate_single_item(item) for item in video))


async def translate_course_meta_data(process_video_request: CourseWrapper, language: str) -> CourseWrapper:
    original_course = process_video_request.course

    # Translate course name and description
    translated_name = llm_client.translate_text(original_course.name, language)
    translated_description = llm_client.translate_text(original_course.description, language)

    # Translate chapters
    translated_chapters = []
    for chapter in original_course.chapters:
        translated_chapter = llm_client.translate_chapter_meta(chapter, language)
        translated_chapters.append(translated_chapter)

    translated_course = Course(
        id=original_course.id,
        name=translated_name,
        description=translated_description,
        chapters=translated_chapters
    )

    return CourseWrapper(course=translated_course)

