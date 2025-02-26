"use strict";

document.addEventListener("click", (e) => {
  // Check if the clicked element is inside a .wrapper element
  const wrapper = e.target.closest(".wrapper");
  if (wrapper) {
    const toggleBox = wrapper.querySelector(".toggle-box");
    if (toggleBox) {
      changeButtonState({ currentTarget: toggleBox });
      // Also update the hidden checkbox (if present)
      const hiddenCheckbox = wrapper.querySelector("input[type='checkbox']");
      if (hiddenCheckbox) {
        hiddenCheckbox.checked = toggleBox.getAttribute("data-active") === "true";
      }
    }
  }
});

function changeButtonState(event) {
  const buttonBox = event.currentTarget;
  const btn = buttonBox.querySelector(".toggle-icon");
  if (!btn) return;
  
  // Get the current state ("true" or "false")
  let state = buttonBox.getAttribute("data-active");
  if (state === "false") {
    btn.style.left = "50%";
    buttonBox.style.background = "blue";
    buttonBox.setAttribute("data-active", "true");
  } else {
    btn.style.left = "15%";
    buttonBox.style.background = "#c0c0c0";
    buttonBox.setAttribute("data-active", "false");
  }
}


// /* Function to add more emergency contacts */
// document.addEventListener("click", (e) => {
//   if (e.target && e.target.id === "add_more_contacts") {
//     e.preventDefault();
//     // Find the first contact block as a template
//     const templateBlock = multiStepContainer.querySelector('.emergency-contact-block');
//     if (templateBlock) {
//       // Clone the block and clear its input values
//       const clone = templateBlock.cloneNode(true);
//       clone.querySelectorAll("input").forEach(input => input.value = "");
//       clone.querySelector("select").selectedIndex = 0;
//       // Append the clone to the container for additional contacts
//       document.querySelector("#additional-contacts").appendChild(clone);
//     }
//   }
// });

const body = document.body;
body.addEventListener("mousemove", (e) => {
  const x = e.clientX / window.innerWidth;
  const y = e.clientY / window.innerHeight;
  const scale = 1 + (x + y) / 10;
  body.style.backgroundSize = `${scale * 100}%`;
  
  body.style.backgroundPosition = `${x * 80}% ${y * 80}%`;
  body.style.transition = "all 0.5s ease";
});



export function displayMessage(message,error = false) {
  let body = document.body;
  let messageContainer = document.createElement("div");
  messageContainer.classList.add("message-container");
  let messageElement = document.createElement("p");
  messageElement.innerText = message;
  messageContainer.append(message);
  body.appendChild(messageContainer);
  if(error){
    messageContainer.style.backgroundColor = "red";
  }
  setTimeout(() => {
    messageContainer.remove();
  }, 3000);
}


export function showLoadingAnimation() {
  const loader = document.querySelector('.loader');
  loader.style.display = "block"
  loader.dataset.dataActive = "true";
}


export function hideLoadingAnimation() {
  const loader = document.querySelector('.loader');
  loader.style.display = "none"
  loader.dataset.dataActive = "false";
}
