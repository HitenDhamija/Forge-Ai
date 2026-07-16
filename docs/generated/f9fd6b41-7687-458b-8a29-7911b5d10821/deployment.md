# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `PORT` | The port number to run the server on (default: 3000) | Yes |
| `API_KEY` | API key for any external services used in production (e.g., for authentication or data fetching) | No |

## Docker
To run the project using Docker, you need a `Dockerfile`. Here is an example of what it might look like:

```dockerfile
# Use official Node.js image as the base image
FROM node:14

# Set working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock) into the container at /app
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project code into the container at /app
COPY . .

# Expose port 3000 for our app to access
EXPOSE 3000

# Start the server on boot and expose it to the host network
CMD ["npm", "start"]
```

You can build your Docker image using:
```sh
docker build -t valentine .
```

To run a container from this image, you would use:
```sh
docker run -p 3000:3000 --name valentine-container valentine
```

## Production Build
For production builds, you can use the following script in your `package.json`:

```json
"scripts": {
    "start": "node dist/index.js",
    "build": "npm run build && npm run minify"
},
"build": "tsc -p .",
"minify": "terser --compress --mangle --output dist/index.min.js dist/index.js"
```

To build the production version:
```sh
npm run build
npm run minify
```

This will create a `dist` directory with optimized files.

## Troubleshooting
### Error: Cannot read properties of undefined

**Description:** This error occurs when you try to access an element that does not exist in your DOM.
**Solution:** Ensure that the elements referenced by `document.querySelector` actually exist. Check for typos and ensure all HTML tags are correctly closed.

### Error: Module parse failed (Use --ignore-locals to suppress this failure)

**Description:** This error occurs when you have a typo or incorrect path reference in your code.
**Solution:** Review your paths and make sure they match the actual file locations. Use relative paths if necessary, and ensure that all paths are correctly specified.

### Error: Unexpected token (TS2304)

**Description:** This error is thrown by TypeScript when it encounters a syntax or type-related issue in your code.
**Solution:** Review the specific line of code causing the error. Ensure you have installed all required packages (`@types/node`, `typescript`) and that they are up-to-date.

### Error: Failed to compile

**Description:** This error occurs when there is an issue with compiling TypeScript or other build steps.
**Solution:** Check your `tsconfig.json` for any errors, such as incorrect paths or missing configurations. Ensure all dependencies are correctly installed and the correct version of Node.js is being used.

### Error: Missing API Key

**Description:** This error occurs when you try to use an external service but do not have a valid API key.
**Solution:** Obtain a valid API key from your provider, set it as an environment variable, and update your code to include the correct API key.