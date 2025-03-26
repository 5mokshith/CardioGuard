import { signUpUser, userSignIn, supabase } from './auth.js';
import { insertUserData } from './sendUserData.js';
import { showLoadingAnimation, hideLoadingAnimation, displayMessage } from './utils.js';

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
      const username = formData.get("username");

      try {
        showLoadingAnimation();
        const session = await signUpUser(email, password, username);
        if (session) {
          transitionToMultiStep();
        }
      } catch (error) {
        console.error("Sign up error:", error);
        displayMessage("Error during sign up. Please try again.", true);
      } finally {
        hideLoadingAnimation();
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

      try {
        showLoadingAnimation();
        const session = await userSignIn(email, password);
        if (session) {
          window.location.replace("./src/markup/dashboard.html");
        }
      } catch (error) {
        console.error("Sign in error:", error);
        displayMessage("Error during sign in. Please try again.", true);
      } finally {
        hideLoadingAnimation();
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
let collectedData = {
  personalInfo: {},
  medicalInfo: {},
  lifestyleInfo: {},
  emergencyContacts: []
};

function updateProgressBar() {
  const progressBar = document.querySelector('.progress-bar');
  const steps = document.querySelectorAll('.step');
  const progressWidth = ((currentStepIndex + 1) / steps.length) * 100;
  
  if (progressBar) {
    progressBar.style.width = `${progressWidth}%`;
  }
  
  steps.forEach((step, index) => {
    if (index <= currentStepIndex) {
      step.classList.add('active');
    } else {
      step.classList.remove('active');
    }
  });
}

function transitionToMultiStep() {
  const mainContainer = document.querySelector('main');
  if (mainContainer) {
    mainContainer.classList.add('fade-out');
    setTimeout(() => {
      mainContainer.style.display = 'none';
      multiStepContainer = document.createElement('div');
      multiStepContainer.id = 'multi-step-container';
      document.body.appendChild(multiStepContainer);
      
      // Add progress bar
      const progressHTML = `
        <div class="progress-container">
          <div class="progress-bar"></div>
          <div class="steps">
            ${steps.map((_, i) => `
              <div class="step ${i === 0 ? 'active' : ''}">${i + 1}</div>
            `).join('')}
          </div>
        </div>
      `;
      multiStepContainer.innerHTML = progressHTML;
      
      loadStep(currentStepIndex);
      updateProgressBar();
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
    preloadStepData(stepData.attr);
    attachStepEventListeners();
  }
}

function attachStepEventListeners() {
  if (!multiStepContainer) return;
  const nextBtn = multiStepContainer.querySelector('button[data-tooltip="Next"]');
  const prevBtn = multiStepContainer.querySelector('button[data-tooltip="Previous"]');

  if (nextBtn) {
    nextBtn.addEventListener("click", async (event) => {
      event.preventDefault();
      if (validateCurrentStep(multiStepContainer)) {
        storeStepData();
        if (currentStepIndex < steps.length - 1) {
          currentStepIndex++;
          transitionStep(currentStepIndex);
        } else {
          // Disable button to prevent duplicate submissions
          nextBtn.disabled = true;
          showLoadingAnimation();
          await submitAllData();
          hideLoadingAnimation();
        }
      } else {
        displayMessage("Please fill in all required fields in this section.", true);
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
  multiStepContainer.classList.add('fade-out');
  setTimeout(() => {
    loadStep(newIndex);
    updateProgressBar();
    multiStepContainer.classList.remove('fade-out');
    multiStepContainer.classList.add('fade-in');
    setTimeout(() => {
      multiStepContainer.classList.remove('fade-in');
    }, 500);
  }, 500);
}

function validateCurrentStep(container) {
  let valid = true;
  const requiredElements = container.querySelectorAll("input[required], select[required], textarea[required]");
  requiredElements.forEach((el) => {
    if (!el.checkValidity()) {
      valid = false;
      el.reportValidity();
      el.classList.add("input-error");
    } else {
      el.classList.remove("input-error");
    }
  });
  return valid;
}

function storeStepData() {
  const stepData = steps[currentStepIndex];

  if (stepData.attr === "data-emergency-info") {
    // Clear previous emergency contacts in case of re-entry
    collectedData.emergencyContacts = [];

    // Get each emergency contact block
    const contactBlocks = multiStepContainer.querySelectorAll('.emergency-contact-block');
    contactBlocks.forEach(block => {
      const newContact = {
        name: block.querySelector('input[name="emergency_full_name"]').value,
        phone: block.querySelector('input[name="emergency_phone"]').value,
        relationship: block.querySelector('select[name="relationship"]').value,
        email: block.querySelector('input[name="emergency_email"]') 
                ? block.querySelector('input[name="emergency_email"]').value 
                : ""
      };
      collectedData.emergencyContacts.push(newContact);
    });
  } else {
    // For other steps, collect data as before:
    const formElements = multiStepContainer.querySelectorAll("input, select, textarea");
    let dataObj = {};
    formElements.forEach((el) => {
      if (el.type === "checkbox") {
        dataObj[el.name] = el.checked;
      } else {
        dataObj[el.name] = el.value;
      }
    });

    if (stepData.attr === "data-personal-info") {
      if (dataObj.hasOwnProperty("name")) {
        delete dataObj.name;
      }
      collectedData.personalInfo = dataObj;
    } else if (stepData.attr === "data-medical-conditions-info") {
      collectedData.medicalInfo = dataObj;
    } else if (stepData.attr === "data-lifestyle-info") {
      collectedData.lifestyleInfo = dataObj;
    } else {
      console.warn("Unrecognized step:", stepData.attr);
    }
  }
}

function preloadStepData(stepAttr) {
  let dataObj;
  if (stepAttr === "data-personal-info") {
    dataObj = collectedData.personalInfo;
  } else if (stepAttr === "data-medical-conditions-info") {
    dataObj = collectedData.medicalInfo;
  } else if (stepAttr === "data-lifestyle-info") {
    dataObj = collectedData.lifestyleInfo;
  } else if (stepAttr === "data-emergency-info") {
    dataObj = collectedData.emergencyContacts[0] || {};
  }
  if (dataObj) {
    Object.keys(dataObj).forEach((key) => {
      const input = multiStepContainer.querySelector(`[name="${key}"]`);
      if (input) {
        if (input.type === "checkbox") {
          input.checked = dataObj[key];
        } else {
          input.value = dataObj[key];
        }
      }
    });
  }
}

async function submitAllData() {
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) {
    displayMessage("User not authenticated. Please log in again.", true);
    return;
  }
  console.log("Submitting data for user:", user.id);
  const response = await insertUserData(
    user.id,
    collectedData.personalInfo,
    collectedData.medicalInfo,
    collectedData.lifestyleInfo,
    collectedData.emergencyContacts
  );
  if (response.success) {
    displayMessage("All data successfully submitted!");
    window.location.replace("./src/markup/dashboard.html");
  } else {
    displayMessage("Error: " + response.message, true);
  }
}

/* Function to add more emergency contacts */
document.addEventListener("click", (e) => {
  if (e.target && e.target.id === "add_more_contacts") {
    e.preventDefault();
    // Find the first contact block as a template
    const templateBlock = multiStepContainer.querySelector('.emergency-contact-block');
    if (templateBlock) {
      // Clone the block and clear its input values
      const clone = templateBlock.cloneNode(true);
      clone.querySelectorAll("input").forEach(input => input.value = "");
      clone.querySelector("select").selectedIndex = 0;
      // Append the clone to the container for additional contacts
      document.querySelector("#additional-contacts").appendChild(clone);
    }
  }
});