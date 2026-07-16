# Getting Started

## Overview
This project, identified by the UUID `6311f899-c082-438c-bc0f-01eb59f7976f`, is a simple Valentine's Day application that asks users whether they love you. The app uses JavaScript for its functionality and styling.

## Prerequisites
The project requires the following installed:
- Node.js version 16.x or higher (as indicated in `package.json`).

## Installation
To install this project, follow these steps:

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/valentine.git
```

### Step 2: Navigate to the Project Directory
```bash
cd valentine/valentines_2025
```

### Step 3: Install Dependencies
Use npm or yarn to install dependencies. The project uses `package.json` for managing dependencies.
```bash
npm install # For using npm
# OR
yarn install # For using Yarn
```

## Running the App
To run the application, use the following command:
```bash
npm start
```
This will start a development server. You can access your app in your browser at `http://localhost:3000`.

## Project Structure

### Directory Layout
The project directory structure is as follows:

- **index.html**: The main HTML file that defines the user interface.
- **script.js**: Contains JavaScript code for handling events and updating the UI dynamically.
- **style.css**: Styles the elements defined in `index.html` using CSS.

### File Locations

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
  <img class="gif" alt="gif" src="https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjJvdWZzYXc1NGJ6aGp1cDE3b2dyNnVzOGN1andkMjVrMmRzeGwwZSZlcD12MV9naWZfYnlfaWQmY3Q9Zw/3OhXBaoR1tVPW/giphy.gif" />
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
}
```

## Conclusion
You have successfully set up and started the Valentine's Day application. You can now explore its functionality by clicking on the buttons in your browser.