

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
import { SMTPClient } from "https://deno.land/x/denomailer@1.6.0/mod.ts";

// Environment variable type definitions
interface EnvConfig {
  SUPABASE_URL: string;
  SUPABASE_SERVICE_ROLE_KEY: string;
  SMTP_HOSTNAME: string;
  SMTP_PORT: number;
  SMTP_USERNAME: string;
  SMTP_PASSWORD: string;
}

const ENV: EnvConfig = {
  SUPABASE_URL: Deno.env.get("SUPABASE_URL") ?? "",
  SUPABASE_SERVICE_ROLE_KEY: Deno.env.get("SUPABASE_SERVICE_ROLE_KEY") ?? "",
  SMTP_HOSTNAME: Deno.env.get("SMTP_HOSTNAME") ?? "smtp.gmail.com",
  SMTP_PORT: Number(Deno.env.get("SMTP_PORT")) || 587,
  SMTP_USERNAME: Deno.env.get("SMTP_USERNAME") ?? "",
  SMTP_PASSWORD: Deno.env.get("SMTP_PASSWORD") ?? ""
};

// Ensure FROM_EMAIL is allowed by your SMTP provider.
// For some providers it must match SMTP_USERNAME.
const FROM_EMAIL = "deepalert743@gmail.com";

// Type definitions for our app
interface User {
  email: string;
  name: string;
}

interface EmergencyContact {
  name: string;
  email: string;
  phone: string;
  relationship: string;
}

interface AlertRecord {
  id: string;
  user_id: string;
  severity: string;
  gps_latitude: number;
  gps_longitude: number;
}

interface NotificationResults {
  successes: number;
  failures: number;
  errors: string[];
}

function validateEnvironment(): void {
  const missing = Object.entries(ENV)
    .filter(([_, value]) => !value)
    .map(([key]) => key);
  if (missing.length > 0) {
    console.warn(`Warning: Missing environment variables: ${missing.join(", ")}`);
  }
}

function generateEmailContent(user: User, record: AlertRecord): string {
  // Return a template literal immediately after "return" to avoid accidental semicolon insertion.
  return `
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #d32f2f;">⚠️ Urgent Medical Alert</h2>
      <div style="background-color: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
        <p style="margin: 10px 0;"><strong>Status:</strong> ECG Anomaly Detected</p>
        <p style="margin: 10px 0;"><strong>Patient:</strong> ${user.name}</p>
        <p style="margin: 10px 0;"><strong>Severity:</strong> ${record.severity}</p>
        <p style="margin: 10px 0;"><strong>Location:</strong> ${record.gps_latitude}, ${record.gps_longitude}</p>
        <p style="margin: 10px 0;"><strong>Time:</strong> ${new Date().toISOString()}</p>
      </div>
      <p style="color: #666; font-size: 0.9em;">This is an automated alert. Please take immediate action if required.</p>
    </div>
  `;
}

async function sendEmail(to: string, subject: string, htmlContent: string): Promise<void> {
  const client = new SMTPClient({
    connection: {
      hostname: ENV.SMTP_HOSTNAME,
      port: ENV.SMTP_PORT,
      tls: true,
      auth: {
        username: ENV.SMTP_USERNAME,
        password: ENV.SMTP_PASSWORD,
      },
    },
  });

  try {
    const trimmedContent = htmlContent.trim();
    console.log("Sending email with content:", trimmedContent);

    await client.send({
      from: FROM_EMAIL,
      to: to,
      subject: subject,
      // Only the HTML property is used.
      html: trimmedContent,
    });
    
    console.log(`Email sent successfully to ${to}`);
  } catch (error) {
    console.error("Failed to send email:", error);
    throw error;
  } finally {
    await client.close();
  }
}

async function getUser(supabase: any, userId: string): Promise<User> {
  const { data, error } = await supabase
    .from("users")
    .select("email, name")
    .eq("id", userId)
    .single();

  if (error) throw error;
  return data;
}

async function getEmergencyContacts(supabase: any, userId: string): Promise<EmergencyContact[]> {
  const { data, error } = await supabase
    .from("emergency_contacts")
    .select("name, email, phone, relationship")
    .eq("user_id", userId);

  if (error) throw error;
  return data;
}

async function updateAlertStatus(supabase: any, alertId: string, results: NotificationResults): Promise<void> {
  try {
    const { error } = await supabase
      .from("alerts")
      .update({
        notifications_sent: results.successes > 0
      })
      .eq("id", alertId);
    if (error) throw error;
  } catch (error) {
    console.error("Failed to update alert status:", error);
    // Continue execution even if update fails.
  }
}

serve(async (req) => {
  try {
    validateEnvironment();

    const { record }: { record: AlertRecord } = await req.json();

    const supabase = createClient(
      ENV.SUPABASE_URL,
      ENV.SUPABASE_SERVICE_ROLE_KEY,
      { auth: { persistSession: false } }
    );

    const [user, contacts] = await Promise.all([
      getUser(supabase, record.user_id),
      getEmergencyContacts(supabase, record.user_id)
    ]);

    const subject = "Urgent Medical Alert";
    const htmlContent = generateEmailContent(user, record);

    const results: NotificationResults = {
      successes: 0,
      failures: 0,
      errors: []
    };

    // Send notifications sequentially
    for (const contact of contacts) {
      if (!contact.email) continue;
      try {
        await sendEmail(contact.email, subject, htmlContent);
        results.successes++;
        console.log(`Email notification sent to ${contact.name} at ${contact.email}`);
      } catch (error) {
        results.failures++;
        results.errors.push(`Failed to notify ${contact.name}: ${error.message}`);
      }
    }

    // Update alert status (but do not fail if this update fails)
    await updateAlertStatus(supabase, record.id, results);

    return new Response(
      JSON.stringify({
        success: results.successes > 0,
        message: `Email notifications sent to ${results.successes} contacts. SMS notifications are disabled.`,
        details: results
      }),
      { headers: { "Content-Type": "application/json" } }
    );
  } catch (error) {
    console.error("Error in alert notification:", error);
    return new Response(
      JSON.stringify({ success: false, error: error.message }),
      { status: 500, headers: { "Content-Type": "application/json" } }
    );
  }
});
