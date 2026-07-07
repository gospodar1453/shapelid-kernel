import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    
    // Read batch files
    const part1Path = '/app/batch_part1.json';
    const part2Path = '/app/batch_part2.json';
    
    let allRecords = [];
    
    // Read files using Deno
    try {
      const part1Data = await Deno.readTextFile(part1Path);
      const part1 = JSON.parse(part1Data);
      allRecords = allRecords.concat(part1);
    } catch (e) {
      console.log('Part 1 not found:', e.message);
    }
    
    try {
      const part2Data = await Deno.readTextFile(part2Path);
      const part2 = JSON.parse(part2Data);
      allRecords = allRecords.concat(part2);
    } catch (e) {
      console.log('Part 2 not found:', e.message);
    }
    
    if (allRecords.length === 0) {
      return new Response(JSON.stringify({ 
        success: false, 
        error: 'No batch files found', 
        uploaded: 0 
      }), { status: 400 });
    }
    
    // Upload records
    let uploadedCount = 0;
    const chunkSize = 50;
    
    for (let i = 0; i < allRecords.length; i += chunkSize) {
      const chunk = allRecords.slice(i, Math.min(i + chunkSize, allRecords.length));
      
      try {
        const result = await base44.entities.ManufacturerLead.createMany(chunk);
        uploadedCount += chunk.length;
        console.log(`Uploaded chunk: ${uploadedCount}/${allRecords.length}`);
      } catch (error) {
        console.error(`Error uploading chunk at index ${i}:`, error);
        return new Response(JSON.stringify({ 
          success: false, 
          error: `Upload failed at chunk ${Math.floor(i/chunkSize)}`, 
          uploaded: uploadedCount,
          message: String(error)
        }), { status: 500 });
      }
    }
    
    return new Response(JSON.stringify({
      success: true,
      uploaded: uploadedCount,
      total: allRecords.length,
      message: `Successfully uploaded ${uploadedCount} ManufacturerLead records`
    }));
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: String(error),
      uploaded: 0
    }), { status: 500 });
  }
});
