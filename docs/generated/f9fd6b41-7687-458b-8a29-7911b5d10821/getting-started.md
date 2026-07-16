# Getting Started

## Overview
This project is a Valentine's Day application that randomly displays a message and an animated GIF based on user interaction. The purpose of this application is to create a simple, interactive way for users to express their feelings towards another person.

## Prerequisites
- Node.js version 14.x or higher installed.
- npm/yarn package manager installed (found in `package.json`).

## Installation
To install the project dependencies:

```bash
npm install # For npm
# OR
yarn install # For yarn
```

## Running the App
To start the development server, use the following command:

```bash
npm run dev # For npm
# OR
yarn dev    # For yarn
```

This will start a local development server on `http://localhost:3000`.

## Project Structure

### Directory Layout
The project structure is as follows:
- **valentine/valentines_2025/index.html**: The main HTML file where the application's UI elements are defined.
- **valentine/valentines_2025/script.js**: JavaScript code that handles user interactions and updates the DOM dynamically.
- **valentine/valentines_2025/style.css**: CSS styles for the application, ensuring a consistent look and feel.

### Actual File Names
- `index.html` is located at: `valentine/valentines_2025/index.html`
- `script.js` is located at: `valentine/valentines_2025/script.js`
- `style.css` is located at: `valentine/valentines_2025/style.css`

### Explanation of the Structure
1. **index.html**: Contains basic HTML structure, including a title and links to CSS and JavaScript files.
   - The `<meta>` tags set character encoding and viewport settings for responsive design.
   - A `<title>` tag sets the document's title.
   - Links are provided to external CSS (`style.css`) and an internal JavaScript file (`script.js`).
2. **script.js**: Handles dynamic content updates based on user interactions (clicking buttons).
   - It uses `document.querySelector()` to select elements with specific classes.
   - Event listeners are attached to the Yes and No buttons, changing the text of a question element and updating an image source attribute when clicked.
3. **style.css**: Styles the application's UI elements for consistency and accessibility.
   - The body is styled with flexbox layout properties to center content vertically and horizontally within its container.
   - Padding and margin are applied to ensure spacing around elements.
   - Background gradients and text colors are used to enhance visual appeal.

By following these steps, you can set up the project locally and start interacting with it.