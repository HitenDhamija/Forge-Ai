# Getting Started

## Overview
This project integrates an Express backend and React frontend to manage financial data such as holdings, orders, and positions. The backend uses MongoDB for database storage and RESTful APIs are provided via Express routes. The React dashboard serves as a user interface where users can interact with the backend through these APIs.

## Prerequisites

### Backend
- Node.js version 14 or higher is required.
- npm/yarn package manager installed (found in `Trivexa\Backend/package.json`).
- MongoDB database server running and accessible via environment variable `MONGO_URL`.
- Express, Mongoose, Passport packages are installed (`Trivexa\Backend/package.json`).

### Frontend
- Node.js version 14 or higher is required.
- npm/yarn package manager installed (found in `Trivexa\frontend/package.json`).
- React and related dependencies listed in `Trivexa\frontend/package.json`.

## Installation

### Backend Setup
1. Navigate to the backend directory: `cd Trivexa\Backend`
2. Install dependencies using npm/yarn:
   - For npm users: `npm install`
   - For yarn users: `yarn`
3. Start the development server with: 
   - `npm start` or for yarn: `yarn start`

### Frontend Setup
1. Navigate to the frontend directory: `cd Trivexa\frontend`
2. Install dependencies using npm/yarn:
   - For npm users: `npm install`
   - For yarn users: `yarn`
3. Start the development server with: 
   - `npm start` or for yarn: `yarn start`

## Running the App

### Backend
1. The backend runs on port 3002 by default.
2. Access it via your browser at [http://localhost:3002](http://localhost:3002).

### Frontend
1. Navigate to the frontend directory: `cd Trivexa\frontend`
2. Start the development server with:
   - `npm start` or for yarn: `yarn start`

## Project Structure

### Backend Directory (`Trivexa\Backend`)
- **index.js**: Entry point of the backend application.
- **model/HoldingsModel.js**: Model file for Holdings data.
- **model/OrdersModel.js**: Model file for Orders data.
- **model/PositionsModel.js**: Model file for Positions data.
- **package.json**: Contains dependencies and scripts for running the app.
- **schemas/HoldingsSchema.js**: Schema definition for Holdings model.
- **schemas/OrdersSchema.js**: Schema definition for Orders model.
- **schemas/PositionsSchema.js**: Schema definition for Positions model.

### Dashboard Directory (`Trivexa\dashboard`)
- **package.json**: Contains dependencies and scripts specific to the React application.
- **src/components/**: Components used in the dashboard UI.
  - **App.js**: Main component of the app.
  - **Dashboard.js**: Main layout component.
  - **Home.js**: Home page component.
  - **Navbar.js**: Navigation bar component.
  - **Menu.js**: Menu component for navigation.
  - **Summary.js**: Summary page component.
- **src/data/**: Data files used by components.
- **index.css**: Global styles file.
- **index.js**: Entry point of the React application.

### Frontend Directory (`Trivexa\frontend`)
- **package.json**: Contains dependencies and scripts specific to the frontend application.
- **public/index.html**: HTML template for the landing page.
- **src/**: Source files for the React components.
  - **index.css**: Global styles file.
  - **index.js**: Entry point of the React application.
  - **landing_page/About/AwardPage.js**: About page component.
  - **landing_page/Home/Hero.js**: Hero section component.
  - **landing_page/Pricing/Brokerage.js**: Pricing page component.

This structure is designed to keep related files together and maintain a clean separation of concerns between the backend and frontend.