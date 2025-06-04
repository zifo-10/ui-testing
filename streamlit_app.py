import streamlit as st
import pandas as pd
import asyncio
from typing import List, Optional
import json
from io import StringIO

# Import your existing services
from app.service.course_service import generate_quiz, get_paragraph, simplify_paragraph_v1

# Pydantic models (you'll need to import these from your existing code)
from app.models.processing_models import QuizResults
from app.schema.video_schema import VideoRequestSchema, MetaDataSchema


def main():
    st.set_page_config(page_title="Video Processing App", layout="wide")

    st.title("📝 Video Script Processing & Quiz Generation")
    st.markdown("Process video scripts to generate paragraphs, simplifications, and quizzes")

    # Initialize session state
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = []
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False

    # Sidebar for input
    with st.sidebar:
        st.header("📝 Input Configuration")

        # Video script input
        video_script = st.text_area(
            "Video Script",
            placeholder="Enter the video script text here...",
            height=200,
            help="Paste the video script/transcript content"
        )

        # Language selection
        language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Other"])
        if language == "Other":
            language = st.text_input("Custom Language", placeholder="Enter language")

        # Objectives section
        st.subheader("🎯 Objectives")
        objectives = []

        # Dynamic objectives input
        if 'num_objectives' not in st.session_state:
            st.session_state.num_objectives = 1

        for i in range(st.session_state.num_objectives):
            obj_name = st.text_input(f"Objective {i + 1}", key=f"obj_{i}", placeholder="Enter objective name")
            if obj_name:
                objectives.append(MetaDataSchema(name=obj_name))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Objective"):
                st.session_state.num_objectives += 1
                st.rerun()
        with col2:
            if st.button("➖ Remove Objective") and st.session_state.num_objectives > 1:
                st.session_state.num_objectives -= 1
                st.rerun()

        # Skills section
        st.subheader("🔧 Skills")
        skills = []

        # Dynamic skills input
        if 'num_skills' not in st.session_state:
            st.session_state.num_skills = 1

        for i in range(st.session_state.num_skills):
            skill_name = st.text_input(f"Skill {i + 1}", key=f"skill_{i}", placeholder="Enter skill name")
            if skill_name:
                skills.append(MetaDataSchema(name=skill_name))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Skill"):
                st.session_state.num_skills += 1
                st.rerun()
        with col2:
            if st.button("➖ Remove Skill") and st.session_state.num_skills > 1:
                st.session_state.num_skills -= 1
                st.rerun()

        # Process button
        st.markdown("---")
        process_button = st.button("🚀 Process Script", type="primary", use_container_width=True)

    # Main content area
    if process_button and video_script:
        if not objectives or not skills:
            st.error("Please add at least one objective and one skill.")
            return

        if not video_script.strip():
            st.error("Please enter the video script content.")
            return

        # Create request schema
        request_data = VideoRequestSchema(
            video=video_script,
            objective=objectives,
            skills=skills,
            language=language
        )

        # Process video script
        with st.spinner("Processing video script... This may take a few minutes."):
            try:
                # Run async functions
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                # Generate paragraph
                paragraph_list = loop.run_until_complete(get_paragraph(request_data))
                st.success("✅ Paragraphs generated")

                # Simplify paragraphs
                simplify_results = loop.run_until_complete(simplify_paragraph_v1(paragraph_list))
                st.success("✅ Paragraphs simplified")

                # Generate quiz
                quiz_results = loop.run_until_complete(generate_quiz(simplify_results))
                st.success("✅ Quiz generated")

                # Store results in session state
                st.session_state.quiz_results = quiz_results
                st.session_state.processing_complete = True

                st.success("🎉 Processing completed successfully!")

            except Exception as e:
                st.error(f"Error processing video script: {str(e)}")
                return

            # Display and edit results
    if st.session_state.processing_complete and st.session_state.quiz_results:
        st.markdown("---")
        st.header("📊 Results - Edit Content & Questions")

        # Tabs for different sections
        tab1, tab2 = st.tabs(["📚 Content Blocks with Questions", "💾 Download"])

        with tab1:
            st.subheader("Content Blocks with Questions")
            st.markdown("Each content block contains the paragraph, simplifications, and all related quiz questions.")

            for i, result in enumerate(st.session_state.quiz_results):
                with st.expander(f"📖 Content Block {i + 1} - {len(result.quiz)} Questions", expanded=True):
                    # Content and Simplifications Section
                    st.markdown("### 📝 Content & Simplifications")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Original paragraph
                        new_paragraph = st.text_area(
                            "Original Paragraph",
                            value=result.paragraph,
                            key=f"paragraph_{i}",
                            height=120
                        )
                        result.paragraph = new_paragraph

                        # Basic explanation
                        new_simplify1 = st.text_area(
                            "Basic Explanation",
                            value=result.simplify1,
                            key=f"simplify1_{i}",
                            height=120
                        )
                        result.simplify1 = new_simplify1

                    with col2:
                        # More simplified
                        new_simplify2 = st.text_area(
                            "More Simplified",
                            value=result.simplify2,
                            key=f"simplify2_{i}",
                            height=120
                        )
                        result.simplify2 = new_simplify2

                        # Child-friendly
                        new_simplify3 = st.text_area(
                            "Child-Friendly",
                            value=result.simplify3,
                            key=f"simplify3_{i}",
                            height=120
                        )
                        result.simplify3 = new_simplify3

                    # Meta information
                    st.markdown("### 📋 Meta Information")
                    meta_col1, meta_col2, meta_col3 = st.columns(3)

                    with meta_col1:
                        st.info(f"**Language:** {result.language}")
                        st.info(f"**Level:** {result.paragraph_level.name}")

                    with meta_col2:
                        objectives_text = ", ".join([obj.name for obj in result.objective])
                        st.info(f"**Objectives:** {objectives_text}")

                    with meta_col3:
                        skills_text = ", ".join([skill.name for skill in result.skills])
                        st.info(f"**Skills:** {skills_text}")

                    # Quiz Questions Section
                    st.markdown("### 🧩 Quiz Questions")

                    for j, quiz in enumerate(result.quiz):
                        st.markdown(f"#### Question {j + 1} of {len(result.quiz)}")

                        # Question content in columns
                        q_col1, q_col2 = st.columns([3, 2])

                        with q_col1:
                            # Question text
                            new_question = st.text_area(
                                "Question Text",
                                value=quiz.question,
                                key=f"question_{i}_{j}",
                                height=80
                            )
                            quiz.question = new_question

                            # Answer options
                            st.write("**Answer Options:**")
                            new_options = []

                            if not quiz.options:
                                quiz.options = ["Option 1", "Option 2", "Option 3", "Option 4"]

                            for k, option in enumerate(quiz.options):
                                new_option = st.text_input(
                                    f"Option {k + 1}",
                                    value=option,
                                    key=f"option_{i}_{j}_{k}"
                                )
                                new_options.append(new_option)
                            quiz.options = new_options

                            # Correct answer
                            new_correct_answer = st.text_input(
                                "Correct Answer",
                                value=quiz.correct_answer,
                                key=f"correct_{i}_{j}"
                            )
                            quiz.correct_answer = new_correct_answer

                        with q_col2:
                            # Question metadata
                            type_index = 0 if quiz.question_type == "multiple_choice" else 1
                            new_question_type = st.selectbox(
                                "Question Type",
                                ["multiple_choice", "true_false"],
                                index=type_index,
                                key=f"qtype_{i}_{j}"
                            )
                            quiz.question_type = new_question_type

                            level_index = int(quiz.question_level) - 1 if quiz.question_level.isdigit() else 0
                            new_question_level = st.selectbox(
                                "Question Level (1-6)",
                                ["1", "2", "3", "4", "5", "6"],
                                index=level_index,
                                key=f"qlevel_{i}_{j}"
                            )
                            quiz.question_level = new_question_level

                            new_post_assessment = st.checkbox(
                                "Post Assessment",
                                value=quiz.post_assessment,
                                key=f"post_assess_{i}_{j}"
                            )
                            quiz.post_assessment = new_post_assessment

                            # Display related skills and objectives
                            if quiz.related_skills:
                                related_skills = ", ".join([skill.name for skill in quiz.related_skills])
                                st.caption(f"**Related Skills:** {related_skills}")

                            if quiz.related_objectives:
                                related_objectives = ", ".join([obj.name for obj in quiz.related_objectives])
                                st.caption(f"**Related Objectives:** {related_objectives}")

                        # Add separator between questions
                        if j < len(result.quiz) - 1:
                            st.markdown("---")

                    # Add separator between content blocks
                    if i < len(st.session_state.quiz_results) - 1:
                        st.markdown("---")
                        st.markdown("---")

        with tab2:
            st.subheader("Download Results")

            # Prepare data for CSV
            csv_data = []

            for i, result in enumerate(st.session_state.quiz_results):
                # Add content data
                base_row = {
                    'content_block': i + 1,
                    'original_paragraph': result.paragraph,
                    'basic_explanation': result.simplify1,
                    'more_simplified': result.simplify2,
                    'child_friendly': result.simplify3,
                    'language': result.language,
                    'objectives': '; '.join([obj.name for obj in result.objective]),
                    'skills': '; '.join([skill.name for skill in result.skills]),
                    'paragraph_level': result.paragraph_level.name
                }

                # Add quiz data
                for j, quiz in enumerate(result.quiz):
                    quiz_row = base_row.copy()
                    quiz_row.update({
                        'question_number': j + 1,
                        'question': quiz.question,
                        'question_type': quiz.question_type,
                        'post_assessment': quiz.post_assessment,
                        'question_level': quiz.question_level,
                        'options': '; '.join(quiz.options),
                        'correct_answer': quiz.correct_answer,
                        'related_skills': '; '.join([skill.name for skill in quiz.related_skills]),
                        'related_objectives': '; '.join([obj.name for obj in quiz.related_objectives])
                    })
                    csv_data.append(quiz_row)

            # Create DataFrame
            df = pd.DataFrame(csv_data)

            # Display preview
            st.write("**Preview of CSV data:**")
            st.dataframe(df.head(10), use_container_width=True)

            # Download button
            csv_string = df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_string,
                file_name="video_processing_results.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )

            # Also provide JSON download option
            json_data = []
            for result in st.session_state.quiz_results:
                json_data.append(result.dict())

            json_string = json.dumps(json_data, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_string,
                file_name="video_processing_results.json",
                mime="application/json",
                use_container_width=True
            )


if __name__ == "__main__":
    main()