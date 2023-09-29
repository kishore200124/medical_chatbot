import streamlit as st

# Add a sidebar menu to select the app to run
app_choice = st.sidebar.selectbox("Select an App", ["Chat with PDF", "Chat with Video"])

if app_choice == "Chat with PDF":
    # Run app.py
    import app
elif app_choice == "Chat with Video":
    # Run app2.py
    import streamlitui
