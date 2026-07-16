# Architecture

## Tech Stack
- Express: ^5.1.0
- MongoDB: mongoose@8.16.1
- Cloudinary: ^1.41.3
- Connect-Flash: ^0.1.1
- Connect-Mongo: ^5.1.0
- Cookie-Parser: ^1.4.7
- Dotenv: ^17.2.1
- EJS: ^3.1.10
- Method-OVERRIDE: ^3.0.0
- Passport: ^0.7.0
- Passport-Local: ^1.0.0
- Passport-Local-Mongoose: ^8.0.0

## Project Structure
- **Traveloop/app.js**: Entry point for the application, setting up middleware and routes.
- **Traveloop/cloudConfig.js**: Configures Cloudinary storage for file uploads.
- **Traveloop/controllers/listings.js**: Handles listing-related operations such as creating, showing, and deleting listings.
- **Traveloop/controllers/reviews.js**: Manages review creation and deletion functionalities.
- **Traveloop/controllers/users.js**: Provides user registration and login functionality.
- **Traveloop/init/data.js**: Initializes the database with sample data for testing purposes.
- **Traveloop/init/index.js**: Sets up mongoose connection to MongoDB.
- **Traveloop/middleware.js**: Contains middleware functions like isLoggedIn and saveredirectUrl.
- **Traveloop/models/listing.js**, **Traveloop/models/review.js**, **Traveloop/models/user.js**: Define the data models for listings, reviews, and users respectively.
- **Traveloop/package.json**: Specifies dependencies and scripts for the project.
- **Traveloop/public/css/rating.css**, **Traveloop/public/css/style.css**, **Traveloop/public/js/script.js**: Stylesheets and JavaScript files for frontend styling and functionality.
- **Traveloop/routes/listing.js**, **Traveloop/routes/review.js**, **Traveloop/routes/user.js**: Define routes for handling HTTP requests related to listings, reviews, and users respectively.
- **Traveloop/schema.js**: Defines data schemas using Joi library.
- **Traveloop/utils/ExpressError.js**: Utility file containing ExpressError class used for custom error responses.

## Data Flow
1. **Request Lifecycle**:
   - User makes a request through the browser to an endpoint defined in `app.js`.
   - Middleware functions like `isLoggedIn` and `saveredirectUrl` are executed.
   - Depending on the route, appropriate controller function is called (e.g., `listings`, `reviews`, or `users`).
   - The controller function interacts with the database through models (`listing.js`, `review.js`, `user.js`) to fetch, create, update, or delete data.
   - After processing, a response is generated and sent back to the client.

2. **Data Flow Through Application**:
   - User requests `/listings` route: 
     - Middleware checks if user is logged in (`isLoggedIn`).
     - Controller function `index` fetches all listings from database using `Listing.find({})`.
     - Response renders `listings/index.ejs` template with the fetched data.
   - User submits a new listing form:
     - Middleware ensures user is authenticated (`isLoggedIn`).
     - Controller function `renderNewform` generates an HTML form for creating a new listing.
   - User submits review on a listing page:
     - Middleware checks if user is logged in (`isLoggedIn`).
     - Controller function `createReview` creates a new review and associates it with the appropriate listing.

## Key Components
- **Listing**: Represents a listing, including title, description, location, price, country, images, etc.
  - File: **Traveloop/models/listing.js**
- **Review**: Represents a review for a listing, containing details about the reviewer and their feedback.
  - File: **Traveloop/models/review.js**
- **User**: Represents a user account with attributes like username, email, password, etc.
  - File: **Traveloop/models/user.js**

## Database Schema
### Listing Model
```javascript
const listingSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: { type: String, required: true },
    location: { type: String, required: true },
    price: { type: Number, required: true, min: 0 },
    country: { type: String, required: true },
    images: [String]
}, {
    timestamps: true
});

module.exports = mongoose.model('Listing', listingSchema);
```

### Review Model
```javascript
const reviewSchema = new mongoose.Schema({
    author: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    text: { type: String, required: true },
    rating: { type: Number, min: 1, max: 5 }
}, {
    timestamps: true
});

module.exports = mongoose.model('Review', reviewSchema);
```

### User Model
```javascript
const userSchema = new mongoose.Schema({
    username: { type: String, required: true },
    email: { type: String, required: true, unique: true },
    password: { type: String, required: true }
}, {
    timestamps: true
});

module.exports = mongoose.model('User', userSchema);
```

This architecture ensures a clean separation of concerns with clear responsibilities for each component and module. The use of Express middleware and routes allows for flexible routing management while maintaining the integrity of the application's flow. MongoDB is used as the primary database, providing scalability and flexibility in data storage and retrieval.