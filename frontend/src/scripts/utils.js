"use strict";

document.addEventListener("click", (e) => {
  // Check if the clicked element is inside a .wrapper element
  const wrapper = e.target.closest(".wrapper");
  if (wrapper) {
    const buttonBox = wrapper.querySelector(".toggle-box");
    if (buttonBox) {
      changeButtonState({ currentTarget: buttonBox });
    }
  }
});

function changeButtonState(event) {
  const buttonBox = event.currentTarget;
  const btn = buttonBox.querySelector(".toggle-icon");
  if (!btn) return;
  
  // Get the current state (should be "true" or "false")
  let buttonState = buttonBox.getAttribute("data-active");
  
  if (buttonState === "false") {
    btn.style.left = "50%";
    buttonBox.style.background = "blue";
    buttonBox.setAttribute("data-active", "true");
  } else if (buttonState === "true") {
    btn.style.left = "15%";
    buttonBox.style.background = "#c0c0c0";
    buttonBox.setAttribute("data-active", "false");
  }
}
