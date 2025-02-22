import { userSignIn } from './auth.js';
import { supabase } from './auth.js';

const button = document.querySelector("#sign-in-btn");
button.addEventListener('click', () => {
    event.preventDefault();
    const formData = new FormData(document.querySelector("#sign-in-form"));
    let email = formData.get("email");
    let password = formData.get("password");
    userSignIn(email, password);
});

const { data, error } = await supabase.functions.invoke("alert-notifications");

if (error) {
  console.error("Error calling alert function:", error);
} else {
  console.log("Alert function executed successfully:", data);
}
