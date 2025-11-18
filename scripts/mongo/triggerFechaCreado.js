exports = function(changeEvent) {
  const collection = context.services.get("ClusterBD2").db("tiendaDB").collection("clientes");
  
  // Solo procesar inserciones
  if (changeEvent.operationType === "insert") {
    const doc = changeEvent.fullDocument;
    const docId = doc._id;
    
    // Actualizar el documento agregando la fecha de creación
    return collection.updateOne(
      { _id: docId },
      { 
        $set: { 
          creado: new Date() 
        } 
      }
    );
  }
};