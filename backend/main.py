from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from google import genai
from PIL import Image
import io
import json
import re
import os
from pydantic import BaseModel
from typing import List

app = FastAPI()

# Inicializa o cliente lendo a chave de forma segura das variáveis de ambiente do servidor
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class AnalisePlanta(BaseModel):
    nome_cientifico: str
    nome_popular: str
    score_saude: int
    diagnostico: str
    cuidados_rega: str
    cuidados_luz: str
    dicas: List[str]

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FloraLab Pro - SaaS Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-900 min-h-screen text-white flex flex-col items-center p-4">

    <div class="max-w-md w-full flex flex-col h-full">
        <header class="text-center my-4">
            <h1 class="text-3xl font-black text-emerald-400">🌿 FloraLab Pro</h1>
            <p class="text-gray-400 text-sm">Diagnóstico Inteligente & Diário de Plantas</p>
        </header>

        <div class="flex bg-gray-800 p-1.5 rounded-2xl mb-6 shadow-inner">
            <button onclick="switchTab('scanner')" id="tabScanner" class="flex-1 py-2.5 rounded-xl font-bold text-sm bg-emerald-600 text-white transition">📸 Escanear</button>
            <button onclick="switchTab('history')" id="tabHistory" class="flex-1 py-2.5 rounded-xl font-bold text-sm text-gray-400 hover:text-white transition">📁 Minhas Plantas</button>
        </div>

        <!-- ABA 1: SCANNER DE CÂMERA -->
        <div id="sectionScanner" class="space-y-4">
            <div id="viewfinder" class="relative rounded-3xl overflow-hidden bg-black aspect-[3/4] shadow-2xl border-2 border-emerald-500/50">
                <video id="video" autoplay playsinline class="w-full h-full object-cover"></video>
                <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div class="w-64 h-64 border-2 border-dashed border-emerald-400/70 rounded-3xl flex items-center justify-center">
                        <span class="text-emerald-400/70 text-xs font-semibold bg-black/40 px-3 py-1 rounded-full">Enquadre a folha aqui</span>
                    </div>
                </div>
            </div>

            <button id="snapBtn" class="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-4 rounded-2xl shadow-lg transition transform active:scale-95 flex items-center justify-center gap-2">
                📸 Capturar e Analisar
            </button>

            <div id="loading" class="hidden text-center py-12">
                <div class="animate-spin text-4xl mb-3">🌿</div>
                <p class="text-emerald-400 font-semibold tracking-wide">Examinando folhagem e saúde...</p>
            </div>

            <!-- Dashboard de Resultados -->
            <div id="resultArea" class="hidden space-y-4 text-gray-800 pb-8">
                <div class="bg-white p-6 rounded-3xl shadow-xl">
                    <div class="flex justify-between items-start mb-1">
                        <div>
                            <h2 id="namePop" class="text-xl font-bold text-gray-900"></h2>
                            <em id="nameSci" class="text-emerald-700 text-sm"></em>
                        </div>
                        <div id="scoreBadge" class="px-3 py-1 rounded-full font-bold text-xs"></div>
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-white p-4 rounded-2xl shadow-xl">
                        <p class="text-xs font-bold uppercase text-gray-400 mb-1">Rega</p>
                        <p id="rega" class="text-gray-800 text-sm font-semibold"></p>
                    </div>
                    <div class="bg-white p-4 rounded-2xl shadow-xl">
                        <p class="text-xs font-bold uppercase text-gray-400 mb-1">Luz</p>
                        <p id="luz" class="text-gray-800 text-sm font-semibold"></p>
                    </div>
                </div>

                <div class="bg-white p-6 rounded-3xl shadow-xl">
                    <h3 class="font-bold text-gray-900 mb-1 text-sm">🩺 Diagnóstico</h3>
                    <p id="diag" class="text-gray-600 text-sm leading-relaxed"></p>
                </div>

                <button id="resetBtn" class="w-full bg-gray-800 hover:bg-gray-700 text-white font-bold py-3.5 rounded-2xl transition shadow-lg">
                    🔄 Escanear Outra Planta
                </button>
            </div>
        </div>

        <!-- ABA 2: HISTÓRICO DE PLANTAS -->
        <div id="sectionHistory" class="hidden space-y-4 pb-8">
            <div id="historyList" class="space-y-4">
                <!-- Inserido dinamicamente via JS -->
            </div>
        </div>
    </div>

    <canvas id="canvas" class="hidden"></canvas>

    <script>
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const snapBtn = document.getElementById('snapBtn');
        const viewfinder = document.getElementById('viewfinder');
        const loading = document.getElementById('loading');
        const resultArea = document.getElementById('resultArea');
        const resetBtn = document.getElementById('resetBtn');

        function switchTab(tab) {
            const scannerSec = document.getElementById('sectionScanner');
            const historySec = document.getElementById('sectionHistory');
            const tabScanBtn = document.getElementById('tabScanner');
            const tabHistBtn = document.getElementById('tabHistory');

            if (tab === 'scanner') {
                scannerSec.classList.remove('hidden');
                historySec.classList.add('hidden');
                tabScanBtn.className = "flex-1 py-2.5 rounded-xl font-bold text-sm bg-emerald-600 text-white transition";
                tabHistBtn.className = "flex-1 py-2.5 rounded-xl font-bold text-sm text-gray-400 hover:text-white transition";
            } else {
                scannerSec.classList.add('hidden');
                historySec.classList.remove('hidden');
                tabHistBtn.className = "flex-1 py-2.5 rounded-xl font-bold text-sm bg-emerald-600 text-white transition";
                tabScanBtn.className = "flex-1 py-2.5 rounded-xl font-bold text-sm text-gray-400 hover:text-white transition";
                renderHistory();
            }
        }

        async function startCamera() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ 
                    video: { facingMode: { ideal: "environment" } } 
                });
                video.srcObject = stream;
            } catch (err) {
                console.error("Câmera indisponível:", err);
            }
        }
        startCamera();

        snapBtn.onclick = async () => {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            canvas.getContext('2d').drawImage(video, 0, 0);

            canvas.toBlob(async (blob) => {
                const formData = new FormData();
                formData.append('file', blob, 'planta.jpg');

                viewfinder.classList.add('hidden');
                snapBtn.classList.add('hidden');
                loading.classList.remove('hidden');

                try {
                    const resp = await fetch('/analisar-planta', { method: 'POST', body: formData });
                    if (!resp.ok) throw new Error('Erro ao processar');
                    
                    const data = await resp.json();
                    saveToHistory(data);

                    document.getElementById('namePop').innerText = data.nome_popular;
                    document.getElementById('nameSci').innerText = data.nome_cientifico;
                    document.getElementById('diag').innerText = data.diagnostico;
                    document.getElementById('rega').innerText = data.cuidados_rega;
                    document.getElementById('luz').innerText = data.cuidados_luz;
                    
                    const badge = document.getElementById('scoreBadge');
                    badge.innerText = data.score_saude + '% Saúde';
                    badge.className = data.score_saude > 70 ? 'bg-green-100 text-green-700 px-3 py-1 rounded-full font-bold text-xs' : 'bg-red-100 text-red-700 px-3 py-1 rounded-full font-bold text-xs';

                    loading.classList.add('hidden');
                    resultArea.classList.remove('hidden');
                } catch (err) {
                    alert('Erro ao analisar a planta. Tente novamente.');
                    loading.classList.add('hidden');
                    viewfinder.classList.remove('hidden');
                    snapBtn.classList.remove('hidden');
                }
            }, 'image/jpeg', 0.9);
        };

        resetBtn.onclick = () => {
            resultArea.classList.add('hidden');
            viewfinder.classList.remove('hidden');
            snapBtn.classList.remove('hidden');
        };

        function saveToHistory(item) {
            let history = JSON.parse(localStorage.getItem('floralab_history') || '[]');
            history.unshift({ ...item, date: new Date().toLocaleDateString('pt-BR') });
            localStorage.setItem('floralab_history', JSON.stringify(history));
        }

        function renderHistory() {
            const container = document.getElementById('historyList');
            let history = JSON.parse(localStorage.getItem('floralab_history') || '[]');

            if (history.length === 0) {
                container.innerHTML = '<div class="text-center text-gray-500 py-12 bg-gray-800 rounded-3xl">Nenhuma planta salva ainda.</div>';
                return;
            }

            container.innerHTML = history.map(item => `
                <div class="bg-white text-gray-800 p-5 rounded-3xl shadow-xl space-y-2">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-bold text-lg text-gray-900">${item.nome_popular}</h4>
                            <em class="text-emerald-700 text-xs">${item.nome_cientifico}</em>
                        </div>
                        <span class="bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full font-bold text-xs">${item.score_saude}% Saúde</span>
                    </div>
                    <p class="text-xs text-gray-500">🗓️ Analisado em: ${item.date}</p>
                    <p class="text-sm text-gray-600 bg-gray-50 p-3 rounded-2xl">${item.diagnostico}</p>
                </div>
            `).join('');
        }
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def read_index():
    return HTML_CONTENT

@app.post("/analisar-planta", response_model=AnalisePlanta)
async def analisar_planta(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        image.thumbnail((1024, 1024))

        prompt = """Analise a planta da imagem. Retorne estritamente um JSON puro contendo exatamente estas chaves:
        {
            "nome_cientifico": "...",
            "nome_popular": "...",
            "score_saude": 85,
            "diagnostico": "...",
            "cuidados_rega": "...",
            "cuidados_luz": "...",
            "dicas": ["...", "..."]
        }
        Retorne apenas o JSON, sem marcações markdown."""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt]
        )

        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match:
            json_text = match.group(0)
        else:
            json_text = response.text.replace("```json", "").replace("```", "").strip()

        return json.loads(json_text)
    except Exception as e:
        print("Erro detalhado:", str(e))
        raise HTTPException(status_code=500, detail=str(e))