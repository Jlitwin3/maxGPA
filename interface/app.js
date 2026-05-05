// Constant list of academic terms used to build the schedule grid
const TERMS = ["Fall", "Winter", "Spring", "Summer"];

// Global application state object
const state = {
  userType: null,                // "student" or "admin"
  majors: [],                    // List of available majors
  selectedMajor: "",             // Currently selected major ID
  startYear: "",                 // Selected start year
  endYear: "",                   // Selected end year
  availableYears: ["AY16", "AY17", "AY18", "AY19", "AY20", "AY21", "AY22", "AY23"], // All selectable academic years
  requiredCourses: [],           // Courses required for the selected major
  schedule: [],                  // Generated schedule grid data structure
  selectedSlot: null,            // Currently selected grid cell
  sidePanelOpen: true            // Tracks whether the graph side panel is open
};

// Object used to store cached DOM element references
const els = {};

// Cache frequently used DOM elements
function cacheElements() {
  els.userSelect = document.getElementById("user-select");
  els.controls = document.getElementById("controls");
  els.grid = document.getElementById("grid");
  els.sidePanel = document.getElementById("side-panel");
}

// Simulated API call that returns available majors
async function fetchMajors() {
  return [
    { id: "cs-ba", name: "Computer Science BA" },
    { id: "business-ba", name: "Business Administration BA" },
    { id: "psychology-ba", name: "Psychology BA" }
  ];
}

// Simulated API call that returns required courses for the selected major
async function fetchRequiredCourses(majorId) {
  const coursesByMajor = {
    "cs-ba": [
      { subject: "CS", number: "122", title: "Introduction to Programming and Problem Solving" },
      { subject: "CS", number: "210", title: "Computer Science I" },
      { subject: "CS", number: "211", title: "Computer Science II" },
      { subject: "CS", number: "313", title: "Intermediate Data Structures" },
      { subject: "CS", number: "315", title: "Algorithms" },
      { subject: "CS", number: "422", title: "Software Methodologies" },
      { subject: "MATH", number: "251", title: "Calculus I" },
      { subject: "MATH", number: "252", title: "Calculus II" }
    ],

    "business-ba": [
      { subject: "BA", number: "101Z", title: "Introduction to Business" },
      { subject: "EC", number: "201", title: "Principles of Microeconomics" },
      { subject: "EC", number: "202", title: "Principles of Macroeconomics" },
      { subject: "MATH", number: "241", title: "Calculus for Business and Social Science I" }
    ],

    "psychology-ba": [
      { subject: "PSY", number: "201", title: "Mind and Brain" },
      { subject: "PSY", number: "202", title: "Mind and Society" },
      { subject: "PSY", number: "302", title: "Statistical Methods in Psychology" },
      { subject: "PSY", number: "304", title: "Research Methods in Psychology" }
    ]
  };

  return coursesByMajor[majorId] || [];
}

// Simulated API call that returns instructors and grade distributions for a course
async function fetchCourseInstructors(course) {
  return [
    {
      crn: "12345",
      name: "Smith",
      grades: { A: 42, B: 31, C: 16, DNF: 5 }
    },
    {
      crn: "23456",
      name: "Patel",
      grades: { A: 35, B: 37, C: 18, DNF: 8 }
    },
    {
      crn: "34567",
      name: "Wang",
      grades: { A: 50, B: 25, C: 12, DNF: 4 }
    }
  ];
}

// Render the initial buttons for choosing student or admin mode
function renderUserSelect() {
  els.userSelect.innerHTML = `
    <button type="button" data-user-type="student">Student</button>
    <button type="button" data-user-type="admin">Admin</button>
  `;
}

// Render the student controls for selecting major, start year, and end year
function renderControls() {
  // Only show these controls for student users
  if (state.userType !== "student") {
    els.controls.innerHTML = "";
    return;
  }

  // Build the controls using the current state values
  els.controls.innerHTML = `
    <label for="major-select">Major:</label>
    <select id="major-select">
      <option value="">Select Major</option>
      ${state.majors
        .map((major) => {
          const selected = state.selectedMajor === major.id ? "selected" : "";
          return `<option value="${major.id}" ${selected}>${major.name}</option>`;
        })
        .join("")}
    </select>

    <label for="start-year">Start Year:</label>
    <select id="start-year">
      <option value="">Start</option>
      ${state.availableYears
        .map((year) => {
          const selected = state.startYear === year ? "selected" : "";
          return `<option value="${year}" ${selected}>${year}</option>`;
        })
        .join("")}
    </select>

    <label for="end-year">End Year:</label>
    <select id="end-year">
      <option value="">End</option>
      ${state.availableYears
        .map((year) => {
          const selected = state.endYear === year ? "selected" : "";
          return `<option value="${year}" ${selected}>${year}</option>`;
        })
        .join("")}
    </select>

    <button id="generate-btn" type="button">Generate Plan</button>
    <button id="toggle-side-panel-btn" type="button">
      ${state.sidePanelOpen ? "Collapse Graph Panel" : "Open Graph Panel"}
    </button>
  `;
}

// Render a temporary placeholder for the admin view
function renderAdminPlaceholder() {
  els.controls.innerHTML = `
    <h2>Admin</h2>
    <p>Admin tools will go here later.</p>
  `;

  // Clear student-specific UI when admin mode is selected
  els.grid.innerHTML = "";
  els.sidePanel.innerHTML = "";
  els.sidePanel.classList.add("collapsed");
}

// Generate the schedule grid from the selected major and year range
async function generateGridFromSelection() {
  // Require all dropdowns to be selected before generating the plan
  if (!state.selectedMajor || !state.startYear || !state.endYear) {
    alert("Please select major, start year, and end year.");
    return;
  }

  // Convert selected years to indexes for range validation
  const startIndex = state.availableYears.indexOf(state.startYear);
  const endIndex = state.availableYears.indexOf(state.endYear);

  // Prevent invalid year ranges
  if (startIndex > endIndex) {
    alert("Start year must be before or equal to end year.");
    return;
  }

  // Load the required courses for the selected major
  state.requiredCourses = await fetchRequiredCourses(state.selectedMajor);

  // Create a list of years included in the selected range
  const selectedYears = state.availableYears.slice(startIndex, endIndex + 1);

  // Build the internal schedule structure for each year and term
  state.schedule = selectedYears.map((year) => ({
    year,
    terms: TERMS.map((term) => ({
      term,
      course: null,
      instructor: null
    }))
  }));

  // Reset selected grid cell and open the graph panel
  state.selectedSlot = null;
  state.sidePanelOpen = true;

  // Render the generated plan UI
  renderGrid();
renderSelectionArea();
renderGraphPanel();

state.selectedMajor = "";
state.startYear = "";
state.endYear = "";

renderControls();
  }



// Render the generated schedule grid
function renderGrid() {
  // Clear the grid if no schedule exists
  if (state.schedule.length === 0) {
    els.grid.innerHTML = "";
    return;
  }

  // Find the selected major object for display in the plan summary
  const selectedMajor = state.majors.find(
    (major) => major.id === state.selectedMajor
  );

  // Start building the grid HTML with a summary and header row
  let html = `
    <section id="plan-summary">
      <h2>Generated Plan</h2>
      <p><strong>Major:</strong> ${selectedMajor ? selectedMajor.name : "None selected"}</p>
      <p><strong>Year Range:</strong> ${state.startYear} to ${state.endYear}</p>
    </section>

    <div class="row header-row">
      <div class="cell"></div>
      ${TERMS.map((term) => `<div class="cell">${term}</div>`).join("")}
    </div>
  `;

  // Add one row for each academic year
  state.schedule.forEach((yearBlock, rowIndex) => {
    html += `
      <div class="row">
        <div class="cell year-cell">${yearBlock.year}</div>
    `;

    // Add one cell for each term in the year
    yearBlock.terms.forEach((termBlock, colIndex) => {
      const label = termBlock.course
        ? `${termBlock.course.subject} ${termBlock.course.number}`
        : "+";

      html += `
        <div class="cell">
          <button class="cell-btn" type="button" data-row="${rowIndex}" data-col="${colIndex}">
            ${label}
          </button>
        </div>
      `;
    });

    html += `</div>`;
  });

  // Add the area where course selection controls will appear
  html += `<section id="selection-area"></section>`;

  els.grid.innerHTML = html;
}




// Render the course selection area below the grid
function renderSelectionArea() {
  const selectionArea = document.getElementById("selection-area");
  if (!selectionArea) return;

  // Show basic scheduling progress when no grid cell is selected
  if (!state.selectedSlot) {
    const scheduledCount = getScheduledCourseKeys().size;
    const totalCount = state.requiredCourses.length;

    selectionArea.innerHTML = `
      <h2>Course Selection</h2>
      <p>${scheduledCount} of ${totalCount} required courses scheduled.</p>
      <p>Select a grid cell to add a course.</p>
    `;
    return;
  }

  // If a grid cell is selected, show the course selector for that cell
  renderCourseSelector();
}

// Render the right-side graph panel
function renderGraphPanel() {
  // Hide and clear the panel when it is collapsed
  if (!state.sidePanelOpen) {
    els.sidePanel.classList.add("collapsed");
    els.sidePanel.innerHTML = "";
    return;
  }

  // Show the side panel when open
  els.sidePanel.classList.remove("collapsed");

  els.sidePanel.innerHTML = `
    <h2>Grade Distribution Graphs</h2>
    <p>Graphs will appear here later.</p>
  `;
}

// Return a Set of course keys for courses already placed in the schedule
function getScheduledCourseKeys() {
  const keys = new Set();

  // Walk through every scheduled term and collect selected courses
  state.schedule.forEach((yearBlock) => {
    yearBlock.terms.forEach((termBlock) => {
      if (termBlock.course) {
        keys.add(getCourseKey(termBlock.course));
      }
    });
  });

  return keys;
}

// Build a unique key for a course using subject and course number
function getCourseKey(course) {
  return `${course.subject}-${course.number}`;
}

// Return the courses that are still available for a selected grid slot
function getAvailableCoursesForSlot(rowIndex, colIndex) {
  const scheduledKeys = getScheduledCourseKeys();
  const currentCourse = state.schedule[rowIndex].terms[colIndex].course;
  const currentKey = currentCourse ? getCourseKey(currentCourse) : null;

  // Exclude already scheduled courses, except the course currently in this slot
  return state.requiredCourses.filter((course) => {
    const key = getCourseKey(course);
    return !scheduledKeys.has(key) || key === currentKey;
  });
}

// Render the dropdown used to choose a course for the selected grid cell
function renderCourseSelector() {
  const selectionArea = document.getElementById("selection-area");
  if (!selectionArea || !state.selectedSlot) return;

  // Get selected grid position
  const { rowIndex, colIndex } = state.selectedSlot;
  const termBlock = state.schedule[rowIndex].terms[colIndex];
  const availableCourses = getAvailableCoursesForSlot(rowIndex, colIndex);

  // Build course selection UI
  selectionArea.innerHTML = `
    <h2>Course Selection</h2>
    <p>${state.schedule[rowIndex].year} ${termBlock.term}</p>

    <label for="course-select">Course:</label>
    <select id="course-select" data-row="${rowIndex}" data-col="${colIndex}">
      <option value="">Select Course</option>
      ${availableCourses
        .map((course) => {
          const key = getCourseKey(course);
          const selected =
            termBlock.course && getCourseKey(termBlock.course) === key
              ? "selected"
              : "";

          return `
            <option value="${key}" ${selected}>
              ${course.subject} ${course.number} - ${course.title}
            </option>
          `;
        })
        .join("")}
    </select>

    <button id="clear-course-btn" type="button" data-row="${rowIndex}" data-col="${colIndex}">
      Clear Cell
    </button>

    <div id="instructor-panel"></div>
  `;

  // If a course is already selected, show instructor options
  if (termBlock.course) {
    renderInstructorPanel(rowIndex, colIndex);
  }
}

// Render instructor radio buttons and grade distribution numbers for a selected course
async function renderInstructorPanel(rowIndex, colIndex) {
  const termBlock = state.schedule[rowIndex].terms[colIndex];
  const panel = document.getElementById("instructor-panel");

  // Do nothing if panel is missing or no course is selected
  if (!panel || !termBlock.course) {
    return;
  }

  // Fetch instructor data for the selected course
  const instructors = await fetchCourseInstructors(termBlock.course);

  // Build instructor selection UI
  panel.innerHTML = `
    <h3>${termBlock.course.subject} ${termBlock.course.number}</h3>
    <p>${termBlock.course.title}</p>

    <h4>Instructor Selection</h4>

    ${instructors
      .map((instructor) => {
        const selected =
          termBlock.instructor && termBlock.instructor.crn === instructor.crn
            ? "checked"
            : "";

        return `
          <label>
            <input
              type="radio"
              name="instructor"
              value="${instructor.crn}"
              data-row="${rowIndex}"
              data-col="${colIndex}"
              ${selected}
            >
            ${instructor.name}
          </label>

          <div>
            A: ${instructor.grades.A},
            B: ${instructor.grades.B},
            C: ${instructor.grades.C},
            DNF: ${instructor.grades.DNF}
          </div>
        `;
      })
      .join("")}
  `;

  // Store instructor data on the panel so it can be reused when a radio button changes
  panel.dataset.instructors = JSON.stringify(instructors);
}

// Find a required course object using its generated course key
function findRequiredCourseByKey(courseKey) {
  return state.requiredCourses.find((course) => getCourseKey(course) === courseKey);
}

// Reset the generated student plan and related UI
function resetStudentPlan() {
  state.schedule = [];
  state.requiredCourses = [];
  state.selectedSlot = null;
  els.grid.innerHTML = "";
  els.sidePanel.innerHTML = "";
  els.sidePanel.classList.add("collapsed");
}

// Handle clicks on the Student/Admin selection buttons
function handleUserSelectClick(event) {
  const button = event.target.closest("[data-user-type]");
  if (!button) return;

  // Store selected user type
  state.userType = button.dataset.userType;
  resetStudentPlan();

  // Render the correct UI based on selected user type
  if (state.userType === "student") {
    state.sidePanelOpen = true;
    renderControls();
  } else {
    renderAdminPlaceholder();
  }
}

// Handle dropdown changes in the controls area
function handleControlsChange(event) {
  // Update selected major and reset any generated plan
  if (event.target.id === "major-select") {
    state.selectedMajor = event.target.value;
    resetStudentPlan();
    renderControls();
  }

  // Update selected start year
  if (event.target.id === "start-year") {
    state.startYear = event.target.value;
  }

  // Update selected end year
  if (event.target.id === "end-year") {
    state.endYear = event.target.value;
  }
}

// Handle button clicks in the controls area
function handleControlsClick(event) {
  // Generate a plan when the generate button is clicked
  if (event.target.id === "generate-btn") {
    generateGridFromSelection();
  }

  // Toggle the side panel open or closed
  if (event.target.id === "toggle-side-panel-btn") {
    state.sidePanelOpen = !state.sidePanelOpen;
    renderControls();
    renderGraphPanel();
  }
}

// Handle clicks inside the schedule grid
function handleGridClick(event) {
  const button = event.target.closest(".cell-btn");
  if (!button) return;

  // Store the clicked grid cell as the selected slot
  state.selectedSlot = {
    rowIndex: Number(button.dataset.row),
    colIndex: Number(button.dataset.col)
  };

  renderSelectionArea();
}

// Handle dropdown and radio button changes inside the grid area
function handleGridChange(event) {
  // Handle course selection changes
  if (event.target.id === "course-select") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const selectedCourseKey = event.target.value;

    const termBlock = state.schedule[rowIndex].terms[colIndex];

    // Assign selected course to the grid cell, or clear it if blank
    termBlock.course = selectedCourseKey
      ? findRequiredCourseByKey(selectedCourseKey)
      : null;

    // Clear instructor selection whenever the course changes
    termBlock.instructor = null;

    // Re-render grid and keep the same slot selected
    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
  }

  // Handle instructor radio button selection
  if (event.target.name === "instructor") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const instructorPanel = document.getElementById("instructor-panel");
    const instructors = JSON.parse(instructorPanel.dataset.instructors || "[]");

    // Find the instructor object matching the selected radio button
    const selectedInstructor = instructors.find(
      (instructor) => instructor.crn === event.target.value
    );

    // Store selected instructor in the schedule
    state.schedule[rowIndex].terms[colIndex].instructor = selectedInstructor;
  }
}

// Handle button clicks inside the grid area
function handleGridButtonClick(event) {
  // Clear the selected course and instructor from a cell
  if (event.target.id === "clear-course-btn") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);

    state.schedule[rowIndex].terms[colIndex].course = null;
    state.schedule[rowIndex].terms[colIndex].instructor = null;

    // Re-render grid and keep the same slot selected
    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
  }
}

// Attach event listeners using event delegation
function attachEvents() {
  els.userSelect.addEventListener("click", handleUserSelectClick);
  els.controls.addEventListener("change", handleControlsChange);
  els.controls.addEventListener("click", handleControlsClick);
  els.grid.addEventListener("click", handleGridClick);
  els.grid.addEventListener("change", handleGridChange);
  els.grid.addEventListener("click", handleGridButtonClick);
}

// Initialize the application after the page loads
async function init() {
  cacheElements();
  state.majors = await fetchMajors();
  renderUserSelect();
  attachEvents();
  els.sidePanel.classList.add("collapsed");
}

// Start the app once the DOM is fully loaded
window.addEventListener("DOMContentLoaded", init);
