# Getting Started

## Overview
This project, identified by the ID `cbc73043-9b85-490a-968d-1b211cfe7d1e`, is an Express application that integrates MongoDB for data storage. It provides functionalities such as user authentication (using Passport Local Mongoose), listing creation, and review submission. The project uses Cloudinary for image uploads.

## Prerequisites
The following software and versions are required to run this project:

- Node.js: `22.12.0`
- MongoDB: `mongodb://127.0.0.1:27017/Traveloop`

Ensure these environments are set up before proceeding with the installation steps.

## Installation
To install and start your application, follow these steps:

### Step 1: Install Dependencies
First, navigate to the project directory:
```bash
cd cbc73043-9b85-490a-968d-1b211cfe7d1e
```
Then install all dependencies using npm/yarn:
```bash
npm install
# or if you are using yarn, replace the above command with:
yarn install
```

### Step 2: Start MongoDB
Ensure that MongoDB is running. You can start it by executing the following command in your terminal:
```bash
mongod
```
This will start a local instance of MongoDB.

### Step 3: Run the Application
Start the Express server using npm/yarn:
```bash
npm run dev
# or if you are using yarn, replace the above command with:
yarn dev
```

## Running the App
The application is now running on `http://localhost:3000`. You can access it in your browser to see how everything works.

## Project Structure

### Directory Layout
Here's a breakdown of the directory structure:

- **Traveloop/app.js**: Entry point for the Express server.
- **Traveloop/cloudConfig.js**: Configuration file for Cloudinary, handling image uploads.
- **Traveloop/controllers/listings.js**: Controller for listing-related operations.
- **Traveloop/controllers/reviews.js**: Controller for review-related operations.
- **Traveloop/controllers/users.js**: Controller for user-related operations (sign-up and login).
- **Traveloop/init/data.js**: Data initialization script to populate the database with sample listings.
- **Traveloop/init/index.js**: Entry point for initializing MongoDB connection and data population.
- **Traveloop/middleware.js**: Middleware functions, including authentication checks.
- **Traveloop/models/listing.js**: Model definition for listing documents.
- **Traveloop/models/review.js**: Model definition for review documents.
- **Traveloop/models/user.js**: Model definition for user documents.
- **Traveloop/package.json**: Project configuration file specifying dependencies and scripts.
- **Traveloop/public/css/rating.css**: CSS styling for rating functionality.
- **Traveloop/public/css/style.css**: General application style sheet.
- **Traveloop/public/js/script.js**: Application JavaScript code.
- **Traveloop/routes/listing.js**: Route definitions for listing-related operations.
- **Traveloop/routes/review.js**: Route definitions for review-related operations.
- **Traveloop/routes/user.js**: Route definitions for user-related operations (sign-up and login).
- **Traveloop/schema.js**: Schema definition files, including `listingSchema` and `reviewSchema`.
- **Traveloop/utils/ExpressError.js**: Custom error handling utility.
- **Traveloop/utils/wrapAsync.js**: Utility to wrap asynchronous functions.

### File Layout
Here are the actual file names and their locations:

#### Traveloop/app.js
```javascript
// Traveloop/app.js

if (process.env.NODE_ENV !== "production") {
    require('dotenv').config();
}

const express = require('express');
const app = express();
const mongoose = require("mongoose");
const path = require("path");
const methodOverride = require("method-override");
const ejsMate = require("ejs-mate");
const ExpressError = require("./utils/ExpressError.js");

// Middleware
app.use(express.urlencoded({ extended: true }));
app.use(methodOverride("_method"));
app.engine('ejs', ejsMate);
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Routes
const listingsController = require('./controllers/listings');
const reviewsController = require('./controllers/reviews');
const usersController = require('./controllers/users');

app.use('/listings', listingsController);
app.use('/reviews', reviewsController);
app.use('/users', usersController);

// Connect to MongoDB
mongoose.connect(process.env.MONGO_URL, {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// Error Handling Middleware
app.use((req, res, next) => {
    const error = new ExpressError("Not Found", 404);
    return next(error);
});

app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).send('Something broke!');
});

module.exports = app;
```

#### Traveloop/cloudConfig.js
```javascript
// Traveloop/cloudConfig.js

const cloudinary = require('cloudinary').v2;
const { CloudinaryStorage } = require('multer-storage-cloudinary');

cloudinary.config({
    cloud_name: process.env.CLOUD_NAME,
    api_key: process.env.CLOUD_API_KEY,
    api_secret: process.env.CLOUD_API_SECRET
});

const storage = new CloudinaryStorage({
    cloudinary,
    params: {
        folder: 'Traveloop_Dev',
        allowed_formats: ['png', 'jpg', 'jpeg']
    }
});

module.exports = {
    cloudinary,
    storage
};
```

#### Traveloop/controllers/listings.js
```javascript
// Traveloop/controllers/listings.js

const Listing = require("../models/listing");

module.exports.index = async (req, res) => {
    const allListings = await Listing.find({});
    res.render("listings/index.ejs", { allListings });
}

module.exports.renderNewform = (req, res) => {
    res.render("listings/new.ejs");
}

module.exports.showListing = async (req, res) => {
    let id = req.params.id;
    const listing = await Listing.findById(id)
        .populate({ path: "reviews", populate: { path: "author" } })
        .populate("owner");

    if (!listing) {
        req.flash("error", "The listing you requested does not exist!");
        res.redirect("/listings");
    }

    res.render("listings/show.ejs", { listing });
}
```

#### Traveloop/controllers/reviews.js
```javascript
// Traveloop/controllers/reviews.js

const Listing = require("../models/listing");
const Review = require("../models/review");

module.exports.createReview = async (req, res) => {
    console.log(req.params.id);
    let listing = await Listing.findById(req.params.id);
    let newReview = new Review(req.body.review);
    newReview.author = req.user._id;
    listing.reviews.push(newReview);
    await newReview.save();
    await listing.save();

    req.flash('success', 'Review added successfully!');
    res.redirect(`/listings/${listing._id}`);
}

module.exports.destroyReview = async (req, res) => {
    let { id, reviewId } = req.params;
    const review = await Review.findById(reviewId);
    if (!review) return res.status(404).send("Review not found");

    listing.reviews.pull(review);
    await review.remove();
    await listing.save();

    req.flash('success', 'Review deleted successfully!');
    res.redirect(`/listings/${id}`);
}
```

#### Traveloop/controllers/users.js
```javascript
// Traveloop/controllers/users.js

const User = require("../models/user");

module.exports.renderSignupForm = (req, res) => {
    res.render("users/signup.ejs");
}

module.exports.signup = async (req, res, next) => {
    try {
        let { username, email, password } = req.body;
        const newUser = new User({ username, email });
        const registeredUser = await User.register(newUser, password);

        console.log(registeredUser);
        req.login(registeredUser, (err) => {
            if (err) {
                return next(err);
            }
            req.flash("success", "Welcome to Traveloop !");
            res.redirect("/listings");
        });
    } catch (error) {
        req.flash("error", error.message);
        res.render("users/signup.ejs", { errorMessage: error.message });
    }
}
```

#### Traveloop/init/data.js
```javascript
// Traveloop/init/data.js

const sampleListings = [
  {
    title: "Cozy Beachfront Cottage",
    description:
      "Escape to this charming beachfront cottage for a relaxing getaway. Enjoy stunning ocean views and easy access to the beach.",
    image: {
      filename: "listingimage",
      url: "https://images.unsplash.com/photo-1552733407-5d5c46c3bb3b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTB8fHRyYXZlbHxlbnwwfHwwfHx8MA%3D%3D&auto=format&fit=crop&w=800&q=60"
    },
    price: 150,
    bedrooms