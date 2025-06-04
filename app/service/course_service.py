import os
import uuid
import asyncio
import logging
from typing import List, Any, Coroutine

from dotenv import load_dotenv

from app.client.llm_client import OpenAITextProcessor
from app.client.vector_db import QdrantDBClient
from app.models.llm_response_model import QuizResponse
from app.models.processing_models import ProcessedParagraph, SimplifyResults, QuizResults
from app.schema.video_schema import VideoRequestSchema, MetaDataSchema

# Load environment variables
load_dotenv()

# Setup logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Initialize the LLM client
llm_client = OpenAITextProcessor(os.getenv(" "), model="gpt-4o", max_workers=5)
vectordb_client = QdrantDBClient(host=os.getenv("QDRANT_URL"), port=6333)


async def get_paragraph(video: VideoRequestSchema) -> List[ProcessedParagraph]:
    try:
        logger.info("Generating paragraphs from video...")
        response = await asyncio.to_thread(llm_client.get_paragraph,
                                           objective=video.objective,
                                           skills=video.skills,
                                           video=video.video)
        logger.info(f"Received {len(response.paragraph)} paragraphs.")

        paragraph_with_id = [
            ProcessedParagraph(
                paragraph=p.paragraph,
                paragraph_level=p.paragraph_level,
                objective=[p.related_objectives],
                skills=[p.related_skills],
                language=video.language,
            )
            for p in response.paragraph
        ]

        return paragraph_with_id
    except Exception as e:
        logger.exception("Error while generating paragraphs")
        raise e

def get_similar_skills(paragraph: str):
    try:
        embedding = llm_client.get_embed(paragraph)
        skills_result = vectordb_client.query(
            collection_name='skills_en',
            vector=embedding,
            limit=1
        )
        for item in skills_result:
            skill_name = item.payload.get('skill_en')
            skill_id = item.payload.get('skill_id')
            return MetaDataSchema(
                name=skill_name,
                id=skill_id,
            )
        return None
    except Exception as e:
        raise e

# def get_skills(paragraph_list: List[ProcessedParagraph]):
#     try:
#         paragraph_list_with_skills = []
#         for paragraph in paragraph_list:
#             paragraph = paragraph.model_dump()
#             skills = get_similar_skills(paragraph['paragraph'])
#             paragraph_with_skills = ProcessedParagraphWithSkills(
#                 video_id=paragraph['video_id'],
#                 paragraph=paragraph['paragraph'],
#                 paragraph_level=paragraph['paragraph_level'],
#                 start_word=paragraph['start_word'],
#                 end_word=paragraph['end_word'],
#                 paragraph_id=paragraph['paragraph_id'],
#                 objective=paragraph['objective'],
#                 skills=[skills],
#                 language=paragraph['language'],
#             )
#             paragraph_list_with_skills.append(paragraph_with_skills)
#         logger.info(f"Extracted skills for {len(paragraph_list_with_skills)} paragraphs.")
#         return paragraph_list_with_skills
#     except Exception as e:
#         logger.exception("Error while extracting skills")
#         raise e


async def simplify_paragraph_v1(paragraphs: List[ProcessedParagraph]) -> List[SimplifyResults]:
    logger.info("Starting paragraph simplification...")

    async def simplify_single(paragraph: ProcessedParagraph) -> SimplifyResults:
        try:
            result = await asyncio.to_thread(llm_client.simplify, paragraph=paragraph.paragraph,
                                                language=paragraph.language)
            return SimplifyResults(
                paragraph=paragraph.paragraph,
                paragraph_level=paragraph.paragraph_level,
                simplify1=result.simplify1,
                simplify2=result.simplify2,
                simplify3=result.simplify3,
                skills=paragraph.skills,
                objective=paragraph.objective,
                language=paragraph.language,
            )
        except Exception as e:
            raise e

    results = await asyncio.gather(*(simplify_single(p) for p in paragraphs))
    logger.info(f"Simplified {len(results)} paragraphs.")
    return results


async def generate_quiz(paragraphs: VideoRequestSchema) -> QuizResponse:
    logger.info("Starting quiz generation...")
    quiz = llm_client.generate_quiz(
        skills=paragraphs.skills,
        objective=paragraphs.objective,
        paragraph_content=paragraphs.video,
        language=paragraphs.language
    )
    return quiz
