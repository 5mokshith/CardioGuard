import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

// Function to handle incoming alert requests
serve(async (req) => {
  try {
    const { user_id, message, condition_severity, latitude, longitude } = await req.json();

    console.log("🚨 New Emergency Alert:", { user_id, message, condition_severity, latitude, longitude });

    // TODO: Integrate SMS & Email APIs (Twilio, SendGrid, etc.)

    return new Response(JSON.stringify({ success: true, message: "Notification sent" }), { status: 200 });
  } catch (error) {
    console.error("❌ Error processing alert:", error);
    return new Response(JSON.stringify({ success: false, error: error.message }), { status: 500 });
  }
});
