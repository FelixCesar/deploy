# backend/bio_server.py
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, os, datetime
from bio_nano_terminal import calcular_totales, WASTE_PROFILES, BIOAI_LEVELS
from utils_visual import generar_estadisticas_visuales

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "historial.json")
os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
if not os.path.exists(DATA_PATH):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

def adaptar_a_frontend(summary):
    """
    Adapta el 'summary' que devuelve bio_nano_terminal.calcular_totales()
    a la estructura que espera el frontend:
      energia.total_kw
      bacterias.total_millones
      gases.CO2 / gases.CH4
      nanobots.activos
    """
    # 1) Energía: el backend entrega kWh; el frontend etiqueta 'kW'.
    #    Mantenemos el valor y la clave para no romper UI (mostrarás número coherente).
    energia_kwh = float(summary.get("total_energy_kwh", 0.0))

    # 2) Bacterias: backend entrega gramos totales
    #    El frontend espera "millones" (M). Convertimos g -> millones de bacterias aprox.
    #    Si no tienes una conversión biofísica real, usamos una métrica visual estable:
    #    1 gramo ~ 1e9 células -> millones = gramos * 1000 (1e9/1e6).
    bacterias_g = float(summary.get("total_bacterias_g", 0.0))
    bacterias_millones = bacterias_g * 1000.0

    # 3) Gases: backend entrega total_gas_kg (mezcla). Dividimos en CO2/CH4 para la UI.
    #    Suposición neutra: 60% CO2, 40% CH4 (puedes ajustar luego si tu equipo define otra proporción).
    total_gas = float(summary.get("total_gas_kg", 0.0))
    co2 = total_gas * 0.60
    ch4 = total_gas * 0.40

    # 4) Nanobots
    nanobots_activos = int(summary.get("total_nanobots", 0))

    adaptado = {
        "energia": {"total_kw": energia_kwh},                 # mantenemos la clave que usa tu UI
        "bacterias": {"total_millones": bacterias_millones},  # número grande pero consistente
        "gases": {"CO2": co2, "CH4": ch4},
        "nanobots": {"activos": nanobots_activos}
    }
    return adaptado

def guardar_historial(entry):
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = []
    data.append(entry)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class BioHandler(BaseHTTPRequestHandler):
    def _set_headers_json(self, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_POST(self):
        if self.path == "/api/calcular":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length)
                data = json.loads(body)

                crew = int(data.get("crew", 1))
                days = int(data.get("days", 1))

                # El bio_nano_terminal usa nombres de perfil/nivel diferentes a los de tu UI.
                # Mapeamos por nombre (si llega string) o usamos defaults.
                perfil_key = data.get("perfil")
                if isinstance(perfil_key, str) and perfil_key in WASTE_PROFILES:
                    perfil = WASTE_PROFILES[perfil_key]
                else:
                    # Fallback sensato al primer perfil del archivo del equipo
                    perfil = list(WASTE_PROFILES.values())[0]

                bioai_key = data.get("bioai")
                # En el archivo del equipo, BIOAI_LEVELS son claves numéricas (0..3)
                # Tu UI manda "N1"/"N2"/"N3". Normalizamos:
                map_bioai = {"N1": 1, "N2": 2, "N3": 3, "Manual": 0}
                bioai_idx = map_bioai.get(bioai_key, 2)
                bioai = BIOAI_LEVELS.get(bioai_idx, BIOAI_LEVELS[2])

                # Llamada al cálculo "original" del equipo (NO lo rompemos)
                summary = calcular_totales(crew, days, perfil, bioai)

                # Adaptamos el resumen a lo que espera tu frontend
                estandar = adaptar_a_frontend(summary)

                # Enriquecemos con visuales para los gráficos circulares
                visual = generar_estadisticas_visuales(estandar)

                payload = {
                    **estandar,
                    "visual": visual,
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

                # Guardar en historial
                guardar_historial({
                    "fecha": payload["fecha"],
                    "tripulantes": crew,
                    "dias": days,
                    "perfil": data.get("perfil", "Estándar_mision"),
                    "bioAI": data.get("bioai", "N2"),
                    "resultados": payload
                })

                self._set_headers_json(200)
                self.wfile.write(json.dumps(payload).encode())

            except Exception as e:
                self._set_headers_json(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                print("❌ Error en /api/calcular:", e)

    def do_GET(self):
        if self.path == "/api/historial":
            try:
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._set_headers_json(200)
                self.wfile.write(json.dumps(data).encode())
                print(f"📜 Historial enviado ({len(data)} registros).")
            except Exception as e:
                self._set_headers_json(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode())
                print("❌ Error en /api/historial:", e)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(("localhost", 5500), BioHandler)
    print("🌿 Servidor BIOIA activo en: http://localhost:5500")
    server.serve_forever()
