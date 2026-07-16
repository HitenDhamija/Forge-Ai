### getting-started.md

# Getting Started

## Overview
This project is a Traveloop application built using Express for the backend, MongoDB for data storage, and Cloudinary for image hosting. The app allows users to create listings, view them, and leave reviews.

## Prerequisites
- Node.js version 22.12.0 or higher.
- MongoDB database installed and running.
- A cloud provider with a Cloudinary account (e.g., AWS, Google Cloud).

## Installation
To install the project dependencies:

```bash
cd Traveloop
npm install
```

## Running the App
To start the development server:

```bash
npm run dev
```

This will start the Express server on port 3000. You can access the application in your browser at <http://localhost:3000>.

## Project Structure
The project is organized into several directories, each serving a specific purpose:
- **Traveloop/app.js**: Entry point for the Express app.
- **Traveloop/controllers/**: Contains controllers that handle HTTP requests and responses. For example, `listings.js` handles listing-related operations.
- **Traveloop/models/**: Defines data models using Mongoose. For instance, `listing.js` defines a schema for listings.
- **Traveloop/routes/**: Routes are defined here to map URLs to controller actions. For example, `listing.js` contains routes related to listings.
- **Traveloop/public/**: Contains static files such as CSS and JavaScript that can be served directly by the Express server.

### API Reference.md

# API Reference

## Endpoints
| Method | Path | Description |
|--------|------|--------------|
| GET     | /listings/ | Retrieve all listings. |
| POST    | /listings/ | Create a new listing. |
| GET     | /listings/:id | Get details of a specific listing. |
| PUT     | /listings/:id | Update an existing listing. |
| DELETE  | /listings/:id | Delete a listing. |

## Request/Response Format
- **Request Example:**
```json
{
    "title": "Luxury Villa",
    "description": "Spacious villa with stunning views.",
    "location": "Miami, FL",
    "price": 200,
    "country": "USA"
}
```

- **Response Example (GET /listings/):**
```json
[
    {
        "_id": "6457891234567890",
        "title": "Luxury Villa",
        "description": "Spacious villa with stunning views.",
        "location": "Miami, FL",
        "price": 200,
        "country": "USA"
    }
]
```

## Authentication
The application uses Passport for authentication. Users can log in and register through the `/login` and `/register` routes respectively.

### Architecture.md

# Architecture

## Tech Stack
- **Express**: For building RESTful APIs.
- **MongoDB**: As the primary database system.
- **Cloudinary**: For image hosting and resizing images uploaded to listings.

## Project Structure
The project is structured as follows:
- **Traveloop/app.js**: Entry point for Express app, includes environment configuration.
- **Traveloop/controllers/**: Contains controllers that handle CRUD operations on models like `listing`, `review`, and `user`.
- **Traveloop/models/**: Defines schemas for data storage using Mongoose. For example, `listing.js` defines the schema for listings.
- **Traveloop/routes/**: Routes are defined here to map URLs to controller actions. For instance, `listing.js` contains routes related to listings.

## Data Flow
1. User interacts with frontend (e.g., submits a listing form).
2. Request is sent to Express server via `/listings/`.
3. Controller (`listings.js`) handles the request and calls corresponding model methods.
4. Model (`listing.js`) interacts with MongoDB database for data storage or retrieval.
5. Response is returned by controller, which may involve rendering views or redirecting.

## Key Components
- **Express**: Handles HTTP requests and responses.
- **Mongoose**: Used to define schemas and models for interacting with MongoDB.
- **Cloudinary**: Manages image uploads and resizing.

### Deployment.md

# Deployment

## Environment Variables
To run the application in production, you need to set up environment variables. The following are required:
- `CLOUD_NAME`: Your Cloudinary cloud name.
- `CLOUD_API_KEY`: Your Cloudinary API key.
- `CLOUD_API_SECRET`: Your Cloudinary API secret.

You can create a `.env` file at the root of your project with these values:

```
CLOUD_NAME=your-cloud-name
CLOUD_API_KEY=your-api-key
CLOUD_API_SECRET=your-api-secret
```

## Docker
To run the application using Docker, follow these steps:
1. Create a `Dockerfile` in the root directory:
```dockerfile
FROM node:latest

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

2. Build and run your Docker container:

```bash
# Build the Docker image
docker build -t traveloop .

# Run the Docker container
docker run -d --name traveloop-container -p 3000:3000 traveloop
```

## Production Build
To prepare for production, you can use `npm` to build your application:

```bash
npm run build
```

This will create a new directory named `dist`, which contains the static files and optimized images.

## Troubleshooting
- **Error: No Environment Variables Loaded**: Ensure that `.env` file is present in the root of your project.
- **Issue with Image Uploads**: Verify that all required environment variables are set correctly for Cloudinary integration.
- **Performance Issues**: Optimize images by resizing them using Cloudinary before uploading.

---

These documents provide detailed information about setting up, running, and deploying this specific project. They reference actual files and paths within the provided codebase to ensure accuracy and relevance.