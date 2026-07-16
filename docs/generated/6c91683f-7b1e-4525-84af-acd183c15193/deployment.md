# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `PORT` | The port number to run the application on (default: 3000) | Yes |
| `GIF_URL` | URL of the gif to display when "Yes" button is clicked (default: https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif) | Yes |
| `QUESTION` | Text to display when the application loads (default: "Do you love me?") | No |

## Docker
To run the project using Docker, follow these steps:

### Step 1: Build the Docker Image

```bash
docker build -t valentine-app .
```

### Step 2: Run the Docker Container

```bash
docker run -p $PORT:$PORT --env-file .env valentine-app
```

Replace `$PORT` with your desired port number. The `--env-file .env` flag will use environment variables from a `.env` file.

## Production Build
To build for production, execute the following command:

```bash
npm run build:prod
```

This will create a new directory named `build` containing all necessary files to serve your application in production mode. You can then deploy these files to your server or hosting platform of choice.

## Troubleshooting

### Error: No GIF URL Provided
**Error Message:** 
```bash
ReferenceError: GifUrl is not defined
```

**Fix:**
Ensure that the `GIF_URL` environment variable is set in your `.env` file. For example:
```plaintext
GIF_URL=https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif
```

### Error: No Question Text Provided
**Error Message:** 
```bash
ReferenceError: QUESTION is not defined
```

**Fix:**
Ensure that the `QUESTION` environment variable is set in your `.env` file. For example:
```plaintext
QUESTION=Do you love me?
```

### General Issues

- **Server Not Responding:** Ensure Docker container is running by checking its status with `docker ps`. If not, start it again using the command provided above.
  
- **CSS/JS Files Missing:** Verify that all necessary CSS and JS files are included in your production build directory. The structure should be similar to:
  ```
  /build
    /assets
      style.css
      script.js
    index.html
  ```

Make sure these files are correctly copied into the `build` directory during the build process.