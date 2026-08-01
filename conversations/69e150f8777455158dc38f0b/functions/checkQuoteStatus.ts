import { createClientFromRequest } from 'npm:@base44/sdk@0.8.31';

Deno.serve(async (req) => {
  try {
    const body = await req.json();
    const base44 = createClientFromRequest(req);
    
    const { order_number } = body;
    
    if (!order_number) {
      return new Response(JSON.stringify({
        success: false,
        error: "Missing order_number"
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }
    
    // Find the order using service role (orders created by syncManualQuoteToPartner)
    const orderResponse = await base44.asServiceRole.entities.Order.list({
      filter: { order_number: order_number }
    });
    
    const orders = orderResponse.items || orderResponse;
    if (!orders || orders.length === 0) {
      return new Response(JSON.stringify({
        success: false,
        error: "Order not found"
      }), { status: 404, headers: { 'Content-Type': 'application/json' } });
    }
    
    const order = orders[0];
    
    // If this is not a manual quote, return the order as-is
    if (!order.manual_quote) {
      return new Response(JSON.stringify({
        success: true,
        order: {
          order_number: order.order_number,
          status: order.status,
          manual_quote: false,
          total_amount: order.total_amount,
          currency: order.currency
        },
        quotes: []
      }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    }
    
    // For manual quotes, fetch quotes from Partner Portal
    let partData = {};
    try {
      const notesObj = JSON.parse(order.notes || '{}');
      partData = notesObj.part_data || {};
    } catch(e) { /* notes might not be JSON */ }
    
    // Call Partner Portal's getQuotesForOrder function
    const partnerPortalAppId = '6a6e0ff6d6f73c86c80473eb';
    const partnerResponse = await fetch(
      `https://app.base44.com/api/apps/${partnerPortalAppId}/backend/functions/getQuotesForOrder`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          order_number: order.order_number,
          source_order_id: order.id,
          customer_email: order.customer_email
        })
      }
    );
    
    const partnerData = await partnerResponse.json();
    
    return new Response(JSON.stringify({
      success: true,
      order: {
        order_number: order.order_number,
        status: order.status,
        manual_quote: true,
        total_amount: order.total_amount,
        currency: order.currency,
        quote_triggers: order.quote_triggers || [],
        customer_name: order.customer_name,
        customer_email: order.customer_email
      },
      quotes: partnerData.quotes || [],
      rfq_number: partnerData.rfq_number || null,
      rfq_status: partnerData.rfq_status || null
    }), { status: 200, headers: { 'Content-Type': 'application/json' } });
    
  } catch (error) {
    return new Response(JSON.stringify({
      success: false,
      error: error.message || String(error)
    }), { status: 500, headers: { 'Content-Type': 'application/json' } });
  }
});
