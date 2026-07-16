# Getting Started

## Overview
This project, identified by the UUID `eb6c49da-3130-4ec1-9607-b13ab71f3f09`, is an Express application that integrates MongoDB for data storage and Cloudinary for image uploads. It provides functionalities to manage listings (accommodation offers), reviews, and users.

## Prerequisites
The project requires the following software installed:

- Node.js version `22.12.0`
- MongoDB server running on `localhost` at port `27017`

You can check your current Node.js version by running:
```bash
node -v
```
Ensure it matches the required version.

## Installation

To install and set up this project, follow these steps:

### Step 1: Install Dependencies
First, navigate to the root directory of the project:
```bash
cd Traveloop
```
Then, run the following command to install all dependencies using npm (or yarn if you prefer):
```bash
npm install
# or for Yarn users
yarn install
```

### Step 2: Start MongoDB Server
Ensure your MongoDB server is running. You can start it with:
```bash
mongod --dbpath /data/db
```
This command starts the MongoDB daemon in a directory where you have write permissions.

### Step 3: Run the Application
To start the development server, execute the following command:
```bash
npm run dev
# or for Yarn users
yarn dev
```

The application will be accessible at `http://localhost:3000`. 

## Running the App

Once you have installed and started the MongoDB server, running the Express app is straightforward. The script to start the development server is defined in `package.json` under the `"scripts"` section:
```json
"scripts": {
  "dev": "node ./app.js"
}
```
This command starts a local web server on port `3000`.

## Project Structure

The project's directory structure is as follows:

- **Traveloop/app.js**: Entry point of the application, where Express app is initialized.
- **Traveloop/cloudConfig.js**: Configuration for Cloudinary storage.
- **Traveloop/controllers/listings.js**, **Traveloop/controllers/reviews.js**, **Traveloop/controllers/users.js**: Controllers handling API routes related to listings, reviews, and users respectively.
- **Traveloop/init/data.js**: Contains sample data that is inserted into the database during application initialization.
- **Traveloop/init/index.js**: Initializes MongoDB connection and inserts initial data.
- **Traveloop/middleware.js**: Middleware functions for authentication and error handling.
- **Traveloop/models/listing.js**, **Traveloop/models/review.js**, **Traveloop/models/user.js**: Models representing entities like listings, reviews, and users in the database.
- **Traveloop/package.json**: Contains project dependencies and scripts.
- **Traveloop/public/css/rating.css**, **Traveloop/public/css/style.css**: CSS files for styling.
- **Traveloop/public/js/script.js**: JavaScript file for client-side logic.
- **Traveloop/routes/listing.js**, **Traveloop/routes/review.js**, **Traveloop/routes/user.js**: Routes for API endpoints.
- **Traveloop/schema.js**: Schemas used by Mongoose to define the structure of documents in MongoDB.
- **Traveloop/utils/ExpressError.js**: Utility class for creating custom Express errors.

This guide provides a comprehensive setup and usage instructions for this project. For any issues or further customization, refer to the respective files within the project directory.