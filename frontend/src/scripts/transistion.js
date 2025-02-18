import { signUpUser, userSignIn } from './auth.js';

document.addEventListener("DOMContentLoaded", () => {
  const signUpBtn = document.querySelector("#sign-up-btn");
  const signInBtn = document.querySelector("#sign-in-btn");

  if (signUpBtn) {
    signUpBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      const form = document.getElementById("sign-up-form");
      const formData = new FormData(form);
      const email = formData.get("email");
      const password = formData.get("password");
      const userName = formData.get("username");

      const session = await signUpUser(email, password, userName);
      if (session) {
        transitionToNextStep();
      }
    });
  }

  if (signInBtn) {
    signInBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      const form = document.getElementById("sign-in-form");
      const formData = new FormData(form);
      const email = formData.get("email");
      const password = formData.get("password");

      const session = await userSignIn(email, password);
      if (session) {
        window.location.replace("/index.html");
      }
    });
  }
});

function transitionToNextStep() {
  // Select the main container (the <main> element)
  const mainContainer = document.querySelector("main");
  // Select the personal info template (using its data attribute)
  const template = document.querySelector("template[data-personal-info='true']");

  if (mainContainer && template) {
    // Add fade-out class to main container
    mainContainer.classList.add("fade-out");

    // After the fade-out transition, remove the main content and insert the new template
    setTimeout(() => {
      mainContainer.style.display = "none";

      // Clone the personal info template
      const personalInfoClone = template.content.cloneNode(true);
      // Append the cloned content to the body (or to another container if preferred)
      document.body.appendChild(personalInfoClone);

      // Optionally add a fade-in class to the newly inserted container
      const personalInfoContainer = document.querySelector(".container-personal-info");
      if (personalInfoContainer) {
        personalInfoContainer.classList.add("fade-in");
      }
    }, 500); // Adjust timing to match your CSS transition duration
  }
}
