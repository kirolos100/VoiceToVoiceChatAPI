from flask import Flask, request, Response, send_from_directory 
import json
import PyPDF2
from flask_cors import CORS
from openai import AzureOpenAI

app = Flask(__name__)
CORS(app)

AZURE_CONFIG = {
    "pdf_path": "AI  Carrier AC Script.pdf",
    "azure_endpoint": "https://genral-openai.openai.azure.com/",
    "api_key": "8929107a6a6b4f37b293a0fa0584ffc3",
    "api_version": "2024-02-01",
    "model": "gpt-4o"
}

llm = AzureOpenAI(
    azure_endpoint=AZURE_CONFIG["azure_endpoint"],
    api_key=AZURE_CONFIG["api_key"],
    api_version=AZURE_CONFIG["api_version"]
)

def extract_text_from_pdf():
    try:
        with open(AZURE_CONFIG["pdf_path"], 'rb') as file:
            return "\n".join([page.extract_text() or "" for page in PyPDF2.PdfReader(file).pages])
    except Exception as e:
        print(f"PDF Error: {str(e)}")
        return ""

pdf_content = extract_text_from_pdf()
conversation_history = [{
    "role": "system",
    "content": """تحدث باللهجة المصرية فقط. القواعد:
    1. ردود عامية مصرية بسيطة
    2. جمل قصيرة وواضحة
    3. لا مصطلحات إنجليزية
    4. اعتماد على معلومات الملف
    5. بدون تنسيقات أو عنواين"""
}]

@app.route('/stream', methods=['GET'])
def stream():
    user_query = request.args.get('query', '')
    
    try:
        current_history = conversation_history.copy()
        current_history.append({
            "role": "user",
            "content": f"المحتوى: {pdf_content}\nالسؤال: {user_query}\nالرد:"
        })

        response = llm.chat.completions.create(
            model=AZURE_CONFIG["model"],
            messages=current_history,
            temperature=0.7,
            max_tokens=500
        )

        full_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": full_response})

        return Response(f"data: {json.dumps({'response': full_response})}\n\n", 
                      content_type='text/event-stream')

    except Exception as e:
        print(f"API Error: {str(e)}")
        return Response(f"data: {json.dumps({'error': 'حدث خطأ في المعالجة'})}\n\n",
                      content_type='text/event-stream')

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
