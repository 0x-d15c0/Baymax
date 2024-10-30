import streamlit as st
import requests
import uuid

st.set_page_config(page_title="🤖🩺 Baymax - Your Personal Healthcare Companion")

with st.sidebar:
    st.title('🤖🩺 Chat with Baymax Health Assistant')
    st.write("Baymax provides you healthcare information and diagnosis")
    st.markdown("**Instructions:** Enter your health-related question below to receive relevant advice.")
    st.markdown("Fill your personal details for a more accurate output.")
    
    # Redirect to personal details form thingy
    if st.button("Fill Personal History"):
        st.experimental_set_query_params(page="personal")

# Generate a unique session ID for each user
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

# Function to get response from FastAPI backend
def get_response_from_backend(prompt_input):
    url = "http://localhost:8000/chat"
    response = requests.post(url, json={"prompt": prompt_input, "session_id": st.session_state.session_id})
    if response.status_code == 200:
        return response.json().get("response", "")
    else:
        return "Error: Unable to fetch response from the server."

# User-provided prompt
if prompt := st.chat_input("Ask a healthcare question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generate a new response if the last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_response_from_backend(prompt)
                st.write(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

# Handle personal history form
if st.experimental_get_query_params().get("page") == ["personal"]:
    st.header("Fill Your Personal History")
    # Example fields for personal history
    age = st.number_input("Age", min_value=1, max_value=120, step=1)
    dietary_restrictions = st.text_input("Dietary Restrictions")
    fitness_goals = st.text_input("Fitness Goals")
    
    if st.button("Submit"):
        personal_history = {
            "age": age,
            "dietary_restrictions": dietary_restrictions,
            "fitness_goals": fitness_goals
        }
        response = requests.post("http://localhost:8000/personal", json=personal_history)
        if response.status_code == 200:
            st.success("Personal details saved successfully!")
            st.experimental_set_query_params(page="")  # Clear the query params to reset the form
        else:
            st.error("Error saving personal details.")
