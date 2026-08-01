import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const body = await req.json();
    const base44 = createClientFromRequest(req);
    
    const {
      company_name,
      contact_email,
      company_phone,
      city,
      district,
      address,
      tax_id,
      tax_office,
      website,
      capabilities,
      certifications,
      materials_supported,
      equipment,
      production_types,
      machine_count,
      employee_count,
      shift_hours,
      monthly_capacity_hours,
      contact_person_name,
      contact_person_title,
      quality_process,
      google_maps_url,
      workspace_id,
      registration_status
    } = body;
    
    if (!company_name || !contact_email) {
      return new Response(JSON.stringify({
        success: false,
        error: "Missing required fields: company_name and contact_email"
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }
    
    // Create a ManufacturerLead record in the Superagent's database
    // This serves as the "kişi listesi" (person list) that the admin can access
    const lead = await base44.asServiceRole.entities.ManufacturerLead.create({
      company_name: company_name,
      phone: company_phone || '',
      address: address || '',
      city: city || '',
      district: district || '',
      osb_name: body.osb_name || '',
      website: website || '',
      email: contact_email,
      capabilities: Array.isArray(production_types) ? production_types.join(', ') : (production_types || ''),
      source: 'partner_portal_registration',
      source_url: 'partner.shapelid.com',
      verification_status: registration_status || 'pending_review',
      notes: JSON.stringify({
        tax_id: tax_id || '',
        tax_office: tax_office || '',
        materials_supported: materials_supported || [],
        equipment: equipment || '',
        certifications: certifications || [],
        machine_count: machine_count || 0,
        employee_count: employee_count || 0,
        shift_hours: shift_hours || 0,
        monthly_capacity_hours: monthly_capacity_hours || 0,
        contact_person_name: contact_person_name || '',
        contact_person_title: contact_person_title || '',
        quality_process: quality_process || '',
        google_maps_url: google_maps_url || '',
        workspace_id: workspace_id || '',
        registered_at: new Date().toISOString()
      }),
      google_maps_url: google_maps_url || '',
      google_rating: 0,
      invited_to_partner: false,
      media_urls: [],
      media_description: ''
    });
    
    return new Response(JSON.stringify({
      success: true,
      lead_id: lead.id,
      message: "Manufacturer registration recorded. Admin notified."
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message || String(error)
    }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
});
