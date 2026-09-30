import os
import sqlite3

from flask import Flask, request, jsonify
from flask_cors import CORS


# ==========================================
# CONFIGURACIÓN
# ==========================================

DB_PATH = "catalog.db"
API_KEY = os.environ.get("API_KEY", "devkey")

app = Flask(__name__)
CORS(app)


# ==========================================
# CONEXIÓN A LA BASE DE DATOS
# ==========================================

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================================
# CREAR TABLA
# ==========================================

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL CHECK(price >= 0)
            )
        """)

        conn.commit()


# Inicializar base de datos
init_db()


# ==========================================
# RUTA PRINCIPAL
# ==========================================

@app.route("/", methods=["GET"])
def inicio():
    return jsonify({
        "message": "Servidor Flask funcionando correctamente"
    })


# ==========================================
# OBTENER TODOS LOS PRODUCTOS
# GET /products
# ==========================================

@app.route("/products", methods=["GET"])
def get_products():

    conn = get_db()

    products = conn.execute("""
        SELECT id, name, price
        FROM products
        ORDER BY id
    """).fetchall()

    conn.close()

    return jsonify([dict(product) for product in products]), 200


# ==========================================
# OBTENER UN PRODUCTO POR ID
# GET /products/<id>
# ==========================================

@app.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    if product is None:
        return jsonify({
            "error": "Producto no encontrado"
        }), 404

    return jsonify(dict(product)), 200


# ==========================================
# CREAR PRODUCTO
# POST /products
# ==========================================

@app.route("/products", methods=["POST"])
def create_product():

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Debes enviar un JSON"
        }), 400

    name = data.get("name")
    price = data.get("price")

    # Validar nombre
    if name is None or str(name).strip() == "":
        return jsonify({
            "error": "El campo 'name' es obligatorio"
        }), 400

    # Validar precio
    if price is None:
        return jsonify({
            "error": "El campo 'price' es obligatorio"
        }), 400

    try:
        price = float(price)
    except (ValueError, TypeError):
        return jsonify({
            "error": "El precio debe ser un número"
        }), 400

    if price < 0:
        return jsonify({
            "error": "El precio no puede ser negativo"
        }), 400

    # Insertar producto
    conn = get_db()

    cursor = conn.execute("""
        INSERT INTO products (name, price)
        VALUES (?, ?)
    """, (str(name).strip(), price))

    conn.commit()

    product_id = cursor.lastrowid

    product = conn.execute("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    return jsonify({
        "message": "Producto creado correctamente",
        "product": dict(product)
    }), 201


# ==========================================
# ACTUALIZAR PRODUCTO
# PUT /products/<id>
# ==========================================

@app.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):

    data = request.get_json()

    if not data:
        return jsonify({
            "error": "Debes enviar un JSON"
        }), 400

    name = data.get("name")
    price = data.get("price")

    # Verificar que el producto exista
    conn = get_db()

    existing_product = conn.execute("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if existing_product is None:
        conn.close()
        return jsonify({
            "error": "Producto no encontrado"
        }), 404

    # Si no se envía nombre, conservar el anterior
    if name is None:
        name = existing_product["name"]
    else:
        name = str(name).strip()

        if name == "":
            conn.close()
            return jsonify({
                "error": "El nombre no puede estar vacío"
            }), 400

    # Si no se envía precio, conservar el anterior
    if price is None:
        price = existing_product["price"]
    else:
        try:
            price = float(price)
        except (ValueError, TypeError):
            conn.close()
            return jsonify({
                "error": "El precio debe ser un número"
            }), 400

        if price < 0:
            conn.close()
            return jsonify({
                "error": "El precio no puede ser negativo"
            }), 400

    # Actualizar
    conn.execute("""
        UPDATE products
        SET name = ?, price = ?
        WHERE id = ?
    """, (name, price, product_id))

    conn.commit()

    product = conn.execute("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    conn.close()

    return jsonify({
        "message": "Producto actualizado correctamente",
        "product": dict(product)
    }), 200


# ==========================================
# ELIMINAR PRODUCTO
# DELETE /products/<id>
# ==========================================

@app.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):

    conn = get_db()

    product = conn.execute("""
        SELECT id, name, price
        FROM products
        WHERE id = ?
    """, (product_id,)).fetchone()

    if product is None:
        conn.close()
        return jsonify({
            "error": "Producto no encontrado"
        }), 404

    conn.execute("""
        DELETE FROM products
        WHERE id = ?
    """, (product_id,))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Producto eliminado correctamente",
        "product": dict(product)
    }), 200


# ==========================================
# MANEJO DE ERRORES
# ==========================================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    return jsonify({
        "error": "Ruta no encontrada"
    }), 404


@app.errorhandler(405)
def metodo_no_permitido(error):
    return jsonify({
        "error": "Método HTTP no permitido para esta ruta"
    }), 405


# ==========================================
# INICIAR SERVIDOR
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)