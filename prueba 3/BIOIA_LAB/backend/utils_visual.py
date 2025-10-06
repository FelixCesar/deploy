def generar_estadisticas_visuales(result):
    energia = result.get("energia", {}).get("total_kw", 0)
    bacterias = result.get("bacterias", {}).get("total_millones", 0)
    gases = result.get("gases", {})
    nanobots = result.get("nanobots", {}).get("activos", 0)

    energia_pct = min(100, (energia / 50) * 100)          # 0–50 kW → 0–100%
    bacterias_pct = min(100, (bacterias / 5000) * 100)    # 0–5000 M → 0–100%
    co2_pct = min(100, (gases.get("CO2", 0) / 100) * 100)
    ch4_pct = min(100, (gases.get("CH4", 0) / 100) * 100)
    nanobots_pct = min(100, (nanobots / 200) * 100)

    return {
        "energia_pct": round(energia_pct, 2),
        "bacterias_pct": round(bacterias_pct, 2),
        "co2_pct": round(co2_pct, 2),
        "ch4_pct": round(ch4_pct, 2),
        "nanobots_pct": round(nanobots_pct, 2)
    }
