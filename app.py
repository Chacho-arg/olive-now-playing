import os
import re

import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

STREAM_URL = os.getenv(
    "STREAM_URL",
    "PEGA_AQUI_LA_URL_DEL_STREAM"
)


def get_stream_title():
    headers = {
        "Icy-MetaData": "1",
        "User-Agent": "FM-Olive-Now-Playing/1.0"
    }

    response = requests.get(
        STREAM_URL,
        headers=headers,
        stream=True,
        timeout=10
    )

    response.raise_for_status()

    metadata_interval = response.headers.get("icy-metaint")

    if not metadata_interval:
        raise RuntimeError(
            "El stream no informó el encabezado icy-metaint"
        )

    metadata_interval = int(metadata_interval)

    stream = response.raw

    # Saltar el primer bloque de audio
    stream.read(metadata_interval)

    # El siguiente byte indica el tamaño del bloque de metadata
    metadata_length_byte = stream.read(1)

    if not metadata_length_byte:
        raise RuntimeError("No se recibió metadata del stream")

    metadata_length = metadata_length_byte[0] * 16
    metadata = stream.read(metadata_length).decode(
        "utf-8",
        errors="ignore"
    )

    match = re.search(r"StreamTitle='(.*?)';", metadata)

    if not match:
        return "Metadata no disponible"

    return match.group(1).strip() or "Metadata no disponible"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/now-playing")
def now_playing():
    try:
        title = get_stream_title()

        return jsonify({
            "success": True,
            "title": title
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "title": "No se pudo consultar la radio",
            "error": str(error)
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )
