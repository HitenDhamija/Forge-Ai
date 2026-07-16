# Getting Started

## Overview
This project, identified by the UUID `508eafc7-c5ce-47ab-8818-1c89d6a1b01e`, is a travel booking application built using Express.js as its web framework and MongoDB for database operations. The purpose of this project is to provide users with an easy-to-use platform where they can list their accommodations, view other listings, leave reviews, and manage user accounts.

## Prerequisites
- Node version: `22.12.0`
- MongoDB server running on `localhost` at port `27017`

## Installation
To set up the project locally, follow these steps:

### Step 1: Install Dependencies
First, ensure you have a package manager installed (npm or yarn). Then install all dependencies using npm:
```bash
npm install
```
or if you are using Yarn:
```bash
yarn install
```

### Step 2: Start the Development Server
Start the development server by running the following command in your terminal:
```bash
npm run dev
```
This will start a local web server on `http://localhost:3000`. You can also use Yarn if you prefer:
```bash
yarn dev
```

## Running the App

### Step 1: Start MongoDB Server
Ensure that your MongoDB server is running. If it's not already running, you can start it using the following command:
```bash
mongod --dbpath /data/db
```
This assumes that MongoDB is configured to use `/data/db` as its data directory.

### Step 2: Run the Development Server
Once MongoDB is up and running, run the development server by executing the following command in your project root folder:
```bash
npm run dev
```
or if you are using Yarn:
```bash
yarn dev
```

## Project Structure

The project structure is organized as follows:

### Directory Layout
- **Traveloop**: The main directory of the application.
  - **app.js**: Entry point for Express server.
  - **cloudConfig.js**: Configuration file for Cloudinary storage.
  - **controllers**: Contains controller functions for handling API routes.
    - **listings.js**
    - **reviews.js**
    - **users.js**
  - **middleware.js**: Middleware functions to handle authentication and other common tasks.
  - **models**: Defines the structure of data models using Mongoose.
    - **listing.js**
    - **review.js**
    - **user.js**
  - **package.json**: Contains scripts for development, testing, etc.
  - **public**: Static files served by Express server (CSS and JS).
    - **css**: Stylesheets
      - **rating.css**
      - **style.css**
    - **js**: JavaScript files
      - **script.js**
  - **routes**: Routes configuration file for Express routes.
    - **listing.js**
    - **review.js**
    - **user.js**
  - **schema.js**: Schemas for Mongoose models.
  - **utils**: Utility functions used throughout the application.
    - **ExpressError.js**
  - **init**: Initialization files.
    - **data.js**
    - **index.js**

### File Layout
- **Traveloop/app.js**:
  ```javascript
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
  const listingMiddleware = require('./middleware/listing');
  const reviewMiddleware = require('./middleware/review');
  const userMiddleware = require('./middleware/user');

  app.set('view engine', 'ejs');
  app.engine('.ejs', ejsMate);

  mongoose.connect(process.env.MONGO_URL, {
    useNewUrlParser: true,
    useUnifiedTopology: true
  });

  // Routes
  const listingRoutes = require('./routes/listing');
  const reviewRoutes = require('./routes/review');
  const userRoutes = require('./routes/user');

  app.use(methodOverride('_method'));
  app.use(express.urlencoded({ extended: false }));
  app.use(express.json());
  app.use(express.static(path.join(__dirname, 'public')));
  
  // Middleware
  app.use(listingMiddleware.isLoggedIn);
  app.use(reviewMiddleware.saveredirectUrl);

  // Routes
  app.use('/listings', listingRoutes);
  app.use('/reviews', reviewRoutes);
  app.use('/users', userRoutes);

  const PORT = process.env.PORT || 3000;
  app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
  });
  ```

- **Traveloop/cloudConfig.js**:
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

- **Traveloop/middleware.js**:
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
      } else {
          delete req.session.redirectUrl;
      }
      next();
  };
  ```

- **Traveloop/controllers/listings.js**:
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
          return res.redirect("/listings");
      }

      res.render("listings/show.ejs", { listing });
  }
  ```

- **Traveloop/controllers/reviews.js**:
  ```javascript
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
      const reviewToDelete = await Review.findById(reviewId);
      if (!reviewToDelete) {
          return res.status(404).send("Review not found.");
      }
      
      listing.reviews.pull(reviewToDelete);
      await reviewToDelete.remove();
      await listing.save();

      req.flash('success', 'Review deleted successfully!');
      res.redirect(`/listings/${id}`);
  }
  ```

- **Traveloop/controllers/users.js**:
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
          req.flash('error', 'Signup failed. Please try again.');
          res.redirect('/users/signup');
      }
  }

  module.exports.login = async (req, res, next) => {
      const { username, password } = req.body;
      User.findOne