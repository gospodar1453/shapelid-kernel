import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

interface ManufacturerRecord {
  company_name: string;
  city: string;
  email?: string;
  phone?: string;
  address?: string;
  capabilities?: string[];
  website?: string;
  source?: string;
  verification_status?: string;
  notes?: string;
  google_maps_url?: string;
  google_rating?: string;
  media_urls?: string[];
  media_description?: string;
  district?: string;
  osb_name?: string;
  invited_to_partner?: boolean;
}

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    const payload = await req.json() as { records: ManufacturerRecord[] };
    const { records } = payload;
    const errors: string[] = [];
    let successCount = 0;

    if (!records || !Array.isArray(records)) {
      return new Response(
        JSON.stringify({
          success: 0,
          failed: 0,
          errors: ['Invalid payload: records must be an array'],
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }

    // Batch insert
    for (const record of records) {
      try {
        await base44.entities.ManufacturerLead.create(record);
        successCount++;
      } catch (err: any) {
        errors.push(`${record.company_name}: ${err.message}`);
      }
    }

    return new Response(
      JSON.stringify({
        success: successCount,
        failed: records.length - successCount,
        errors: errors.slice(0, 10),
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    );
  } catch (err: any) {
    return new Response(
      JSON.stringify({ error: err.message }),
      { status: 500, headers: { 'Content-Type': 'application/json' } }
    );
  }
});
