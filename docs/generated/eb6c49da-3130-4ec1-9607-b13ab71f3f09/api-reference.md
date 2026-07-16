# API Reference

## Endpoints

| Method | Path                                                                                     | Description                                                                                                                                                                                                                           |
|--------|-----------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /listings/                                                                                 | Fetches all listings from the database.                                                                                                                                                                                           |
| POST    | /listings/new                                                                               | Creates a new listing and redirects to the index page of listings after successful creation.                                                                                                                                 |
| PUT     | /listings/:id                                                                              | Updates an existing listing with the provided data.                                                                                                                                                                                |
| DELETE  | /listings/:id                                                                              | Deletes a specific listing from the database.                                                                                                                                                                                        |
| GET     | /reviews/:listingId                                                                 | Fetches all reviews for a specific listing, including details about the reviewer and author of each review.                                                                                                                             |
| POST    | /reviews/:listingId/new                                                                      | Creates a new review for a specific listing by the authenticated user.                                                                                                                                                             |
| DELETE  | /reviews/:listingId/:reviewId                                                               | Deletes a specific review from a listing associated with the authenticated user.                                                                                                                                                  |
| GET     | /users/signup                                                                               | Renders the signup form for users to create an account.                                                                                                                                                                    |
| POST    | /users/signup/new                                                                             | Registers a new user and logs them in, then redirects to the listings page after successful registration.                                                                                                                              |
| GET     | /listings/:id/                                                                                 | Fetches details of a specific listing by its ID.                                                                                                                                                                                        |
| PUT     | /listings/:id/edit                                                                               | Edits an existing listing with the provided data and updates it in the database.                                                                                                                                                      |
| DELETE  | /listings/:id/delete                                                                             | Deletes a specific listing from the database.                                                                                                                                                                                        |

## Request/Response Format

### GET /listings/
**Request:**
```json
{
    "query": {
        "sort_by": "title",
        "order": "asc"
    }
}
```

**Response:**
```json
[
  {
    "_id": "6429f81c50b7a3e2d59f66d4",
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States",
    "__v": 0
  }
]
```

### POST /listings/new
**Request:**
```json
{
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States"
}
```

**Response:**
```json
{
    "_id": "6429f81c50b7a3e2d59f66d4",
    "__v": 0,
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States"
}
```

### PUT /listings/:id
**Request:**
```json
{
    "title": "Updated Cozy Beachfront Cottage",
    "description": "Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "updated-listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States"
}
```

**Response:**
```json
{
    "_id": "6429f81c50b7a3e2d59f66d4",
    "__v": 0,
    "title": "Updated Cozy Beachfront Cottage",
    "description": "Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "updated-listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States"
}
```

### DELETE /listings/:id
**Request:**
```json
{
    "id": "6429f81c50b7a3e2d59f66d4"
}
```

**Response:**
```json
{
    "_id": "6429f81c50b7a3e2d59f66d4",
    "__v": 0,
    "title": "Cozy Beachfront Cottage",
    "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    "image": {
      "filename": "listingimage",
      "url": "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    "price": 1500,
    "location": "Malibu",
    "country": "United States"
}
```

### GET /reviews/:listingId
**Request:**
```json
{
    "id": "6429f81c50b7a3e2d59f66d4"
}
```

**Response:**
```json
[
  {
    "_id": "6429f81c50b7a3e2d59f66d5",
    "author": "6429f81c50b7a3e2d59f66d3",
    "review": {
      "title": "Great Stay!",
      "description": "The cottage was perfect for a weekend getaway. The location is great and the view from the balcony is breathtaking.",
      "rating": 4
    },
    "__v": 0,
    "listingId": "6429f