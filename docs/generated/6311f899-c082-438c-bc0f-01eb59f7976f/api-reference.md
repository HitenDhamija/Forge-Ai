# API Reference

## Endpoints

| Method | Path                                                                                     | Description                                                                                                                                                                                                                               |
|--------|------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /valentines_2025/love-status                                                             | Fetches a love status message and an animated GIF based on user interaction.                                                                                                                                                      |
| POST    | /valentines_2025/generate-love-message                                                   | Generates a personalized love message for the user, which is then displayed in the webpage.                                                                                                                                                |
| GET     | /valentines_2025/random-gif                                                             | Fetches a random animated GIF from an external source and displays it on the page.                                                                                                                                                      |
| POST    | /valentines_2025/change-love-status                                                      | Changes the love status message based on user input, updating both the text and the associated GIF.                                                                                                                                          |
| GET     | /valentines_2025/user-profile                                                             | Fetches a profile for the authenticated user (if any).                                                                                                                                                                                     |
| POST    | /valentines_2025/authenticate                                                          | Authenticates a user by sending their credentials and returns an authentication token.                                                                                                                                                |

## Request/Response Format

### GET /valentines_2025/love-status
- **Request Payload:** None (empty body)
- **Response Payload:**
```json
{
  "message": "Being with you is my biggest blessing. I love you.",
  "gifUrl": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif"
}
```

### POST /valentines_2025/generate-love-message
- **Request Payload:**
```json
{
  "message": "I love you more than words can express.",
  "gifUrl": "https://media.giphy.com/media/3o7XK1Qq96W84mZzjR/giphy.gif"
}
```
- **Response Payload:**
```json
{
  "status": "success",
  "message": "Love message generated successfully.",
  "data": {
    "message": "I love you more than words can express.",
    "gifUrl": "https://media.giphy.com/media/3o7XK1Qq96W84mZzjR/giphy.gif"
  }
}
```

### GET /valentines_2025/random-gif
- **Request Payload:** None (empty body)
- **Response Payload:**
```json
{
  "gifUrl": "https://media.giphy.com/media/3o7XK1Qq96W84mZzjR/giphy.gif"
}
```

### POST /valentines_2025/change-love-status
- **Request Payload:**
```json
{
  "message": "I love you more than ever.",
  "gifUrl": "https://media.giphy.com/media/3o7XK1Qq96W84mZzjR/giphy.gif"
}
```
- **Response Payload:**
```json
{
  "status": "success",
  "message": "Love status updated successfully.",
  "data": {
    "message": "I love you more than ever.",
    "gifUrl": "https://media.giphy.com/media/3o7XK1Qq96W84mZzjR/giphy.gif"
  }
}
```

### GET /valentines_2025/user-profile
- **Request Payload:** None (empty body)
- **Response Payload:**
```json
{
  "status": "success",
  "message": "User profile fetched successfully.",
  "data": {
    "username": "user1234",
    "email": "user@example.com"
  }
}
```

### POST /valentines_2025/authenticate
- **Request Payload:**
```json
{
  "username": "user1234",
  "password": "password123"
}
```
- **Response Payload:**
```json
{
  "status": "success",
  "message": "Authentication successful.",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDLdLCJpYXQiOjE2MTQxNzU1OTcsImV4cCI6MTk2ODA3NTYwMX0.8P7TfFmZ9nCvKqoWbGgRi9uYIe5BdJHhXpMjyLrEaSs"
  }
}
```

## Error Handling

### Authentication Errors
- **Status Code:** 401 Unauthorized
- **Error Response:**
```json
{
  "status": "error",
  "message": "Invalid credentials. Please try again."
}
```

### Request Payload Validation Errors
- **Status Code:** 422 Unprocessable Entity
- **Error Response:**
```json
{
  "status": "error",
  "message": "Request payload is invalid.",
  "errors": [
    {
      "field": "username",
      "message": "Username cannot be empty."
    },
    {
      "field": "password",
      "message": "Password cannot be empty."
    }
  ]
}
```

### Internal Server Errors
- **Status Code:** 500 Internal Server Error
- **Error Response:**
```json
{
  "status": "error",
  "message": "An unexpected error occurred. Please try again later."
}
```

These examples are based on the provided code snippets and demonstrate how different API endpoints interact with the frontend application for Valentine's Day greetings.