# Architecture

## Tech Stack
- Express.js version 5.1.0
- MongoDB version 8.15.2
- React version 19.1.0
- Axios version 1.10.0
- Mongoose version 8.15.2
- Passport version 0.7.0
- Passport-local version 1.0.0
- Passport-local-mongoose version 8.0.0

## Project Structure
The project is organized into two main directories: `Trivexa\Backend` and `Trivexa\dashboard`. The backend directory contains the server-side logic, while the dashboard directory houses the frontend application.

### Backend Directory
- **index.js**: Entry point for the backend server. Uses Express to handle HTTP requests.
- **model/HoldingsModel.js**: Defines a model for Holdings data using Mongoose.
- **model/OrdersModel.js**: Defines a model for Orders data using Mongoose.
- **model/PositionsModel.js**: Defines a model for Positions data using Mongoose.
- **schemas/HoldingsSchema.js**: Holds the schema definition for Holdings data.
- **schemas/OrdersSchema.js**: Holds the schema definition for Orders data.
- **schemas/PositionsSchema.js**: Holds the schema definition for Positions data.

### Dashboard Directory
- **package.json**: Contains dependencies and scripts specific to the frontend application.
- **src/components/**: Components used in the dashboard, such as `App`, `Home`, `Dashboard`, etc.
- **src/data/data.js**: Data management logic for components.
- **index.css**: Stylesheet for the root component.
- **index.js**: Entry point for the React app.

## Data Flow
The data flow through the application is structured around CRUD operations (Create, Read, Update, Delete) on different types of financial positions. The backend server handles API requests and interacts with MongoDB to manage Holdings, Orders, and Positions models. These models are used by the frontend components to display and manipulate data.

### Request Lifecycle
1. **Client-Side**: A user makes a request via an HTTP GET or POST method through React Router.
2. **Backend Server**: The Express server receives the request and routes it based on the URL path.
3. **Model Interaction**: Depending on the type of request, relevant models (HoldingsModel, OrdersModel, PositionsModel) are queried from MongoDB to fetch data or update records.
4. **Data Processing**: Data is processed according to business logic defined in the backend server.
5. **Response Generation**: The appropriate response is generated and sent back to the client.

### Key Components
- **App.js**: Root component of the application, responsible for rendering other components.
- **Dashboard.js**: Main dashboard component that displays various financial data charts and tables.
- **Home.js**: Component used as a landing page or home screen.
- **Orders.js**: Component displaying recent orders made by users.
- **Positions.js**: Component showing current positions held by the user.

## Database Schema
### Holdings Model
```javascript
const { Schema } = require('mongoose');

const HoldingsSchema  = new Schema({
    name: String,
    qty: Number,
    avg: Number,
    price: Number,
    net: String,
    day: String,
});

module.exports = { HoldingsSchema };
```

### Orders Model
```javascript
const { Schema } = require('mongoose');

const OrdersSchema = new Schema({
    name: String,
    qty: Number,
    price: Number,
    mode: String,
});

module.exports = { OrdersSchema };
```

### Positions Model
```javascript
const { Schema } = require('mongoose');

const PositionsSchema = new Schema({
    product: String,
    name: String,
    qty: Number,
    avg: Number,
    price: Number,
    net: String,
    day: String,
    isLoss: Boolean,
});

module.exports = { PositionsSchema };
```

These schemas define the structure of documents stored in MongoDB for Holdings, Orders, and Positions respectively.