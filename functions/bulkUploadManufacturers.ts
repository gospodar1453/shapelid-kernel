import { base44 } from "@base44/functions";
import * as fs from "fs";
import * as path from "path";

export default async function bulkUploadManufacturers(request: {
  batch_number?: number;
}) {
  try {
    // Tüm kayıtları /tmp/final_upload_all_433.json'dan oku
    const filePath = "/tmp/final_upload_all_433.json";
    
    if (!fs.existsSync(filePath)) {
      return {
        success: false,
        error: "File not found",
        file: filePath
      };
    }

    const fileContent = fs.readFileSync(filePath, "utf-8");
    const allRecords = JSON.parse(fileContent);

    // Batch 100 kayıt halinde yükle
    const batchSize = 100;
    let uploadedCount = 0;
    let failedCount = 0;

    for (let i = 0; i < allRecords.length; i += batchSize) {
      const batch = allRecords.slice(i, i + batchSize);
      
      try {
        // ManufacturerLead entity'sine bulk create
        // SDK tarafından otomatik olarak yapılacak
        for (const record of batch) {
          try {
            await base44.entities.ManufacturerLead.create(record);
            uploadedCount++;
          } catch (err) {
            failedCount++;
            console.error(`Record creation failed: ${record.company_name}`, err);
          }
        }
      } catch (err) {
        console.error(`Batch ${i / batchSize} failed`, err);
      }
    }

    return {
      success: true,
      totalRecords: allRecords.length,
      uploadedCount,
      failedCount,
      message: `Bulk upload complete: ${uploadedCount} created, ${failedCount} failed`
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}
