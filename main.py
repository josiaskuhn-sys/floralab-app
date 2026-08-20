from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from PIL import Image
import io
import os

app = FastAPI()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class PaisRequest(BaseModel):
    pais: str

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
            "o espaço disponível e o estilo do local. Com base nisso, recomende espécies de plantas "
            "que se adaptariam perfeitamente a este espaço, incluindo dicas práticas de plantio e cultivo. "
            "Retorne a resposta de forma clara e estruturada contendo: "
            "1. Diagnóstico do ambiente (luz e espaço). "
            "2. As espécies recomendadas (nome popular e científico). "
            "3. Guia passo a passo de como plantar e cuidar de cada uma."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
        
        return {"resultado": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/avaliar-planta")
async def avaliar_planta(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        prompt = (
            "Analise esta planta mostrada na imagem. "
            "Forneça um relatório botânico completo contendo: "
            "1. Identificação (Nome popular e científico da espécie). "
            "2. Estado de saúde e diagnóstico (análise de folhas, vitalidade ou sinais de pragas/doenças). "
            "3. Guia prático de plantio/replantio e tipo de solo ideal. "
            "4. Cuidados essenciais de rega, luz e adubação."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
        
        return {"resultado": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/explorar-pais")
async def explorar_pais(data: PaisRequest):
    try:
        prompt = (
            f"Aja como um botânico especialista em biogeografia e jardinagem. "
            f"Liste 3 plantas populares originárias de ou muito cultivadas na {data.pais} "
            f"que possuem excelente adaptação ao clima do Brasil (seja para cultivo interno ou jardins). "
            f"Para cada planta, forneça de forma estruturada: "
            f"1. Nome popular e científico. "
            f"2. História fascinante ou curiosidade de origem. "
            f"3. Guia prático de plantio e forma de cultivo nas condições brasileiras."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt]
        )
        
        return {"resultado": response.text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))