/**
 * PayTR Direct API Integration
 * 
 * Actions:
 * - action=token: Generate payment token + form data for Direct API
 * - action=callback: Handle PayTR payment callback (must return "OK")
 * - action=cards: List saved cards (CAPI LIST)
 * - action=recurring: Recurring payment from saved card
 * - action=refund: Refund a payment
 */

const crypto = require('crypto');

// PayTR credentials from environment
const MERCHANT_ID = process.env.PAYTR_MERCHANT_ID;
const MERCHANT_KEY = process.env.PAYTR_MERCHANT_KEY;
const MERCHANT_SALT = process.env.PAYTR_MERCHANT_SALT;

// PayTR API URLs
const PAYTR_PAYMENT_URL = 'https://www.paytr.com/odeme';
const PAYTR_TOKEN_URL = 'https://www.paytr.com/odeme/api/get-token';
const PAYTR_CAPI_LIST_URL = 'https://www.paytr.com/odeme/capi/list';

// Helper: Generate HMAC-SHA256 paytr_token
function generateToken(hashStr) {
  return Buffer.from(
    crypto.createHmac('sha256', MERCHANT_KEY).update(hashStr + MERCHANT_SALT).digest()
  ).toString('base64');
}

// Helper: Verify callback hash
function verifyCallbackHash(merchantOid, status, totalAmount) {
  const hashStr = merchantOid + MERCHANT_SALT + status + totalAmount;
  const expectedHash = Buffer.from(
    crypto.createHmac('sha256', MERCHANT_KEY).update(hashStr).digest()
  ).toString('base64');
  return expectedHash;
}

// Helper: Generate unique merchant_oid
function generateMerchantOid() {
  const timestamp = Date.now();
  const random = Math.floor(Math.random() * 1000000);
  return `SHP${timestamp}${random}`;
}

module.exports = async function(req, res) {
  const action = req.query.action || (req.body && req.body.action) || '';
  
  try {
    // ============================================
    // ACTION: TOKEN — Generate payment form data
    // ============================================
    if (action === 'token') {
      const {
        email,
        payment_amount,
        user_name,
        user_address,
        user_phone,
        user_basket,
        installment_count = 0,
        currency = 'TL',
        test_mode = 0,
        non_3d = 0,
        merchant_ok_url,
        merchant_fail_url,
        utoken = '',
        store_card = 0,
        order_id
      } = req.body;
      
      // Validate required fields
      if (!email || !payment_amount || !user_basket) {
        return res.json({ status: 'error', msg: 'Missing required fields: email, payment_amount, user_basket' });
      }
      
      const merchant_oid = order_id || generateMerchantOid();
      const user_ip = req.headers['x-forwarded-for'] || req.headers['x-real-ip'] || req.connection?.remoteAddress || '127.0.0.1';
      const payment_type = 'card';
      
      // Build hash string for token
      const hash_str = MERCHANT_ID + user_ip + merchant_oid + email + payment_amount + 
                       payment_type + installment_count + currency + test_mode + non_3d;
      
      const paytr_token = generateToken(hash_str);
      
      // Build user_basket if it's an array
      let basketStr = user_basket;
      if (Array.isArray(user_basket)) {
        basketStr = Buffer.from(JSON.stringify(user_basket)).toString('base64');
      }
      
      // Return form data that frontend will use to POST to PayTR
      const formData = {
        merchant_id: MERCHANT_ID,
        paytr_token,
        user_ip,
        merchant_oid,
        email,
        payment_amount,
        payment_type,
        installment_count,
        currency,
        test_mode,
        non_3d,
        merchant_ok_url: merchant_ok_url || 'https://app.shapelid.com/order-success',
        merchant_fail_url: merchant_fail_url || 'https://app.shapelid.com/order-failed',
        user_name,
        user_address,
        user_phone,
        user_basket: basketStr,
        debug_on: 1,
      };
      
      // Card storage fields
      if (store_card) {
        formData.store_card = 1;
        if (utoken) formData.utoken = utoken;
      }
      
      return res.json({
        status: 'success',
        merchant_oid,
        post_url: PAYTR_PAYMENT_URL,
        form_data: formData
      });
    }
    
    // ============================================
    // ACTION: CALLBACK — Handle PayTR notification
    // ============================================
    if (action === 'callback') {
      const post = req.body || {};
      
      const {
        merchant_oid,
        status,
        total_amount,
        hash,
        failed_reason_code,
        failed_reason_msg,
        test_mode,
        payment_type,
        currency,
        payment_amount,
        utoken,
        ctoken
      } = post;
      
      // Verify hash
      const expectedHash = verifyCallbackHash(merchant_oid, status, total_amount);
      
      if (hash !== expectedHash) {
        // Bad hash — do not return OK, potential fraud
        return res.status(403).send('PAYTR notification failed: bad hash');
      }
      
      // Find order by merchant_oid and update
      try {
        // Read existing order
        const { Order, Payment } = await import('@base44/sdk');
        
        const orders = await Order.filter({ order_number: merchant_oid });
        
        if (orders.length > 0) {
          const order = orders[0];
          
          // Update order status
          if (status === 'success') {
            await Order.update(order.id, {
              status: 'paid',
              payment_status: 'success',
              paytr_oid: merchant_oid
            });
          } else {
            await Order.update(order.id, {
              payment_status: 'failed'
            });
          }
          
          // Create payment record
          await Payment.create({
            order_id: order.id,
            merchant_oid,
            paytr_status: status,
            total_amount: parseFloat(total_amount) / 100,
            payment_amount: payment_amount ? parseFloat(payment_amount) / 100 : null,
            payment_type: payment_type || 'card',
            utoken: utoken || '',
            ctoken: ctoken || '',
            installment_count: 0,
            currency: currency || 'TL',
            test_mode: test_mode === '1',
            failed_reason_code: failed_reason_code || '',
            failed_reason_msg: failed_reason_msg || '',
            callback_raw: post
          });
        }
      } catch (dbErr) {
        console.error('DB error in callback:', dbErr);
        // Still return OK to PayTR — we don't want retries
      }
      
      // MUST return plain text "OK"
      return res.send('OK');
    }
    
    // ============================================
    // ACTION: CARDS — List saved cards (CAPI LIST)
    // ============================================
    if (action === 'cards') {
      const { utoken } = req.body;
      
      if (!utoken) {
        return res.json({ status: 'error', msg: 'utoken is required' });
      }
      
      const user_ip = req.headers['x-forwarded-for'] || '127.0.0.1';
      
      const hash_str = MERCHANT_ID + user_ip + utoken;
      const paytr_token = generateToken(hash_str);
      
      const postData = {
        merchant_id: MERCHANT_ID,
        utoken,
        paytr_token,
        user_ip
      };
      
      // Make request to PayTR CAPI LIST
      const response = await fetch(PAYTR_CAPI_LIST_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(postData).toString()
      });
      
      const result = await response.json();
      return res.json(result);
    }
    
    // ============================================
    // ACTION: RECURRING — Recurring payment (subscription)
    // ============================================
    if (action === 'recurring') {
      const {
        email,
        payment_amount,
        user_name,
        user_address,
        user_phone,
        user_basket,
        utoken,
        ctoken,
        installment_count = 0,
        currency = 'TL',
        merchant_ok_url,
        merchant_fail_url
      } = req.body;
      
      if (!utoken || !ctoken) {
        return res.json({ status: 'error', msg: 'utoken and ctoken are required for recurring payment' });
      }
      
      const merchant_oid = generateMerchantOid();
      const user_ip = req.headers['x-forwarded-for'] || '127.0.0.1';
      const payment_type = 'card';
      const test_mode = 0;
      const non_3d = 1; // Recurring must be Non3D
      const recurring_payment = 1;
      
      const hash_str = MERCHANT_ID + user_ip + merchant_oid + email + payment_amount + 
                       payment_type + installment_count + currency + test_mode + non_3d;
      
      const paytr_token = generateToken(hash_str);
      
      const basketStr = Array.isArray(user_basket) 
        ? Buffer.from(JSON.stringify(user_basket)).toString('base64') 
        : user_basket;
      
      const formData = {
        merchant_id: MERCHANT_ID,
        paytr_token,
        user_ip,
        merchant_oid,
        email,
        payment_amount,
        payment_type,
        installment_count,
        currency,
        test_mode,
        non_3d,
        merchant_ok_url: merchant_ok_url || 'https://app.shapelid.com/subscription-success',
        merchant_fail_url: merchant_fail_url || 'https://app.shapelid.com/subscription-failed',
        user_name,
        user_address,
        user_phone,
        user_basket: basketStr,
        utoken,
        ctoken,
        recurring_payment
      };
      
      // POST to PayTR server-side
      const response = await fetch(PAYTR_PAYMENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(formData).toString()
      });
      
      const result = await response.json();
      
      return res.json({
        status: 'success',
        merchant_oid,
        paytr_response: result
      });
    }
    
    // ============================================
    // ACTION: REFUND — Refund a payment
    // ============================================
    if (action === 'refund') {
      const { merchant_oid, return_amount, reference_no } = req.body;
      
      if (!merchant_oid || !return_amount) {
        return res.json({ status: 'error', msg: 'merchant_oid and return_amount are required' });
      }
      
      const user_ip = req.headers['x-forwarded-for'] || '127.0.0.1';
      const hash_str = merchant_oid + return_amount + MERCHANT_SALT;
      const paytr_token = generateToken(hash_str);
      
      const postData = {
        merchant_id: MERCHANT_ID,
        merchant_oid,
        return_amount,
        paytr_token,
        user_ip
      };
      
      if (reference_no) postData.reference_no = reference_no;
      
      const response = await fetch('https://www.paytr.com/odeme/iade', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(postData).toString()
      });
      
      const result = await response.json();
      return res.json(result);
    }
    
    // Unknown action
    return res.json({ status: 'error', msg: 'Unknown action. Use: token, callback, cards, recurring, refund' });
    
  } catch (err) {
    console.error('PayTR integration error:', err);
    return res.json({ status: 'error', msg: err.message });
  }
};
