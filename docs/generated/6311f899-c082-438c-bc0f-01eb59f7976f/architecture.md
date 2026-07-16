# Architecture

## Tech Stack
- JavaScript (ES6+)

## Project Structure
The project structure is relatively simple and straightforward, as it consists of only three files: `index.html`, `script.js`, and `style.css`.

### Directory Breakdown:
```
valentine/
└── valentines_2025/
    ├── index.html
    ├── script.js
    └── style.css
```

## Data Flow
The data flow in this project is quite simple. The user interacts with the application through a web page, which contains HTML elements for displaying text and an image.

### Request Lifecycle:
1. **User Interaction**: A user visits `index.html` to see the greeting message.
2. **HTML Rendering**: The browser loads `index.html`, parses it, and renders the content based on the structure defined in `style.css`.
3. **Event Handling**: When a button is clicked (either "Yes" or "No"), JavaScript (`script.js`) handles this event by changing the text of the question and updating the image source.
4. **Response**: The updated HTML elements are sent back to the browser, which then updates the page with the new content.

## Key Components
- `index.html`: This file contains the basic structure of the web page including the greeting message, buttons, and an animated GIF.
- `script.js`: Handles user interactions by listening for button clicks and updating the HTML elements accordingly. It also hides one of the buttons after a click event is triggered.

## Database Schema
No database schema or data storage mechanism is present in this project as it only involves client-side JavaScript interacting with static HTML content and CSS styling.

### Actual Files:
- `index.html`
- `script.js`
- `style.css`