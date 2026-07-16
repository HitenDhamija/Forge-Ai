# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `NODE_ENV` | The environment in which the application is running (e.g., development, production). | Yes |
| `MONGO_URI` | Connection string to MongoDB database. | Yes |
| `CLOUD_NAME` | Cloudinary cloud name. | Yes |
| `CLOUD_API_KEY` | Cloudinary API key. | Yes |
| `CLOUD_API_SECRET` | Cloudinary API secret. | Yes |

## Docker
To run the application using Docker, you need to have a `Dockerfile` and possibly a `docker-compose.yml` file in your project directory.

### Dockerfile
The Dockerfile is located at `Traveloop/Dockerfile`. It sets up an environment for running the Express server with MongoDB connection. Here’s what it does:

```Dockerfile
# Use official Node.js image as base image
FROM node:14

# Set working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json files into container
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application code into container
COPY . .

# Expose port 3000 for the server to listen on
EXPOSE 3000

# Start the app with npm start command
CMD ["npm", "start"]
```

### docker-compose.yml
The `docker-compose.yml` file is located at the root of your project directory. It defines services and volumes needed for running the application.

```yaml
version: '3'
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      MONGO_URI: mongodb://mongo/mongo_db?authSource=admin
      CLOUD_NAME: your_cloud_name
      CLOUD_API_KEY: your_api_key
      CLOUD_API_SECRET: your_secret_key

  mongo:
    image: mongo:latest
    container_name: mongo_container
    environment:
      MONGO_INITDB_DATABASE: db
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: password
    volumes:
      - ./data:/data/db
```

### Running Docker
To run the application using `docker-compose`, navigate to your project directory and execute:

```bash
docker-compose up --build
```

This command will build the images (if they don't exist) and start the services defined in `docker-compose.yml`.

## Production Build

For building for production, you can use npm scripts. In your `package.json` file, there is a script called `build:prod`. This script compiles all assets into the `dist/` directory.

```json
"scripts": {
  "test": "echo \"Error: no test specified\" && exit 1",
  "start": "node dist/app.js",
  "build:dev": "node ./bin/build.js",
  "build:prod": "npm run build:dev -- --env.production"
}
```

To build for production, execute:

```bash
npm run build:prod
```

This will create a `dist/` directory with optimized files ready to be served by your server.

## Troubleshooting

### Error 500 - Internal Server Error
**Issue:** The application is not able to connect to the MongoDB database.
**Solution:** Ensure that the `MONGO_URI` environment variable in your Docker Compose file or `.env` file points to a valid connection string. If using Docker, ensure you have created and mounted a volume for the data directory.

### Error 404 - Not Found
**Issue:** The application is not able to find routes.
**Solution:** Check if all route files (e.g., `listing.js`, `user.js`) are correctly defined in your Express app. Ensure that middleware such as `isLoggedIn` and `saveredirectUrl` are properly set up.

### Error 401 - Unauthorized
**Issue:** The application is not able to authenticate users.
**Solution:** Verify if the user authentication logic (e.g., passport setup) is correctly implemented in your Express app. Ensure that session middleware (`express-session`) and authentication middleware (`isLoggedIn`, `saveredirectUrl`) are properly configured.

### Error 403 - Forbidden
**Issue:** The application is not able to access resources.
**Solution:** Check if the user has the necessary permissions or roles for accessing certain routes or actions. Ensure that session management (e.g., setting up sessions) and authorization middleware (`isLoggedIn`, `saveredirectUrl`) are correctly implemented.

By following these steps, you should be able to deploy your application successfully in a production environment.