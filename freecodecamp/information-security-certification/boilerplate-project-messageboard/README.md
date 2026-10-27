# Anonymous Message Board

This is the boilerplate for the Anonymous Message Board project. Instructions for completing your project can be found at https://www.freecodecamp.org/learn/information-security/information-security-projects/anonymous-message-board

Full-stack JavaScript solution for the freeCodeCamp Information Security Anonymous Message Board project.

## Run locally

    npm install
    npm start

Open http://localhost:3000/ or a board at http://localhost:3000/b/general/.

## Run the ten functional tests

    npm test

Set DB to a MongoDB connection string in .env for persistent storage. When NODE_ENV=test and DB is unavailable, tests use an isolated in-memory store so the API contract can be verified locally.

Passwords are hashed before storage. API output never includes delete passwords or report flags, and Helmet CSP allows scripts and styles only from this server.
