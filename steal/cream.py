import streamlit as st
import google.generativeai as genai
from datetime import datetime
import json
import re

# Configure Gemini API
genai.configure(api_key='AIzaSyDsp-Q1M2CM548oSCoAAO_UCAaeM2dOdVI')
model = genai.GenerativeModel('gemini-pro')

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'user_info' not in st.session_state:
    st.session_state.user_info = {}
if 'current_message' not in st.session_state:
    st.session_state.current_message = ""
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
if 'sound_enabled' not in st.session_state:
    st.session_state.sound_enabled = True
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# Previous question flow and helper functions remain the same
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

def generate_meal_plan_prompt(user_info, daily_calories):
    """Generate a structured prompt for the meal plan"""
    return f"""Create a detailed 7-day meal plan based on these parameters:
User Profile:
- Daily Calorie Target: {int(daily_calories)} kcal
- Diet Type: {user_info.get('recipe_q_4', 'No preference')}
- Dietary Restrictions: {user_info.get('recipe_q_5', 'None')}
- Preferred Foods: {user_info.get('recipe_q_6', 'No specific preferences')}
- Meals per Day: {user_info.get('recipe_q_7', '3')}
- Available Cooking Time: {user_info.get('recipe_q_8', '30 minutes')}

Please provide a structured response in this format:

HEALTH METRICS ANALYSIS
[Provide brief analysis of BMI and health metrics]

7-DAY MEAL PLAN
Day 1:
- Breakfast (X calories): [Meal description]
- Lunch (X calories): [Meal description]
- Dinner (X calories): [Meal description]
[Continue for all specified meals]

[Repeat for Days 2-7]

PREPARATION GUIDELINES
- Shopping List
- Meal Prep Tips
- Storage Recommendations

NUTRITION TIPS
- Portion Control
- Meal Timing
- Healthy Substitutions
"""

def calculate_bmi(height_cm, weight_kg):
    try:
        height_m = float(height_cm) / 100
        weight = float(weight_kg)
        bmi = weight / (height_m * height_m)
        return round(bmi, 2)
    except:
        return None

def check_diet_safety(height, weight, age, goal):
    try:
        bmi = calculate_bmi(height, weight)
        if bmi is None:
            return False, "Unable to calculate BMI with provided measurements."
        
        if bmi >= 30:
            if goal.lower() == "gain weight":
                return False, "Based on your BMI, gaining weight might be unsafe. Consider a weight loss or maintenance plan instead."
        elif bmi < 18.5:
            if goal.lower() == "lose weight":
                return False, "Based on your BMI, losing weight might be unsafe. Consider a weight gain or maintenance plan instead."
        return True, "Your goal appears appropriate for your current health status."
    except:
        return False, "Unable to assess diet safety with provided information."

def generate_recipe_recommendations():
    """Generate structured diet plan based on collected information"""
    try:
        height = float(st.session_state.user_info.get('recipe_q_0', 0))
        weight = float(st.session_state.user_info.get('recipe_q_1', 0))
        age = float(st.session_state.user_info.get('recipe_q_2', 0))
        goal = st.session_state.user_info.get('recipe_q_3', '')

        bmi = calculate_bmi(height, weight)
        
        if bmi:
            # Calculate BMR using Mifflin-St Jeor Equation
            bmr = (10 * weight) + (6.25 * height) - (5 * age)
            if st.session_state.user_info.get('gender', 'male').lower() == 'male':
                bmr += 5
            else:
                bmr -= 161

            # Activity factor (using moderate activity by default)
            daily_calories = bmr * 1.55

            # Adjust calories based on goal
            if goal.lower() == 'lose weight':
                daily_calories -= 500
            elif goal.lower() == 'gain weight':
                daily_calories += 500

            # Generate structured meal plan prompt
            prompt = generate_meal_plan_prompt(st.session_state.user_info, daily_calories)

            try:
                # Split the generation into multiple calls to ensure completeness
                health_metrics = model.generate_content(
                    prompt + "\nProvide only the HEALTH METRICS ANALYSIS section:"
                ).text

                meal_plan = model.generate_content(
                    prompt + "\nProvide only the 7-DAY MEAL PLAN section:"
                ).text

                guidelines = model.generate_content(
                    prompt + "\nProvide only the PREPARATION GUIDELINES and NUTRITION TIPS sections:"
                ).text

                # Combine all sections
                complete_response = f"""
{health_metrics}

{meal_plan}

{guidelines}

Note: This meal plan is a general guideline. Please consult with a healthcare provider before starting any new diet plan.
"""
                return complete_response.strip()

            except Exception as e:
                return "I apologize, but I'm having trouble generating your personalized meal plan. Please try again."

        else:
            return "Unable to calculate BMI and generate recommendations. Please ensure all measurements are valid numbers."

    except Exception as e:
        return f"There was an error generating your meal plan: {str(e)}"

def update_memory(user_input, bot_response):
    name_match = re.search(r"my name is (\w+)", user_input.lower())
    if name_match and not st.session_state.memory['name']:
        st.session_state.memory['name'] = name_match.group(1)
    
    st.session_state.memory['context'].append({
        'user_input': user_input,
        'bot_response': bot_response,
        'timestamp': str(datetime.now())
    })
    
    if len(st.session_state.memory['context']) > 10:
        st.session_state.memory['context'] = st.session_state.memory['context'][-10:]

def get_memory_context():
    context = ""
    if st.session_state.memory['name']:
        context += f"The user's name is {st.session_state.memory['name']}. "
    
    if st.session_state.memory['context']:
        context += "Recent conversations:\n"
        for conv in st.session_state.memory['context'][-3:]:
            context += f"User: {conv['user_input']}\nAssistant: {conv['bot_response']}\n"
    
    return context

def process_user_input(user_input):
    if any(keyword in user_input.lower() for keyword in ["diet", "meal", "food", "eat", "nutrition", "healthy recipes"]):
        st.session_state.questioning_mode = True
        st.session_state.current_question_index = 0
        response = RECIPE_QUESTIONS[0]
        update_memory(user_input, response)
        return response
    
    if st.session_state.questioning_mode:
        st.session_state.user_info[f"recipe_q_{st.session_state.current_question_index}"] = user_input
        
        if st.session_state.current_question_index == 3:
            height = float(st.session_state.user_info.get('recipe_q_0', 0))
            weight = float(st.session_state.user_info.get('recipe_q_1', 0))
            age = float(st.session_state.user_info.get('recipe_q_2', 0))
            goal = user_input
            
            is_safe, message = check_diet_safety(height, weight, age, goal)
            if not is_safe:
                st.session_state.questioning_mode = False
                st.session_state.current_question_index = 0
                return f"⚠️ {message} Please consult with a healthcare provider for personalized advice."
        
        st.session_state.current_question_index += 1
        
        if st.session_state.current_question_index < len(RECIPE_QUESTIONS):
            response = RECIPE_QUESTIONS[st.session_state.current_question_index]
            update_memory(user_input, response)
            return response
        else:
            st.session_state.questioning_mode = False
            response = generate_recipe_recommendations()
            update_memory(user_input, response)
            return response
    
    response = get_bot_response(user_input)
    update_memory(user_input, response)
    return response

def get_bot_response(user_input):
    memory_context = get_memory_context()
    context = f"""You are MAX, a professional diet planning assistant. Act as a certified nutritionist who:
- Provides evidence-based dietary advice
- Creates personalized meal plans
- Calculates and explains BMI
- Offers practical nutrition guidance
Keep responses focused on nutrition and diet advice. Be direct and concise.

Memory Context:\n{memory_context}"""
    prompt = f"{context}\nUser: {user_input}\nMAX:"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return "I apologize, but I'm having trouble generating a response right now. Could you please try again?"

def show_diet_assistant():
    st.title("MAX - Your Personal Diet Planning Assistant")
    st.write("I can help you create a personalized diet plan. You can type or speak!")

    # Chat container
    chat_container = st.container()
    with chat_container:
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                        <div style="background-color: #DCF8C6; padding: 10px; border-radius: 10px; max-width: 70%;">
                            {message["content"]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                        <div style="background-color: #E8E8E8; padding: 10px; border-radius: 10px; max-width: 70%;">
                            {message["content"]}
                        </div>
                    </div>
                """, unsafe_allow_html=True)

    # Form for input handling
    with st.form(key="message_form"):
        user_input = st.text_input("Type your message here...")
        col1, col2 = st.columns([10, 1])
        
        with col2:
            submit_button = st.form_submit_button("Send")

        if submit_button and user_input:
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_input
            })
            
            bot_response = process_user_input(user_input)
            
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": bot_response
            })
            
            st.rerun()

def main():
    st.set_page_config(page_title="Health Assistant", layout="wide")
    
    with st.sidebar:
        st.title("MAX - The Personal Diet Planner")
        st.markdown("You can ask MAX anything related to diet here.")
        st.markdown("### About")
        
        page = st.selectbox("Choose a feature", ["Diet Assistant"])
        
        if st.button("Clear Chat"):
            st.session_state.chat_history = []
            st.session_state.user_info = {}
            st.session_state.current_message = ""
            st.session_state.current_question_index = 0
            st.session_state.questioning_mode = False
            st.session_state.memory = {'name': None, 'preferences': {}, 'context': []}
            st.rerun()

    if page == "Diet Assistant":
        show_diet_assistant()

if __name__ == "__main__":
    main()