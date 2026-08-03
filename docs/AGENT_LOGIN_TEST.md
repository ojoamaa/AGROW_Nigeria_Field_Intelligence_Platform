# Agent Registration and Login Test

1. Start the application with `python -m streamlit run app.py`.
2. Open the **Signup** tab.
3. Complete all fields and capture the agent photograph.
4. Enter `DATADEV` as the Organisation Invite Code.
5. Create and confirm a password of at least six characters.
6. Note the generated username shown before submission, for example `KN-01`.
7. Click **Create Agent Account**.
8. Confirm the success message repeats the generated username.
9. Open the **Login** tab.
10. Use the generated username and the exact password created during signup.
11. Confirm the agent dashboard opens.

Usernames are case-insensitive and surrounding spaces are ignored. Passwords are trimmed at registration and login.
