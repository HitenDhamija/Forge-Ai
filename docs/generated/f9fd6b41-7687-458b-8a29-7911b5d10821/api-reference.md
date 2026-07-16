# API Reference

## Endpoints

| Method | Path                                                                 | Description                                                                                                                                                                                                                   |
|--------|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET    | /style.css                                                            | Returns the CSS file for styling purposes. Used to apply styles to HTML elements dynamically.                                                                                                                              |
| GET    | /script.js                                                             | Returns the JavaScript file used to handle user interactions and dynamic content updates on the page.                                                                                                                                 |
| GET    | /index.html                                                            | Returns the main HTML document that contains all other resources (CSS, JS). This is the root endpoint of the application.                                                                                                           |

## Request/Response Format

### GET Requests
- **Path:** `/style.css`
  - **Request:**
    ```css
    /* Example CSS */
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
        ...
    }
    ```
- **Response:**
    ```css
    /* Example Response */
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
        ...
    }
    ```

- **Path:** `/script.js`
  - **Request:**
    ```javascript
    // Example JavaScript code
    const yesBtn = document.querySelector(".yes-btn");
    const noBtn = document.querySelector(".no-btn");
    const question = document.querySelector(".question");
    const gif = document.querySelector(".gif"); 

    yesBtn.addEventListener("click", () => {
        question.innerHTML = "Being with you is my biggest blessing. I love you.";
        gif.src = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif";

        noBtn.style.display = "none";
    });
    ```
- **Response:**
    ```javascript
    // Example Response
    const yesBtn = document.querySelector(".yes-btn");
    const noBtn = document.querySelector(".no-btn");
    const question = document.querySelector(".question");
    const gif = document.querySelector(".gif"); 

    yesBtn.addEventListener("click", () => {
        question.innerHTML = "Being with you is my biggest blessing. I love you.";
        gif.src = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif";

        noBtn.style.display = "none";
    });
    ```

### Error Handling
- **Status Codes:** The application does not explicitly handle errors. Errors are typically indicated by the absence of expected content or unexpected behavior, such as a broken link to CSS/JS files.
- **Error Format:** No specific error format is defined in the codebase.

## Error Handling

The application uses HTTP status codes for error handling:
- **404 Not Found:** When a requested resource (CSS/JS file) cannot be found. This could happen if there are typos or incorrect paths specified.
  
### Example of Error Response
```json
{
    "error": {
        "status": 404,
        "message": "Resource not found"
    }
}
```

## File Tree

- `valentine/valentines_2025/index.html`
- `valentine/valentines_2025/script.js`
- `valentine/valentines_2025/style.css`