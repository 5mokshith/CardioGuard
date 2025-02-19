
"use strict";

import { supabase } from "./auth.js";

async function insertUserData(userId, personalInfo, medicalInfo, lifestyleInfo, emergencyContacts) {
  try {

    console.log("Final medicalInfo:", medicalInfo); // Debugging log

    // Insert into Personal Info
    const { error: personalError } = await supabase
      .from("personal_info")
      .insert([{ user_id: userId, ...personalInfo }]);
    if (personalError) throw personalError;

    // Insert into Medical Info
    const { error: medicalError } = await supabase
      .from("medical_info")
      .insert([{ user_id: userId, ...medicalInfo }]);
    if (medicalError) throw medicalError;

    // Insert into Lifestyle Info
    const { error: lifestyleError } = await supabase
      .from("lifestyle")
      .insert([{ user_id: userId, ...lifestyleInfo }]);
    if (lifestyleError) throw lifestyleError;

    // Ensure emergencyContacts is an array
    if (!Array.isArray(emergencyContacts)) {
      emergencyContacts = [];
    }

    // Insert Emergency Contacts
    for (let contact of emergencyContacts) {
      const { error: contactError } = await supabase
        .from("emergency_contacts")
        .insert([{ user_id: userId, ...contact }]);
      if (contactError) throw contactError;
    }

    return { success: true, message: "All data submitted successfully!" };
  } catch (error) {
    console.error("Error inserting user data:", error.message);
    return { success: false, message: error.message };
  }
}

export { insertUserData };
