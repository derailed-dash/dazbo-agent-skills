# Unified Testing Documentation

This document serves as the comprehensive guide for testing strategy, execution, and manual verification for the Rickbot-ADK project.

## Table of Contents

0. [General Testing Principles](#general-testing-principles)
   - [CI-Aware Execution](#ci-aware-execution)
   - [Running Tests (All Commands)](#running-tests-all-commands)
1. [Backend Testing Strategy](#backend-testing-strategy)
   - [Test Summary](#test-summary)
   - [Configuration & Test Mode](#configuration--test-mode)
2. [Frontend Testing Strategy](#frontend-testing-strategy)
   - [Stack Overview](#stack-overview)
   - [Writing Frontend Tests](#writing-frontend-tests)
3. [Authentication & Session Management](#authentication--session-management)
   - [Retrieving Bearer Tokens](#retrieving-bearer-tokens)
   - [Mock Tokens](#mock-tokens)
4. [Manual API Verification](#manual-api-verification)
   - [Using Curl with Authentication](#using-curl-with-authentication)
   - [Artifact Retrieval](#artifact-retrieval)

---

## General Testing Principles

Regardless of the component being tested (Backend or Frontend), the following principles apply:

### CI-Aware Execution

All test runners should be aware of the `CI` environment variable. When `CI=true`:
- Test runners must execute once and exit (no watch mode).
- Interactive prompts must be suppressed.
- Output should be optimized for logs.

### Running Tests (All Commands)

#### Backend (Python)

- Run unit tests: `make test`
- Run all tests (Unit + Integration): `make test-all`
- Run specific test file: `uv run pytest -v -s src/tests/unit/test_config.py`

#### Frontend (React/Next.js)

- Run all tests: `make test-ui` (or `cd src/nextjs_fe && npm test`)
- Run in watch mode: `cd src/nextjs_fe && npm run test:watch`

---

## Backend Testing Strategy

This section covers the strategy for testing the Python backend components of the Rickbot-ADK project.

### Test Summary

The following table summarizes the existing backend tests, their category, and their purpose:

| File | Category | Purpose |
| :--- | :--- | :--- |
| `test_config.py` | Unit | Verifies the loading and validation of application configuration from `config.py`. |
| `test_create_auth_secrets.py` | Unit | Tests the utility script for creating Streamlit authentication secrets. |
| `test_logging_utils.py` | Unit | Validates the setup and functionality of the logging utilities. |
| `test_personality.py` | Unit | Tests the `Personality` data class and ensures personalities are loaded correctly from the YAML configuration. |
| `test_auth_models.py` | Unit | Tests the `AuthUser` Pydantic model for user authentication data. |
| `test_auth_dependency.py` | Unit | Verifies the token validation logic, including mock token support. |
| `test_api_auth.py` | Unit | Tests authentication endpoints and logic within the API. |
| `test_api_fastapi.py` | Unit | Tests core FastAPI application configuration and middleware. |
| `test_api_personas.py` | Unit | Detailed unit tests for the `/personas` endpoint logic. |
| `test_access_control_services.py` | Unit | Tests the retrieval of user roles and persona requirements from Firestore (mocked). |
| `test_access_control_middleware.py` | Unit | Verifies that the `PersonaAccessMiddleware` correctly enforces RBAC and returns structured errors. |
| `test_artifacts.py` | Integration | Verifies that file uploads are saved as ADK Artifacts and can be retrieved via the `/artifacts` endpoint. |
| `test_tool_status.py` | Integration | Verifies that tool call events are correctly emitted by the `/chat_stream` endpoint. |
| `test_api.py` | Integration | Contains tests for the FastAPI `/chat` endpoint. Includes a mocked test for basic success and a true integration test for multi-turn conversation memory. |
| `test_personalities.py` | Integration | Runs a simple query against every available agent personality to ensure each one can be loaded and can respond. |
| `test_rickbot_agent_multiturn.py` | Integration | Verifies the agent's conversation memory by directly using the ADK `Runner` for a two-turn conversation. |
| `test_server_e2e.py` | Integration (E2E) | Provides an end-to-end test by starting the actual FastAPI server via `uvicorn` and testing endpoints like `/chat` and `/chat_stream`. |
| `test_gcs_integration.py` | Integration | Mocks GCS environment and client to ensure `GcsArtifactService` is correctly instantiated and utilized when `ARTIFACT_BUCKET` is set. |

### Configuration & Test Mode

To ensure tests can run without requiring production secrets (specifically those for "Dazbo" or other protected personalities), the test suite runs in **Test Mode**.

- **Mechanism**: The `RICKBOT_TEST_MODE` environment variable is set to `"true"` automatically for all tests via `src/tests/conftest.py`.
- **Behavior**: When `RICKBOT_TEST_MODE` is active, if the application fails to retrieve a system prompt secret from Google Secret Manager, it falls back to a dummy system prompt (`"You are {name}. (DUMMY PROMPT FOR TESTING)"`) instead of raising a `ValueError`.
- **Purpose**: This ensures that unit and integration tests (such as `test_personalities.py`) do not crash due to missing local secrets or permissions, while still allowing the actual logic to be exercised.

#### Conftest

The `src/tests/conftest.py` file is a global Pytest configuration that:
1.  Sets `RICKBOT_TEST_MODE=true` for the entire test session.
2.  Ensures consistent environment variables are available for both unit and integration tests.

---

## Frontend Testing Strategy

The Rickbot-ADK frontend is built with Next.js and is tested using a modern React testing stack.

### Stack Overview

- **Jest**: The primary test runner and assertion library.
- **React Testing Library (RTL)**: Used for rendering components and interacting with them in a way that mimics user behavior.
- **jest-environment-jsdom**: Provides a browser-like environment for testing React components.
- **next/jest**: Official Next.js integration for Jest, which automatically configures transform and environment settings.

### Writing Frontend Tests

Frontend tests are located in `src/nextjs_fe/__tests__/`. We follow these conventions:

- **Component Tests**: Focused on individual UI components (e.g., `AuthButton.test.tsx`).
- **Page Tests**: Focused on full pages and their accessibility (e.g., `Privacy.test.tsx`).
- **User-Centric Testing**: Prefer testing behavior (what the user sees and does) over implementation details (internal state or props).

---

## Authentication & Session Management

The Rickbot-ADK backend requires a valid Bearer token for most operations. This section explains how to obtain a token for manual testing and how to use mock tokens in development.

### Retrieving Bearer Tokens

The easiest way to obtain a valid Bearer token for an active session is using the browser's Developer Tools.

#### From the Network Tab (Recommended)

1. Open the Rickbot UI in your browser and sign in.
2. Open **Developer Tools** (F12 or `Cmd+Opt+I` on Mac).
3. Select the **Network** tab.
4. Refresh the page or perform an action (like changing the personality or sending a message).
5. Look for a request to the backend API (e.g., `personas`, `chat_stream`).
6. Click on the request and go to the **Headers** tab.
7. Locate the **Request Headers** section and find the `Authorization` header.
8. Copy the value after `Bearer ` (e.g., the long string of characters).

#### From the Console
If you have access to the source code and want to quickly log the token, you can temporarily add `console.log(session.idToken)` in `Chat.tsx` and view it in the **Console** tab.

### Mock Tokens

For local development and testing, the backend supports a "Mock Token" format that bypasses Google/GitHub OAuth verification.

- **Format**: `mock:unique_id:email:display_name`
- **Example**: `mock:123:tester@example.com:TesterUser`

To use a mock token:
1. Ensure the backend is NOT in production mode (or `RICKBOT_TEST_MODE=true`).
2. Use the mock string directly in your `Authorization` header:
   ```bash
   Authorization: Bearer mock:123:tester@example.com:TesterUser
   ```

**Note**: Mock tokens are only accepted if the backend's `verify_token` logic allows them, which is typically enabled in development environments.

## Manual API Verification

Once you have obtained a Bearer token, you can use `curl` to manually interact with the API. It is recommended to store your token in an environment variable.

```bash
export AUTH_TOKEN="your_retrieved_token_here"
# OR use a mock token
export AUTH_TOKEN="mock:123:tester@example.com:TesterUser"
```

### Using Curl with Authentication

#### List Available Personas

```bash
curl -X GET "http://localhost:8000/personas" \
  -H "Authorization: Bearer $AUTH_TOKEN"
```

#### Send a Message (Single-Turn)

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "prompt=Hello Rick!" \
  -F "personality=Rick" \
  -F "user_id=test_user"
```

#### Stream a Conversation

```bash
curl -X POST "http://localhost:8000/chat_stream" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "prompt=Tell me a joke" \
  -F "personality=Rick" \
  -F "user_id=test_user"
```

### Artifact Retrieval

One of the primary uses for manual `curl` testing is verifying ADK Artifacts (files, images, videos) that the agent might have generated or received.

#### Download/Retrieve an Artifact

Replace `<FILENAME>` with the actual filename of the artifact (e.g., `image_123.png`).

```bash
curl -X GET "http://localhost:8000/artifacts/<FILENAME>" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  --output downloaded_artifact.png
```

**Note**: You can find artifact filenames in the JSON response or stream data from the `/chat` or `/chat_stream` endpoints.

### Access Control (RBAC) Verification

To manually verify that persona access restrictions are working correctly, use the following `curl` commands with different mock users.

#### 1. Verify Restricted Access (Standard User)
Attempt to access a 'supporter'-tier persona (e.g., Yasmin) with a 'standard' mock user.

```bash
curl -v -X POST http://localhost:8000/chat \
  -F "personality=Yasmin" \
  -F "prompt=hi" \
  -H "Authorization: Bearer mock:1:user@example.com:User"
```
**Expected Outcome**: `403 Forbidden` with a JSON body containing `"error_code": "UPGRADE_REQUIRED"`.

#### 2. Verify Allowed Access (Supporter User)
Access a 'supporter'-tier persona (e.g., Dazbo) with a mock user who has the 'supporter' role seeded in Firestore.

```bash
curl -v -X POST http://localhost:8000/chat \
  -F "personality=Dazbo" \
  -F "prompt=hi" \
  -H "Authorization: Bearer mock:derailed-dash:derailed.dash@gmail.com:Dazbo"
```
**Expected Outcome**: `200 OK` with a valid agent response.
