/**
 * Bulk upload ManufacturerLead batch
 * POST /bulkUploadBatch
 */
export async function bulkUploadBatch(req) {
  const { records } = req.body;
  
  if (!Array.isArray(records) || records.length === 0) {
    return { error: "Invalid records array", status: 400 };
  }

  try {
    const uploaded = await base44.entities.ManufacturerLead.create(records);
    return {
      success: true,
      count: uploaded.length,
      ids: uploaded.map(r => r.id),
      message: `${uploaded.length} kayıt başarıyla yüklendi`
    };
  } catch (err) {
    console.error("Bulk upload error:", err);
    return { error: err.message, status: 500 };
  }
}
