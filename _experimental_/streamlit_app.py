import asyncio
import streamlit as st
import threading
from _experimental_.asyncAutomateDice import async_main as run_playwright_script
from _data_.Profiles.main_profile import user_profile, display_profile

# Streamlit UI
st.title("Automated Job Search Application")

# Display user profile
st.subheader("User Profile")
st.write(f"Name: {user_profile.name}")
st.write(f"Email: {user_profile.email}")
st.write(f"City: {user_profile.city}")
st.write(f"Country: {user_profile.country}")
st.write(f"Timezone: {user_profile.timezone}")
st.write(f"Apply Every: {user_profile.apply_every.value}")

# Display the profile in a detailed view
st.subheader("Full Profile Details")
st.text(display_profile(user_profile))

# Function to run the Playwright script asynchronously on a separate thread
def run_script():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_playwright_script())

# Run the Playwright script in a separate thread
if st.button("Run Job Search"):
    st.write("Starting job search...")
    
    # Start the Playwright script in a new thread
    thread = threading.Thread(target=run_script)
    thread.start()

    thread.join()  # Wait for the thread to finish
    
    st.success("Job search completed.")
