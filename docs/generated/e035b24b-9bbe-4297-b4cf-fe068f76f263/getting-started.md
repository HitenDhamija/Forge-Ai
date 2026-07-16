# Getting Started

## Overview
This project is a simple Valentine's Day application that uses JavaScript to dynamically change text and display an animated GIF when a user clicks on either "Yes" or "No" buttons.

## Prerequisites
- Node.js version 16.x.x (as specified in the `package.json` file)
- npm/yarn installed

## Installation
To set up this project, follow these steps:

### Step 1: Install Dependencies
First, you need to install the necessary dependencies. Open your terminal and navigate to the root directory of the project.

```bash
cd e035b24b-9bbe-4297-b4cf-fe068f76f263/valentines_2025
npm install
```

### Step 2: Start the Development Server
Once the dependencies are installed, you can start the development server. Use the following command:

```bash
npm run dev
```

This will start a local development server at `http://localhost:3000`.

## Running the App

The application is already set up to run using npm's built-in scripts. The `dev` script runs the development server.

### Accessing the Application
Open your web browser and navigate to `http://localhost:3000`. You should see a page with a question asking if you love someone, along with two buttons labeled "Yes" and "No". Clicking either button will change the text of the question and display an animated GIF.

## Project Structure

The project structure is as follows:

- **index.html**: This file contains the HTML content for the application. It includes a title, meta tags, and links to CSS and JavaScript files.
  - File Path: `valentine/valentines_2025/index.html`
  - Example Content:
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

- **script.js**: This file contains the JavaScript code that handles user interactions and updates the DOM.
  - File Path: `valentine/valentines_2025/script.js`
  - Example Content:
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

    // Change text and gif when the No button is clicked
    noBtn.addEventListener("click", () => {
      question.innerHTML = "I understand. We can still be friends.";
      gif.src = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif";

      // Show the No button
      noBtn.style.display = "none";
    });
    ```

- **style.css**: This file contains CSS styles for the application.
  - File Path: `valentine/valentines_2025/style.css`
  - Example Content:
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

This structure ensures that all files are organized and accessible, making it easier to maintain and develop the application.