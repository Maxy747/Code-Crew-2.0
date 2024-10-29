import os
import streamlit as st
import google.generativeai as gen_ai

# Load API key from environment variable for security
GOOGLE_API_KEY = "AIzaSyDI7pcFS0F1q9t37i5J0s16uKUejiwFCIo"

# Check if the API key is available
if not GOOGLE_API_KEY:
    st.error("Google API key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Set up Google Gemini-Pro AI model
gen_ai.configure(api_key=GOOGLE_API_KEY)
model = gen_ai.GenerativeModel('gemini-pro')

st.set_page_config(
    page_title="Chat with Gemini-Pro!",
    page_icon=":smile:",  # Favicon emoji
)

# Function to translate roles between Gemini-Pro and Streamlit terminology
def translate_role_for_streamlit(user_role):
    if user_role == "model":
        return "assistant"
    else:
        return user_role

# Initialize chat session in Streamlit if not already present
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Function to determine if the question is relevant to fitness or nutrition
def is_relevant_question(question):
    keywords = ["fitness", "exercise", "workout", "training", "nutrition", "diet", "meal", "calories", "protein","bulk","bicep","chest","back","triceps","leg","shoulder","abs","cut","weight loss","fat loss","Macronutrients", "Micronutrients", "Dietary restrictions", "Meal prep", "Portion control", "Glycemic index/load", "Thermic effect of food", "Body composition", "Rest and recovery", "Flexibility", "High-intensity interval training", "Resistance training", "Cardiovascular exercise", "Functional fitness", "Mindful eating", "Mind-body connection", "Nutrient timing", "Pre-workout nutrition", "Post-workout nutrition", "Sustainable lifestyle changes"]
    return any(keyword in question.lower() for keyword in keywords)

# Display the chatbot's title on the page
st.title("FitMate")

# Display the chat history
for message in st.session_state.chat_session.history:
    with st.chat_message(translate_role_for_streamlit(message.role)):
        st.markdown(message.parts[0].text)

# Input field for user's message
user_prompt = st.chat_input("Ask me about fitness or nutrition...")
if user_prompt:
    # Add user's message to chat and display it
    st.chat_message("user").markdown(user_prompt)

    # Check if the question is relevant
    if is_relevant_question(user_prompt):
        try:
            # Send user's message to Gemini-Pro and get the response
            gemini_response = st.session_state.chat_session.send_message(user_prompt)
            
            # Display Gemini-Pro's response
            with st.chat_message("assistant"):
                st.markdown(gemini_response.text)
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        # Respond with a standard message for irrelevant questions
        with st.chat_message("assistant"):
            st.markdown("I'm here to help with fitness and nutrition questions. Please ask me about those topics!")
