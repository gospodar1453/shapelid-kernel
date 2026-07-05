import base44 from "@base44/sdk";

export default async function bulkUploadManuInBatches(req: any, res: any) {
  try {
    // batch_to_upload_mega.json dosyasını oku
    const fs = require("fs");
    const path = require("path");

    const filePath = path.join(__dirname, "../batch_to_upload_mega.json");
    if (!fs.existsSync(filePath)) {
      return res.json({
        success: false,
        error: "batch_to_upload_mega.json dosyası bulunamadı",
      });
    }

    const fileContent = fs.readFileSync(filePath, "utf-8");
    const records = JSON.parse(fileContent);

    console.log(`📦 Toplam ${records.length} kayıt yüklenmek üzere...`);

    // 50'li batch'larla yükle
    const batchSize = 50;
    let uploadedCount = 0;
    const errors = [];

    for (let i = 0; i < records.length; i += batchSize) {
      const batch = records.slice(i, Math.min(i + batchSize, records.length));

      try {
        await base44.entities.ManufacturerLead.bulkCreate(batch);
        uploadedCount += batch.length;
        console.log(
          `✅ Batch ${Math.floor(i / batchSize) + 1}: ${batch.length} kayıt yüklendi (toplam: ${uploadedCount})`
        );
      } catch (batchError: any) {
        const errMsg = `Batch ${Math.floor(i / batchSize) + 1} başarısız: ${batchError.message}`;
        console.error(errMsg);
        errors.push(errMsg);
      }
    }

    return res.json({
      success: errors.length === 0,
      uploadedCount,
      totalRecords: records.length,
      errors: errors.length > 0 ? errors : null,
      message:
        errors.length === 0
          ? `✅ Tüm ${uploadedCount} kayıt başarıyla yüklendi`
          : `⚠️ ${uploadedCount}/${records.length} kayıt yüklendi, ${errors.length} hata`,
    });
  } catch (error: any) {
    console.error("Hata:", error.message);
    return res.json({
      success: false,
      error: error.message,
    });
  }
}
