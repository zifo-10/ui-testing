import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from openai import OpenAI
from openai.types.chat import ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam

from app.contant_manager import paragraph_generator, simplify_prompt, question_generation_prompt, paragraph_level, \
    EMBEDDING_MODEL, quiz_note, translate_quiz_prompt, translate_content, translate_video_metadata
from app.models.llm_response_model import ParagraphResponse, SimplifyResponse, QuizResponse
from app.models.processing_models import SimplifyResults, TranslateP1Response, TranslateP2Response
from app.models.translate_video_metadata import CourseWrapper, Chapter


class OpenAITextProcessor:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", max_workers: int = 5):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = OpenAI(api_key=self.api_key)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def get_embed(self, arabic_text: str):
        embed = self.client.embeddings.create(
            input=arabic_text,
            model=EMBEDDING_MODEL
        )

        return embed.data[0].embedding

    def get_paragraph(self, video: str, objective: list, skills: list) -> ParagraphResponse | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=paragraph_generator
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"##Script: {video}\n"
                                f"##Paragraph Level: {paragraph_level}\n"
                                f"##Objectives: {objective}\n"
                                f"##Skills: {skills}\n##\n"
                    )
                ],
                temperature=0,
                response_format=ParagraphResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def simplify(self, paragraph: str, language: str) -> SimplifyResponse | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=simplify_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"##Script: {paragraph}\n##\n##Answer in {language} language:\n##\n"
                    )
                ],
                temperature=0,
                response_format=SimplifyResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def generate_quiz(self, paragraph_content, skills: list, objective: list, language: str) -> QuizResponse:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=question_generation_prompt
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=f"{quiz_note}\n"
                                f"##Script: {paragraph_content}\n"
                                f"##Skills: {skills}\n##Objectives: {objective}\n##\n"
                                f"##Answer in {language} language:\n##\n"
                    )
                ],
                temperature=0,
                response_format=QuizResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_quiz(self, quiz, language: str) -> QuizResponse:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_quiz_prompt.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=quiz
                    )
                ],
                temperature=0,
                response_format=QuizResponse,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_content(self, video_data, language: str) -> SimplifyResults | None:
        try:
            p1_translate = {
                "video_id": video_data['video_id'],
                "objective": video_data['objective'],
                "language": language,
                "paragraph_id": video_data['paragraph_id'],
                "paragraph": video_data['paragraph'],
                "paragraph_level": video_data['paragraph_level'],
                "start_word": video_data['start_word'],
                "end_word": video_data['end_word'],
                "skills": video_data['skills'],
                "simplify1_id": video_data['simplify1_id'],
                "simplify1": video_data['simplify1'],
                "simplify1_first_word": video_data['simplify1_first_word'],
                "simplify1_last_word": video_data['simplify1_last_word']
            }
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_content.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(p1_translate)
                    )
                ],
                temperature=0,
                response_format=TranslateP1Response,
                timeout=600
            )

            # Extract the translated content from the response
            p1_translate_response = response.choices[0].message.parsed

            p2_translate = {
                "simplify2_id": video_data['simplify2_id'],
                "simplify2": video_data['simplify2'],
                "simplify2_first_word": video_data['simplify2_first_word'],
                "simplify2_last_word": video_data['simplify2_last_word'],
                "simplify3_id": video_data['simplify3_id'],
                "simplify3": video_data['simplify3'],
                "simplify3_first_word": video_data['simplify3_first_word'],
                "simplify3_last_word": video_data['simplify3_last_word']
            }
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_content.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(p2_translate)
                    )
                ],
                temperature=0,
                response_format=TranslateP2Response,
                timeout=600
            )
            p2_translate_response = response.choices[0].message.parsed
            return SimplifyResults(
                video_id=p1_translate_response.video_id,
                objective=p1_translate_response.objective,
                language=language,
                paragraph_id=p1_translate_response.paragraph_id,
                paragraph=p1_translate_response.paragraph,
                paragraph_level=p1_translate_response.paragraph_level,
                start_word=p1_translate_response.start_word,
                end_word=p1_translate_response.end_word,
                skills=p1_translate_response.skills,
                simplify1_id=p1_translate_response.simplify1_id,
                simplify1=p1_translate_response.simplify1,
                simplify1_first_word=p1_translate_response.simplify1_first_word,
                simplify1_last_word=p1_translate_response.simplify1_last_word,
                simplify2_id=p2_translate_response.simplify2_id,
                simplify2=p2_translate_response.simplify2,
                simplify2_first_word=p2_translate_response.simplify2_first_word,
                simplify2_last_word=p2_translate_response.simplify2_last_word,
                simplify3_id=p2_translate_response.simplify3_id,
                simplify3=p2_translate_response.simplify3,
                simplify3_first_word=p2_translate_response.simplify3_first_word,
                simplify3_last_word=p2_translate_response.simplify3_last_word
            )
        except Exception as e:
            raise e

    def translate_chapter_meta(self, chapter_data: Chapter, language: str) -> Chapter:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_video_metadata.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(chapter_data)
                    )
                ],
                temperature=0,
                response_format=Chapter,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e

    def translate_text(self, text: str, language: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"Translate the following text to {language}."},
                    {"role": "user", "content": text}
                ],
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise e

    def translate_video_meta(self, video_data, language: str) -> CourseWrapper | None:
        try:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    ChatCompletionSystemMessageParam(
                        role="system",
                        content=translate_video_metadata.replace("{language}", language)
                    ),
                    ChatCompletionUserMessageParam(
                        role="user",
                        content=str(video_data)
                    )
                ],
                temperature=0,
                response_format=CourseWrapper,
                timeout=600
            )
            return response.choices[0].message.parsed
        except Exception as e:
            raise e