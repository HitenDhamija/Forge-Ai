# API Reference

## Endpoints

| Method | Path                                                                                          | Description                                                                                                                                                                                                                   |
|--------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /listings/                                                                                            | Retrieve all listings.                                                                                                                                                                                                            |
| POST    | /listings/new                                                                                     | Create a new listing.                                                                                                                                                                                                              |
| PUT     | /listings/:id                                                                                      | Update an existing listing with the provided ID.                                                                                                                                                                          |
| DELETE  | /listings/:id                                                                                      | Delete a listing by its ID.                                                                                                                                                                                                          |
| GET     | /reviews/                                                                                         | Retrieve all reviews.                                                                                                                                                                                                             |
| POST    | /reviews/new/:listingId                                                               | Create a new review for a specific listing with the provided ID.                                                                                                                                                             |
| DELETE  | /reviews/:reviewId/:listingId                                                             | Delete a review by its ID and associated listing ID.                                                                                                                                                                        |
| GET     | /users/signup                                                                                     | Render the signup form for users.                                                                                                                                                                                        |
| POST    | /users/signup                                                                                      | Handle user registration, including password hashing and saving to database.                                                                                                                                               |
| GET     | /listings/:id/reviews/:reviewId                                                          | Retrieve a specific review by its ID and associated listing ID.                                                                                                                                                             |
| PUT     | /listings/:listingId/reviews/:reviewId                                                       | Update an existing review for a specific listing with the provided IDs.                                                                                                                                                       |
| DELETE  | /users/logout                                                                                     | Log out the currently authenticated user.                                                                                                                                                                                |
| GET     | /users/login                                                                                      | Render the login form for users.                                                                                                                                                                                        |
| POST    | /users/login                                                                                      | Handle user authentication and session management.                                                                                                                                                                        |

## Request/Response Format

### Example Request Payloads
#### Create Listing:
```json
{
  "listing": {
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "location": "Malibu",
    "price": 1500,
    "country": "United States"
  }
}
```

#### Create Review:
```json
{
  "review": {
    "rating": 4.5,
    "comment": "Great place, loved the view and the staff was very friendly.",
    "listingId": "6883d0dea924b6ba92f5b9e5",
    "userId": "6883d0dea924b6ba92f5b9e5"
  }
}
```

### Example Response Payloads
#### Create Listing:
```json
{
  "_id": "6883d0dea924b6ba92f5b9e5",
  "title": "Cozy Beachfront Cottage",
  "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
  "location": "Malibu",
  "price": 1500,
  "country": "United States"
}
```

#### Create Review:
```json
{
  "_id": "6883d0dea924b6ba92f5b9e5",
  "rating": 4.5,
  "comment": "Great place, loved the view and the staff was very friendly.",
  "listingId": "6883d0dea924b6ba92f5b9e5",
  "userId": "6883d0dea924b6ba92f5b9e5"
}
```

## Error Handling

### Status Codes
- **401**: Unauthorized (Invalid credentials or session expired)
- **404**: Not Found (Resource not found)
- **500**: Internal Server Error (Unexpected error occurred)

### Response Format for Errors
```json
{
  "error": {
    "message": "Error message",
    "code": 401,
    "status": 401
  }
}
```

## Reference to Actual Route Files and Handler Names

- **Listing Endpoints**: `Traveloop\routes\listing.js`
- **Review Endpoints**: `Traveloop\routes\review.js`
- **User Endpoints**: `Traveloop\routes\user.js`