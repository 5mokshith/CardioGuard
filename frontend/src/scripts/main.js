import { supabase } from "./auth.js";

function initializeSupabase() {
  return supabase;
}

async function say() {
  console.log(await supabase.auth.getSession());
}

async function loadAllUserData(user_id) {
  try {
    const [
      { data: user },
      { data: personalInfo },
      { data: medicalInfo },
      { data: lifestyle },
      { data: emergencyContactsData },
    ] = await Promise.all([
      supabase.from("users").select("*").eq("id", user_id).single(),
      supabase
        .from("personal_info")
        .select("*")
        .eq("user_id", user_id)
        .single(),
      supabase.from("medical_info").select("*").eq("user_id", user_id).single(),
      supabase.from("lifestyle").select("*").eq("user_id", user_id).single(),
      supabase.from("emergency_contacts").select("*").eq("user_id", user_id),
    ]);

    if (
      !user ||
      !personalInfo ||
      !medicalInfo ||
      !lifestyle ||
      !Array.isArray(emergencyContactsData)
    ) {
      throw new Error(
        "Could not fetch user data or emergencyContacts is not an array"
      );
    }

    updateProfileHeaders(user.name);
    updatePersonalInfo(user, personalInfo);
    updateMedicalInfo(medicalInfo);
    updateLifestyleInfo(lifestyle);
    updateEmergencyContacts(emergencyContactsData);
  } catch (error) {
    console.error("Error in loadAllUserData:", error);
    throw error;
  }
}

function updateProfileHeaders(userName) {
  document.querySelector(
    ".sidebar-header h2"
  ).textContent = `${userName}'s Portal`;
  document.querySelector(".sidebar-nav-container h3").textContent = userName;
  document.querySelector(".user-info span").textContent = userName;
}

function updatePersonalInfo(user, personalInfo) {
  const container = document.querySelector(
    "#personal-info-section .sidebar-section-content"
  );

  if (!container) return;

  container.innerHTML = `
        <div class="data-item">
            <span class="data-label">Full Name</span>
            <span class="data-value">${user.name}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Email</span>
            <span class="data-value">${user.email}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Date of Birth</span>
            <span class="data-value">${new Date(
              personalInfo.dob
            ).toLocaleDateString()}</span>
        </div>
        <div class="data-item">
            <span class="data-label">Blood Type</span>
            <span class="data-value">${
              personalInfo.blood_type || "Not specified"
            }</span>
        </div>
        <div class="data-item">
            <span class="data-label">Height</span>
            <span class="data-value">${
              personalInfo.height_cm || "Not specified"
            } cm</span>
        </div>
        <div class="data-item">
            <span class="data-label">Weight</span>
            <span class="data-value">${
              personalInfo.weight_kg || "Not specified"
            } kg</span>
        </div>
    `;
}

function updateMedicalInfo(medicalInfo) {
  const container = document.querySelector(
    "#medical-history-section .sidebar-section-content"
  );

  if (!container) return;

  const conditions = [
    { name: "Diabetes", value: medicalInfo.diabetes },
    { name: "Hypertension", value: medicalInfo.hypertension },
    { name: "Heart Disease", value: medicalInfo.heart_disease },
    { name: "Asthma", value: medicalInfo.asthma },
    { name: "Allergies", value: medicalInfo.allergies },
  ];

  container.innerHTML = "";

  conditions.forEach((condition) => {
    if (condition.value) {
      const div = document.createElement("div");
      div.className = "medical-condition active";
      div.innerHTML = `
          <span class="condition-name"> Diagnosed with : ${condition.name} </span>
          <span class="condition-status"></span>
      `;
      container.appendChild(div);
    }
  });

  if (medicalInfo.notes) {
    const notesDiv = document.createElement("div");
    notesDiv.classList.add("notes-section");
    notesDiv.innerHTML = `
      <h4>Additional Notes</h4>
      <p>${medicalInfo.notes}</p>
    `;
    container.appendChild(notesDiv);
  }


}

function updateEmergencyContacts(emergencyContacts) {
  const container = document.querySelector(
    "#emergency-contacts-section .sidebar-section-content"
  );
  if (!container) return;

  container.innerHTML = ""; 

  if (!Array.isArray(emergencyContacts) || emergencyContacts.length === 0) {
    container.innerHTML =
      "<div class='no-contacts'>No emergency contacts available</div>";
    return;
  }

  emergencyContacts.forEach((contact) => {
    const contactDiv = document.createElement("div");
    contactDiv.classList.add("contact-item");
    contactDiv.innerHTML = `
        <div class="contact-name"><strong>${contact.name}</strong> (${
      contact.relationship
    })</div>
        <div class="contact-phone">📞 ${contact.phone}</div>
        <div class="contact-email">✉️ ${contact.email}</div>
        ${
          contact.is_primary
            ? '<div class="primary-contact">⭐ Primary Contact</div>'
            : ""
        }
    `;
    container.appendChild(contactDiv);
  });
}

function updateLifestyleInfo(lifestyle) {
  const container = document.querySelector(
    "#lifestyle-section .sidebar-section-content"
  );
  if (!container) return;

  container.innerHTML = `
    <div class="data-item">
        <span class="data-label">Smoking</span>
        <span class="data-value">${
          lifestyle.smoking ? "Yes 🚬" : "No 🚭"
        }</span>
    </div>
    <div class="data-item">
        <span class="data-label">Alcohol</span>
        <span class="data-value">${lifestyle.alcohol ? "Yes 🍷" : "No "}</span>
    </div>
    <div class="data-item">
        <span class="data-label">Exercise</span>
        <span class="data-value">${
          lifestyle.exercise ? "Yes 🏋️" : "No ❌"
        }</span>
    </div>
  `;
}

// Initialize charts and set up event listeners
// Initialize charts and set up event listeners
document.addEventListener("DOMContentLoaded", async function () {
  say();

  try {
    const { data: sessionData, error } = await supabase.auth.getSession();

    if (error || !sessionData || !sessionData.session) {
      console.error("No active session");
      return;
    }

    const user_id = sessionData.session.user.id;
    console.log("User ID:", user_id);

    await loadAllUserData(user_id);
  } catch (error) {
    console.error("Error in DOMContentLoaded:", error);
  }

  // Initialize both charts
  const spo2Chart = echarts.init(document.getElementById("spo2Chart"));
  const ecgChart = echarts.init(document.getElementById("ecgChart")); // Add this line

  const ecgData = Array.from({ length: 50 }, (_, i) => [
    i,
    Math.sin(i / 5) * 10 + Math.random() * 2,
  ]);

  const ecgOption = {
    title: { text: "ECG Waveform" },
    xAxis: { type: "category" },
    yAxis: { type: "value" },
    series: [
      {
        type: "line",
        data: ecgData,
        smooth: true,
        lineStyle: {
          width: 2,
        },
      },
    ],
  };
  ecgChart.setOption(ecgOption);

  const spo2Data = Array.from({ length: 50 }, (_, i) => [
    i,
    95 + Math.random() * 3,
  ]);

  const spo2Option = {
    title: { text: "SpO2 Levels" },
    xAxis: { type: "category" },
    yAxis: {
      type: "value",
      min: 90,
      max: 100,
    },
    series: [
      {
        type: "line",
        data: spo2Data,
        smooth: true,
        lineStyle: {
          width: 2,
        },
      },
    ],
  };
  spo2Chart.setOption(spo2Option);

  // Profile Handler Code
  const userProfile = document.getElementById("userProfile");
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.getElementById("overlay");
  const closeSidebarBtn = document.getElementById("closeSidebar");
  const contentWrapper = document.getElementById("contentWrapper");

  // Profile click handler
  userProfile.addEventListener("click", async function () {
    try {
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();

      if (error) throw error;

      if (!session) {
        console.error("No active session");
        window.location.href = "/src/markup/sign-up.html";
        return;
      }

      await loadAllUserData(session.user.id);

      // Show sidebar and overlay
      sidebar.classList.add("open");
      overlay.classList.add("show");
      contentWrapper.classList.add("sidebar-open");

      // Ensure only navigation menu is visible on open
      document.querySelector(".sidebar-nav-container").classList.add("visible");

      // Hide all content sections initially
      document
        .querySelectorAll(".sidebar-section:not(.sidebar-nav-container)")
        .forEach((section) => {
          section.classList.remove("visible");
        });
    } catch (error) {
      console.error("Error loading profile:", error);
      alert("Error loading profile data");
    }
  });

  // Close sidebar handler
  function closeSidebar() {
    sidebar.classList.remove("open");
    overlay.classList.remove("show");
    contentWrapper.classList.remove("sidebar-open");
  }

  closeSidebarBtn.addEventListener("click", closeSidebar);
  overlay.addEventListener("click", closeSidebar);

  // Improved navigation handler - each click shows only that section and hides others
  const navItems = document.querySelectorAll(".sidebar-nav-item");
  navItems.forEach((item) => {
    item.addEventListener("click", function () {
      // Remove active class from all items
      navItems.forEach((nav) => nav.classList.remove("active"));
      // Add active class to clicked item
      this.classList.add("active");

      // Hide all content sections first
      document
        .querySelectorAll(".sidebar-section:not(.sidebar-nav-container)")
        .forEach((section) => {
          section.classList.remove("visible");
        });

      // Show the selected section
      const sectionName = this.getAttribute("data-section");
      const targetSection = document.getElementById(`${sectionName}-section`);
      if (targetSection) {
        targetSection.classList.add("visible");
      }
    });
  });
});

// Handle window resize events for chart responsiveness
window.addEventListener("resize", function () {
  const ecgChart = echarts.getInstanceByDom(
    document.getElementById("ecgChart")
  );
  const spo2Chart = echarts.getInstanceByDom(
    document.getElementById("spo2Chart")
  );

  if (ecgChart) {
    ecgChart.resize();
  }

  if (spo2Chart) {
    spo2Chart.resize();
  }
});

export { loadAllUserData, initializeSupabase };
