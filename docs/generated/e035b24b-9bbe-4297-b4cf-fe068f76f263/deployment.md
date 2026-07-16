# Deployment

## Environment Variables
| Variable | Description | Required |
| --- | --- | --- |
| `PORT` | The port number to run the server on (default: 3000) | Yes |
| `API_KEY` | API key for any external services used in production (e.g., for authentication, analytics) | No |

## Docker
To run the application using Docker, you need a `Dockerfile`. The `Dockerfile` is located at the root of your project directory.

### Running with Docker

1. **Build Image**:
   ```bash
   docker build -t valentine-app .
   ```

2. **Run Container**:
   ```bash
   docker run -p 3000:3000 --name valentine-container -d valentine-app
   ```
   
### Production Build

To create a production-ready build, you can use the following command from your project directory:

```bash
npm run build
```

This will generate static files in the `dist` folder which can be served directly without running a server.

## Troubleshooting
- **Error: Cannot read properties of undefined**
  - Ensure all required environment variables are set. For example, if you're using `PORT`, it should be defined.
  
- **Error: No module found for external service API key**
  - Verify that the API key is correctly configured in your `.env` file or passed as an argument to any services used.

- **Error: Missing CSS/JS files**
  - Ensure all required assets (CSS, JS) are included and referenced properly. Check if there are any typos in paths or filenames.
  
- **Error: Server not running on the specified port**
  - Verify that your environment variable `PORT` is correctly set to the desired port number.

This guide assumes you have a basic understanding of Docker and Node.js environments. Adjust as necessary based on specific project requirements and external dependencies.