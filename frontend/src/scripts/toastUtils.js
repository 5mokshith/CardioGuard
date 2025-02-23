// toast-utils.js

export const showToast = (message, type = "info") => {
  const toastConfig = {
    text: message,
    duration: 3000,
    close: true,
    gravity: "top",
    position: "right",
    stopOnFocus: true,
    style: {
      background:
        type === "success"
          ? "#59981A"
          : type === "error"
          ? "#DF362D"
          : type === "warning"
          ? "#FC2E20"
          : "#2196f3",
      color: "white",
      borderRadius: "8px",
      fontFamily: "'Noto Sans', sans-serif",
      fontSize: "14px",
    },
  };

  Toastify(toastConfig).showToast();
};

export const toastTypes = {
  SUCCESS: "success",
  ERROR: "error",
  WARNING: "warning",
  INFO: "info",
};
