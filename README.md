# SignalWire Call Fabric Client Setup

This guide will walk you through the configuration and setup of your SignalWire Call Fabric client application. Follow the steps below to get your application running smoothly.

## Prerequisites

Ensure you have the following prerequisites installed:

- Node.js (Version 14 or higher recommended)
- npm (usually comes with Node.js)

## Configuration

### Step 1: Clone the Repository

First, clone the repository to your local machine using:

```bash
git clone gh repo clone jongray00/call-fabric-beta-app
cd call-fabric-beta-app
```
### Step 2: Install Dependencies
Install the necessary Node.js dependencies:


```bash
npm install
```

### Step 3: Set Up Environment Variables
You'll need to configure the environment variables required for the application. Rename the provided .env.sample file to .env:

``` bash
cp .env.sample .env
```


Fill out the .env file with your specific values:
```
SIGNALWIRE_PROJECT_KEY: Your SignalWire project key.
SIGNALWIRE_TOKEN: Your SignalWire token.
SIGNALWIRE_SPACE: Your SignalWire workspace URL (e.g., your-space.signalwire.com).
DEFAULT_DESTINATION: The default CF route your application will use internally.
SIGNALWIRE_FABRIC_API_URL: The API URL, typically set to https://puc.signalwire.com.

// Firebase Parameters
FIREBASE_API_KEY: Your Firebase API key.
FIREBASE_AUTH_DOMAIN: Your Firebase auth domain.
FIREBASE_DATABASE_URL: Your Firebase database URL.
FIREBASE_PROJECT_ID: Your Firebase project ID.
FIREBASE_STORAGE_BUCKET: Your Firebase storage bucket.
FIREBASE_MESSAGING_SENDER_ID: Your Firebase messaging sender ID.
FIREBASE_APP_ID: Your Firebase app ID.

// OAuth Settings:
OAUTH_CLIENT_ID: Enter the UID provided by SignalWire.
OAUTH_SECRET: Enter your OAuth secret.
SESSION_SECRET: A secret string used to secure sessions.
Ensure other OAuth URLs and IDs are correct.
SAT_CH: Custom parameter, set as needed.
```

Important:
Do not share your .env file or expose sensitive keys publicly.

### Step 4: Run the Application
Once your environment variables are set, start your application using:

```bash
npm run start
```
Your application should now be running on http://localhost:3000 (or another specified port). Ensure your application's callbacks and webhooks are correctly set up to interact with external services.

### Troubleshooting
If you encounter any issues:

Check that all environment variables are correctly set.
Ensure that your SignalWire space and API URLs are accessible.
Verify network settings and firewall rules.
For more detailed logs, run your application with debugging enabled:

```bash
DEBUG=signalwire* npm run start
```

## API Notes
#### Call Fabric Client Beta
This repository is a Work in Progress (WIP) and features a limited release application leveraging the new Call Fabric SDK from SignalWire.

## Features
# API Notes

## Call Fabric Client Beta

This repository is a Work in Progress (WIP) and features a limited release application leveraging the new Call Fabric SDK from SignalWire.

### Features

- **Inbound and Outbound Calling**: Demonstrates how to handle both inbound and outbound calls using a server-side token or through client-side authentication with OAuth.

### Implementations

- **Minimal and Full**: Start with the minimal implementation and use the full version as a reference to add more features as needed.

### Getting Started

- **Environment Setup**: Copy `env.example` to `.env` and fill it with your SignalWire credentials. Set `DEFAULT_DESTINATION` to a resource in your space. If the `Resources` tab is not visible in your space, contact Support for beta program enrollment.

### Getting a Token

- **Token Request Example**:

  ```bash
  curl --location 'https://YOURSPACE.signalwire.com/api/fabric/subscribers/tokens' \
  --form 'reference="foo"' \
  --form 'password="dont-tell"' \
  --form 'application_id="our-client-app-id"' \
  --user 'YOURPROJECTKEY:YOURTOKEN'
    ```
  
### Initializing and Making Calls
Client and Call Initialization:
```javascript

client = await SignalWire.SignalWire({
token: _token,
rootElement: document.getElementById('rootElement'),
})

const call = await client.dial({
to: document.getElementById('destination').value,
logLevel: 'debug',
debug: { logWsTraffic: true },
})

await call start()
```

### Debugging
Enable Debugging: It is recommended to run with debugging turned on to assist in reporting any issues.


