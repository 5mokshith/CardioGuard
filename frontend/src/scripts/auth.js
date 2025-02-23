import { createClient } from "@supabase/supabase-js";
import { showToast, toastTypes } from "./toastUtils.js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;
export const supabase = createClient(supabaseUrl, supabaseKey);

// Spinner and button control functions
const showSpinner = () => {
  document.querySelector(".spinner-overlay").classList.add("active");
  // Disable submit buttons while loading
  const signInBtn = document.querySelector("#sign-up-btn");
  if (signInBtn) {
    signInBtn.disabled = true;
    signInBtn.style.opacity = "0.7";
    signInBtn.style.cursor = "not-allowed";
  }
};

const hideSpinner = () => {
  document.querySelector(".spinner-overlay").classList.remove("active");
  // Re-enable submit buttons after loading
  const signInBtn = document.querySelector("#sign-up-btn");
  if (signInBtn) {
    signInBtn.disabled = false;
    signInBtn.style.opacity = "1";
    signInBtn.style.cursor = "pointer";
  }
};

// Function to transition to personal info template
const showPersonalInfoTemplate = () => {
  const container = document.querySelector(".container");
  const personalInfoTemplate = document.querySelector(
    '[data-personal-info="true"]'
  );
  const personalInfoContent = personalInfoTemplate.content.cloneNode(true);

  // Update progress bar
  const steps = document.querySelectorAll(".step");
  steps[0].classList.remove("active");
  steps[1].classList.add("active");

  // Replace current content with personal info template
  container.innerHTML = "";
  container.appendChild(personalInfoContent);
};

export async function signUpUser(email, password, userName) {
  try {
    showSpinner();
    const { data, error } = await supabase.auth.signUp({
      email: email,
      password: password,
    });

    if (error) {
      console.error("Error signing up:", error);
      hideSpinner(); // Immediately hide spinner on error
      showToast("Failed to sign up: " + error.message, toastTypes.ERROR);
      return null;
    }

    // Check if user is already registered (email exists)
    if (data?.user?.identities?.length === 0) {
      console.log("User already exists");
      hideSpinner(); // Hide spinner for existing user
      showToast(
        "Email already registered. Please sign in or use a different email.",
        toastTypes.ERROR
      );
      return null;
    }

    console.log("Sign up data:", data);
    let session = await userSignIn(email, password);

    if (!session) {
      console.error("Sign-in failed after sign-up.");
      hideSpinner(); // Hide spinner on sign-in failure
      showToast("Failed to complete signup process", toastTypes.ERROR);
      return null;
    }

    let userId = session.user.id;
    const { error: insertError } = await supabase.from("users").insert([
      {
        id: userId,
        email: email,
        name: userName,
      },
    ]);

    if (insertError) {
      console.error("Error inserting user:", insertError);
      hideSpinner(); // Hide spinner on insert error
      showToast("Failed to create user profile", toastTypes.ERROR);
      return null;
    }

    console.log("User inserted successfully");
    // Keep spinner for a short moment then show next template
    setTimeout(() => {
      hideSpinner();
      showPersonalInfoTemplate();
    }, 1000);

    return session;
  } catch (error) {
    console.error("Unexpected error during signup:", error);
    hideSpinner(); // Hide spinner on unexpected error
    showToast("An unexpected error occurred", toastTypes.ERROR);
    return null;
  }
}

export async function userSignIn(email, password) {
  try {
    showSpinner();
    const { data, error } = await supabase.auth.signInWithPassword({
      email: email,
      password: password,
    });

    if (error) {
      console.error("Error signing in:", error);
      showToast("Failed to sign in: " + error.message, toastTypes.ERROR);
      return null;
    }

    console.log("User signed in:", data.user);
    return data;
  } finally {
    hideSpinner();
  }
}
