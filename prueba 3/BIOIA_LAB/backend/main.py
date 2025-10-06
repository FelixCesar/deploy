# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json, os, datetime
from bio_nano_terminal import calcular_totales, WASTE_PROFILES, BIOAI_LEVELS
from utils_visual import generar_estadisticas_visuales

app = FastAPI(title="BioNano Reclaimer API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta para el archivo de datos
DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "historial.json")
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

def adaptar_a_frontend(summary):
    """Adapta los datos del backend para el frontend"""
    energia_kwh = float(summary.get("total_energy_kwh", 0.0))
    bacterias_g = float(summary.get("total_bacterias_g", 0.0))
    bacterias_millones = bacterias_g * 1000.0
    total_gas = float(summary.get("total_gas_kg", 0.0))
    co2 = total_gas * 0.60
    ch4 = total_gas * 0.40
    nanobots_activos = int(summary.get("total_nanobots", 0))

    return {
        "energia": {"total_kw": energia_kwh},
        "bacterias": {"total_millones": bacterias_millones},
        "gases": {"CO2": co2, "CH4": ch4},
        "nanobots": {"activos": nanobots_activos}
    }

def guardar_historial(entry):
    """Guarda en el historial JSON"""
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []
    
    data.append(entry)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

@app.post("/api/calcular")
async def calcular_simulacion(data: dict):
    try:
        crew = int(data.get("crew", 1))
        days = int(data.get("days", 1))

        # Mapear perfil
        perfil_key = data.get("perfil")
        if isinstance(perfil_key, str) and perfil_key in WASTE_PROFILES:
            perfil = WASTE_PROFILES[perfil_key]
        else:
            perfil = list(WASTE_PROFILES.values())[0]

        # Mapear nivel BioAI
        map_bioai = {"N1": 1, "N2": 2, "N3": 3, "Manual": 0}
        bioai_key = data.get("bioai", "N2")
        bioai_idx = map_bioai.get(bioai_key, 2)
        bioai = BIOAI_LEVELS.get(bioai_idx, BIOAI_LEVELS[2])

        # Calcular
        summary = calcular_totales(crew, days, perfil, bioai)
        estandar = adaptar_a_frontend(summary)
        visual = generar_estadisticas_visuales(estandar)

        payload = {
            **estandar,
            "visual": visual,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        # Guardar historial
        guardar_historial({
            "fecha": payload["fecha"],
            "tripulantes": crew,
            "dias": days,
            "perfil": data.get("perfil", "Estándar_mision"),
            "bioAI": data.get("bioai", "N2"),
            "resultados": payload
        })

        return payload

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/historial")
async def obtener_historial():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Montar archivos estáticos del frontend
app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")

@app.get("/")
async def root():
    return {"message": "BioNano Reclaimer API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)