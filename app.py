import os
from flask import Flask, render_template, request
from google import genai
from google.genai import types

app = Flask(__name__)

# API Açarı konfiqurasiyası
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

SYSTEM_PROMPT = """
Sən peşəkar riyaziyyat müəllimisən. İstifadəçi sənə bir riyaziyyat sualı və ya məsələsi verəcək.
SƏNİN ƏSAS QAYDAN: Məsələnin son cavabını (ədədi nəticəni) BİRBAŞA VERMƏ!
Bunun əvəzinə:
1. Məsələnin hansı mövzuya aid olduğunu de.
2. Həll üçün istifadə olunacaq düstur və ya qaydanı xatırlat.
3. Tələbənin cavabı özü tapması üçün addım-addım həll yolunu və ipucularını ver.
Aydın, mehriban və həvəsləndirici ton istifadə et.
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    response_text = ""
    user_question = ""
    if request.method == 'POST':
        user_question = request.form.get('question')
        if user_question:
            try:
                client = genai.Client(api_key=GEMINI_API_KEY)
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=user_question,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT
                    )
                )
                response_text = response.text
            except Exception as e:
                response_text = f"Xəta baş verdi: {str(e)}"
    
    return render_template('index.html', response=response_text, question=user_question)

if __name__ == '__main__':
    app.run(debug=True)