# Deployment

## Environment Variables

| Variable | Description | Required |
| --- | --- | --- |
| MONGO_URL | Connection string for MongoDB database | Yes |
| PORT | Port number to run server on (default is 3002) | Yes |

## Docker

To run the backend using Docker, you can use a `Dockerfile` or a `docker-compose.yml`. Below are examples of both:

### Using Dockerfile
The `Dockerfile` for this project would look something like this:

```Dockerfile
# Use an official Node.js runtime as a parent image
FROM node:14

# Set the working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json (or npm-shrinkwrap.json) into the container at /app
COPY package*.json ./

# Install any needed packages specified in package.json
RUN npm install

# Copy local code to the container at /app
COPY . .

# Make port 3002 available to the world outside this Dockerfile.
EXPOSE 3002

# Define environment variable for MONGO_URL
ENV MONGO_URL=mongodb://localhost:27017/trivexa

# Run `npm start` command inside the container
CMD ["npm", "start"]
```

### Using docker-compose.yml
If you prefer to use a `docker-compose.yml`, it would look like this:

```yaml
version: '3'
services:
  backend:
    build: .
    environment:
      MONGO_URL: mongodb://localhost:27017/trivexa
    ports:
      - "3002:3002"
```

## Production Build

To build the frontend for production, you can use `npm run build`. For the backend, if using Docker, simply start it with `docker-compose up --build`.

### Frontend Build Command
```bash
npm run build
```
This command will create a new folder named `build` in your project directory containing all files needed to deploy.

### Backend Start Command (Docker)
If you are running the backend using Docker, simply start it with:
```bash
docker-compose up --build
```

## Troubleshooting

### Common Issues and Fixes

#### Issue: Error connecting to MongoDB
**Fix:** Ensure your `MONGO_URL` environment variable is correctly set. If you're using a local MongoDB instance, ensure the database name (`trivexa`) matches what's specified in your backend code.

#### Issue: Missing Environment Variables
**Fix:** Make sure all required environment variables are defined before starting the application. You can define them via Docker or directly on your server if running manually.

#### Issue: CORS Issues
**Fix:** Ensure that your frontend is correctly configured to handle CORS requests. This might involve setting up a proxy in your `package.json` for development, or configuring CORS headers in your backend code.

### Example Error Messages and Fixes

- **Error Message:** "Cannot GET /addHoldings"
  - **Fix:** Check if the route `/addHoldings` is correctly defined and accessible. Ensure that middleware like `cors` is properly configured to allow requests from frontend origins.
  
- **Error Message:** "MongoDB connection error: connect ECONNREFUSED"
  - **Fix:** Verify your MongoDB server is running on the specified host (`localhost`) and port (`27017`). If using a different setup, ensure you have updated `MONGO_URL` accordingly.

This guide provides specific steps for deploying your Trivexa project. Make sure to adapt these instructions based on your environment and any additional configurations required by your application.