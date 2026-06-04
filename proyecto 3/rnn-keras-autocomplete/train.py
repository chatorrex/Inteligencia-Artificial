import json
import numpy as np
import tensorflow as tf
from pathlib import Path

# Configuración
ROOT = Path(__file__).resolve().parent
DATASET_PATH = ROOT.parent / "dataset_funciones_c.txt"
BLOCK_SIZE = 64  # Contexto de caracteres
BATCH_SIZE = 64
EPOCHS = 50      # Ajusta según necesites precisión

def train():
    # 1. Cargar el dataset
    if not DATASET_PATH.exists():
        print(f"Error: No se encuentra el dataset en {DATASET_PATH}")
        return

    text = DATASET_PATH.read_text(encoding="utf-8")
    chars = sorted(list(set(text)))
    vocab_size = len(chars)
    
    stoi = {c: i for i, c in enumerate(chars)}
    itos = {i: c for i, c in enumerate(chars)}

    # 2. Guardar meta.json para el servidor
    meta = {
        "block_size": BLOCK_SIZE,
        "chars": chars
    }
    (ROOT / "meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    # 3. Preparar datos de entrenamiento
    data = [stoi[c] for c in text]
    X, Y = [], []
    for i in range(0, len(data) - BLOCK_SIZE):
        X.append(data[i : i + BLOCK_SIZE])
        # El objetivo es predecir el siguiente caracter para cada posición
        Y.append(data[i + 1 : i + BLOCK_SIZE + 1])

    X = np.array(X)
    Y = np.array(Y)

    # 4. Construir Modelo RNN Vanilla (SimpleRNN)
    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(vocab_size, 64, input_length=BLOCK_SIZE),
        tf.keras.layers.SimpleRNN(128, return_sequences=True),
        tf.keras.layers.Dense(vocab_size)
    ])

    model.compile(
        optimizer="adam", 
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True)
    )

    print("Iniciando entrenamiento...")
    model.fit(X, Y, batch_size=BATCH_SIZE, epochs=EPOCHS)

    # 5. Guardar el modelo
    model.save(ROOT / "model.keras")
    print(f"Modelo guardado en {ROOT / 'model.keras'}")

if __name__ == "__main__":
    train()