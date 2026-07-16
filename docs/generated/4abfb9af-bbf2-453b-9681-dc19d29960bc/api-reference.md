# API Reference

## Endpoints

| Method | Path                                                                                          | Description                                                                                                                                                                                                                           |
|--------|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /listings/                                                                                            | Fetches all listings from the database.                                                                                                                                                                                              |
| POST    | /listings/new                                                                                     | Creates a new listing and saves it to the database.                                                                                                                                                                                  |
| PUT     | /listings/:id                                                                                      | Updates an existing listing with the provided data. The `:id` parameter is required to identify which specific listing should be updated.                                                                                       |
| DELETE  | /listings/:id                                                                                     | Deletes a listing from the database identified by the `:id` parameter.                                                                                                                                                                |
| GET     | /reviews/                                                                                            | Fetches all reviews associated with listings, including details about the author and the listing owner.                                                                                                                                 |
| POST    | /reviews/:listingId/review/new                                                               | Creates a new review for a specific listing and saves it to the database. The `:listingId` parameter is required to identify which listing's review should be created.                                                                 |
| DELETE  | /reviews/:reviewId/delete                                                                   | Deletes a review from the database identified by the `:reviewId` parameter.                                                                                                                                                                |
| GET     | /users/signup/                                                                                        | Renders the signup form for users.                                                                                                                                                                                                |
| POST    | /users/signup/new                                                                                   | Registers a new user and logs them in, then redirects to listings page after successful registration.                                                                                                                                 |
| GET     | /listings/:id/reviews/new                                                                               | Renders the review creation form for a specific listing identified by `:id`.                                                                                                                                                             |

## Request/Response Format

### Create Listing
**Request Payload**
```json
{
  "title": "Cozy Beachfront Cottage",
  "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
  "location": "Malibu",
  "price": 1500,
  "country": "United States"
}
```

**Response Payload**
```json
{
  "_id": "63f789d24b5e8a001c7d89a2",
  "title": "Cozy Beachfront Cottage",
  "description": "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
  "location": "Malibu",
  "price": 1500,
  "country": "United States",
  "__v": 0
}
```

### Create Review
**Request Payload**
```json
{
  "review": {
    "rating": 4.5,
    "comment": "Great place, loved the view and the staff was very friendly."
  }
}
```

**Response Payload**
```json
{
  "_id": "63f789d24b5e8a001c7d89a3",
  "rating": 4.5,
  "comment": "Great place, loved the view and the staff was very friendly.",
  "__v": 0
}
```

## Error Handling

### ExpressError
Errors are handled using `ExpressError` middleware which is defined in `utils/ExpressError.js`. The error object contains a status code (400 for bad request, 500 for internal server errors) and an error message. For example:

```javascript
module.exports = function (err, req, res, next) {
    const { statusCode, message } = err;
    res.status(statusCode || 500).json({ error: message });
};
```

### Error Status Codes
- **400 Bad Request**: When the request is malformed or missing required parameters.
- **500 Internal Server Error**: When an unexpected error occurs on the server side.

### Example of Error Handling in `listing.js`
```javascript
module.exports.createReview = async (req, res) => {
    try {
        const { listingId } = req.params;
        let listing = await Listing.findById(listingId);
        if (!listing) {
            throw new ExpressError("Listing not found", 404);
        }
        
        // Additional validation and logic
        const review = new Review(req.body.review);
        review.author = req.user._id; // Assuming `req.user` is a valid user object

        listing.reviews.push(review);
        await listing.save();
        res.status(201).json({ message: "Review added successfully", review });
    } catch (err) {
        return next(err);
    }
};
```

### Error Handling in `user.js`
```javascript
module.exports.signup = async (req, res, next) => {
    try {
        const { username, email, password } = req.body;
        const newUser = new User({ username, email });
        const registeredUser = await User.register(newUser, password);

        req.login(registeredUser, (err) => {
            if (err) {
                return next(err);
            }
            res.redirect("/listings");
        });

    } catch (err) {
        const error = new ExpressError("Invalid Credentials", 400);
        return next(error);
    }
};
```

These examples demonstrate how errors are handled and returned in the API.