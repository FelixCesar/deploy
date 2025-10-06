#!/usr/bin/env python3
# bio_nano_terminal.py
# Simulación interactiva Bio_Nano Reclaimer - terminal (sin librerías externas)
# Guarda: python bio_nano_terminal.py
# Autor: BioAI prototype (respuesta al usuario)

from datetime import datetime

# ---------------------------
# Datos base / presets
# ---------------------------

# Tipos de desechos típicos en misiones espaciales (fracciones por persona)
WASTE_PROFILES = {
    "Estándar_mision": {
        "descripcion": "Perfil promedio (combinado) para misiones de larga duración",
        "per_person_kg_day": 1.45,  # kg/persona/día (según NASA paper)
        "breakdown_pct": {
            "Plástico_PET": 0.24,
            "Orgánico": 0.31,
            "Metal_ligero": 0.06,
            "Textil": 0.11,
            "Higiene_y_papeleria": 0.10,
            "Otros": 0.18
        }
    },
    "Alto_organico": {
        "descripcion": "Mayor fracción orgánica (habitats con agricultura)",
        "per_person_kg_day": 1.6,
        "breakdown_pct": {
            "Plástico_PET": 0.18,
            "Orgánico": 0.45,
            "Metal_ligero": 0.05,
            "Textil": 0.12,
            "Higiene_y_papeleria": 0.10,
            "Otros": 0.10
        }
    }
}

# Bacterias y variantes (incluye "modificadas para espacio")
BACTERIA_LIBRARY = {
    "Ideonella_sakaiensis": {
        "target": "Plástico_PET",
        "ef_base": 0.35,
        "nota": "Degrada PET; versión espacial: tolerancia a radiación baja->media",
        "almacenamiento": "Módulo Bacteriano T-1",
        "bacterias_g_por_kg_target": 15  # gramos bacterias por kg de residuo target (estimación)
    },
    "Deinococcus_radiodurans": {
        "target": "Orgánico",
        "ef_base": 0.55,
        "nota": "Extremófilo resistente; base para modificación espacial",
        "almacenamiento": "BioCámara O-7",
        "bacterias_g_por_kg_target": 20
    },
    "Bacillus_metallidurans": {
        "target": "Metal_ligero",
        "ef_base": 0.15,
        "nota": "Metalófaga para biolixiviación",
        "almacenamiento": "Contenedor M-5",
        "bacterias_g_por_kg_target": 25
    },
    "Pseudomonas_textilis": {
        "target": "Textil",
        "ef_base": 0.25,
        "nota": "Degrada celulosa / fibras",
        "almacenamiento": "Unidad BioTextil-2",
        "bacterias_g_por_kg_target": 12
    },
    "Geobacter_electrogenes": {
        "target": "Orgánico",
        "ef_base": 0.30,
        "nota": "Genera corriente eléctrica (bioelectrogénica)",
        "almacenamiento": "BioCell E-2",
        "bacterias_g_por_kg_target": 18
    }
}

# Nanobots: capacidad de transporte bacterias (g) y coste unitario estimado (USD)
NANOBOT_SPEC = {
    "capacidad_bacteria_g": 50.0,   # gramos que puede transportar/entregar por ciclo
    "eficiencia_transporte": 0.95,  # fracción que llega operativa
    "coste_unit_usd": 200.0         # coste estimado por unidad (fabricación + integración)
}

# Contenedores y capacidades (litros) y coste aproximado
CONTAINERS = {
    "Módulo_Bacteriano_T-1": {"vol_L": 5, "capacidad_g": 2000, "coste_usd": 500},
    "BioCámara_O-7": {"vol_L": 12, "capacidad_g": 5000, "coste_usd": 1200},
    "Contenedor_M-5": {"vol_L": 4, "capacidad_g": 1500, "coste_usd": 400},
    "Unidad_BioTextil_2": {"vol_L": 6, "capacidad_g": 2500, "coste_usd": 600},
    "Banco_Bio_Nano": {"vol_L": 10, "capacidad_unidades": 500, "coste_usd": 3000}
}

# Factores de conversión y supuestos económicos/energéticos
GAS_YIELD_PER_KG_SUBPRODUCT = 0.60    # kg de gas útil (CH4/O2 equivalente) por kg subproducto
ENERGY_KWH_PER_KG_GAS = 3.5          # kWh obtenidos por kg de gas transformado (valor heurístico)
COST_PRODUCCION_BACTERIA_PER_G = 0.02  # USD por gramo (cultivo/encapsulamiento) estimado
COST_TRANSPORTE_PER_KG_TO_ORBIT_USD = 20000  # USD/kg (very rough for LEO); for Mars higher but used for reference

# BioAI automation levels (ajustan eficiencia global)
BIOAI_LEVELS = {
    0: {"name": "Manual", "boni_ef": 0.00},
    1: {"name": "Asistida", "boni_ef": 0.05},
    2: {"name": "Automatizada (BioAI)", "boni_ef": 0.12},
    3: {"name": "BioAI Avanzada + ML", "boni_ef": 0.20}
}

# Default mission assumptions
DEFAULT_CREW = 8
DEFAULT_MISSION_DAYS = 365

# ---------------------------
# Funciones de ayuda / calculos
# ---------------------------

def seleccionar_perfil():
    print("\nPerfiles de generación de desechos disponibles:")
    keys = list(WASTE_PROFILES.keys())
    for i, k in enumerate(keys, 1):
        print(f" {i}) {k} - {WASTE_PROFILES[k]['descripcion']} (k g/persona/día: {WASTE_PROFILES[k]['per_person_kg_day']})")
    print(f" {len(keys)+1}) Personalizar valores manualmente")
    choice = input("Selecciona perfil (número): ").strip()
    try:
        c = int(choice)
    except:
        c = 1
    if 1 <= c <= len(keys):
        return WASTE_PROFILES[keys[c-1]]
    else:
        # manual
        val = float(input("Introduce kg por persona por día (ej. 1.45): ") or "1.45")
        # default breakdown evenly among 6 categories
        breakdown = {
            "Plástico_PET": 0.20,
            "Orgánico": 0.30,
            "Metal_ligero": 0.05,
            "Textil": 0.10,
            "Higiene_y_papeleria": 0.10,
            "Otros": 0.25
        }
        return {"descripcion":"Manual","per_person_kg_day": val, "breakdown_pct": breakdown}

def seleccionar_bioai_level():
    print("\nNiveles de BioAI (automatización):")
    for k, v in BIOAI_LEVELS.items():
        print(f" {k}) {v['name']} (bonus eficiencia: +{int(v['boni_ef']*100)}%)")
    choice = input("Selecciona nivel (número): ").strip()
    try:
        c = int(choice)
    except:
        c = 2
    return BIOAI_LEVELS.get(c, BIOAI_LEVELS[2])

def calcular_totales(crew_size, days, profile, bioai_level, custom_bacteria_map=None, use_nanobots=True):
    # totals per waste type
    per_person = profile["per_person_kg_day"]
    total_waste_kg = crew_size * per_person * days
    breakdown = profile["breakdown_pct"]
    details = {}
    total_gas_kg = 0.0
    total_energy_kwh = 0.0
    total_cost_usd = 0.0
    total_bacteria_cost = 0.0
    total_bacterias_g = 0.0
    total_nanobots = 0

    for wtype, pct in breakdown.items():
        mass = total_waste_kg * pct
        # select bacteria: prefer custom map if provided else library match by target
        selected_bact = None
        if custom_bacteria_map and wtype in custom_bacteria_map:
            selected_bact = custom_bacteria_map[wtype]
        else:
            # search in BACTERIA_LIBRARY for target
            for bname, binfo in BACTERIA_LIBRARY.items():
                if binfo["target"] == wtype:
                    selected_bact = {"name": bname, **binfo}
                    break
        if not selected_bact:
            # default generic bacteria
            selected_bact = {"name":"Generic_bacterium", "target":wtype, "ef_base":0.20,
                             "bacterias_g_por_kg_target":15, "almacenamiento":"GenericContainer"}

        # compute efficiency with BioAI bonus
        ef = selected_bact["ef_base"] * (1.0 + bioai_level["boni_ef"])
        ef = min(0.95, ef)  # cap realistic
        # compute subproduct produced (assume ef fraction of mass can be converted over mission lifetime)
        subproduct = mass * ef
        gas = subproduct * GAS_YIELD_PER_KG_SUBPRODUCT
        energy_kwh = gas * ENERGY_KWH_PER_KG_GAS
        # bacterias grams required (scaled by mass and inversely by efficiency)
        bact_g_per_kg = selected_bact.get("bacterias_g_por_kg_target", 15)
        bacterias_needed_g = mass * bact_g_per_kg * (1.0 / max(ef, 0.01))
        # nanobots required to transport these bacteria (if used)
        nanobots_needed = 0
        if use_nanobots:
            cap = NANOBOT_SPEC["capacidad_bacteria_g"] * NANOBOT_SPEC["eficiencia_transporte"]
            nanobots_needed = int((bacterias_needed_g / cap) + 0.9999)

        # storage container selection (match library)
        cont_name = selected_bact.get("almacenamiento", "GenericContainer")
        container = CONTAINERS.get(cont_name.replace(" ", "_"), None)
        # cost estimates
        bact_cost = bacterias_needed_g * COST_PRODUCCION_BACTERIA_PER_G
        nanobot_cost = nanobots_needed * NANOBOT_SPEC["coste_unit_usd"]
        container_cost = 0.0
        if container:
            # number of containers needed by grams capacity
            n_cont = int((bacterias_needed_g / container["capacidad_g"]) + 0.9999)
            container_cost = n_cont * container["coste_usd"]
        # add approximate transport cost to orbit (for Earth comparison)
        transport_cost = (mass * COST_TRANSPORTE_PER_KG_TO_ORBIT_USD)  # rough

        # aggregate
        details[wtype] = {
            "masa_total_kg": mass,
            "bacteria": selected_bact["name"],
            "ef_ajustada": ef,
            "subproduct_kg": subproduct,
            "gas_kg": gas,
            "energy_kwh": energy_kwh,
            "bacterias_g": bacterias_needed_g,
            "nanobots_unidades": nanobots_needed,
            "almacenamiento": selected_bact.get("almacenamiento"),
            "coste_bacterias_usd": bact_cost,
            "coste_nanobots_usd": nanobot_cost,
            "coste_contenedores_usd": container_cost,
            "coste_transporte_usd": transport_cost
        }

        total_gas_kg += gas
        total_energy_kwh += energy_kwh
        total_cost_usd += bact_cost + nanobot_cost + container_cost + transport_cost
        total_bacterias_g += bacterias_needed_g
        total_bacteria_cost += bact_cost
        total_nanobots += nanobots_needed

    summary = {
        "crew_size": crew_size,
        "days": days,
        "per_person_kg_day": per_person,
        "total_waste_kg": total_waste_kg,
        "total_gas_kg": total_gas_kg,
        "total_energy_kwh": total_energy_kwh,
        "total_cost_usd": total_cost_usd,
        "total_bacterias_g": total_bacterias_g,
        "total_nanobots": total_nanobots,
        "details": details,
        "bioai_level": bioai_level["name"]
    }
    return summary

def print_report(summary, filename_save=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = []
    lines.append("BIO_NANO RECLAIMER - INFORME RESUMIDO")
    lines.append(f"Generado: {now}")
    lines.append(f"BioAI nivel: {summary['bioai_level']}")
    lines.append(f"Crew size: {summary['crew_size']} | Días: {summary['days']} | Kg/persona/día: {summary['per_person_kg_day']:.3f}")
    lines.append(f"Total residuos (kg): {summary['total_waste_kg']:.2f}")
    lines.append(f"Total gases estimados (kg): {summary['total_gas_kg']:.2f}")
    lines.append(f"Energía estimada recuperada (kWh): {summary['total_energy_kwh']:.2f}")
    lines.append(f"Total bacterias necesarias (g): {summary['total_bacterias_g']:.0f}")
    lines.append(f"Total nanobots necesarios (unid): {summary['total_nanobots']}")
    lines.append(f"Coste total estimado (USD): {summary['total_cost_usd']:.2f}")
    lines.append("-" * 60)
    lines.append("Detalle por tipo de residuo:")
    for wtype, info in summary["details"].items():
        lines.append(f" {wtype}:")
        lines.append(f"   Masa total (kg): {info['masa_total_kg']:.2f}")
        lines.append(f"   Bacteria: {info['bacteria']} (almacenamiento: {info['almacenamiento']})")
        lines.append(f"   Eficiencia ajustada: {info['ef_ajustada']:.3f}")
        lines.append(f"   Subproducto (kg): {info['subproduct_kg']:.2f}")
        lines.append(f"   Gas util (kg): {info['gas_kg']:.2f}")
        lines.append(f"   Energia (kWh): {info['energy_kwh']:.2f}")
        lines.append(f"   Bacterias necesarias (g): {info['bacterias_g']:.0f}")
        lines.append(f"   Nanobots unidades: {info['nanobots_unidades']}")
        lines.append(f"   Costes (bact/nano/cont/transport) USD: {info['coste_bacterias_usd']:.2f} / {info['coste_nanobots_usd']:.2f} / {info['coste_contenedores_usd']:.2f} / {info['coste_transporte_usd']:.2f}")
        lines.append("")
    # Impacto en Tierra (comparativo simple)
    lines.append("-" * 60)
    lines.append("Impacto comparado en Tierra:")
    lines.append(" - Menor necesidad de envío desde la Tierra reduce emisiones asociadas al transporte.")
    lines.append(" - Posible reutilización de subproductos para impresión 3D y agricultura reduce demanda de materias primas terrestres.")
    lines.append(" - Coste estimado incluye transporte a órbita como referencia; costes reales a Marte serían significativamente mayores.")
    lines.append("-" * 60)
    # aesthetics & compactness notes
    lines.append("Diseño recomendado (compacto y accesible):")
    lines.append(" - Módulos de tamaño microondas (40x40x40 cm) para BioCámaras y almacenamiento.")
    lines.append(" - Paneles solares flexibles integrados en la carcasa (estético y ligero).")
    lines.append(" - Interfaz modular: contenedores intercambiables y recarga de NanoBots en banco integrado.")
    lines.append("-" * 60)

    report_text = "\n".join(lines)
    print("\n" + report_text + "\n")

    if filename_save:
        try:
            with open(filename_save, "w", encoding="utf-8") as f:
                f.write(report_text)
            print(f"Informe guardado en: {filename_save}")
        except Exception as e:
            print("Error guardando informe:", e)

# ---------------------------
# Interfaz principal (terminal)
# ---------------------------

def main():
    print("==============================================")
    print("  BIO_NANO RECLAIMER - SIMULACIÓN (TERMINAL)  ")
    print("==============================================")
    # crew & mission
    try:
        crew = int(input(f"Ingrese número de tripulantes (default {DEFAULT_CREW}): ") or DEFAULT_CREW)
    except:
        crew = DEFAULT_CREW
    try:
        days = int(input(f"Ingrese duración de misión en días (default {DEFAULT_MISSION_DAYS}): ") or DEFAULT_MISSION_DAYS)
    except:
        days = DEFAULT_MISSION_DAYS

    profile = seleccionar_perfil()
    bioai = seleccionar_bioai_level()

    # option to edit or map bacteria manually
    print("\n¿Deseas revisar / personalizar la asignación de bacterias por tipo de residuo? (s/n)")
    custom_map = {}
    if input("> ").strip().lower() == "s":
        print("Se mostrarán los tipos de residuo detectados en el perfil. Para cada tipo puedes seleccionar:")
        # show types
        types = list(profile["breakdown_pct"].keys())
        for t in types:
            print(f"\nTipo: {t}")
            # list available bacteria that target it
            candidates = [b for b,info in BACTERIA_LIBRARY.items() if info["target"] == t]
            if candidates:
                print(" Opciones disponibles:", ", ".join(candidates))
            else:
                print(" No hay bacterias específicas en la librería para este tipo.")
            print(" Selecciones:")
            print("  1) Usar bacteria recomendada (si existe)")
            print("  2) Ingresar nombre bacteria personalizada")
            print("  3) Mantener sin cambios (usar genérico)")
            choice = input(" Opción (1/2/3): ").strip()
            if choice == "1" and candidates:
                selected = candidates[0]
                custom_map[t] = {"name": selected, **BACTERIA_LIBRARY[selected]}
            elif choice == "2":
                name = input(" Nombre bacteria: ").strip() or f"Custom_{t}"
                ef = float(input(" Eficiencia base estimada (0.1-0.9): ") or "0.20")
                gpk = float(input(" Gramos bacterias por kg objetivo (ej.15): ") or "15")
                storage = input(" Contenedor/almacenamiento recomendado: ") or "CustomContainer"
                custom_map[t] = {"name": name, "target": t, "ef_base": ef, "bacterias_g_por_kg_target": gpk, "almacenamiento": storage}
            else:
                # keep generic
                pass

    # nanobots use
    use_nano = input("\n¿Usar Nanobots automatizados para transporte y entrega de bacterias? (s/n, default s): ").strip().lower()
    if use_nano == "" or use_nano == "s":
        use_nanobots = True
    else:
        use_nanobots = False

    # run calculation
    summary = calcular_totales(crew, days, profile, bioai, custom_bacteria_map=custom_map, use_nanobots=use_nanobots)

    # print and save
    print_report(summary)
    save = input("¿Deseas guardar el informe en un archivo .txt? (s/n): ").strip().lower()
    if save == "s":
        fname = input("Nombre de archivo (ej. informe_mision.txt): ").strip() or "informe_mision.txt"
        print_report(summary, filename_save=fname)

    print("\nFIN DE SIMULACIÓN. Gracias. Puedes usar este informe para análisis manual y ajustar parámetros para nuevas corridas.")

if __name__ == "__main__":
    main()
