# API Reference

## Endpoints

| Method | Path                                                                                     | Description                                                                                                                                                                                                                   |
|--------|------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /valentines_2025/                                                                    | Serve index.html file, which contains a greeting and a GIF. This is the main entry point for the Valentine's Day application.                                                                                                     |
| POST    | /valentines_2025/script.js                                                           | Not directly exposed in the HTML or CSS files; this endpoint handles dynamic content updates triggered by user interactions (clicking on Yes or No buttons). The response from this endpoint is handled client-side via JavaScript. |

## Request/Response Format

### GET /valentines_2025/
**Request:**
```http
GET /valentines_2025/ HTTP/1.1
Host: localhost:3000
```

**Response:**
```json
{
  "html": "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n  <meta charset=\"UTF-8\">\n  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n  <title>Random No Button</title>\n  <link rel=\"stylesheet\" href=\"style.css\" />\n</head>\n<body>\n<div class=\"wrapper\">\n  <h2 class=\"question\">Do you love me?</h2>\n  <img class=\"gif\" alt=\"gif\" src=\"https://i.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjJvdWZzYXc1NGJ6aGp1cDE3b2dyNnVzOGN1andkMjVrMmRzeGwwZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3OhXBaoR1tVPW/giphy.gif\" />\n  <div class=\"btn-group\">\n    <button class=\"yes-btn\">Yes</button>\n    <button class=\"no-btn\">No</button>\n  </div>\n</div>\n</body>\n</html>"
}
```

### POST /valentines_2025/script.js
**Request:**
```http
POST /valentines_2025/script.js HTTP/1.1
Host: localhost:3000
Content-Type: application/javascript

// JavaScript code for handling Yes and No button clicks, updating the greeting and GIF.
```

**Response (Client-Side):**
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

## Error Handling

No specific error handling is implemented in this project. Any errors would be handled by the client-side JavaScript, such as invalid requests or network issues.

### Example of a POST request with an incorrect Content-Type:
**Request:**
```http
POST /valentines_2025/script.js HTTP/1.1
Host: localhost:3000

// Incorrect content type
```

**Response (Client-Side):**
```javascript
console.error("Invalid request, expected application/javascript but received text/html.");
```

### Example of a GET request:
**Request:**
```http
GET /valentines_2025/ HTTP/1.1
Host: localhost:3000
```

**Response (Client-Side):**
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

Note: The actual code for the endpoints is not available in this project, as only HTML and JavaScript files are provided.