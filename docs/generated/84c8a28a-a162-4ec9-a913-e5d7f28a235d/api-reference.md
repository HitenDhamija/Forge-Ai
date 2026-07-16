# API Reference

## Endpoints

| Method | Path                                                                 | Description                                                                                                                                                                                                                           |
|--------|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| GET    | /addHoldings                                                            | Adds new holdings to the database.                                                                                                                                                                                              |
| POST   | /orders/newOrder                                                          | Creates a new order.                                                                                                                                                                                                                  |
| PUT    | /holdings/:id                                                             | Updates an existing holding's details.                                                                                                                                                                                                        |
| DELETE | /holdings/:id                                                             | Deletes a specific holding from the database.                                                                                                                                                                                                    |
| GET    | /positions                                                              | Retrieves all positions in the user's portfolio.                                                                                                                                                                                            |
| POST   | /orders/newOrder                                                          | Creates a new order.                                                                                                                                                                                                                  |
| PUT    | /positions/:id                                                           | Updates an existing position's details.                                                                                                                                                                                                        |
| DELETE | /positions/:id                                                           | Deletes a specific position from the database.                                                                                                                                                                                                    |

## Request/Response Format

### Example Request for `/addHoldings`

```json
{
  "name": "Apple Inc",
  "qty": 10,
  "avg": 150,
  "price": 200,
  "net": "Loss"
}
```

### Example Response for `/addHoldings`

```json
{
  "_id": "63f8d9e7c4a8b40001f25b1c",
  "name": "Apple Inc",
  "qty": 10,
  "avg": 150,
  "price": 200,
  "net": "Loss"
}
```

### Example Request for `/positions`

```json
{
  "product": "AAPL",
  "name": "Apple Inc",
  "qty": 10,
  "avg": 150,
  "price": 200,
  "net": "Loss",
  "day": "2023-04-07"
}
```

### Example Response for `/positions`

```json
[
  {
    "_id": "63f8d9e7c4a8b40001f25b1c",
    "product": "AAPL",
    "name": "Apple Inc",
    "qty": 10,
    "avg": 150,
    "price": 200,
    "net": "Loss",
    "day": "2023-04-07"
  },
  {
    "_id": "63f8d9e7c4a8b40001f25b1d",
    "product": "GOOGL",
    "name": "Alphabet Inc (Google)",
    "qty": 5,
    "avg": 250,
    "price": 300,
    "net": "Profit",
    "day": "2023-04-07"
  }
]
```

## Error Handling

### Status Codes
- **400 Bad Request** - When the request is malformed or invalid.
- **401 Unauthorized** - When authentication fails, typically due to incorrect credentials.
- **404 Not Found** - When a requested resource cannot be found.
- **500 Internal Server Error** - When an unexpected error occurs on the server.

### Example Response for Errors

```json
{
  "error": {
    "message": "Invalid request",
    "status": 400
  }
}
```

### Actual Route Files and Handler Names from Codebase

- **Backend**
  - `index.js` handles all routes.
  - `model/HoldingsModel.js`, `model/OrdersModel.js`, `model/PositionsModel.js` handle database interactions for respective models.

- **Dashboard** (React frontend)
  - No direct API endpoints are defined in the codebase. The dashboard interacts with backend APIs via Axios or Fetch calls, but no specific route definitions exist within the React components themselves.
  
- **Frontend**
  - `index.js` and other files handle routing and rendering of pages.

### Configuration Files

#### Backend
```json
{
  "name": "backend",
  "version": "1.0.0",
  "main": "index.js",
  "scripts": {
    "start": "nodemon index.js"
  },
  "author": "",
  "license": "ISC",
  "description": "",
  "devDependencies": {
    "nodemon": "^3.1.10"
  },
  "dependencies": {
    "body-parser": "^2.2.0",
    "cors": "^2.8.5",
    "dotenv": "^16.5.0",
    "express": "^5.1.0",
    "mongoose": "^8.15.2",
    "passport": "^0.7.0",
    "passport-local": "^1.0.0",
    "passport-local-mongoose": "^8.0.0"
  }
}
```

#### Dashboard
```json
{
  "name": "dashboard",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@emotion/react": "^11.14.0",
    "@emotion/styled": "^11.14.0",
    "@mui/icons-material": "^7.1.1",
    "@mui/material": "^7.1.1",
    "@testing-library/dom": "^10.4.0",
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.10.0",
    "chart.js": "^4.5.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.0",
    "react-router-dom": "^7.6.2",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
```

#### Frontend
```json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/dom": "^10.4.0",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^13.5.0",
    "axios": "^1.10.0",
    "react": "^19.1.0",
    "react-dom": "^19.1.2",
    "react-router-dom": "^6.4.2",
    "react-scripts": "5.0.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test --env=jsdom",
    "eject": ""
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": [
    ">0.2%",
    "not dead",
    "not op_mini all"
  ],
  "devDependencies": {
    "@testing-library/react-hooks": "^9.0.3"
  }
}
```