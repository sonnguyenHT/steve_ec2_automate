import streamlit as st

# Set the page configuration
st.set_page_config(page_title="Instance Runner", page_icon="🚀", layout="wide")

# Add custom CSS to style the layout
st.markdown("""
    <style>
        .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background-color: #4B0082;
            padding: 20px;
            border-radius: 10px;
        }
        .container div {
            flex: 1;
            text-align: center;
            margin: 0 10px;
        }
        .container div input, .container div select, .container div button {
            width: 90%;
            padding: 10px;
            border-radius: 5px;
            border: none;
            margin: 5px auto;
        }
        .container div input {
            background-color: #FFFFFF;
        }
        .container div select {
            background-color: #D8BFD8;
        }
        .container div button {
            background-color: #FFD700;
            color: #000000;
            font-weight: bold;
        }
    </style>
""", unsafe_allow_html=True)

# Create the layout
st.markdown('<div class="container">', unsafe_allow_html=True)

# Input field for typing the name to tag the instance
name = st.text_input("", placeholder="Type name to tag instance", key="name_input")

# Dropdown for selecting a template
template = st.selectbox("", ["Search template", "Template 1", "Template 2", "Template 3"], key="template_select")

# Button to run the instance
if st.button("Run Instance", key="run_button"):
    st.write(f"Running instance tagged as: {name} with template: {template}")

st.markdown('</div>', unsafe_allow_html=True)
