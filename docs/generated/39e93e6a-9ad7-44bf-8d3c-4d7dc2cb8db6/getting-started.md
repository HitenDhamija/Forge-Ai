# Getting Started

## Overview
This project is a React application that integrates Three.js for rendering interactive 3D graphics and uses Express as its backend server to serve static assets, such as images from Cloudinary. The frontend leverages Tailwind CSS for styling and includes features like a customizer interface where users can manipulate the appearance of shirts using various controls provided by the app.

## Prerequisites
- Node.js version: 19.0.0 (as specified in `threejs_shirt\react\package.json`)
- npm/yarn version: 6.2.0 (as specified in `threejs_shirt\react\vite.config.js`)

## Installation

### Frontend Setup
1. Navigate to the frontend directory:
   ```sh
   cd threejs_shirt/react
   ```
2. Install dependencies using npm or yarn:
   ```sh
   npm install
   # or
   yarn install
   ```

3. Start the development server:
   ```sh
   npm run dev
   # or
   yarn dev
   ```

### Backend Setup
1. Navigate to the backend directory:
   ```sh
   cd threejs_shirt/server
   ```
2. Install dependencies using npm or yarn:
   ```sh
   npm install
   # or
   yarn install
   ```

3. Start the server:
   ```sh
   npm start
   # or
   yarn start
   ```

## Running the App

### Frontend
The app is served at `http://localhost:5174`. You can access it via your browser.

### Backend
The backend serves static assets and routes. It listens on port 3000 by default, accessible via `http://localhost:3000`.

## Project Structure

### Frontend Directory (`threejs_shirt/react`)

- **package.json**: Contains scripts for development, build, linting, etc.
- **index.html**: Entry point of the React app. The `<script type="module">` tag points to `main.jsx`.
- **src**:
  - **App.jsx**: Main component that renders other components like Home and Canvas.
  - **canvas**:
    - **Backdrop.jsx**: Background canvas for rendering 3D objects.
    - **CameraRig.jsx**: Camera setup for the 3D scene.
    - **Shirt.jsx**: Component representing a shirt in the 3D environment.
    - **index.jsx**: Entry point for all Canvas components.
  - **components**:
    - **AIPicker.jsx**: AI picker component.
    - **ColorPicker.jsx**: Color picker component.
    - **CustomButton.jsx**: Custom button component.
    - **FilePicker.jsx**: File picker component.
    - **Tab.jsx**: Tab component.
    - **index.js**: Export all components from this file.
  - **config**:
    - **config.js**: Configuration for the app, including API keys and other settings.
    - **constants.js**: Constants used throughout the application.
    - **helpers.js**: Helper functions for common tasks.
    - **motion.js**: Motion utilities for animations.
  - **index.css**: Custom CSS styles using Tailwind CSS.
  - **main.jsx**: Entry point of the React app, rendering `App`.
  - **pages**:
    - **Customizer.jsx**: Customizer page where users can interact with the shirt.
    - **home.jsx**: Home page component.
  - **store**:
    - **index.js**: Redux store configuration.
  - **tailwind.config.js**: Tailwind CSS config file.
  - **vite.config.js**: Vite config for development environment.

### Backend Directory (`threejs_shirt/server`)

- **package.json**: Contains scripts for server start and other tasks.
- **index.js**: Main entry point of the Express app.
- **routes**:
  - **dalle.routes.js**: Routes related to DALL-E API calls (assuming this is a placeholder name).

This structure should help you get started with both frontend and backend components. Ensure that all dependencies are correctly installed as specified in their respective `package.json` files.