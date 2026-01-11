import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from fpdf import FPDF

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

# Stop app if GEMINI_API_KEY is missing
if not API_KEY:
    st.error("GEMINI_API_KEY missing from .env file. Add it and restart.")
    st.stop()

genai.configure(api_key = API_KEY )

st.set_page_config(
	page_title = "NOTEZA AI",
	page_icon = "📚"
)

# Main Code
st.title("NOTEZA AI")

PROMPT_TEMPLATE = """

You are an assistant who creates exam-oriented study notes.
Generate well-structured, comprehensive notes on topic: **{TOPIC}**

Use this format:
Use Markdown headings (##, ###) for sections and subsections.
Define {TOPIC} first (1-2 lines)
Use bullet points for key ideas/definitions
Give 1-2 examples per major concept.
**Bold** technical terms
[KEEP SENTENCES SHORT AND CLEAR, NO UNNECESSARY STORYTELLING]
[ADAPT TO "{DETAIL_LEVEL}": **Brief**=fragments only, max 10 words per bullet, make the entire output under 150 words, Detailed=Use full sentences. Explain the "why" and "how" of each concept.]
[DONT USE EMOJIS]

"""
# Initialize history in session_state

if 'notes' not in st.session_state:
	st.session_state.notes = []
if 'selected_note' not in st.session_state:
	st.session_state.selected_note = None

with st.sidebar:
	# Display History
	st.header("History")
	for i, note in enumerate(st.session_state.notes[-8:][::-1]):
		if st.button(f"📖 {note['topic']} ({note['level']})", key = f"note_{len(st.session_state.notes) - i}"):
			st.session_state.selected_note = note['text']

	# Clear Button
	if st.button("🗑️ Clear All", key = "delete_history"):
		st.session_state.notes = []
		st.session_state.selected_note = None
		st.rerun() 		 # Refresh the app to reflect changes


# Function to generate PDF
def generate_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.multi_cell(0, 6, text)
    return bytes(pdf.output(dest='S'))

# Display Download Buttons
def show_download_buttons(text, topic_name):
    """Display MD and PDF download buttons for notes"""
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download as MD",
            data=text,
            file_name=f"{topic_name} notes.md",
            mime="text/markdown"
        )
    with col2:
        pdf_bytes = generate_pdf(text)
        st.download_button(
            label="📄 Download as PDF",
            data=pdf_bytes,
            file_name=f"{topic_name} notes.pdf",
            mime="application/pdf"
        )

if st.session_state.selected_note:
	st.markdown(st.session_state.selected_note)
	
	match_note = None 		# Find note that matches currently selected note
	for note in st.session_state.notes:
		if note['text'] == st.session_state.selected_note:
			match_note = note
			break
			
	if match_note:
		topic_name = match_note['topic']
		show_download_buttons(st.session_state.selected_note, match_note['topic'])
	else:
		st.warning("Note metadata not found.")
    	
	st.divider()
	if st.button("✨ Generate New Notes", key="generate_new"):
		st.session_state.selected_note = None
		st.rerun() 		 # Refresh the app to reflect changes


else:
	# Show input form if no note is selected
	topic = st.text_input("What's on your mind today?")
	detail_level = st.selectbox("Detail level:", ["Brief", "Detailed"])
	button = st.button("✨ Generate")

	if button and topic.strip() == "":
		st.warning("Please Enter a topic")
	elif button and topic.strip():
		with st.spinner("Generating your notes......"):

			# Fill prompt template with user topic and detail level
			prompt = PROMPT_TEMPLATE.format(TOPIC =  topic, DETAIL_LEVEL = detail_level)      
			model = genai.GenerativeModel("gemini-2.5-flash")
			response = model.generate_content(prompt)

			st.session_state.notes.append({
				"topic" : topic,
				"level" : detail_level,
				"text" : response.text
			})
			st.session_state.selected_note = response.text
			st.rerun()   # Refresh the app to reflect changes