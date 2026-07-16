# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `NODE_ENV` | The environment in which the application is running (e.g., development, production). | Yes |
| `MONGO_URL` | Connection string for MongoDB database. | Yes |
| `CLOUD_NAME` | Cloudinary cloud name used to store images. | Yes |
| `CLOUD_API_KEY` | Cloudinary API key used to store images. | Yes |
| `CLOUD_API_SECRET` | Cloudinary API secret used to store images. | Yes |

## Docker
To run the application with Docker, you need a `Dockerfile` or a `docker-compose.yml`. The project does not have a `Dockerfile`, but it has a `docker-compose.yml` file that can be used as follows:

```yaml
version: '3'
services:
  app:
    build: .
    command: npm run start
    container_name: traveloop_app
    environment:
      - NODE_ENV=production
      - MONGO_URL=mongodb://127.0.0.1:27017/Traveloop
      - CLOUD_NAME=${CLOUD_NAME}
      - CLOUD_API_KEY=${CLOUD_API_KEY}
      - CLOUD_API_SECRET=${CLOUD_API_SECRET}
    depends_on:
      - db
    networks:
      - app-net
  db:
    image: mongo:latest
    container_name: traveloop_db
    environment:
      - MONGO_INITDB_DATABASE=Traveloop
    ports:
      - "27017:27017"
    networks:
      - app-net
networks:
  app-net:
```

To build and run the Docker containers, use these commands:

```bash
# Build the docker image
docker-compose build

# Run the container(s)
docker-compose up --build
```

## Production Build
For production builds, you can use npm scripts. The `production` script in your `package.json` is used to create a production-ready version of your application.

```json
"scripts": {
  "test": "echo \"Error: no test specified\" && exit 1",
  "start": "node index.js",
  "build": "npm run build && node dist/app.js"
}
```

To perform the production build, you can use:

```bash
# Build for production and start server
npm run build && npm start
```

## Troubleshooting

### Error: Cannot connect to MongoDB
**Issue:** The application cannot connect to the MongoDB database.

**Solution:** Ensure that your `MONGO_URL` environment variable is correctly set. If you are using Docker, ensure that the container for MongoDB is running and accessible by checking its logs:

```bash
docker-compose up --build -d db
docker-compose logs db
```

If there are any connection issues, check the MongoDB service in your `docker-compose.yml`.

### Error: Missing Cloudinary API Key or Secret
**Issue:** The application cannot upload images to Cloudinary because it is missing either the API key or secret.

**Solution:** Ensure that both `CLOUD_API_KEY` and `CLOUD_API_SECRET` environment variables are set correctly. You can also add these variables in your `.env` file if you have one:

```dotenv
CLOUD_NAME=yourcloudnamehere
CLOUD_API_KEY=yourapikeyhere
CLOUD_API_SECRET=yourapisecrethere
```

### Error: Missing Environment Variables
**Issue:** The application is unable to find required environment variables.

**Solution:** Ensure that all required environment variables are set in your `.env` file or passed as Docker environment variables. For example, if you're using a `.env` file:

```dotenv
NODE_ENV=production
MONGO_URL=mongodb://127.0.0.1:27017/Traveloop
CLOUD_NAME=yourcloudnamehere
CLOUD_API_KEY=yourapikeyhere
CLOUD_API_SECRET=yourapisecrethere
```

If you are using Docker, ensure that the environment variables are passed to your container:

```bash
docker-compose up --build -d db
docker-compose run app npm start
```

### Error: Missing Cloudinary Image Upload
**Issue:** The application is unable to upload images due to missing or incorrect configuration.

**Solution:** Ensure that the `cloudinary` module and its dependencies are installed. Also, check your `cloudConfig.js` file for any errors:

```bash
npm install cloudinary multer-storage-cloudinary
```

If you have a `.env` file, ensure it contains the correct Cloudinary credentials:

```dotenv
CLOUD_NAME=yourcloudnamehere
CLOUD_API_KEY=yourapikeyhere
CLOUD_API_SECRET=yourapisecrethere
```

### Error: Missing Session Data
**Issue:** The application is unable to populate session data.

**Solution:** Ensure that your `middleware.js` file correctly handles the session middleware. If you are using Express-session, ensure it is installed and configured properly:

```bash
npm install express-session
```

In your `middleware.js`, make sure you have the correct imports for session handling:

```javascript
const session = require('express-session');
const MongoStore = require('connect-mongo')(session);
const mongoose = require('mongoose');

module.exports.sessionMiddleware = (req, res, next) => {
  const store = new MongoStore({
    mongoUrl: process.env.MONGO_URL,
    collection: 'sessions'
  });

  if (!process.env.SESSION_SECRET) {
    throw new Error("SESSION_SECRET environment variable is missing");
  }

  const sessionOptions = {
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: true,
    store: store
  };

  req.session = new session(sessionOptions);

  next();
}
```

### Error: Missing User Registration or Login
**Issue:** The application is unable to handle user registration or login.

**Solution:** Ensure that your `passport-local-mongoose` and related configurations are correct. Also, check if the middleware for handling sessions (`sessionMiddleware`) is correctly set up in your `middleware.js`.

```javascript
module.exports.sessionMiddleware = (req, res, next) => {
  const sessionOptions = {
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: true,
    store: new MongoStore({
      mongoUrl: process.env.MONGO_URL,
      collection: 'sessions'
    })
  };

  req.session = new session(sessionOptions);

  next();
}
```

### Error: Missing Cloudinary Image Upload
**Issue:** The application is unable to upload images due to missing or incorrect configuration.

**Solution:** Ensure that the `cloudinary` module and its dependencies are installed. Also, check your `cloudConfig.js` file for any errors:

```bash
npm install cloudinary multer-storage-cloudinary
```

In your `cloudConfig.js`, ensure you have correctly configured Cloudinary with your credentials:

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

### Error: Missing Environment Variable for Session Secret
**Issue:** The application is unable to handle sessions due to missing or incorrect `SESSION_SECRET` environment variable.

**Solution:** Ensure that the `SESSION_SECRET` environment variable is set correctly in your `.env` file:

```dotenv
SESSION_SECRET=yoursecrethere
```

### Error: Missing Environment Variable for Cloudinary API Key or Secret
**Issue:** The application is unable to upload images due to missing or incorrect Cloudinary API key or secret.

**Solution:** Ensure that the `CLOUD_API_KEY` and `CLOUD_API_SECRET` environment variables are set correctly in your `.env` file:

```dotenv
CLOUD_NAME=yourcloudnamehere
CLOUD_API_KEY=yourapikeyhere
CLOUD_API_SECRET=yourapisecrethere
```

### Error: Missing Environment Variable for MongoDB Connection
**Issue:** The application is unable to connect to the MongoDB database due to missing or incorrect `MONGO_URL` environment variable.

**Solution:** Ensure that the `MONGO_URL` environment variable is set correctly in your `.env` file:

```dotenv
MONGO_URL=mongodb://127.0.0.1:27017/Traveloop
```

### Error: Missing Environment Variable for Cloudinary Configuration
**Issue:** The application is unable to configure Cloudinary due to missing or incorrect environment variables.

**Solution:** Ensure that the `CLOUD_NAME`, `CLOUD_API_KEY`, and `CLOUD_API_SECRET` environment variables are set correctly in your `.env` file:

```dotenv
CLOUD_NAME=yourcloudnamehere
CLOUD_API_KEY=yourapikeyhere
CLOUD_API_SECRET=yourapisecrethere
```

### Error: Missing Environment Variable for Session Secret
**Issue:** The application is unable to handle sessions due to missing or incorrect `SESSION_SECRET` environment variable.

**Solution:** Ensure that the `SESSION_SECRET` environment variable is set correctly in your `.env` file:

```dotenv