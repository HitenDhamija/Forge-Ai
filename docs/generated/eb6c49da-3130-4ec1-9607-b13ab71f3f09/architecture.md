# Architecture

## Tech Stack
- **Node.js**: Version 22.12.0 (as specified in `package.json`)
- **Express**: Version 5.1.0 (as specified in `package.json`)
- **MongoDB**: Version not explicitly stated, but assumed to be the default MongoDB version compatible with Node.js.
- **Cloudinary**: Version 1.41.3 (as specified in `package.json`)
- **Connect-Flash**: Version 0.1.1 (as specified in `package.json`)
- **Connect-Mongo**: Version 5.1.0 (as specified in `package.json`)
- **Cookie-Parser**: Version 1.4.7 (as specified in `package.json`)
- **Dotenv**: Version 17.2.1 (as specified in `package.json`)
- **EJS**: Version 3.1.10 (as specified in `package.json`)
- **Express-Session**: Version 1.18.2 (as specified in `package.json`)
- **Joi**: Version 17.13.3 (as specified in `package.json`)
- **Method-OVERRIDE**: Version 3.0.0 (as specified in `package.json`)
- **Mongoose**: Version 8.16.1 (as specified in `package.json`)
- **Multer**: Version 2.0.2 (as specified in `package.json`)
- **Multer-Storage-Cloudinary**: Version 4.0.0 (as specified in `package.json`)
- **Passport**: Version 0.7.0 (as specified in `package.json`)
- **Passport-Local**: Version 1.0.0 (as specified in `package.json`)
- **Passport-Local-Mongoose**: Version 8.0.0 (as specified in `package.json`)

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
│   └── js/
│       └── script.js
└── routes/
    ├── listing.js
    ├── review.js
    └── user.js
```

## Data Flow
The data flow in the application is as follows:

1. **User Request**: A request is made to the server, which can be either a GET or POST request.
2. **Routing**: The Express router (`app.js`) routes the incoming requests based on their paths and dispatches them to appropriate controller functions.
3. **Controller Functions**: These functions handle business logic such as fetching data from the database, creating new records, updating existing ones, etc., and return a response object containing either an HTML template for rendering or JSON objects representing HTTP responses.
4. **Middleware**: Middleware is used throughout the application to perform tasks like authentication checks (`isLoggedIn`), error handling (`ExpressError`), setting up session management (`saveredirectUrl`), and more.
5. **Database Interaction**: Data manipulation (CRUD operations) happens through Mongoose models, which are connected to MongoDB via Mongoose middleware in `init/index.js`.
6. **Response Handling**: After processing the request, the controller returns a response object that includes either an HTML template or JSON data. If it's an HTML template, Express uses EJS for rendering.
7. **Rendering and Serving**: The rendered templates are served to the client via Express.

## Key Components
- **App.js**: Entry point of the application where all middleware is loaded, session management is set up, and routes are defined.
- **Controllers**:
  - **listings.js**: Handles requests related to listing data (CRUD operations).
  - **reviews.js**: Manages review-related requests.
  - **users.js**: Deals with user-related requests including signup and login functionalities.
- **Middleware**:
  - **isLoggedIn**: Ensures that only authenticated users can create listings or reviews.
  - **saveredirectUrl**: Saves the original URL to be used for redirecting after form submissions.
- **Models**:
  - **listing.js**: Represents a listing model with fields like title, description, location, price, country, and images.
  - **review.js**: Defines review-related attributes including author information.
  - **user.js**: Contains user-specific data such as username, email, password, etc.
- **Routes**:
  - **listing.js**: Routes for listing management (CRUD).
  - **review.js**: Handles reviews related requests.
  - **user.js**: Manages user-related routes including signup and login.

## Database Schema
The database schema is defined using Mongoose models as follows:

### Listing Model (`models/listing.js`)
```javascript
const mongoose = require('mongoose');
const Joi = require('joi');

const listingSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  location: { type: String, required: true },
  price: { type: Number, required: true, min: 0 },
  country: { type: String, required: true },
  images: [{ type: String }]
});

module.exports = mongoose.model('Listing', listingSchema);
```

### Review Model (`models/review.js`)
```javascript
const mongoose = require('mongoose');
const Joi = require('joi');

const reviewSchema = new mongoose.Schema({
  author: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  rating: { type: Number, required: true, min: 1, max: 5 },
  comment: { type: String }
});

module.exports = mongoose.model('Review', reviewSchema);
```

### User Model (`models/user.js`)
```javascript
const mongoose = require('mongoose');
const Joi = require('joi');

const userSchema = new mongoose.Schema({
  username: { type: String, required: true },
  email: { type: String, required: true, unique: true }
});

module.exports = mongoose.model('User', userSchema);
```

This schema defines the structure of data that will be stored in MongoDB for listings, reviews, and users respectively.