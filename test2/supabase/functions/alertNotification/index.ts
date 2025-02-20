import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') || ''
const SUPABASE_ANON_KEY = Deno.env.get('SUPABASE_ANON_KEY') || ''

// For SMS - example using Twilio
const TWILIO_ACCOUNT_SID = Deno.env.get('TWILIO_ACCOUNT_SID') || ''
const TWILIO_AUTH_TOKEN = Deno.env.get('TWILIO_AUTH_TOKEN') || ''
const TWILIO_PHONE_NUMBER = Deno.env.get('TWILIO_PHONE_NUMBER') || ''

serve(async (req) => {
  try {
    const { record } = await req.json()
    
    // Initialize Supabase client with service role for internal operations
    const supabase = createClient(
      SUPABASE_URL,
      SUPABASE_ANON_KEY,
      { global: { headers: { Authorization: req.headers.get('Authorization')! } } }
    )
    
    // Get user info
    const { data: user, error: userError } = await supabase
      .from('users')
      .select('email, name')
      .eq('id', record.user_id)
      .single()
    
    if (userError) throw userError
    
    // Get emergency contacts
    const { data: contacts, error: contactsError } = await supabase
      .from('emergency_contacts')
      .select('name, phone, email, relationship')
      .eq('user_id', record.user_id)
    
    if (contactsError) throw contactsError
    
    // Process alerts
    const alertMessage = `MEDICAL ALERT: ECG anomaly detected for ${user.name}. Location: ${record.gps_latitude}, ${record.gps_longitude}. Severity: ${record.severity}`
    
    // Send notifications to all emergency contacts
    const notifications = []
    
    for (const contact of contacts) {
      // Send SMS notification
      if (contact.phone) {
        const smsResult = await sendSMS(contact.phone, alertMessage)
        notifications.push({ type: 'sms', recipient: contact.phone, status: smsResult.status })
      }
      
      // Send email notification
      if (contact.email) {
        const emailResult = await sendEmail(contact.email, 'Urgent Medical Alert', alertMessage)
        notifications.push({ type: 'email', recipient: contact.email, status: emailResult.status })
      }
    }
    
    // Update the alert record with notification status
    await supabase
      .from('alerts')
      .update({ notifications_sent: true, notification_details: notifications })
      .eq('id', record.id)
    
    return new Response(
      JSON.stringify({ success: true, message: 'Notifications sent', notifications }),
      { headers: { 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 400, headers: { 'Content-Type': 'application/json' } }
    )
  }
})

// Helper function to send SMS via Twilio
async function sendSMS(to, body) {
  try {
    const twilioEndpoint = `https://api.twilio.com/2010-04-01/Accounts/${TWILIO_ACCOUNT_SID}/Messages.json`
    
    const response = await fetch(twilioEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': `Basic ${btoa(`${TWILIO_ACCOUNT_SID}:${TWILIO_AUTH_TOKEN}`)}`
      },
      body: new URLSearchParams({
        To: to,
        From: TWILIO_PHONE_NUMBER,
        Body: body
      })
    })
    
    const result = await response.json()
    return { status: 'sent', sid: result.sid }
  } catch (error) {
    console.error('SMS sending error:', error)
    return { status: 'failed', error: error.message }
  }
}

// Helper function to send email
// This is a placeholder - you'd implement this using a service like SendGrid or Resend
async function sendEmail(to, subject, body) {
  // Replace with actual email service integration
  console.log(`Would send email to ${to} with subject "${subject}"`)
  return { status: 'sent' }
}