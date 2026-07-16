# API Reference

## Endpoints

| Method | Path                                                                                          | Description                                                                                                                                                                                                                           |
|--------|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET     | /listings/                                                                                            | Fetches all listings from the database and renders them in an ejs template.                                                                                                                                               |
| POST    | /listings/new/                                                                     | Creates a new listing form to be submitted for review by the admin.                                                                                                                                                    |
| GET     | /listings/:id                                                                                     | Displays details of a specific listing, including reviews and images.                                                                                                                                                   |
| DELETE   | /listings/:id/delete/                                                                    | Deletes a listing from the database. The listing must have been approved by an admin before deletion can occur.                                                                                                             |
| POST    | /listings/:id/reviews/new/                                                               | Allows users to submit a review for a specific listing, which is then saved and associated with the listing.                                                                                                                                 |
| GET     | /users/signup/                                                                               | Renders the signup form for new user registration.                                                                                                                                                                         |
| POST    | /users/signup/                                                                               | Registers a new user account and logs them in upon successful submission of the signup form.                                                                                                                                   |
| GET     | /listings/new/                                                                                | Displays the listing creation form to users who are logged in.                                                                                                                                                               |
| DELETE   | /logout/                                                                                    | Logs out the currently authenticated user.                                                                                                                                                                               |

## Request/Response Format

### Listing Index
- **Request**
  ```json
  {
    "method": "GET",
    "url": "/listings/",
    "headers": {},
    "body": null
  }
  ```
- **Response**
  ```json
  {
    "status": 200,
    "body": "<html><head></head><body><%- ejs.render('listings/index.ejs', { allListings }) %></body></html>"
  }
  ```

### Listing Show
- **Request**
  ```json
  {
    "method": "GET",
    "url": "/listings/:id",
    "headers": {},
    "body": null
  }
  ```
- **Response**
  ```json
  {
    "status": 200,
    "body": "<html><head></head><body><%- ejs.render('listings/show.ejs', { listing }) %></body></html>"
  }
  ```

### Listing Create Form
- **Request**
  ```json
  {
    "method": "GET",
    "url": "/listings/new/",
    "headers": {},
    "body": null
  }
  ```
- **Response**
  ```json
  {
    "status": 200,
    "body": "<html><head></head><body><%- ejs.render('listings/new.ejs', { listing: {} }) %></body></html>"
  }
  ```

### Listing Create
- **Request**
  ```json
  {
    "method": "POST",
    "url": "/listings/:id/reviews/new/",
    "headers": {},
    "body": {
      "review": {}
    }
  }
  ```
- **Response**
  ```json
  {
    "status": 201,
    "body": "<html><head></head><body>Review added successfully!</body></html>"
  }
  ```

### User Signup Form
- **Request**
  ```json
  {
    "method": "GET",
    "url": "/users/signup/",
    "headers": {},
    "body": null
  }
  ```
- **Response**
  ```json
  {
    "status": 200,
    "body": "<html><head></head><body><%- ejs.render('users/signup.ejs', { user: {} }) %></body></html>"
  }
  ```

### User Signup
- **Request**
  ```json
  {
    "method": "POST",
    "url": "/users/signup/",
    "headers": {},
    "body": {
      "username": "",
      "email": "",
      "password": ""
    }
  }
  ```
- **Response**
  ```json
  {
    "status": 201,
    "body": "<html><head></head><body>Welcome to Traveloop!</body></html>"
  }
  ```

### User Logout
- **Request**
  ```json
  {
    "method": "GET",
    "url": "/logout/",
    "headers": {},
    "body": null
  }
  ```
- **Response**
  ```json
  {
    "status": 200,
    "body": "<html><head></head><body>Logged out successfully.</body></html>"
  }
  ```

## Error Handling

### ExpressError
If an error occurs, it is handled by the `ExpressError` middleware. The response will include a status code and an error message.

- **Status Codes**
  - 401: Unauthorized (User not authenticated)
  - 403: Forbidden (Action not allowed for current user)
  - 500: Internal Server Error

### Example Response
```json
{
    "status": 401,
    "body": "<html><head></head><body>Unauthorized</body></html>"
}
```

## References

- `Traveloop/app.js`
- `Traveloop/controllers/listings.js`
- `Traveloop/controllers/reviews.js`
- `Traveloop/controllers/users.js`