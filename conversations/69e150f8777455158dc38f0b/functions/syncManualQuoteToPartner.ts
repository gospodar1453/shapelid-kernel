import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const body = await req.json();
    const base44 = createClientFromRequest(req);
    
    const { 
      order_number,
      customer_email,
      customer_name,
      customer_phone,
      customer_address,
      total_amount,
      currency,
      items,
      quote_triggers,
      notes,
      part_data
    } = body;

    // Validate required fields
    if (!order_number || !customer_email || !customer_name) {
      return new Response(JSON.stringify({
        success: false,
        error: "Missing required fields: order_number, customer_email, customer_name"
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    if (!part_data || !part_data.file_url) {
      return new Response(JSON.stringify({
        success: false,
        error: "Missing part_data.file_url"
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    // Create Order in Superagent's own app (triggers entity automation)
    const order = await base44.entities.Order.create({
      order_number,
      customer_email,
      customer_name,
      customer_phone: customer_phone || "",
      customer_address: customer_address || "",
      status: "pending_rfq",
      total_amount: total_amount || 0,
      currency: currency || "TRY",
      items: items || [],
      payment_status: "pending",
      manual_quote: true,
      quote_triggers: quote_triggers || [],
      notes: JSON.stringify({ original_notes: notes || "", part_data })
    });

    return new Response(JSON.stringify({
      success: true,
      order_id: order.id || order._id,
      order_number: order_number,
      message: "Manual quote request created. RFQ will be synced to Partner Portal automatically."
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });

  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message || String(error)
    }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
});
