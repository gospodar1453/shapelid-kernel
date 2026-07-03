import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    
    // Parse request body
    const body = await req.json();
    const { records } = body || {};
    
    if (!records || !Array.isArray(records)) {
      return new Response(
        JSON.stringify({ error: 'No records array provided' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    console.log(`Starting bulk upload of ${records.length} ManufacturerLead records...`);
    
    // Create records using service role to bypass RLS
    const created = await base44.asServiceRole.entities.ManufacturerLead.create(
      records
    );
    
    console.log(`✅ Successfully created ${created.length} records`);
    
    return new Response(
      JSON.stringify({
        success: true,
        created_count: created.length,
        message: `Uploaded ${created.length} records`
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (error: any) {
    console.error('Bulk upload error:', error);
    return new Response(
      JSON.stringify({ 
        error: error.message || 'Bulk upload failed'
      }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
});
