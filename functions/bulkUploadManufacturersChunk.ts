
import json

export async function bulkUploadManufacturers(req, res) {
  const batchData = req.body.batch;
  const chunkIndex = req.body.chunkIndex || 0;
  
  if (!batchData || !Array.isArray(batchData)) {
    return res.status(400).json({ error: "batch must be an array" });
  }
  
  try {
    const ManufacturerLead = base44.entities.ManufacturerLead;
    
    // Create all records in batch
    const created = await Promise.all(
      batchData.map(record => ManufacturerLead.create(record))
    );
    
    return res.json({
      success: true,
      chunk: chunkIndex,
      uploaded: created.length,
      total_batch: batchData.length
    });
  } catch (error) {
    console.error("Upload error:", error);
    return res.status(500).json({ error: error.message });
  }
}
