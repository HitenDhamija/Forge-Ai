# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `PORT` | The port number to run the server on (default: 3000) | Yes |
| `API_KEY` | API key for any external services used in the application | No |

## Docker
To run the project using Docker, you can use a simple `docker-compose.yml` file. Here's an example of how it might look:

```yaml
version: '3'
services:
  valentine-server:
    image: valentine_server_image_name
    container_name: valentine-server
    environment:
      - PORT=3000
      - API_KEY=my_api_key
    ports:
      - "3000:3000"
```

Replace `valentine_server_image_name` with the name of your Docker image and update `API_KEY` to any value you need. The `docker-compose.yml` file can be run using:

```bash
docker-compose up --build
```

## Production Build
To build for production, use the following command in the project directory:

```bash
npm run build:prod
```

This will create a new folder named `dist`, which contains all the optimized and minified files ready to be deployed.

## Troubleshooting
### Error: No API_KEY found in environment variables.
**Fix:** Ensure that the `API_KEY` is defined in your environment. You can set it using:

```bash
export API_KEY=my_api_key
```

Or if you are running a Docker container, ensure it has an environment variable set.

### Error: Missing Yes button click event listener.
**Fix:** The script.js file seems to be missing the event listener for the No button. Here is how you can add it:

```javascript
const yesBtn = document.querySelector(".yes-btn");
const noBtn = document.querySelector(".no-btn");
const question = document.querySelector(".question");
const gif = document.querySelector(".gif"); 

// Change text and gif when the Yes button is clicked
yesBtn.addEventListener("click", () => {
    question.innerHTML = "Being with you is my biggest blessing. I love you.";
    gif.src = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExbGNhdXh1b252b2F2b2U4cHRlNGkwMDZsajllaGF1cDJyb2p4NXl2YiZlcD12MV9naWZzX3NlYXJjaCZjdD1n/G6N0pDDgDpLjUvNoyQ/giphy.gif";

    // Hide the No button
    noBtn.style.display = "none";
});

// Add event listener for the No button click
noBtn.addEventListener("click", () => {
    question.innerHTML = "I love you too, but not as much.";
    gif.src = "https://media.giphy.com/media/3o7XK6W8QqRw129Y5M/giphy.gif";

    // Show the Yes button
    yesBtn.style.display = "block";
});
```

### Error: No GIF found at specified URL.
**Fix:** Ensure that the URLs provided in the script are correct and accessible. If you're using an external service, make sure it's up and running.

By following these steps and troubleshooting tips, your project should be ready for deployment.