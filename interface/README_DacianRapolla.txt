AUTHOR: Dacian Rapolla; Last updated May 4th, 2026
Created index.html, app.js, style.css, and this README.
Responsible for all student-facing UI functionality and interactions.

The Student Interface (Frontend)

BASIC OVERVIEW:
- general overview
- the program files
- system behavior
- interaction with backend
- justification of design

--------------------------------------------------
OVERVIEW
--------------------------------------------------

The frontend is the student-facing portion of MaxGPA. It allows a user to:

- Select a major and academic year range
- Generate a graduation plan grid
- Add required courses to specific terms
- Select instructors for each course
- View grade distribution context

The system is entirely event-driven and dynamically updates the UI based on user interaction.
All scheduling logic is maintained in a global state object in app.js.

No external libraries are used; all functionality is implemented using vanilla JavaScript, HTML, and CSS.

--------------------------------------------------
THE PROGRAM FILES
--------------------------------------------------

== index.html ==

This file defines the layout of the student interface.

Main sections:
- user-select: allows choosing Student/Admin
- controls: major and year selection
- main-layout:
    - grid: graduation plan
    - instructor-panel: instructor selection (right of grid)
- selection-area: course selection and actions
- side-panel: collapsible grade distribution panel

The layout is intentionally simple and structured to support dynamic rendering from app.js.

--------------------------------------------------

== app.js ==

This is the core logic file for the frontend. It manages state, rendering, and all user interaction.

-- global state --

const state = {
    userType,
    selectedMajor,
    startYear,
    endYear,
    requiredCourses,
    schedule,
    selectedSlot,
    sidePanelOpen
}

This state object controls all UI behavior and ensures consistency across components.

-- key functionality --

renderUserSelect()
- Displays Student/Admin selection buttons.

renderControls()
- Displays dropdowns for major and year selection.
- Handles resetting values after plan generation.

generateGridFromSelection()
- Validates user input.
- Builds the schedule grid based on selected years.
- Initializes all term slots.

renderGrid()
- Dynamically generates the graduation plan grid.
- Each cell is clickable and tied to a schedule slot.

renderSelectionArea()
- Displays course selection UI for the selected cell.
- Shows locked classes, pending selections, and action buttons.

renderCourseSelector()
- Allows user to choose a course for a term.
- Prevents duplicate course scheduling.

renderInstructorPanel()
- Displays instructor options for the selected course.
- Shows grade distribution summaries.
- Allows radio selection of instructor.

renderInstructorPanelArea()
- Controls when instructor panel is populated vs placeholder.

renderGraphPanel()
- Controls the collapsible side panel.
- Only displays "Grade Distribution Graphs" header (no instructor UI).

-- event handlers --

handleUserSelectClick()
- Switches between Student/Admin modes.

handleControlsChange()
- Updates selected major and years.

handleControlsClick()
- Handles Generate Plan and toggle panel actions.

handleGridClick()
- Selects a cell and triggers UI updates.

handleSelectionAreaChange()
- Handles course selection dropdown.

handleInstructorPanelChange()
- Handles instructor radio selection.

handleSelectionAreaClick()
- Handles:
    - Lock In Class
    - Cancel Current Class
    - Clear Cell

All rendering functions are called after state updates to keep the UI synchronized.

--------------------------------------------------

== style.css ==

Provides layout and styling for the interface.

Key design elements:
- Flexbox layout for main app structure
- Grid-style layout using rows and cells
- Separate instructor panel positioned to the right of the grid
- Collapsible side panel for graph display

No external CSS frameworks are used.

--------------------------------------------------
SYSTEM BEHAVIOR
--------------------------------------------------

The system operates as follows:

1. User selects "Student"
2. User selects major and year range
3. User generates a plan
4. Grid is dynamically created
5. User clicks a cell
6. User selects a course
7. Instructor options appear in right panel
8. User selects instructor
9. User locks in class
10. Repeat until plan is complete

Constraints:
- Maximum 4 classes per cell
- No duplicate courses allowed
- Instructor must be selected before locking a class

--------------------------------------------------
INTERACTION WITH BACKEND
--------------------------------------------------

Currently, all data is mocked in the frontend using:

fetchMajors()
fetchRequiredCourses()
fetchCourseInstructors()

These functions simulate API calls and will be replaced with real backend endpoints.

The frontend expects backend data in the following structure:

course = { subject, number, title }

instructor = {
    crn,
    name,
    grades: { A, B, C, DNF }
}

The frontend is designed so backend integration can be added without changing UI logic.

--------------------------------------------------
JUSTIFICATION OF DESIGN
--------------------------------------------------

The frontend is structured around a centralized state object to ensure:

- Consistent UI updates
- Predictable behavior
- Easy debugging and modification

Separation of concerns:
- Grid handles scheduling
- Selection area handles course logic
- Instructor panel handles instructor choice
- Side panel handles graph display

Flexbox layout was chosen for simplicity and responsiveness.

No frameworks were used to reduce overhead and maintain full control over behavior.

--------------------------------------------------
NOTES
--------------------------------------------------

- Instructor selection is intentionally separate from the graph panel to improve usability.
- Graph panel is collapsible to avoid blocking the schedule view.
- The system prioritizes clarity and step-by-step interaction for the user.
- The overall design ensures the user has the flexibility to sytematically choose the 
  optimal schedule, or deviate from the optimal schedule to accommodate for personal
  preferences such as particular instructors or class time if they have that information
  from outside sources. 
