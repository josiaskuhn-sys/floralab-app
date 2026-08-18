from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Inicializa o cliente Gemini com a chave de ambiente
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def home():
    # Lê o arquivo index.html da raiz para servir a interface
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>FloraLabApp Online!</h1><p>index.html não encontrado na raiz.</p>"

@app.post("/analisar-ambiente")
async def analisar_ambiente(file: UploadFile = File(...)):
    try:
        # Lê os bytes da imagem enviada pela câmera do celular
        image_bytes = await file.read()
        
        # Prepara o prompt instruindo a IA a atuar como botânica especialista em paisagismo interno
        prompt = (
            "Analise este ambiente mostrado na imagem. Avalie a incidência de luz natural, "
            "o espaço disponível e o estilo do local. Com base nisso, recomende 3 espécies de plantas "
            "que se adaptariam perfeitamente a este espaço. "
            "Retorne a resposta de forma clara e estruturada contendo: "
            "1. Diagnóstico do ambiente (luz e espaço). "
            "2. As 3 plantas recomendadas com nome popular e científico. "
            "3. Cuidados específicos de rega e luz para cada uma delas."
        )
        
        # Envia a imagem e o prompt para o modelo Gemini 2.5 Flash (rápido e excelente para visão computacional)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[
                prompt,
                {
                    "mime_type": file.content_type or "image/jpeg",
                    "data": image_bytes
                }
            ]
        )
        
        return {"resultado": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))