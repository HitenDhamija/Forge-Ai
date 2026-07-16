# Getting Started

## Overview
This project, identified by the ID `d850fdf3-c984-4b7d-90f4-cc15f3a02535`, is an Express server that integrates with MongoDB for data storage. The application allows users to create listings and reviews, while also managing user authentication using Passport.js.

## Prerequisites
The project requires the following software installed:

- Node.js version `22.12.0`
- MongoDB

You can verify these requirements by checking your current environment variables:
```bash
echo "NODE_ENV" >> .env
echo "MONGO_URI" >> .env
```

To install all dependencies, run:
```bash
npm install
# or if using yarn: 
yarn install
```

## Installation
The project is set up to use npm for dependency management. To start the development server, execute:
```bash
npm run dev
# or with Yarn:
yarn dev
```
This command starts a local server at `http://localhost:3000`.

## Running the App

### Starting the Server
To start the Express app, you can use the following script from package.json:
```json
"scripts": {
  "dev": "node ./app.js",
  "start": "node ./app.js"
}
```
Simply run `npm run dev` or `npm start`.

### Accessing the Application
After starting the server, navigate to your browser and visit `http://localhost:3000`. The application should be accessible there.

## Project Structure

The project directory structure is as follows:

- **Traveloop/app.js**: Entry point of the Express app.
- **Traveloop/cloudConfig.js**: Configures Cloudinary for image uploads.
- **Traveloop/controllers/listings.js**: Handles listing-related operations like creating, reading, updating, and deleting listings.
- **Traveloop/controllers/reviews.js**: Manages reviews associated with listings. Allows users to create or delete reviews.
- **Traveloop/controllers/users.js**: Manages user authentication and signup functionality.
- **Traveloop/init/data.js**: Contains sample data for testing purposes.
- **Traveloop/models/listing.js**: Defines the schema for listing documents in MongoDB.
- **Traveloop/models/review.js**: Defines the schema for review documents in MongoDB.
- **Traveloop/models/user.js**: Defines the schema for user documents in MongoDB.
- **Traveloop/package-lock.json**: Lock file to ensure consistent dependency versions across your team or environment.
- **Traveloop/package.json**: Contains project metadata and scripts, including dependencies and devDependencies.
- **Traveloop/public/css/rating.css**: Stylesheet used by the application for rating functionality.
- **Traveloop/public/css/style.css**: General styling of the application.
- **Traveloop/public/js/script.js**: JavaScript files that are loaded in the public directory.
- **Traveloop/routes/listing.js**: Routes related to listing operations.
- **Traveloop/routes/review.js**: Routes related to review operations.
- **Traveloop/routes/user.js**: Routes for user-related operations.
- **Traveloop/schema.js**: Defines schemas for models using Joi library.
- **Traveloop/utils/ExpressError.js**: Utility file containing ExpressError class used for custom error handling in the application.

This structure ensures that all components are organized and easily accessible.