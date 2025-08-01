# Gemini MCP Client/Server

This project implements a client-server architecture to interact with Google's Gemini Pro model. The server acts as a proxy, handling requests from multiple clients and communicating with the Gemini API. The client provides a simple command-line interface for users to send prompts and receive responses.

## Technology Stack

*   **Language:** Python 3.11
*   **Libraries:**
    *   `google-generativeai`: To interact with the Gemini API.
    *   `websockets`: For real-time, bidirectional communication between the client and server.
*   **Containerization:**
    *   `Docker`: To containerize the server application.
    *   `docker-compose`: To define and run the multi-container Docker application.

## How to Use

### Prerequisites

*   Python 3.11 or later
*   Docker and Docker Compose
*   A Google Gemini API key

### Instructions

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/mcpClientWithGemini.git
    cd mcpClientWithGemini
    ```

2.  **Generate SSL Certificate:**

    To secure the connection with WSS, you need to generate a self-signed SSL certificate:

    ```bash
    mkdir certs
    openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -sha256 -days 365 -nodes -subj "/C=US/ST=California/L=Mountain View/O=Google/OU=AI/CN=localhost"
    ```

3.  **Create a `.env` file:**

    Create a file named `.env` in the root of the project and add your Gemini API key and a secret token for the server:

    ```
    GEMINI_API_KEY=your_api_key
    MCP_SERVER_TOKEN=your_secret_token
    ```
    Replace `your_secret_token` with a strong, randomly generated string.

4.  **Run the server:**

    You can run the server using Docker Compose:

    ```bash
    docker-compose up -d
    ```

    This will build the Docker image and start the server in detached mode. The server will automatically use the certificate and key in the `certs` directory to enable `wss`.

5.  **Run the client:**

    Open a new terminal. The client also needs the `MCP_SERVER_TOKEN` to authenticate. You can set it as an environment variable before running the client:

    ```bash
    export MCP_SERVER_TOKEN=your_secret_token
    python3 mcp_client_gemini.py
    ```
    The client will automatically detect the certificate and connect using `wss`.

6.  **Interact with the model:**

    Once the client is connected, you can start sending prompts to the Gemini model. Type your message and press Enter. To exit, type `salir` or `exit`.

## Utility Scripts

*   `run_client.sh`: A convenience script to set up a Python virtual environment, install client dependencies, and run the `mcp_client_gemini.py` application.
*   `audit_dependencies.sh`: This script performs a security audit of the project's Python dependencies using `pip-audit` to check for known vulnerabilities.