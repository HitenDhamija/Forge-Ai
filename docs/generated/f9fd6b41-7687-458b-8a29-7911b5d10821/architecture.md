# Architecture

## Tech Stack
- JavaScript (ES6+)

## Project Structure
The project structure is relatively simple and straightforward, as it consists of three main files: `index.html`, `script.js`, and `style.css`.

### index.html
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Random No Button</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body>
<div class="wrapper">
  <h2 class="question">Do you love me?</h2>
  <img class="gif" alt="gif" src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjJvdWZzYXc1NGJ6aGp1cDE3b2dyNnVzOGN1andkMjVrMmRzeGwwZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3OhXBaoR1tVPW/giphy.gif" />
  <div class="btn-group">
    <button class="yes-btn">Yes</button>
    <button class="no-btn">No</button>
  </div>
</div>
<script src="script.js"></script>
</body>
</html>
```

### script.js
```javascript
const yesBtn = document.querySelector(".yes-btn");
const noBtn = document.querySelector(".no-btn");
const question = document.querySelector(".question");
const gif = document.querySelector(".gif");

// Change text and gif when the Yes button is clicked
yesBtn.addEventListener("click", () => {
    question.innerHTML = "Being with you is my biggest blessing. I love you.";
    gif.src = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif";

    // Hide the No button
    noBtn.style.display = "none";
});
```

### style.css
```css
/* style.css */
body {
    margin: 0;
    padding: 0;
    font-family: 'Poppins', Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100vh;
    background: linear-gradient(135deg, #ffafbd, #ffc3a0);
    color: #333;
}

.wrapper {
    position: relative;
    width: 90%;
    max-width: 500px;
    text-align: center;
    background: white;
    padding: 30px 20px;
    border-radius: 15px;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.question {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
    color: #333;
}

.gif {
    max-width: 100%;
    height: auto;
}
```

## Data Flow
The application's data flow is quite simple. The user interacts with the `index.html` file, which contains a form where they can choose between "Yes" or "No". When the user clicks on either button, JavaScript in `script.js` updates the content of the page and hides one of the buttons.

### Request Lifecycle
1. **User Interaction**: User navigates to the application's landing page (`index.html`) via a browser.
2. **HTML Rendering**: The HTML file is rendered by the browser, including the CSS for styling and JavaScript for interactivity.
3. **JavaScript Execution**: When the user clicks on either "Yes" or "No", `script.js` detects this event through an event listener attached to the respective button.
4. **Data Update**: Depending on which the button clicked, the content of a question element is updated with a message and the image source changes accordingly.
5. **Button Visibility Change**: The visibility of the "No" button is changed by setting its `display` property to `"none"`.

## Key Components
- **index.html**: This file contains the HTML structure for the application, including buttons, images, and text elements.
- **script.js**: Handles user interactions via event listeners. It updates content and hides buttons based on user input.
- **style.css**: Styles the page, ensuring it is visually appealing and responsive.

## Database Schema
No database schema was provided in this codebase; therefore, no specific data structures or models can be described here.