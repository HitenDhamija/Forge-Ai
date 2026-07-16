# Architecture

## Tech Stack
- Express: ^5.1.0
- MongoDB: Driver version is not specified in package.json, but typically used as part of mongoose.
- Cloudinary: ^1.41.3
- Connect-Flash: ^0.1.1
- Connect-Mongo: ^5.1.0
- Cookie-Parser: ^1.4.7
- Dotenv: ^17.2.1
- EJS: ^3.1.10
- Method-OVERRIDE: ^3.0.0
- Mongoose: ^8.16.1
- Multer: ^2.0.2
- Multer-Storage-Cloudinary: ^4.0.0
- Passport: ^0.7.0
- Passport-Local: ^1.0.0
- Passport-Local-Mongoose: ^8.0.0

## Project Structure
- **Traveloop/app.js**: Entry point for the application, responsible for initializing Express and middleware.
- **Traveloop/cloudConfig.js**: Configures Cloudinary storage for file uploads.
- **Traveloop/controllers/listings.js**: Handles listing-related routes such as creating, showing, and deleting listings.
- **Traveloop/controllers/reviews.js**: Manages review creation and deletion.
- **Traveloop/controllers/users.js**: Manages user signup and login functionalities.
- **Traveloop/init/data.js**: Initializes the database with sample data for testing purposes.
- **Traveloop/init/index.js**: Connects to MongoDB and initializes the database by deleting existing entries and inserting sample data.
- **Traveloop/middleware.js**: Contains middleware functions like `isLoggedIn` which checks if a user is logged in before allowing them to create listings, or `saveredirectUrl` that saves the redirect URL for future use.
- **Traveloop/models/listing.js**, **Traveloop/models/review.js**, **Traveloop/models/user.js**: Define the data models for listings, reviews, and users respectively. These are likely Mongoose schemas.
- **Traveloop/utils/ExpressError.js**: Contains ExpressError class which is used to throw custom errors in routes.
- **Traveloop/utils/wrapAsync.js**: Wraps asynchronous functions with error handling.

## Data Flow
1. **User Interaction**: A user interacts with the application, whether it be signing up, logging in, or creating a listing.
2. **Authentication and Authorization**: If authentication is required (e.g., for creating listings), middleware checks if the user is logged in before allowing them to proceed.
3. **Data Handling**: Depending on the action taken by the user:
   - For users: User data is validated and saved into the database using Mongoose models (`user.js`).
   - For listings: Listing details are validated, stored in the database via Mongoose models (`listing.js`), and associated with reviews.
4. **Data Retrieval**: Data from the database (users, listings, reviews) is retrieved for display purposes or further processing.
5. **File Uploads**: File uploads to Cloudinary are handled through middleware configured in `cloudConfig.js`.
6. **Response Generation**: After data manipulation and retrieval, responses are generated using EJS templates (`ejs-mate`), which are rendered based on the route.

## Key Components
- **Listing Model**: Represents listings with fields like title, description, location, price, country, images, etc.
- **Review Model**: Represents reviews associated with a listing. Includes author and review details.
- **User Model**: Represents users with attributes such as username, email, password, etc.
- **Middleware Functions**:
  - `isLoggedIn`: Ensures only authenticated users can create listings or perform certain actions.
  - `saveredirectUrl`: Saves the redirect URL to be used for future redirections after a user action.

## Database Schema
### Listing Model
```javascript
const listingSchema = new mongoose.Schema({
    title: { type: String, required: true },
    description: { type: String, required: true },
    location: { type: String, required: true },
    price: { type: Number, required: true, min: 0 },
    country: { type: String, required: true },
    images: [{ type: String, default: null }]
}, {
    timestamps: true
});
```

### Review Model
```javascript
const reviewSchema = new mongoose.Schema({
    author: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
    listing: { type: mongoose.Schema.Types.ObjectId, ref: 'Listing' },
    text: { type: String, required: true },
    rating: { type: Number, min: 1, max: 5 }
}, {
    timestamps: true
});
```

### User Model
```javascript
const userSchema = new mongoose.Schema({
    username: { type: String, unique: true, required: true },
    email: { type: String, unique: true, required: true },
    password: { type: String, required: true }
}, {
    timestamps: true
});
```

This schema defines the structure of data stored in MongoDB for listings, reviews, and users respectively.