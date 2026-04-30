Google Gemini for Motiv “Workout coach”
========================================

There is no separate “PIN” for Gemini. You use an API key (a long secret string).

Steps
1) Open https://aistudio.google.com/apikey (Google AI Studio).
2) Sign in with your Google account.
3) Click “Create API key” and choose a Google Cloud project (or let Google create one).
4) Copy the key (starts with “AIza…”).
5) In your Motiv project folder, edit the .env file next to app.py and add a line (no spaces around =):
   GEMINI_API_KEY=AIza...your_actual_key...
   You can also use GOOGLE_API_KEY or GEMINI_KEY as the variable name if you prefer.
   Do not wrap the value in quotes unless your whole value is quoted; stray quotes are stripped automatically.
6) Save .env. Never commit .env to git (it should stay in .gitignore).
7) If your IDE defines an empty GEMINI_API_KEY for debugging, remove it or the app will load the real key from .env (dotenv override is enabled).
8) Install Python dependency:  pip install 'google-genai>=1.0.0,<2'
   (or: pip install -r requirements.txt)
9) Restart the Flask server so it reloads .env.

Optional: set GEMINI_MODEL in .env to force one model id (e.g. gemini-2.5-flash). Otherwise the app tries a few current 2.x models in order.

The key is read only on the server. The browser never sees it.

Optional: free tier has rate limits; if you hit errors, wait a minute or check the message in the UI.
