# Architecture

## Tech Stack
- **Node.js**: Version `22.12.0`
- **Express**: Version `5.1.0`
- **MongoDB**: Version `8.16.1`
- **Cloudinary**: Version `1.41.3`
- **EJS**: Version `3.1.10`
- **Multer**: Version `2.0.2`
- **Multer-Storage-Cloudinary**: Version `4.0.0`
- **Passport**: Version `0.7.0`
- **Passport-Local-Mongoose**: Version `8.0.0`
- **Joi**: Version `17.13.3`

## Project Structure
The project is organized as follows:
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
│   ├── index.js
├── middleware.js
├── models/
│   ├── listing.js
│   ├── review.js
│   └── user.js
├── package-lock.json
├── package.json
├── public/
│   ├── css/
│   │   ├── rating.css
│   │   └── style.css
│   └── js/
│       └── script.js
└── routes/
    ├── listing.js
    ├── review.js
    └── user.js
```

## Data Flow
The request lifecycle in the application involves several steps:
1. **Request**: The client sends a request to the server.
2. **Middleware Execution**: Middleware functions are executed, including authentication checks and error handling.
3. **Routing**: Express routes match the incoming request based on URL patterns.
4. **Controller Execution**: Controller functions handle business logic specific to each route.
5. **Model Operations**: Model operations (like finding or saving data) may be performed within controllers.
6. **Rendering**: The response is rendered using EJS templates, with data passed from controllers and models.
7. **Response**: The server sends the response back to the client.

## Key Components
### Main Modules/Classes and Their Responsibilities:
- **app.js** - Entry point of the application, initializes Express app and middleware.
- **controllers/** - Contains all controller functions for handling HTTP requests. For example, `listings.js` handles listing-related operations.
- **middleware.js** - Contains middleware functions that handle authentication (`isLoggedIn`) and redirecting after form submissions (`saveredirectUrl`).
- **models/** - Contains data models (e.g., `listing.js`, `review.js`, `user.js`). These are used for database interactions.
- **routes/** - Contains route definitions, mapping URLs to controller functions. For example, `listing.js` defines routes related to listings.

## Database Schema
The schema for the main entities is defined in the models directory:
### Listing Model
```javascript
const mongoose = require("mongoose");
const Joi = require('joi');

module.exports.listingSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  location: { type: String, required: true },
  price: { type: Number, required: true, min: 0 },
  country: { type: String, required: true },
  images: [{ type: String }],
});

const Listing = mongoose.model("Listing", listingSchema);
module.exports.Listing = Listing;
```

### Review Model
```javascript
const mongoose = require("mongoose");
const Joi = require('joi');

module.exports.reviewSchema = new mongoose.Schema({
  author: { type: mongoose.Schema.Types.ObjectId, ref: "User" },
  rating: { type: Number, required: true, min: 1, max: 5 },
  comment: { type: String },
});

const Review = mongoose.model("Review", reviewSchema);
module.exports.Review = Review;
```

### User Model
```javascript
const mongoose = require("mongoose");
const Joi = require('joi');

module.exports.userSchema = new mongoose.Schema({
  username: { type: String, required: true, unique: true },
  email: { type: String, required: true, unique: true },
  password: { type: String, required: true },
});

const User = mongoose.model("User", userSchema);
module.exports.User = User;
```

Each schema uses Joi for data validation. The `images` field in the `listingSchema` is an array of image URLs.

This architecture ensures that each component has a clear responsibility and integrates well with the database using Mongoose, which simplifies working with MongoDB collections through JavaScript objects.