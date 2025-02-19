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
