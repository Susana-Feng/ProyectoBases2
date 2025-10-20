use tiendaDB;

// =======================
// Colección: clientes
// =======================
db.createCollection("clientes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nombre", "email", "genero", "pais", "preferencias", "creado"],
      properties: {
        nombre: { bsonType: "string", description: "Nombre del cliente" },
        email: { bsonType: "string", pattern: "^.+@.+\\..+$", description: "Correo válido" },
        genero: {
          enum: ["Masculino", "Femenino", "Otro"],
          description: "Debe ser Masculino, Femenino u Otro"
        },
        pais: { bsonType: "string", description: "Código de país" },
        preferencias: {
          bsonType: "object",
          required: ["canal"],
          properties: {
            canal: {
              bsonType: ["array"],
              items: { enum: ["WEB", "TIENDA"] },
              description: "Lista de canales permitidos"
            }
          }
        },
        creado: { bsonType: "date", description: "Fecha de creación" }
      }
    }
  }
});

// =======================
// Colección: productos
// =======================
db.createCollection("productos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["codigo_mongo", "nombre", "categoria", "equivalencias"],
      properties: {
        codigo_mongo: { bsonType: "string", description: "Código interno" },
        nombre: { bsonType: "string", description: "Nombre del producto" },
        categoria: { bsonType: "string", description: "Categoría del producto" },
        equivalencias: {
          bsonType: "object",
          properties: {
            sku: { bsonType: ["string", "null"], description: "Código SKU (opcional)" },
            codigo_alt: { bsonType: ["string", "null"], description: "Código alterno (opcional)" }
          }
        }
      }
    }
  }
});

// =======================
// Colección: ordenes
// =======================
db.createCollection("ordenes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cliente_id", "fecha", "canal", "moneda", "total", "items"],
      properties: {
        cliente_id: { bsonType: "objectId", description: "Referencia a cliente" },
        fecha: { bsonType: "date", description: "Fecha de la orden" },
        canal: { enum: ["WEB", "TIENDA"], description: "Canal de venta" },
        moneda: { enum: ["CRC", "USD"], description: "Moneda usada" },
        total: { bsonType: "int", minimum: 0, description: "Total en colones" },
        items: {
          bsonType: "array",
          minItems: 1,
          items: {
            bsonType: "object",
            required: ["producto_id", "cantidad", "precio_unit"],
            properties: {
              producto_id: { bsonType: "objectId", description: "Referencia a producto" },
              cantidad: { bsonType: "int", minimum: 1, description: "Cantidad de unidades" },
              precio_unit: { bsonType: "int", minimum: 0, description: "Precio unitario" }
            }
          }
        },
        metadatos: {
          bsonType: ["object", "null"],
          properties: {
            cupon: { bsonType: "string", description: "Código de cupón aplicado" }
          }
        }
      }
    }
  }
});
