# Architecture

## Tech Stack
- Express: ^5.1.0
- MongoDB: Mongoose ^8.16.1
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

### Request Lifecycle
1. **Client-Side**: Client sends a request to the server.
2. **Middleware**: Express middleware (e.g., `isLoggedIn`, `saveredirectUrl`) are applied, handling authentication and redirecting if necessary.
3. **Routing**: Routes (`listing.js`, `review.js`, `user.js`), defined in `Traveloop/routes/`, handle requests based on the HTTP method and route path.
4. **Controllers**: Controllers (e.g., `listings.js`, `reviews.js`, `users.js`) are called to process business logic, such as fetching data from MongoDB or creating new records.
5. **Models**: Models (`listing.js`, `review.js`, `user.js`) interact with the database using Mongoose for schema validation and CRUD operations.
6. **Response**: Controllers return a response object that includes rendered views (using EJS) or JSON responses.

### Key Components
- **App.js**: Entry point of the application, where Express is initialized and middleware are configured.
- **Controllers**: Handle specific business logic like listing creation, review submission, user registration, etc. Each controller file corresponds to a route in `routes/`.
- **Models**: Define data structures using Mongoose schemas for entities such as listings, reviews, and users.
- **Middleware.js**: Contains utility functions that handle common tasks like authentication (`isLoggedIn`) and redirecting after form submissions (`saveredirectUrl`).
- **Routes**: Define routes for different HTTP methods (GET, POST, PUT, DELETE) to map URLs to controllers.

## Database Schema

### Listing Model
```javascript
const listingSchema = new mongoose.Schema({
  title: { type: String, required: true },
  description: { type: String, required: true },
  location: { type: String, required: true },
  price: { type: Number, required: true, min: 0 },
  country: { type: String, required: true },
  images: [{ type: String }],
  owner: { type: mongoose.Schema.Types.ObjectId, ref: 'User' }
}, {
  timestamps: true
});
```

### Review Model
```javascript
const reviewSchema = new mongoose.Schema({
  author: { type: mongoose.Schema.Types.ObjectId, ref: 'User' },
  listing: { type: mongoose.Schema.Types.ObjectId, ref: 'Listing' },
  content: { type: String, required: true },
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

These schemas are defined in `Traveloop/models/` and used by the models to interact with MongoDB.