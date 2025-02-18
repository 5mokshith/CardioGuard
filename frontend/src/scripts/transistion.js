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
        transitionToMultiStep();
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

const steps = [
  { attr: "data-personal-info", name: "Personal Information" },
  { attr: "data-medical-conditions-info", name: "Medical Conditions" },
  { attr: "data-lifestyle-info", name: "Lifestyle" },
  { attr: "data-emergency-info", name: "Emergency Info" }
];

let currentStepIndex = 0;
let multiStepContainer = null;

function transitionToMultiStep() {
  const mainContainer = document.querySelector("main");
  if (mainContainer) {
    mainContainer.classList.add("fade-out");
    setTimeout(() => {
      mainContainer.style.display = "none";
      multiStepContainer = document.createElement("div");
      multiStepContainer.id = "multi-step-container";
      document.body.appendChild(multiStepContainer);
      loadStep(currentStepIndex);
    }, 500);
  }
}

function loadStep(index) {
  if (!multiStepContainer) return;
  multiStepContainer.innerHTML = "";
  const stepData = steps[index];
  const template = document.querySelector(`template[${stepData.attr}="true"]`);
  if (template) {
    const clone = template.content.cloneNode(true);
    multiStepContainer.appendChild(clone);
    attachStepEventListeners();
  }
}

function attachStepEventListeners() {
  if (!multiStepContainer) return;
  const nextBtn = multiStepContainer.querySelector('button[data-tooltip="Next"]');
  const prevBtn = multiStepContainer.querySelector('button[data-tooltip="previous"]');

  if (nextBtn) {
    nextBtn.addEventListener("click", (event) => {
      event.preventDefault();
      if (validateCurrentStep(multiStepContainer)) {
        if (currentStepIndex < steps.length - 1) {
          currentStepIndex++;
          transitionStep(currentStepIndex);
        } else {
          submitAllData();
        }
      } else {
        alert("Please fill in all required fields in this section.");
      }
    });
  }
  if (prevBtn) {
    prevBtn.addEventListener("click", (event) => {
      event.preventDefault();
      if (currentStepIndex > 0) {
        currentStepIndex--;
        transitionStep(currentStepIndex);
      }
    });
  }
}

function transitionStep(newIndex) {
  multiStepContainer.classList.add("fade-out");
  setTimeout(() => {
    loadStep(newIndex);
    multiStepContainer.classList.remove("fade-out");
    multiStepContainer.classList.add("fade-in");
    setTimeout(() => {
      multiStepContainer.classList.remove("fade-in");
    }, 500);
  }, 500);
}

function validateCurrentStep(container) {
  let valid = true;
  const requiredElements = container.querySelectorAll("input[required], select[required], textarea[required]");
  requiredElements.forEach((el) => {
    if (el.value.trim() === "") {
      valid = false;
      // TODO: Display error message
      el.classList.add("input-error");
    } else {
      el.classList.remove("input-error");
    }
  });
  return valid;
}

function submitAllData() {
  // Collect data from all steps (store user input in a global object or FormData as you navigate)
  console.log("All steps completed. Submitting the combined data...");
  alert("All data validated. Form submitted!");
  // Here you can call your API to submit the combined data, or redirect as needed.
  // TODO: submission of data
}
