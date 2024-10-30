import streamlit as st
import google.generativeai as genai
from datetime import datetime
import re

# Configure Gemini API
genai.configure(api_key='AIzaSyDsp-Q1M2CM548oSCoAAO_UCAaeM2dOdVI')  # Your API key here
model = genai.GenerativeModel('gemini-pro')

# Initialize session state
def init_session_state():
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {}
    if 'current_question_index' not in st.session_state:
        st.session_state.current_question_index = 0
    if 'questioning_mode' not in st.session_state:
        st.session_state.questioning_mode = False
    if 'memory' not in st.session_state:
        st.session_state.memory = {
            'name': None,
            'preferences': {},
            'context': []
        }

# Recipe questions and constants
RECIPE_QUESTIONS = [
    "What is your height in centimeters?",
    "What is your weight in kilograms?",
    "What is your age?",
    "What is your goal? (lose weight/gain weight/maintain weight)",
    "Do you prefer vegetarian, non-vegetarian, or both types of food?",
    "Do you have any dietary restrictions or allergies?",
    "What are your favorite foods or cuisines?",
    "How many meals do you prefer per day? (2-6)",
    "How much time can you spend on cooking per day?"
]

def calculate_bmi(height_cm, weight_kg):
    """Calculate BMI from height in cm and weight in kg"""
    try:
        height_m = float(height_cm) / 100
        weight = float(weight_kg)
        return round(weight / (height_m * height_m), 2)
    except (ValueError, ZeroDivisionError):
        return None

def check_diet_safety(height, weight, age, goal):
    """Check if the diet goal is safe based on BMI"""
    try:
        bmi = calculate_bmi(height, weight)
        if bmi is None:
            return False, "Unable to calculate BMI with provided measurements."
        
        if bmi >= 30 and goal.lower() == "gain weight":
            return False, "Based on your BMI, gaining weight might be unsafe. Consider a weight loss or maintenance plan instead."
        elif bmi < 18.5 and goal.lower() == "lose weight":
            return False, "Based on your BMI, losing weight might be unsafe. Consider a weight gain or maintenance plan instead."
        return True, "Your goal appears appropriate for your current health status."
    except Exception as e:
        return False, f"Unable to assess diet safety: {str(e)}"

def generate_meal_plan(user_info):
    """Generate a meal plan based on user information"""
    try:
        height = float(user_info.get('recipe_q_0', 0))
        weight = float(user_info.get('recipe_q_1', 0))
        age = float(user_info.get('recipe_q_2', 0))
        
        # Calculate BMR using Mifflin-St Jeor Equation
        bmr = (10 * weight) + (6.25 * height) - (5 * age)
        
        # Adjust for gender (defaulting to a middle ground if not specified)
        bmr = bmr - 78  # Average of male (+5) and female (-161) adjustments
        
        # Calculate daily calories with moderate activity factor
        daily_calories = bmr * 1.55
        
        # Adjust based on goal
        goal = user_info.get('recipe_q_3', '').lower()
        if goal == 'lose weight':
            daily_calories -= 500
        elif goal == 'gain weight':
            daily_calories += 500
            
        # Generate meal plan using Gemini
        prompt = f"""Create a 7-day meal plan for:
- Daily Calories: {int(daily_calories)}
- Diet Type: {user_info.get('recipe_q_4', 'No preference')}
- Restrictions: {user_info.get('recipe_q_5', 'None')}
- Favorite Foods: {user_info.get('recipe_q_6', 'No specific preferences')}
- Meals per day: {user_info.get('recipe_q_7', '3')}
- Cooking time: {user_info.get('recipe_q_8', '30 minutes')}"""
        
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating meal plan: {str(e)}"

def update_memory(user_input, bot_response):
    """Update conversation memory"""
    name_match = re.search(r"my name is (\w+)", user_input.lower())
    if name_match and not st.session_state.memory['name']:
        st.session_state.memory['name'] = name_match.group(1)
    
    st.session_state.memory['context'].append({
        'user_input': user_input,
        'bot_response': bot_response,
        'timestamp': str(datetime.now())
    })
    
    # Keep only last 10 conversations
    if len(st.session_state.memory['context']) > 10:
        st.session_state.memory['context'] = st.session_state.memory['context'][-10:]

def process_user_input(user_input):
    """Process user input and generate appropriate response"""
    if any(keyword in user_input.lower() for keyword in ["diet", "meal", "food", "eat", "nutrition"]):
        st.session_state.questioning_mode = True
        st.session_state.current_question_index = 0
        return RECIPE_QUESTIONS[0]
    
    if st.session_state.questioning_mode:
        st.session_state.user_info[f"recipe_q_{st.session_state.current_question_index}"] = user_input
        
        # Check diet safety after getting goal
        if st.session_state.current_question_index == 3:
            height = st.session_state.user_info.get('recipe_q_0', 0)
            weight = st.session_state.user_info.get('recipe_q_1', 0)
            age = st.session_state.user_info.get('recipe_q_2', 0)
            is_safe, message = check_diet_safety(height, weight, age, user_input)
            if not is_safe:
                st.session_state.questioning_mode = False
                return f"⚠️ {message} Please consult with a healthcare provider."
        
        st.session_state.current_question_index += 1
        
        if st.session_state.current_question_index < len(RECIPE_QUESTIONS):
            return RECIPE_QUESTIONS[st.session_state.current_question_index]
        else:
            st.session_state.questioning_mode = False
            return generate_meal_plan(st.session_state.user_info)
    
    # Default response using Gemini
    try:
        response = model.generate_content(f"As a diet planning assistant: {user_input}")
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error: {str(e)}"

def main():
    st.set_page_config(page_title="Diet Planning Assistant", layout="wide")
    init_session_state()
    
    st.title("Diet Planning Assistant")
    
    # Sidebar
    with st.sidebar:
        st.title("Menu")
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.user_info = {}
            st.session_state.current_question_index = 0
            st.session_state.questioning_mode = False
            st.session_state.memory = {'name': None, 'preferences': {}, 'context': []}
            st.rerun()
    
    # Chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.write(prompt)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("assistant"):
            response = process_user_input(prompt)
            st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})
            update_memory(prompt, response)

if __name__ == "__main__":
    main()