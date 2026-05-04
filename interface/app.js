const TERMS = ["Fall", "Winter", "Spring", "Summer"];

const state = {
  userType: null,
  majors: [],
  selectedMajor: "",
  startYear: "",
  endYear: "",
  availableYears: ["AY16", "AY17", "AY18", "AY19", "AY20", "AY21", "AY22", "AY23"],
  requiredCourses: [],
  schedule: [],
  selectedSlot: null,
  sidePanelOpen: true
};

const els = {};

function cacheElements() {
  els.userSelect = document.getElementById("user-select");
  els.controls = document.getElementById("controls");
  els.grid = document.getElementById("grid");
  els.instructorPanel = document.getElementById("instructor-panel");
  els.sidePanel = document.getElementById("side-panel");
}

function hideInstructorPanel() {
  els.instructorPanel.style.display = "none";
  els.instructorPanel.innerHTML = "";
}

function showInstructorPanel() {
  els.instructorPanel.style.display = "block";
}

async function fetchMajors() {
  return [
    { id: "cs-ba", name: "Computer Science BA" },
    { id: "business-ba", name: "Business Administration BA" },
    { id: "psychology-ba", name: "Psychology BA" }
  ];
}

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

function renderUserSelect() {
  els.userSelect.innerHTML = `
    <button type="button" data-user-type="student">Student</button>
    <button type="button" data-user-type="admin">Admin</button>
  `;
}

function renderControls() {
  if (state.userType !== "student") {
    els.controls.innerHTML = "";
    return;
  }

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

function renderAdminPlaceholder() {
  els.controls.innerHTML = `
    <h2>Admin</h2>
    <p>Admin tools will go here later.</p>
  `;

  els.grid.innerHTML = "";
  hideInstructorPanel();
  els.sidePanel.innerHTML = "";
  els.sidePanel.classList.add("collapsed");
}

async function generateGridFromSelection() {
  if (!state.selectedMajor || !state.startYear || !state.endYear) {
    alert("Please select major, start year, and end year.");
    return;
  }

  const startIndex = state.availableYears.indexOf(state.startYear);
  const endIndex = state.availableYears.indexOf(state.endYear);

  if (startIndex > endIndex) {
    alert("Start year must be before or equal to end year.");
    return;
  }

  state.requiredCourses = await fetchRequiredCourses(state.selectedMajor);

  const selectedYears = state.availableYears.slice(startIndex, endIndex + 1);

  state.schedule = selectedYears.map((year) => ({
    year,
    terms: TERMS.map((term) => ({
      term,
      lockedClasses: [],
      pendingCourse: null,
      pendingInstructor: null
    }))
  }));

  state.selectedSlot = null;
  state.sidePanelOpen = true;

  showInstructorPanel();

  renderGrid();
  renderSelectionArea();
  renderGraphPanel();
  renderInstructorPanelArea();

  state.selectedMajor = "";
  state.startYear = "";
  state.endYear = "";

  renderControls();
}

function renderGrid() {
  let html = "";

  html += '<div class="row">';
  html += '<div class="cell"></div>';

  for (let term of TERMS) {
    html += `<div class="cell">${term}</div>`;
  }

  html += "</div>";

  state.schedule.forEach((yearBlock, rowIndex) => {
    html += '<div class="row">';
    html += `<div class="cell">${yearBlock.year}</div>`;

    yearBlock.terms.forEach((termBlock, colIndex) => {
      let cellText = "+";

      if (termBlock.lockedClasses.length > 0 || termBlock.pendingCourse) {
        const lockedText = termBlock.lockedClasses
          .map((item) => `${item.course.subject} ${item.course.number}`)
          .join("<br>");

        const pendingText = termBlock.pendingCourse
          ? `<br><em>${termBlock.pendingCourse.subject} ${termBlock.pendingCourse.number}</em>`
          : "";

        cellText = `${lockedText}${pendingText}`;
      }

      html += `
        <div class="cell">
          <button class="cell-btn" data-row="${rowIndex}" data-col="${colIndex}">
            ${cellText}
          </button>
        </div>
      `;
    });

    html += "</div>";
  });

  els.grid.innerHTML = html;
}

function renderSelectionArea() {
  const selectionArea = document.getElementById("selection-area");
  if (!selectionArea) return;

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

  renderCourseSelector();
}

function renderGraphPanel() {
  if (!state.sidePanelOpen) {
    els.sidePanel.classList.add("collapsed");
    els.sidePanel.innerHTML = "";
    return;
  }

  els.sidePanel.classList.remove("collapsed");
  els.sidePanel.innerHTML = `<h2>Grade Distribution Graphs</h2>`;
}

function renderInstructorPanelPlaceholder() {
  els.instructorPanel.innerHTML = `
    <h2>Instructor Selection</h2>
    <p>Select a grid cell and choose a course.</p>
  `;
}

async function renderInstructorPanelArea() {
  if (!state.selectedSlot) {
    renderInstructorPanelPlaceholder();
    return;
  }

  const { rowIndex, colIndex } = state.selectedSlot;
  const termBlock = state.schedule[rowIndex].terms[colIndex];

  if (!termBlock.pendingCourse) {
    renderInstructorPanelPlaceholder();
    return;
  }

  await renderInstructorPanel(rowIndex, colIndex);
}

function getScheduledCourseKeys() {
  const keys = new Set();

  state.schedule.forEach((yearBlock) => {
    yearBlock.terms.forEach((termBlock) => {
      termBlock.lockedClasses.forEach((item) => {
        keys.add(getCourseKey(item.course));
      });

      if (termBlock.pendingCourse) {
        keys.add(getCourseKey(termBlock.pendingCourse));
      }
    });
  });

  return keys;
}

function getCourseKey(course) {
  return `${course.subject}-${course.number}`;
}

function getAvailableCoursesForSlot(rowIndex, colIndex) {
  const scheduledKeys = getScheduledCourseKeys();

  return state.requiredCourses.filter((course) => {
    const key = getCourseKey(course);
    return !scheduledKeys.has(key);
  });
}

function renderCourseSelector() {
  const selectionArea = document.getElementById("selection-area");
  if (!selectionArea || !state.selectedSlot) return;

  const { rowIndex, colIndex } = state.selectedSlot;
  const termBlock = state.schedule[rowIndex].terms[colIndex];
  const availableCourses = getAvailableCoursesForSlot(rowIndex, colIndex);
  const isFull = termBlock.lockedClasses.length >= 4;
  const canLock = termBlock.pendingCourse && termBlock.pendingInstructor;

  selectionArea.innerHTML = `
    <h2>Course Selection</h2>
    <p>${state.schedule[rowIndex].year} ${termBlock.term}</p>
    <p>${termBlock.lockedClasses.length} of 4 classes locked in this cell.</p>

    <div>
      <strong>Locked classes:</strong>
      ${
        termBlock.lockedClasses.length > 0
          ? `<ul>
              ${termBlock.lockedClasses
                .map(
                  (item) =>
                    `<li>${item.course.subject} ${item.course.number} - ${item.instructor.name}</li>`
                )
                .join("")}
            </ul>`
          : `<p>No classes locked in this cell.</p>`
      }
    </div>

    ${
      termBlock.pendingCourse
        ? `
          <p>
            <strong>Currently choosing:</strong>
            ${termBlock.pendingCourse.subject} ${termBlock.pendingCourse.number}
            ${
              termBlock.pendingInstructor
                ? `with ${termBlock.pendingInstructor.name}`
                : "(choose an instructor to the right of the grid)"
            }
          </p>
        `
        : ""
    }

    ${
      !isFull && !termBlock.pendingCourse
        ? `
          <label for="course-select">Add Course:</label>
          <select id="course-select" data-row="${rowIndex}" data-col="${colIndex}">
            <option value="">Select Course</option>
            ${availableCourses
              .map((course) => {
                const key = getCourseKey(course);

                return `
                  <option value="${key}">
                    ${course.subject} ${course.number} - ${course.title}
                  </option>
                `;
              })
              .join("")}
          </select>
        `
        : ""
    }

    ${isFull ? `<p>This cell already has 4 classes.</p>` : ""}

    ${
      termBlock.pendingCourse
        ? `
          <button id="lock-class-btn" type="button" data-row="${rowIndex}" data-col="${colIndex}" ${
            canLock ? "" : "disabled"
          }>
            Lock In Class
          </button>

          <button id="clear-pending-btn" type="button" data-row="${rowIndex}" data-col="${colIndex}">
            Cancel Current Class
          </button>
        `
        : ""
    }

    <button id="clear-course-btn" type="button" data-row="${rowIndex}" data-col="${colIndex}">
      Clear Cell
    </button>
  `;
}

async function renderInstructorPanel(rowIndex, colIndex) {
  const termBlock = state.schedule[rowIndex].terms[colIndex];

  if (!termBlock.pendingCourse) {
    renderInstructorPanelPlaceholder();
    return;
  }

  const instructors = await fetchCourseInstructors(termBlock.pendingCourse);

  els.instructorPanel.innerHTML = `
    <h2>Instructor Selection</h2>

    <h3>${termBlock.pendingCourse.subject} ${termBlock.pendingCourse.number}</h3>
    <p>${termBlock.pendingCourse.title}</p>

    ${instructors
      .map((instructor) => {
        const selected =
          termBlock.pendingInstructor && termBlock.pendingInstructor.crn === instructor.crn
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

  els.instructorPanel.dataset.instructors = JSON.stringify(instructors);
}

function findRequiredCourseByKey(courseKey) {
  return state.requiredCourses.find((course) => getCourseKey(course) === courseKey);
}

function resetStudentPlan() {
  state.schedule = [];
  state.requiredCourses = [];
  state.selectedSlot = null;

  els.grid.innerHTML = "";
  hideInstructorPanel();
  els.sidePanel.innerHTML = "";

  els.sidePanel.classList.add("collapsed");

  const selectionArea = document.getElementById("selection-area");
  if (selectionArea) {
    selectionArea.innerHTML = "";
  }
}

function handleUserSelectClick(event) {
  const button = event.target.closest("[data-user-type]");
  if (!button) return;

  state.userType = button.dataset.userType;
  resetStudentPlan();

  if (state.userType === "student") {
    state.sidePanelOpen = true;
    renderControls();
  } else {
    renderAdminPlaceholder();
  }
}

function handleControlsChange(event) {
  if (event.target.id === "major-select") {
    state.selectedMajor = event.target.value;
    resetStudentPlan();
    renderControls();
  }

  if (event.target.id === "start-year") {
    state.startYear = event.target.value;
  }

  if (event.target.id === "end-year") {
    state.endYear = event.target.value;
  }
}

function handleControlsClick(event) {
  if (event.target.id === "generate-btn") {
    generateGridFromSelection();
  }

  if (event.target.id === "toggle-side-panel-btn") {
    state.sidePanelOpen = !state.sidePanelOpen;
    renderControls();
    renderGraphPanel();
  }
}

function handleGridClick(event) {
  const button = event.target.closest(".cell-btn");
  if (!button) return;

  state.selectedSlot = {
    rowIndex: Number(button.dataset.row),
    colIndex: Number(button.dataset.col)
  };

  renderSelectionArea();
  renderGraphPanel();
  renderInstructorPanelArea();
}

function handleSelectionAreaChange(event) {
  if (event.target.id === "course-select") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const selectedCourseKey = event.target.value;

    if (!selectedCourseKey) return;

    const termBlock = state.schedule[rowIndex].terms[colIndex];

    if (termBlock.lockedClasses.length >= 4) {
      alert("You can only add up to 4 classes per cell.");
      event.target.value = "";
      return;
    }

    const selectedCourse = findRequiredCourseByKey(selectedCourseKey);

    if (!selectedCourse) return;

    termBlock.pendingCourse = selectedCourse;
    termBlock.pendingInstructor = null;

    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
    renderGraphPanel();
    renderInstructorPanelArea();
  }
}

function handleInstructorPanelChange(event) {
  if (event.target.name === "instructor") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const instructors = JSON.parse(els.instructorPanel.dataset.instructors || "[]");

    const selectedInstructor = instructors.find(
      (instructor) => instructor.crn === event.target.value
    );

    state.schedule[rowIndex].terms[colIndex].pendingInstructor = selectedInstructor;

    renderSelectionArea();
  }
}

function handleSelectionAreaClick(event) {
  if (event.target.id === "lock-class-btn") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const termBlock = state.schedule[rowIndex].terms[colIndex];

    if (!termBlock.pendingCourse || !termBlock.pendingInstructor) {
      alert("Please choose both a course and an instructor before locking in the class.");
      return;
    }

    if (termBlock.lockedClasses.length >= 4) {
      alert("You can only add up to 4 classes per cell.");
      return;
    }

    termBlock.lockedClasses.push({
      course: termBlock.pendingCourse,
      instructor: termBlock.pendingInstructor
    });

    termBlock.pendingCourse = null;
    termBlock.pendingInstructor = null;

    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
    renderGraphPanel();
    renderInstructorPanelArea();
  }

  if (event.target.id === "clear-pending-btn") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const termBlock = state.schedule[rowIndex].terms[colIndex];

    termBlock.pendingCourse = null;
    termBlock.pendingInstructor = null;

    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
    renderGraphPanel();
    renderInstructorPanelArea();
  }

  if (event.target.id === "clear-course-btn") {
    const rowIndex = Number(event.target.dataset.row);
    const colIndex = Number(event.target.dataset.col);
    const termBlock = state.schedule[rowIndex].terms[colIndex];

    termBlock.lockedClasses = [];
    termBlock.pendingCourse = null;
    termBlock.pendingInstructor = null;

    renderGrid();
    state.selectedSlot = { rowIndex, colIndex };
    renderSelectionArea();
    renderGraphPanel();
    renderInstructorPanelArea();
  }
}

function attachEvents() {
  const selectionArea = document.getElementById("selection-area");

  els.userSelect.addEventListener("click", handleUserSelectClick);
  els.controls.addEventListener("change", handleControlsChange);
  els.controls.addEventListener("click", handleControlsClick);
  els.grid.addEventListener("click", handleGridClick);
  els.instructorPanel.addEventListener("change", handleInstructorPanelChange);

  if (selectionArea) {
    selectionArea.addEventListener("change", handleSelectionAreaChange);
    selectionArea.addEventListener("click", handleSelectionAreaClick);
  }
}

async function init() {
  cacheElements();
  state.majors = await fetchMajors();
  renderUserSelect();
  attachEvents();
  els.sidePanel.classList.add("collapsed");
  hideInstructorPanel();
}

window.addEventListener("DOMContentLoaded", init);
