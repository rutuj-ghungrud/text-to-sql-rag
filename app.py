import os
import re
import sqlite3
from pathlib import Path

from google import genai
import streamlit as st
from dotenv import load_dotenv


st.set_page_config(page_title="Text to SQL")

PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "student.db"
ENV_PATH = PROJECT_DIR / ".env"

if ENV_PATH.exists():
    try:
        load_dotenv(dotenv_path=ENV_PATH, encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            with ENV_PATH.open(encoding="utf-16") as env_file:
                load_dotenv(stream=env_file)
        except UnicodeError as error:
            st.error(f"Could not read the .env file: {error}")
            st.stop()
else:
    load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY is missing. Add it to the .env file and restart the app.")
    st.stop()

client = genai.Client(api_key=api_key)

SQL_PROMPT = """
Convert the user's question into one SQLite SELECT query for this table:
students(Name, Class, Section, Marks)

Return only the SQL query, without Markdown fences or explanation.
Use the exact table and column names above. Do not generate statements that
change data.
"""


def get_gemini_response(question: str) -> str:
    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=[SQL_PROMPT, question],
    )
    if not response.text:
        raise ValueError("Gemini did not return a SQL query.")

    sql = response.text.strip()
    fenced_sql = re.fullmatch(r"```(?:sql)?\s*(.*?)\s*```", sql, re.IGNORECASE | re.DOTALL)
    if fenced_sql:
        sql = fenced_sql.group(1).strip()
    if not re.match(r"^(SELECT|WITH)\b", sql, re.IGNORECASE):
        raise ValueError("Gemini returned something other than a SELECT query.")
    return sql


def read_sql_query(sql: str) -> list[dict[str, object]]:
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"Database not found at {DATABASE_PATH}. Run sql.py once to create it."
        )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    allowed_actions = {
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    }
    if hasattr(sqlite3, "SQLITE_RECURSIVE"):
        allowed_actions.add(sqlite3.SQLITE_RECURSIVE)

    def authorize(action: int, _arg1: str | None, _arg2: str | None,
                  _database: str | None, _trigger: str | None) -> int:
        return (
            sqlite3.SQLITE_OK
            if action in allowed_actions
            else sqlite3.SQLITE_DENY
        )

    try:
        connection.set_authorizer(authorize)
        rows = connection.execute(sql).fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


st.title("Ask questions about student data")
with st.form("question_form"):
    question = st.text_input("Your question", key="input")
    submit = st.form_submit_button("Ask the question")

if submit:
    if not question.strip():
        st.warning("Enter a question first.")
    else:
        try:
            with st.spinner("Contacting Gemini and querying the student database..."):
                generated_sql = get_gemini_response(question.strip())
                results = read_sql_query(generated_sql)
            st.session_state["last_question"] = question.strip()
            st.session_state["last_sql"] = generated_sql
            st.session_state["last_results"] = results
        except (genai.errors.APIError, sqlite3.Error, ValueError, OSError) as error:
            st.session_state.pop("last_question", None)
            st.session_state.pop("last_sql", None)
            st.session_state.pop("last_results", None)
            st.error(f"Could not answer the question: {type(error).__name__}: {error}")

if "last_results" in st.session_state:
    st.subheader("Answer")
    st.caption(f"Question: {st.session_state['last_question']}")
    st.code(st.session_state["last_sql"], language="sql")
    if st.session_state["last_results"]:
        st.dataframe(st.session_state["last_results"], use_container_width=True)
    else:
        st.info("The query ran successfully but returned no rows.")
