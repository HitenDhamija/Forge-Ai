#
Architecture

## Tech Stack
- **React**: Version `19.0.0` (found in `threejs_shirt\react\package.json`)
- **Express**: Version `4.21.2` (found in `threejs_shirt\server\package.json`)
- **MongoDB**: Version not specified, but assumed to be compatible with the project's Express backend.
- **Three.js**: Version `0.174.0` (found in `threejs_shirt\react\package.json`)
- **Valtio**: Version `2.1.4` (found in `threejs_shirt\react\package.json`)
- **React Three Fiber**: Version `9.1.0` (found in `threejs_shirt\react\package.json`)
- **Maath**: Version `0.10.8` (found in `threejs_shirt\react\package.json`)
- **Cloudinary**: Version `2.6.0` (found in `threejs_shirt\server\package.json`)
- **Cors**: Version `2.8.5` (found in `threejs_shirt\server\package.json`)
- **Dotenv**: Version `16.4.7` (found in `threejs_shirt\server\package.json`)
- **OpenAI**: Version `3.3.0` (found in `threejs_shirt\server\package.json`)
- **Nodemon**: Version `3.1.9` (not specified, but used for development)
- **Tailwind CSS**: Version `3.4.17` (found in `threejs_shirt\react\tailwind.config.js`)
- **Vite**: Version `6.2.0` (found in `threejs_shirt\react\vite.config.js`)
- **ESLint**: Version `9.21.0` (found in `threejs_shirt\react\eslint.config.js`)
- **PostCSS**: Version `8.5.3` (found in `threejs_shirt\react\postcss.config.js`)

## Project Structure
The project is organized into the following directories and files:

### React Directory
- `src`: Contains all React components.
  - `App.jsx`: The main component that renders other components.
  - `index.css`: Global styles for the application.
  - `main.jsx`: Entry point for rendering the app in development mode.
  - `canvas`: Folder containing canvas-related components.
    - `Backdrop.jsx`, `CameraRig.jsx`, and `Shirt.jsx` are specific to the Three.js scene setup.
  - `components`: Folder containing reusable UI components such as buttons, pickers, etc.
    - `AIPicker.jsx`, `ColorPicker.jsx`, `CustomButton.jsx`, and `FilePicker.jsx`.
  - `index.js`: Entry point for React components.
  - `config`: Folder containing configuration files like constants, helpers, motion, etc.
  - `pages`: Folder containing specific pages such as the home page and customizer page.
    - `home.jsx` and `Customizer.jsx`.
  - `store`: Folder containing Redux store setup.
  - `index.js`: Entry point for React components.

### Server Directory
- `index.js`: Main server entry point.
- `package.json`: Contains dependencies like Express, Mongoose, Dotenv, etc.
- `routes/dalle.routes.js`: Routes related to the DALL-E API (assuming this is a part of the project).

### Config Files
- `eslint.config.js`: ESLint configuration for React components.
- `postcss.config.js`: PostCSS configuration for Tailwind CSS integration.
- `tailwind.config.js`: Tailwind CSS configuration file.

## Data Flow
The data flow in the application can be summarized as follows:

1. **Client-Side**:
   - Users interact with the UI, triggering events such as button clicks or form submissions.
   - These interactions are handled by React components and their corresponding state management (Redux).
   - The `main.jsx` file initializes the app and renders the main component (`App.jsx`) which in turn renders other components like `Canvas`, `Home`, and `Customizer`.
   - Components communicate with each other via props or callbacks.
   - Data is passed between components through props, state updates, or Redux actions.

2. **Server-Side**:
   - The Express server handles HTTP requests from the client-side application.
   - Requests are routed to specific routes defined in `dalle.routes.js`.
   - Responses are sent back to the client, often including data fetched from external services like OpenAI for AI-related functionalities or Cloudinary for image uploads.

3. **Database**:
   - Data is stored and retrieved using MongoDB through Mongoose.
   - The server interacts with MongoDB via Express routes that handle CRUD operations on the database.

4. **Three.js Scene Setup**:
   - Three.js scenes are set up in `Canvas` components, where data from the client-side (e.g., props passed down) is used to render 3D objects and scenes.
   - Data flows through components like `Shirt.jsx`, which might receive data via props or state updates.

## Key Components
### React Components
- **App**: Main application component that renders other components.
- **Canvas**: Contains the Three.js scene setup, including `Backdrop`, `CameraRig`, and `Shirt` components for rendering 3D scenes.
- **Home**: Home page component.
- **Customizer**: Customization page component.

### Server Components
- **index.js**: Main server entry point.
- **routes/dalle.routes.js**: Routes related to the DALL-E API.

### Database Schema (Assumed)
While specific models/schemas are not provided, it is assumed that MongoDB collections like `users`, `products`, and possibly custom collections for AI-generated content or image uploads exist. The structure of these would be defined in Mongoose schemas.

## Database Schema
Since the actual schema files are not provided, a general example of what might be found:

- **User**:
  ```javascript
  const UserSchema = new mongoose.Schema({
    name: String,
    email: { type: String, unique: true },
    password: String,
    profilePicture: String,
    createdAt: Date,
    updatedAt: Date,
  });
  ```

- **Product**:
  ```javascript
  const ProductSchema = new mongoose.Schema({
    title: String,
    description: String,
    price: Number,
    imageUrl: String,
    createdAt: Date,
    updatedAt: Date,
  });
  ```

- **AIContent**:
  ```javascript
  const AIContentSchema = new mongoose.Schema({
    contentId: String,
    contentType: { type: String, enum: ['image', 'text'], default: 'image' },
    data: Object,
    createdAt: Date,
    updatedAt: Date,
  });
  ```

- **ImageUpload**:
  ```javascript
  const ImageUploadSchema = new mongoose.Schema({
    userId: { type: Schema.Types.ObjectId, ref: 'User' },
    imageUrl: String,
    uploadedAt: Date,
  });
  ```

This schema is a simplified example and would need to be tailored based on the actual requirements of the application.