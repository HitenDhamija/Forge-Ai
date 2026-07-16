# API Reference

## Endpoints

| Method | Path                                                                                          | Description                                                                                                                                                                                                                      |
|--------|------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /listings/                                                                                            | Retrieve all listings.                                                                                                                                                                                                                  |
| POST    | /listings/new                                                                                     | Create a new listing.                                                                                                                                                                                                                        |
| PUT     | /listings/:id                                                                                     | Update an existing listing by ID.                                                                                                                                                                                                            |
| DELETE  | /listings/:id                                                                                     | Delete a listing by ID.                                                                                                                                                                                                                    |
| GET     | /reviews/:listingId                                                                               | Retrieve all reviews for a specific listing.                                                                                                                                                                                        |
| POST    | /reviews/:listingId                                                                               | Create a new review for a specific listing.                                                                                                                                                                                          |
| DELETE  | /reviews/:listingId/:reviewId                                                                      | Delete a specific review from a listing by both listing and review IDs.                                                                                                                                                |
| GET     | /users/signup/                                                                                        | Render the signup form for users.                                                                                                                                                                                                          |
| POST    | /users/signup/                                                                                        | Handle user registration with email, username, and password.                                                                                                                                                                        |
| GET     | /listings/:id/reviews/new                                                                               | Render a new review creation form for a specific listing.                                                                                                                                                                          |
| POST    | /listings/:id/reviews/new                                                                               | Create a new review for a specific listing using the authenticated user's information.                                                                                                                                    |
| GET     | /users/login/                                                                                        | Render the login form for users.                                                                                                                                                                                                          |
| POST    | /users/login/                                                                                        | Handle user authentication with email and password.                                                                                                                                                                                     |

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
    "comment": "Great place, loved the view and beach access."
  },
  "listingId": "6883d0dea924b6ba92f5b9e5"
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
  "comment": "Great place, loved the view and beach access.",
  "author": {
    "_id": "6883d0dea924b6ba92f5b9e5"
  },
  "listing": {
    "_id": "6883d0dea924b6ba92f5b9e5",
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "location": "Malibu",
    "price": 1500,
    "country": "United States"
  }
}
```

## Error Handling

### Status Codes
- **400**: Bad Request - Invalid request payload.
- **401**: Unauthorized - Authentication failure (e.g., invalid credentials).
- **403**: Forbidden - Insufficient permissions to perform the requested action.
- **404**: Not Found - Resource not found.
- **500**: Internal Server Error - Unexpected server error.

### Error Response Format
```json
{
  "error": {
    "message": "An unexpected error occurred."
  }
}
```

## Reference

### Route Files and Handler Names from the Code
- `app.js` for Express setup.
- `cloudConfig.js` for Cloudinary configuration.
- `middleware.js` for middleware functions like authentication checks.
- `schema.js` for Joi schema definitions.
- `controllers/listings.js`, `controllers/reviews.js`, `controllers/users.js` for route handlers in the controllers directory.
- `init/data.js` and `init/index.js` for initial data seeding.

### File Tree
```
Traveloop/
├── app.js
├── cloudConfig.js
├── controllers/
│   ├── listings.js
│   ├── reviews.js
│   └── users.js
├── init/
│   ├── data.js
│   └── index.js
├── middleware.js
├── models/
│   ├── listing.js
│   ├── review.js
│   └── user.js
├── package.json
├── public/
│   ├── css/
│   │   └── rating.css
│   │   └── style.css
│   └── js/
│       └── script.js
└── routes/
    ├── listing.js
    ├── review.js
    └── user.js
```