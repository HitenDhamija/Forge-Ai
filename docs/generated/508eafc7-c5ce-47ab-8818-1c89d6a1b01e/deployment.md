# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `NODE_ENV` | The environment in which the application is running (development, production). | Yes |
| `MONGO_URL` | MongoDB connection string for database access. Defaults to `mongodb://127.0.0.1:27017/Traveloop`. | Yes |
| `CLOUD_NAME`, `CLOUD_API_KEY`, `CLOUD_API_SECRET` | Cloudinary credentials for image uploads. | No (if not using cloud storage) |

## Docker
To run the application with Docker, use the following command:
```bash
docker-compose up --build
```
This assumes you have a `docker-compose.yml` file in the root directory of your project that looks something like this:

```yaml
version: '3'
services:
  app:
    build: .
    volumes:
      - .:/app
    ports:
      - "3000:3000"
    depends_on:
      - db
  db:
    image: mongo
    environment:
      MONGO_INITDB_DATABASE: Traveloop
```

## Production Build
To build the application for production, use these commands:

1. Install dependencies:
```bash
npm install
```
2. Build the project:
```bash
npm run build
```

This will create a `dist` directory with optimized files ready for deployment.

## Troubleshooting

### Error: Cannot connect to MongoDB
**Issue:** The application cannot connect to the database.
**Solution:** Ensure that your `MONGO_URL` environment variable is correctly set. If you are using Docker, ensure your `docker-compose.yml` file has a proper connection string or MongoDB service is running.

### Error: Missing Cloudinary credentials
**Issue:** The application fails to upload images due to missing Cloudinary credentials.
**Solution:** Set the required environment variables for Cloudinary:
```bash
export CLOUD_NAME=<your-cloud-name>
export CLOUD_API_KEY=<your-api-key>
export CLOUD_API_SECRET=<your-secret-key>
```
Or set them in your `.env` file if you have one.

### Error: Missing session middleware
**Issue:** The application fails to handle sessions.
**Solution:** Ensure that the `connect-mongo` and `express-session` packages are installed. If using Docker, ensure these dependencies are included in your `docker-compose.yml`.

### Error: ExpressError not defined
**Issue:** An error is thrown because the `ExpressError` class is not defined.
**Solution:** Verify that you have a file named `utils/ExpressError.js` with an export for this class. If it does not exist, create one and ensure it exports the correct implementation.

### Error: Missing environment variables
**Issue:** The application fails to start because some required environment variables are missing.
**Solution:** Ensure all required environment variables (`NODE_ENV`, `MONGO_URL`, etc.) are set before starting your application. You can use a `.env` file for this purpose:
```bash
# .env
NODE_ENV=production
MONGO_URL=mongodb://your-mongo-url:27017/Traveloop
CLOUD_NAME=<your-cloud-name>
CLOUD_API_KEY=<your-api-key>
CLOUD_API_SECRET=<your-secret-key>
```

### Error: Missing middleware for authentication
**Issue:** The application fails to authenticate users.
**Solution:** Ensure that the `isLoggedIn` and `saveredirectUrl` middleware are correctly defined in your `middleware.js`. If using Docker, ensure these files are included.

By addressing these common issues, you should be able to deploy and run your Traveloop application successfully.