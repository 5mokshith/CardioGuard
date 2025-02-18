"use strict"
const buttonBoxes = document.querySelectorAll(".toggle-box");
const btns = document.querySelectorAll(".toggle-icon");
const wrappers = document.querySelectorAll(".wrapper");

/* This is for if this same file i used for another page then this prevents from crashing */
if (wrappers.length > 0) {
    wrappers.forEach((wrapper) => {
        wrapper.addEventListener("click", function (event) {
            const buttonBox = wrapper.querySelector(".toggle-box");
            changeButtonState({ currentTarget: buttonBox });
        });
    });
}
function changeButtonState(event) {
  const buttonBox = event.currentTarget;
  const btn = buttonBox.querySelector(".toggle-icon");
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