
"use strict";

import { supabase } from "./auth.js";
import { showToast, toastTypes } from "../scripts/toastUtils.js";

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
    if (!Array.isArray(emergencyContacts) || emergencyContacts.length === 0) {
      emergencyContacts = [];
    }

    // Format emergency contacts to include user_id
    const formattedContacts = emergencyContacts.map(contact => ({
      user_id: userId,
      ...contact
    }));

    // Insert multiple emergency contacts in a single query
    const { error: contactError } = await supabase
      .from("emergency_contacts")
      .insert(formattedContacts);

    if (contactError) throw contactError;

    showToast("Profile information saved successfully!", toastTypes.SUCCESS);
    return { success: true, message: "All data submitted successfully!" };
  } catch (error) {
    console.error("Error inserting user data:", error.message);
    showToast("Error saving profile: " + error.message, toastTypes.ERROR);
    return { success: false, message: error.message };
  }
}     

export { insertUserData };
