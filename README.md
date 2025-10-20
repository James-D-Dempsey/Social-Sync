# Social-Sync 
Social Sync is a full-stack application that connects to Spotify, collects user listening history, and generates personalized music recommendations.
It leverages a FastAPI backend, React frontend, and MySQL database to provide a seamless and persistent music recommendation experience.

## Authentication & Data Collection

Spotify OAuth Integration: Users securely log in using their Spotify account.

Listening History Retrieval: Spotify APIs (via Spotipy) are used to fetch and store user listening history for further processing.

## Recommendation Generation

Personalized Recommendations: Music recommendations are generated based on friends music histories, providing them with the least popular songs their friends actively listen to.

Endpoints: The backend exposes APIs for managing users and retrieving tailored recommendations.

## System Architecture

Frontend: React app (frontend/spotify-recs/)

Backend: FastAPI server (backend/src/)

Database: MySQL for persistent storage (credentials in .env)

Integration Layer: Spotipy library handles OAuth and data fetching from Spotify
