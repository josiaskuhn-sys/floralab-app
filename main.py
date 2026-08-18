from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from google import genai
from PIL import Image
import io
import os

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.get("/", response_class=HTMLResponse)
async def home():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>FloraLabApp Online!</h1>"

@app.post("/analisar-ambiente")
async def analisar_ambiente(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = (
            "Analise este ambiente mostrado na imagem. Avalie a incidência de luz natural, "
            "o espaço disponível e o estilo do local. Com base nisso, recomende 3 espécies de plantas "
            "que se adaptariam perfeitamente a este espaço. "
            "Retorne a resposta de forma clara e estruturada contendo: "
            "1. Diagnóstico do ambiente (luz e espaço). "
            "2. As 3 plantas recomendadas com nome popular e científico. "
            "3. Cuidados específicos de rega e luz para cada uma delas."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
        
        return {"resultado": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))