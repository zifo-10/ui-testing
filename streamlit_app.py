import streamlit as st
import pandas as pd
import asyncio
from typing import List, Dict, Any
import io
from datetime import datetime
from streamlit_tags import st_tags

# Import your actual schemas and service
from app.schema.video_schema import VideoRequestSchema, MetaDataSchema
from app.models.llm_response_model import QuizResponse
from app.service.course_service import generate_quiz
from app.contant_manager import question_generation_prompt

def convert_quiz_to_dataframe(quiz_response: QuizResponse) -> pd.DataFrame:
    data = []
    for i, quiz_item in enumerate(quiz_response.quiz):
        data.append({
            'Question_ID': i + 1,
            'Question': quiz_item.question,
            'Question_Type': quiz_item.question_type,
            'Post_Assessment': quiz_item.post_assessment,
            'Question_Level': quiz_item.question_level,
            'Options': ' | '.join(quiz_item.options),
            'Correct_Answer': quiz_item.correct_answer,
            'Related_Skills': ' | '.join([skill.name for skill in quiz_item.related_skills]),
            'Related_Objectives': ' | '.join([obj.name for obj in quiz_item.related_objectives]),
            'Alternative_Questions': quiz_item.alternative_questions
        })
    return pd.DataFrame(data)

def convert_dataframe_to_quiz(df: pd.DataFrame) -> List[Dict[str, Any]]:
    quiz_data = []
    for _, row in df.iterrows():
        quiz_data.append({
            'question': row['Question'],
            'question_type': row['Question_Type'],
            'post_assessment': row['Post_Assessment'],
            'question_level': str(row['Question_Level']),
            'options': row['Options'].split(' | ') if row['Options'] else [],
            'correct_answer': row['Correct_Answer'],
            'related_skills': row['Related_Skills'].split(' | ') if row['Related_Skills'] else [],
            'related_objectives': row['Related_Objectives'].split(' | ') if row['Related_Objectives'] else [],
            'alternative_questions': row['Alternative_Questions']
        })
    return quiz_data

def create_excel_download(df: pd.DataFrame) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Quiz_Data', index=False)
        worksheet = writer.sheets['Quiz_Data']
        for column in worksheet.columns:
            max_length = 0
            column_name = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            worksheet.column_dimensions[column_name].width = min(max_length + 2, 50)
    return output.getvalue()

def main():
    st.set_page_config(page_title="Quiz Generator", page_icon="📝", layout="wide")
    st.title("📝 Quiz Generator")
    st.markdown("Generate quizzes from video content, edit them, and download as Excel")

    if 'quiz_generated' not in st.session_state:
        st.session_state.quiz_generated = False
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    if 'edited_df' not in st.session_state:
        st.session_state.edited_df = None

    with st.sidebar:
        st.header("📋 Quiz Configuration")

        video_input = st.text_area(
            "Video URL or Content",
            placeholder="Enter video URL or describe the video content...",
            height=100
        )

        st.subheader("🛠 Skills")
        skills_input = st_tags(
            label='💡 Enter Skills:',
            text='Press Enter to add more',
            value=[],
            suggestions=["Critical Thinking", "Problem Solving", "Collaboration", "Communication"],
            maxtags=20,
            key='skills'
        )

        st.subheader("🎯 Objectives")
        objectives_input = st_tags(
            label='📌 Enter Objectives:',
            text='Press Enter to add more',
            value=[],
            suggestions=["Understand concepts", "Apply knowledge", "Evaluate solutions"],
            maxtags=20,
            key='objectives'
        )

        language = st.selectbox(
            "Language",
            ["English", "Spanish", "French", "German", "Italian", "Portuguese"],
            index=0
        )

        generate_button = st.button("🔄 Generate Quiz", type="primary", use_container_width=True)
        if st.button("📜 Show Prompt", use_container_width=True):
            st.code(question_generation_prompt, language="python")

    if generate_button and video_input and skills_input and objectives_input:
        skills = [MetaDataSchema(name=s.strip()) for s in skills_input if s.strip()]
        objectives = [MetaDataSchema(name=o.strip()) for o in objectives_input if o.strip()]
        request = VideoRequestSchema(video=video_input, skills=skills, objective=objectives, language=language)

        with st.spinner("🤖 Generating quiz..."):
            try:
                quiz_response = asyncio.run(generate_quiz(request))
                st.session_state.quiz_data = quiz_response
                st.session_state.quiz_generated = True
                st.success("✅ Quiz generated successfully!")
            except Exception as e:
                st.error(f"❌ Error generating quiz: {str(e)}")

    elif generate_button:
        st.warning("⚠️ Please fill in all required fields")

    if st.session_state.quiz_generated and st.session_state.quiz_data:
        st.header("📊 Generated Quiz")

        df = convert_quiz_to_dataframe(st.session_state.quiz_data)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Questions", len(df))
        col2.metric("Multiple Choice", len(df[df['Question_Type'] == 'multiple_choice']))
        col3.metric("True/False", len(df[df['Question_Type'] == 'true_false']))
        col4.metric("Post Assessment", len(df[df['Post_Assessment'] == True]))

        st.markdown("---")
        st.subheader("✏️ Edit Quiz Questions")

        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Question_ID": st.column_config.NumberColumn("ID", disabled=True),
                "Question": st.column_config.TextColumn("Question", width="large"),
                "Question_Type": st.column_config.SelectboxColumn("Type", options=["multiple_choice", "true_false"]),
                "Post_Assessment": st.column_config.CheckboxColumn("Post Assessment"),
                "Question_Level": st.column_config.SelectboxColumn("Level", options=["1", "2", "3", "4", "5", "6"]),
                "Options": st.column_config.TextColumn("Options (separated by |)", width="large"),
                "Correct_Answer": st.column_config.TextColumn("Correct Answer"),
                "Related_Skills": st.column_config.TextColumn("Skills (separated by |)", width="medium"),
                "Related_Objectives": st.column_config.TextColumn("Objectives (separated by |)", width="medium"),
                "Alternative_Questions": st.column_config.CheckboxColumn("Alternative")
            },
            key="quiz_editor"
        )

        st.session_state.edited_df = edited_df

        st.markdown("---")
        st.subheader("💾 Download Quiz")

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("📥 Download as Excel", type="primary", use_container_width=True):
                excel_data = create_excel_download(edited_df)
                filename = f"quiz_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                st.download_button(
                    label="📁 Click to Download Excel File",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        with col2:
            csv_data = edited_df.to_csv(index=False)
            filename = f"quiz_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            st.download_button(
                label="📄 Download as CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                use_container_width=True
            )

        with st.expander("👀 Preview Quiz Questions"):
            for _, row in edited_df.iterrows():
                st.markdown(f"**Question {int(row['Question_ID'])}:** {row['Question']}")
                st.markdown(f"*Type:* {row['Question_Type']} | *Level:* {row['Question_Level']} | *Post Assessment:* {row['Post_Assessment']}")
                if row['Options']:
                    st.markdown(f"*Options:* {row['Options']}")
                st.markdown(f"*Correct Answer:* {row['Correct_Answer']}")
                st.markdown("---")

    if not st.session_state.quiz_generated:
        st.markdown("""
        ## 🚀 How to Use

        1. **Enter Video Info**: Provide the video URL or content.
        2. **Add Skills/Objectives**: Use tags to define key skills and learning goals.
        3. **Select Language**: Choose quiz language.
        4. **Generate**: Let the assistant create quiz questions.
        5. **Edit**: Customize questions as needed.
        6. **Download**: Export as Excel or CSV.

        ### 📝 Tips
        - Use "|" to separate multiple options
        - Levels: 1 (Easy) to 6 (Advanced)
        - Post Assessment = final evaluation
        - "Alternative" marks optional question versions
        """)

if __name__ == "__main__":
    main()