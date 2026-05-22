"""
fix_mujer_sombrero.py — Corrige el artwork 'Mujer en un Sombrero' en la DB del Pi.
Ejecutar en el RPi5:
    cd /home/pi/pixartek
    python3 fix_mujer_sombrero.py
"""
import sqlite3, json, os, shutil

# ── CONFIG ──────────────────────────────────────────────────────────────────
DB_PATH    = "/home/pi/pixartek/backend/pixartek.db"
PUBLIC_SRC = "/home/pi/pixartek/frontend/public/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES"
STANDALONE = "/home/pi/pixartek/frontend/.next/standalone/public/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES"
# ────────────────────────────────────────────────────────────────────────────

STAGES = [
    {
        "number": 1,
        "title": "Fondo Azul y Contorno",
        "description": "Pinta el fondo azul cielo y traza los contornos principales de la figura.",
        "duration_min": 17,
        "image": "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa1.png",
        "colors": ["Azul Cielo", "Blanco"],
        "materials": ["Pintura acrílica azul", "Agua"],
        "brushes": ["Brocha plana grande", "Pincel fino"],
        "objective": "Establecer el fondo y los contornos base del retrato",
    },
    {
        "number": 2,
        "title": "Sombrero Morado",
        "description": "Rellena el sombrero con tono morado violáceo.",
        "duration_min": 17,
        "image": "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa2.png",
        "colors": ["Morado", "Violeta"],
        "materials": ["Pintura acrílica morada", "Agua"],
        "brushes": ["Brocha redonda mediana", "Esponja"],
        "objective": "Pintar el sombrero característico con tono morado",
    },
    {
        "number": 3,
        "title": "Rostro Verde",
        "description": "Aplica el tono verde al rostro y elementos curvos del retrato.",
        "duration_min": 17,
        "image": "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa3.png",
        "colors": ["Verde Fresco", "Verde Oscuro"],
        "materials": ["Pintura acrílica verde", "Agua"],
        "brushes": ["Brocha redonda pequeña", "Pincel de punta"],
        "objective": "Definir el rostro y elementos curvos con tono verde",
    },
    {
        "number": 4,
        "title": "Cabello y Sombras Negras",
        "description": "Pinta el cabello y las sombras profundas en negro.",
        "duration_min": 17,
        "image": "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa4.png",
        "colors": ["Negro Profundo", "Gris Oscuro"],
        "materials": ["Pintura acrílica negra", "Agua"],
        "brushes": ["Brocha fina pequeña", "Pincel de punta aguda"],
        "objective": "Añadir cabello y sombras que dan profundidad al retrato",
    },
    {
        "number": 5,
        "title": "Cuerpo Azul",
        "description": "Completa el cuerpo y hombros con tono azul intenso.",
        "duration_min": 17,
        "image": "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa5.png",
        "colors": ["Azul Intenso", "Azul Oscuro"],
        "materials": ["Pintura acrílica azul", "Agua"],
        "brushes": ["Brocha plana mediana", "Rodillo pequeño"],
        "objective": "Completar el cuerpo y dar el toque final al retrato",
    },
]

def update_db():
    print(f"[DB] Abriendo: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    cur.execute("SELECT id FROM artworks WHERE id='mujer-sombrero'")
    exists = cur.fetchone()

    if exists:
        cur.execute(
            "UPDATE artworks SET stages=?, image=? WHERE id='mujer-sombrero'",
            (json.dumps(STAGES), "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa1.png")
        )
        print("[DB] Artwork actualizado.")
    else:
        cur.execute(
            """INSERT INTO artworks (id, title, artist, year, difficulty, duration_min, color, image, tags, stages)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                "mujer-sombrero", "Mujer en un Sombrero", "Desconocido", 2026,
                "intermediate", 85, "#8B4513",
                "/artworks/MUJER-EN-UN-SOMBRERO-DIVISIONES/Etapa1.png",
                json.dumps(["retrato", "mujer", "sombrero", "moda"]),
                json.dumps(STAGES),
            )
        )
        print("[DB] Artwork insertado.")

    conn.commit()

    # Verificar
    cur.execute("SELECT stages FROM artworks WHERE id='mujer-sombrero'")
    stages = json.loads(cur.fetchone()[0])
    for s in stages:
        print(f"  ✓ Etapa {s['number']}: {s['title']} → {s['image']}")
    conn.close()


def copy_images():
    os.makedirs(STANDALONE, exist_ok=True)
    if not os.path.isdir(PUBLIC_SRC):
        print(f"[IMG] ADVERTENCIA: {PUBLIC_SRC} no existe. Copia las imágenes manualmente.")
        return
    for i in range(1, 6):
        src  = os.path.join(PUBLIC_SRC, f"Etapa{i}.png")
        dst  = os.path.join(STANDALONE, f"Etapa{i}.png")
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"[IMG] ✓ Etapa{i}.png → standalone")
        else:
            print(f"[IMG] ✗ No encontrado: {src}")


if __name__ == "__main__":
    update_db()
    copy_images()
    print("\n✅ Listo. Reinicia el frontend: sudo systemctl restart pixartek-frontend")
