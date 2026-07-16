# API Reference

## Endpoints

| Method | Path                                                                 | Description                                                                                                                                                                                                                   |
|--------|-----------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET    | /valentines_2025/love-check                                                | Endpoint to check if the user loves the application. This is triggered by clicking on a button in the HTML file, and it does not require any request body or response payload.                                             |
| POST   | /api/v1/generate-gif                                                      | Generates a GIF based on user input (e.g., love message). The endpoint accepts JSON payloads with a `message` field to customize the text of the GIF. No response is expected from this endpoint.                           |
| DELETE | /api/v1/love-check-confirmation                                             | Endpoint for confirming if the user loves the application. This is triggered by clicking on a button in the HTML file, and it does not require any request body or response payload.                                             |

## Request/Response Format

### GET: `/valentines_2025/love-check`
**Request Payload**: None
**Response Payload**:
```json
{
  "message": "Being with you is my biggest blessing. I love you.",
  "gifUrl": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif"
}
```

### POST: `/api/v1/generate-gif`
**Request Payload**: JSON
```json
{
  "message": "I love you so much!"
}
```
**Response Payload**: None

### DELETE: `/api/v1/love-check-confirmation`
**Request Payload**: None
**Response Payload**: None

## Error Handling

No specific error handling is implemented in the code. Errors are not returned as HTTP status codes or JSON responses.

### Example of Error Handling (if any):
Since no error handling is coded, there's no actual implementation to reference from the codebase. However, if this were a real application, errors might be handled by checking for specific HTTP status codes and logging them in the server logs or returning appropriate error messages with detailed information about what went wrong.

### Actual Route Files and Handler Names:
- `/api/v1/generate-gif` is handled by `generateGifHandler` function.
- `/api/v1/love-check-confirmation` is handled by `confirmLoveCheckHandler` function.