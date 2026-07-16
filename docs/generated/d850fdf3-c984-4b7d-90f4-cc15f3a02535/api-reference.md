# API Reference

## Endpoints

| Method | Path                                                                 | Description                                                                                                                                                                                                                           |
|--------|-----------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET    | /listings                                                               | Retrieve all listings.                                                                                                                                                                                                                  |
| POST   | /listings                                                               | Create a new listing.                                                                                                                                                                                                                        |
| GET    | /listings/:id                                                          | Show details of a specific listing by its ID.                                                                                                                                                                                      |
| DELETE | /listings/:id                                                           | Delete a listing with the specified ID.                                                                                                                                                                                             |
| GET    | /reviews/:listingId                                                     | Retrieve all reviews for a specific listing.                                                                                                                                                                                       |
| POST   | /reviews/:listingId                                                    | Create a new review for a specific listing.                                                                                                                                                                                          |
| DELETE | /reviews/:listingId/:reviewId                                          | Delete a review by its ID and the associated listing ID.                                                                                                                                                                           |
| GET    | /users/signup                                                           | Render the signup form for users.                                                                                                                                                                                               |
| POST   | /users/signup                                                           | Handle user registration, including password hashing and login.                                                                                                                                                                |
| GET    | /listings/new                                                             | Render a form to create a new listing.                                                                                                                                                                                              |
| GET    | /listings/:id/reviews                                                   | Show all reviews for a specific listing.                                                                                                                                                                                          |
| POST   | /listings/:id/reviews                                                    | Create a review for a specific listing and associate it with the user who created it.                                                                                                                                        |

## Request/Response Format

### Example Request Payloads
#### For `/listings` (POST)
```json
{
  "title": "Cozy Beachfront Cottage",
  "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
  "location": "Malibu",
  "price": 1500,
  "country": "United States"
}
```

#### For `/reviews/:listingId` (POST)
```json
{
  "rating": 4,
  "comment": "Great place, would stay again!",
  "author": {
    "_id": "638f9a1c7b05e2000d4e5565"
  }
}
```

### Example Response Payloads
#### For `/listings` (GET)
```json
{
  "allListings": [
    {
      "_id": "638f9a1c7b05e2000d4e5565",
      "title": "Cozy Beachfront Cottage",
      "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
      "location": "Malibu",
      "price": 1500,
      "country": "United States"
    }
  ]
}
```

#### For `/reviews/:listingId` (GET)
```json
{
  "allReviews": [
    {
      "_id": "638f9a1c7b05e2000d4e5565",
      "rating": 4,
      "comment": "Great place, would stay again!",
      "author": {
        "_id": "638f9a1c7b05e2000d4e5565"
      }
    }
  ]
}
```

## Error Handling

### Status Codes
- **400**: Bad Request - When the request is malformed or invalid.
- **401**: Unauthorized - When a user tries to access content that requires authentication but does not provide valid credentials.
- **403**: Forbidden - When a user attempts an action that they are not allowed to perform (e.g., trying to delete another user's listing).
- **404**: Not Found - When the requested resource is not found on the server.
- **500**: Internal Server Error - When there is an unexpected error or issue within the application.

### Error Response Format
```json
{
  "error": {
    "message": "Error message",
    "status": 400,
    "code": 123 // Custom code for specific errors
  }
}
```

### Example Error Responses
#### For `/listings` (POST) - Bad Request
```json
{
  "error": {
    "message": "Invalid request body. Missing required fields.",
    "status": 400,
    "code": 101
  }
}
```

#### For `/reviews/:listingId` (POST) - Unauthorized
```json
{
  "error": {
    "message": "User is not authenticated to create a review for this listing.",
    "status": 401,
    "code": 203
  }
}
```

### Reference Files and Handler Names from the Codebase

- **app.js**: Initializes Express app, connects to MongoDB, sets up middleware.
- **middleware.js**: Contains authentication middleware (`isLoggedIn`), redirect URL saver middleware (`saveredirectUrl`).
- **controllers/listings.js**: Handles listing-related routes (e.g., `index`, `renderNewform`, `showListing`).
- **controllers/reviews.js**: Handles review-related routes (e.g., `createReview`, `destroyReview`).
- **controllers/users.js**: Handles user registration and login (`signup`), signup form rendering.
- **init/data.js**: Contains sample data for testing purposes.