# Getting Started

## Overview
This project, identified by the UUID `4abfb9af-bbf2-453b-9681-dc19d29960bc`, is an Express application that integrates with MongoDB for data storage and management. It also utilizes Cloudinary for image uploads and Passport.js for authentication. The purpose of this project is to provide a platform where users can create listings, manage reviews, and authenticate themselves.

## Prerequisites
- Node version: `22.12.0`
- MongoDB database

## Installation
To install the necessary dependencies, run the following commands in your terminal:

```bash
# Install npm packages (using yarn as per package.json)
yarn install

# Or if you prefer to use npm
npm install
```

## Running the App
To start the development server, execute the following command:

```bash
# Start the Express app with nodemon for auto-restart on file changes
yarn dev:app
```

Alternatively, if you are using `npm`:

```bash
npm run dev:app
```

This will start a local development server at `http://localhost:3000`.

## Project Structure

### Application Files and Directories

- **Traveloop/app.js**: The main application file where Express is initialized.
  - This file sets up the environment based on the value of `process.env.NODE_ENV`.
  - It requires necessary modules like Express, Mongoose, EJS for rendering views, and middleware functions.

- **Traveloop/cloudConfig.js**: Configures Cloudinary to handle image uploads. The configuration uses environment variables stored in `.env` files.
  - This file is crucial for integrating Cloudinary with your application.

- **Traveloop/controllers/listings.js**: Contains routes related to listings (e.g., listing creation, retrieval).
  - Functions include `index`, which fetches all listings from the database and renders them on a template; `renderNewform` which displays a form for creating new listings; and `showListing`, which retrieves details of a specific listing.

- **Traveloop/controllers/reviews.js**: Handles reviews related operations.
  - This includes functions like `createReview` to add a review, and `destroyReview` to remove a review from a listing.

- **Traveloop/controllers/users.js**: Manages user authentication and signup functionalities.
  - Functions include `renderSignupForm`, which renders the signup form; and `signup`, which handles the creation of new users with password hashing.

- **Traveloop/init/data.js**: Contains sample data for testing purposes. This file is not used in production but can be useful during development to populate the database quickly.

### Directory Layout

Here's a breakdown of the directory structure:

```
Traveloop/
├── app.js
├── cloudConfig.js
├── controllers/
│   ├── listings.js
│   ├── reviews.js
│   └── users.js
├── init/
│   └── data.js
├── middleware.js
├── models/
│   ├── listing.js
│   ├── review.js
│   └── user.js
├── package-lock.json
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

### Configuration Files

- **Traveloop/package.json**: Specifies the dependencies and scripts for your project.
  - The `engines` section ensures that Node version `22.12.0` is used.
  - Dependencies like Express, Mongoose, Cloudinary, Passport, etc., are listed under `dependencies`.

### Code Samples

- **Traveloop/app.js**: Initializes the application and sets up environment variables based on `process.env.NODE_ENV`.
  ```javascript
  if (process.env.NODE_ENV !== "production") {
      require('dotenv').config();
  }
  
  const express = require('express');
  const app = express();

  // Other configurations...
  ```

- **Traveloop/cloudConfig.js**: Configures Cloudinary for image uploads.
  ```javascript
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

- **Traveloop/middleware.js**: Defines middleware functions for handling user sessions and authentication.
  ```javascript
  const Listing = require("../models/listing");
  const Review = require("../models/review");
  const { listingSchema, reviewSchema } = require('./schema.js');
  const ExpressError = require("./utils/ExpressError.js");

  module.exports.isLoggedIn = (req, res, next) => {
      if (!req.isAuthenticated()) {
          req.session.redirectUrl = req.originalUrl;
          req.flash("error", "You must be logged in to create listing!");
          return res.redirect("/login");
      }
      next();
  };

  module.exports.saveredirectUrl = (req, res, next) => {
      if (req.session.redirectUrl) {
          res.locals.redirectUrl = req.session.redirectUrl;
      }
      next();
  };
  ```

- **Traveloop/schema.js**: Defines schemas for Mongoose models.
  ```javascript
  const Joi = require('joi');
  const joi = require('joi');

  module.exports.listingSchema = Joi.object({
      listing: Joi.object({
          title: Joi.string().required(),
          description: Joi.string().required(),
          location: Joi.string().required(),
          price: Joi.number().required().min(0),
          country: Joi.string().required(),
          images: Joi.array().items(Joi.string()).allow(null)
      }).required()
  });

  module.exports.reviewSchema = joi.object({
      review: Joi.object({
          // Schema for review model
      })
  });
  ```

- **Traveloop/controllers/listings.js**: Contains routes and functions related to listings.
  ```javascript
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
          res.redirect("/listings/new");
      }
  }
  ```

- **Traveloop/controllers/reviews.js**: Handles review-related operations.
  ```javascript
  const Listing = require("../models/listing");
  const Review = require("../models/review");

  module.exports.createReview = async (req, res) => {
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
      const reviewToDelete = await Review.findById(reviewId);
      if (!reviewToDelete) {
          return res.status(404).send("Review not found");
      }
      listing.reviews.pull(reviewToDelete);
      await reviewToDelete.remove();
      await listing.save();
      req.flash('success', 'Review removed successfully!');
      res.redirect(`/listings/${id}`);
  }
  ```

- **Traveloop/controllers/users.js**: Manages user authentication and signup functionalities.
  ```javascript
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
          req.flash('error', 'Registration failed. Please try again.');
          res.redirect('/users/signup');
      }
  }
  ```

- **Traveloop/init/data.js**: Contains sample data for testing purposes.
  ```javascript
  const Listing = require("../models/listing");

  module.exports.sampleListings = [
    {
        title: