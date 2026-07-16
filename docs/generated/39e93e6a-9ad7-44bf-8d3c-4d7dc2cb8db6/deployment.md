# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `MONGO_URI` | Connection string for MongoDB database | Yes |
| `CLOUDINARY_API_KEY` | Cloudinary API key to upload images | Yes |
| `CLOUDINARY_SECRET_KEY` | Cloudinary secret key to upload images | Yes |
| `OPENAI_API_KEY` | OpenAI API key for text generation | No (optional) |

## Docker
To run the project using Docker, you need a `Dockerfile` in your root directory. Assuming you have a basic one like this:

```dockerfile
# Dockerfile
FROM node:14

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

You can run the container with:
```bash
docker build -t threejs_shirt .
docker run --rm -p 3000:3000 threejs_shirt
```

## Production Build
To create a production build, use these commands in your project directory:

1. Install dependencies for building:
   ```bash
   npm install
   ```

2. Create the production build:
   ```bash
   npm run build
   ```

The built files will be located in the `build` folder.

## Troubleshooting
### Error: `ReferenceError: process is not defined`
**Cause:** Running a Node.js application directly from Docker container.
**Solution:** Use `CMD ["npm", "run", "build"]` in your `Dockerfile` to build and serve the production build. 

### Error: `TypeError: Cannot read properties of undefined (reading 'then')`
**Cause:** Using Promises incorrectly or not handling asynchronous operations properly.
**Solution:** Ensure all Promises are correctly handled, especially when dealing with async functions like those from Axios or Fetch.

### Error: `Error: connect ECONNREFUSED 127.0.0.1:3000`
**Cause:** The server is not running or the port is in use.
**Solution:** Ensure your server process (e.g., Express app) is started before attempting to access it via Docker.

### Error: `Error: ENOENT: no such file or directory, open 'package.json'`
**Cause:** Missing or corrupted package.json file.
**Solution:** Verify that the `package.json` exists and is correctly formatted. If necessary, reinstall dependencies with `npm install`.

---

This guide provides specific details for deploying your project using Docker, building it in production mode, and addressing common issues encountered during deployment.