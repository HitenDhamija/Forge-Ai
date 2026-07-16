# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `NODE_ENV` | The environment to run in (development, production). | Yes |
| `MONGO_URL` | MongoDB connection string. | Yes |
| `CLOUD_NAME` | Cloudinary cloud name. | Yes |
| `CLOUD_API_KEY` | Cloudinary API key. | Yes |
| `CLOUD_API_SECRET` | Cloudinary API secret. | Yes |

## Docker
To run the project using Docker, you need to have Docker installed and running on your machine.

### Steps:
1. Ensure that a MongoDB server is running locally or remotely accessible.
2. Create a `.env` file in the root directory with the following variables:

```plaintext
NODE_ENV=production
MONGO_URL=mongodb://your-mongo-url:27017/Traveloop
CLOUD_NAME=your-cloud-name
CLOUD_API_KEY=your-cloud-api-key
CLOUD_API_SECRET=your-cloud-api-secret
```

3. Build the Docker image:

```bash
docker build -t traveloop .
```

4. Run the container with the following command, replacing `your-mongo-url` and other variables as needed:

```bash
docker run --name traveloop-container \
  -e NODE_ENV=production \
  -e MONGO_URL=mongodb://your-mongo-url:27017/Traveloop \
  -e CLOUD_NAME=your-cloud-name \
  -e CLOUD_API_KEY=your-cloud-api-key \
  -e CLOUD_API_SECRET=your-cloud-api-secret \
  -p 3000:3000 \
  --link your-mongo-container:mysql \
  traveloop
```

Replace `your-mongo-url` and `your-mongo-container` with the appropriate values for your MongoDB setup.

## Production Build
To build the application for production, run:

```bash
npm run build
```

This command will create a production-ready version of your app in the `dist/` directory. You can then serve this from any web server or directly using Node.js if you have Express set up to handle static files.

## Troubleshooting
### Error: No data found for listing with id [id]
**Cause:** The provided `listingId` does not exist in the database.
**Solution:** Ensure that the `listingId` is correct and exists within your MongoDB collection. If it doesn’t, you may need to add a new listing or review.

### Error: Failed to connect to MongoDB
**Cause:** There might be an issue with connecting to your MongoDB server.
**Solution:** Verify that your MongoDB service is running and accessible from the Docker container. Check for any network issues or firewall rules blocking access.

### Error: Missing required environment variable [variable_name]
**Cause:** The specified environment variable is missing or not set correctly in the `.env` file.
**Solution:** Ensure all required environment variables are defined in your `.env` file and that they match the names used in your code.