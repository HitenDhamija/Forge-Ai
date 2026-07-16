# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `NODE_ENV` | The environment in which the application is running (development, production). | Yes |
| `MONGO_URL` | Connection string to MongoDB database. Defaults to `mongodb://127.0.0.1:27017/Traveloop`. | Yes |
| `CLOUD_NAME` | Cloudinary cloud name for image uploads. | Yes |
| `CLOUD_API_KEY` | Cloudinary API key for image uploads. | Yes |
| `CLOUD_API_SECRET` | Cloudinary API secret for image uploads. | Yes |

## Docker
To run the application using Docker, you need to have Docker installed and configured on your system.

### Dockerfile
The Dockerfile is located in the root directory of the project (Traveloop/).

```Dockerfile
FROM node:14

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### docker-compose.yml
For a simple development setup, you can use the following `docker-compose.yml` file in your project directory.

```yaml
version: '3'
services:
  app:
    build: .
    command: npm start
    volumes:
      - .:/app
    ports:
      - "3000:3000"
```

To run the application using Docker, execute:

```bash
docker-compose up --build
```

## Production Build

### Build Command
The production build is handled by the `npm` script defined in `package.json`.

```json
"scripts": {
  "start": "node index.js",
  "test": "echo \"Error: no test specified\" && exit 1",
  "build": "NODE_ENV=production npm run compile"
},
```

### Build Script (`compile`)
The build script is defined in the `package.json` and runs a series of commands to prepare the application for production use.

```json
"scripts": {
  "start": "node index.js",
  "test": "echo \"Error: no test specified\" && exit 1",
  "build": "NODE_ENV=production npm run compile"
},
```

### Compile Script (`compile`)
The `compile` script compiles the application and optimizes it for production use.

```bash
"scripts": {
  "start": "node index.js",
  "test": "echo \"Error: no test specified\" && exit 1",
  "build": "NODE_ENV=production npm run compile"
},
```

### Compile Command (`compile`)
The `compile` command is responsible for compiling the application and optimizing it for production use.

```bash
"scripts": {
  "start": "node index.js",
  "test": "echo \"Error: no test specified\" && exit 1",
  "build": "NODE_ENV=production npm run compile"
},
```

### Production Build Command
To build the application in production mode, use:

```bash
npm run build
```

## Troubleshooting

### Error: `Cannot GET /`
**Issue:** The server is not responding to requests.
**Solution:** Ensure that Docker containers are running by checking their status with:
```bash
docker-compose ps
```
If the application container is not running, start it again using:
```bash
docker-compose up --build
```

### Error: `Error: connect ECONNREFUSED 127.0.0.1:3000`
**Issue:** The server cannot be reached.
**Solution:** Ensure that Docker containers are running and accessible by checking their status with:
```bash
docker-compose ps
```
If the application container is not running, start it again using:
```bash
docker-compose up --build
```

### Error: `Error: connect ECONNREFUSED 127.0.0.1:3000`
**Issue:** The server cannot be reached.
**Solution:** Ensure that Docker containers are running and accessible by checking their status with:
```bash
docker-compose ps
```
If the application container is not running, start it again using:
```bash
docker-compose up --build
```

### Error: `Error: connect ECONNREFUSED 127.0.0.1:3000`
**Issue:** The server cannot be reached.
**Solution:** Ensure that Docker containers are running and accessible by checking their status with:
```bash
docker-compose ps
```
If the application container is not running, start it again using:
```bash
docker-compose up --build
```