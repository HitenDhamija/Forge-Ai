# Getting Started

## Overview
This project is a Valentine's Day application that randomly displays a message and an animated GIF based on user interaction. The app uses JavaScript for dynamic behavior, HTML/CSS for structure and styling, and includes basic file management through package.json.

## Prerequisites
- Node.js version 18.x or above (as specified in the `engines` field of `package.json`)
- npm/yarn installed as per your preference (both are used by this project)

## Installation
To install dependencies for this application, run:

```bash
npm install
```

or

```bash
yarn install
```

These commands will install all necessary packages listed in the `package.json` file.

## Running the App
To start the development server and see your app running locally, execute:

```bash
npm run dev
```

or 

```bash
yarn dev
```

This command starts a local web server on port 3000. You can access the application by navigating to `http://localhost:3000` in your browser.

## Project Structure

### Directory Layout
The project directory structure is as follows:

- **valentine/valentines_2025/index.html**: The main HTML file where the user interface elements are defined.
- **valentine/valentines_2025/script.js**: Contains JavaScript code that handles event listeners and updates DOM content based on button clicks.
- **valentine/valentines_2025/style.css**: Styles the application, ensuring it looks visually appealing.

### Real File Names
- `index.html`: Located at `valentine/valentines_2025/index.html`
- `script.js`: Located at `valentine/valentines_2025/script.js`
- `style.css`: Located at `valentine/valentines_2025/style.css`

### Files and Their Contents
#### index.html
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
</body>
</html>
```

#### script.js
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

#### style.css
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

This structure and content provide a clear, functional example of how the project is set up.