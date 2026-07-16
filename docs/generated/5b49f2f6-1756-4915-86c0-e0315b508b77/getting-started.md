# Getting Started

## Overview
This project is an Express application that integrates MongoDB for data storage and Cloudinary for image uploads. The purpose of this application is to facilitate listing, review creation, and user management functionalities.

## Prerequisites
- Node.js version 22.12.0
- MongoDB installed on your local machine or accessible via a connection string.
- Cloudinary account setup with the necessary API keys (cloud_name, api_key, api_secret) available in `Traveloop/cloudConfig.js`.

## Installation

### Step 1: Install Dependencies
```bash
npm install
```

### Step 2: Start MongoDB Server
Ensure your local MongoDB server is running. If you are using a remote database, replace the connection string with your actual MongoDB URI.

### Step 3: Run the Application
Start the development server by executing:
```bash
npm run dev
```
This command will start both the Express server and the MongoDB server if not already running.

## Running the App

The application is set up to automatically restart when changes are made. To manually restart, use:
```bash
npm run start
```

## Project Structure

### Application Files
- **Traveloop/app.js**: Entry point for the Express app.
- **Traveloop/cloudConfig.js**: Configures Cloudinary for image uploads.
- **Traveloop/controllers/listings.js**: Handles listing-related routes and operations.
- **Traveloop/controllers/reviews.js**: Manages review creation and deletion functionalities.
- **Traveloop/controllers/users.js**: Provides user management features including signup, login, and logout.
- **Traveloop/init/data.js**: Seeds the database with initial data for testing purposes.
- **Traveloop/init/index.js**: Initializes MongoDB connection and seeds the database.

### Middleware
- **Traveloop/middleware.js**: Contains middleware functions like `isLoggedIn` to ensure users are authenticated before accessing certain routes, and `saveredirectUrl` to save the redirect URL in session storage.

### Models
- **Traveloop/models/listing.js**: Defines the structure of a listing.
- **Traveloop/models/review.js**: Represents review data.
- **Traveloop/models/user.js**: Manages user-related operations.

### Routes
- **Traveloop/routes/listing.js**: Handles routes related to listings.
- **Traveloop/routes/review.js**: Manages review creation and deletion.
- **Traveloop/routes/user.js**: Provides endpoints for user management functionalities like signup, login, and logout.

### Utilities
- **Traveloop/utils/ExpressError.js**: Custom error handling utility.
- **Traveloop/utils/wrapAsync.js**: Wraps asynchronous functions to handle errors gracefully.

## Folder Layout

The project directory structure is as follows:

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
│   │   └── style.css
│   └── js/
│       └── script.js
├── routes/
│   ├── listing.js
│   ├── review.js
│   └── user.js
└── schema.js
└── utils/
    ├── ExpressError.js
    └── wrapAsync.js
```

This structure is designed to keep your application organized and maintainable. Each file serves a specific purpose, contributing to the overall functionality of the Traveloop application.