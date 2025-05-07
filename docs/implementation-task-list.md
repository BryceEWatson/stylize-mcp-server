Okay, this is an excellent implementation plan. Let's break it down into a detailed, step-by-step task list suitable for an AI agent software engineer and a human approver/reviewer.

The tasks will be prefixed with:
*   **[AI Agent]** for tasks the AI is expected to perform.
*   **[Human Reviewer]** for tasks requiring human oversight, review, or approval.
*   **[Both]** for collaborative tasks or discussions.

We'll follow the structure of your implementation plan.

---

**Project: Stylize MCP Server MVP - Detailed Task List**

**Goal:** Deliver the MVP version of the Stylize MCP Server.

**Team:**
*   AI Software Engineer (Implementer)
*   Human Product Owner/Engineer (Approver/Reviewer)

---

**Phase 1: Project Setup and Scaffolding**
*Milestone Criteria: Repository setup, running server with stubbed `GET /health` and `POST /stylize_image`, FastMCP initialized with dummy tool. Human engineer reviews project structure and baseline code.*

1.  **Task 1.1: Repository and Initial Structure**
    *   **[AI Agent]:** Initialize a new private GitHub repository named `stylize-mcp-server` (or similar).
    *   **[AI Agent]:** Select Python as the primary language.
    *   **[AI Agent]:** Create the initial directory structure:
        *   `stylize-mcp-server/`
            *   `app/` (for application code)
            *   `infra/` (for Terraform IaC)
            *   `docs/` (for documentation)
            *   `.gitignore` (Python template)
            *   `README.md` (initial draft)
            *   `requirements.txt` (or `pyproject.toml` if using Poetry/PDM)
    *   **[AI Agent]:** Populate `README.md` with:
        *   Project Title: Stylize MCP Server MVP
        *   Brief overview of the service.
        *   MVP Goals (summarized from vision).
        *   Placeholder for "Local Development Setup" instructions.
    *   **[AI Agent]:** Commit and push initial structure to the `main` (or `master`) branch.
    *   **[Human Reviewer]:** Review GitHub repository settings (e.g., branch protection rules if desired later).
    *   **[Human Reviewer]:** Review directory structure and initial `README.md` for clarity and completeness. Approve or request changes.

2.  **Task 1.2: Define API Contract (MVP)**
    *   **[AI Agent]:** Create `docs/api_contract_mvp.md`.
    *   **[AI Agent]:** Document `POST /stylize_image`:
        *   Method: `POST`
        *   Path: `/stylize_image`
        *   Request: `multipart/form-data` with `image` (file) and `style_id` (string).
        *   Response (Success 200 OK): JSON `{"original_id": "string", "style": "string", "stylized_image_url": "string_url"}` (placeholder values).
        *   Response (Error 400 Bad Request): JSON `{"error": "message"}`.
    *   **[AI Agent]:** Document `GET /styles`:
        *   Method: `GET`
        *   Path: `/styles`
        *   Response (Success 200 OK): JSON array `[{"id": "string", "name": "string", "description": "string", "prompt_fragment": "string"}]` (placeholder).
    *   **[AI Agent]:** Document `GET /health`:
        *   Method: `GET`
        *   Path: `/health`
        *   Response (Success 200 OK): JSON `{"status": "ok"}`.
    *   **[AI Agent]:** Document MVP Authentication Decision: "For MVP, no specific authentication will be implemented for `/stylize_image` or `/styles`. Requests will be processed under a single global user context for quota purposes initially. User identification for quotas will be handled via client IP or a simple, non-validated header if necessary." (Or specify API key if decided).
    *   **[Human Reviewer]:** Review `api_contract_mvp.md`. Ensure it aligns with MVP goals and is clear for implementation. Approve or request changes.

3.  **Task 1.3: Baseline Application Skeleton (FastAPI)**
    *   **[AI Agent]:** Initialize FastAPI project in `app/` (e.g., `app/main.py`).
    *   **[AI Agent]:** Add `fastapi`, `uvicorn[standard]`, `python-multipart` to `requirements.txt`. Install dependencies.
    *   **[AI Agent]:** Implement `GET /health` endpoint returning `{"status": "ok"}`.
    *   **[AI Agent]:** Implement stubbed `POST /stylize_image` endpoint:
        *   Accepts `UploadFile` and `style_id` (form data).
        *   Returns a placeholder JSON response, e.g., `{"original_id": "temp_id", "style": style_id, "stylized_image_url": "http://example.com/placeholder.jpg"}`.
    *   **[AI Agent]:** Implement stubbed `GET /styles` endpoint returning an empty list `[]`.
    *   **[AI Agent]:** Implement basic request logging middleware (e.g., log request method, path, client IP, request ID).
    *   **[AI Agent]:** Implement basic error handling middleware to catch unhandled exceptions and return a generic JSON error response (e.g., `{"detail": "Internal server error"}`).
    *   **[AI Agent]:** Add instructions to `README.md` on how to run the server locally (e.g., `uvicorn app.main:app --reload`).
    *   **[AI Agent]:** Commit and push changes.
    *   **[Human Reviewer]:** Pull changes. Run the server locally. Test `GET /health`, stubbed `POST /stylize_image` (using curl or Postman), and stubbed `GET /styles`. Review code for clarity, basic logging, and error handling. Approve or request changes.

4.  **Task 1.4: MCP Server Initialization (FastMCP)**
    *   **[AI Agent]:** Add `fastmcp` to `requirements.txt`. Install.
    *   **[AI Agent]:** In `app/main.py` (or a dedicated `app/mcp_server.py` imported by `main.py`):
        *   Initialize `mcp = FastMCP("StylizeServer")`.
        *   Define a placeholder MCP tool:
            ```python
            @mcp.tool()
            async def stylize_image_mcp_tool(image_bytes: bytes, style_id: str) -> str: # Or appropriate signature
                """(Placeholder) Stylizes an image with the given style. Returns URL of stylized image."""
                return f"Placeholder: Image with style '{style_id}' processed. Output at http://example.com/mcp_placeholder.jpg"
            ```
    *   **[AI Agent]:** Ensure FastMCP integrates with FastAPI. (If FastMCP provides a FastAPI router, mount it. Otherwise, research and document how it will run alongside, e.g. FastMCP's built-in server on a different port for now, or if it can be made to use FastAPI's ASGI lifecycle). For MVP, aim for FastMCP's recommended FastAPI integration.
    *   **[AI Agent]:** Document in `README.md` or `docs/` how the MCP server is expected to run/be accessed for local testing (e.g., SSE endpoint URL).
    *   **[AI Agent]:** Commit and push changes.
    *   **[Human Reviewer]:** Review MCP initialization code, dummy tool definition, and the integration strategy with FastAPI. Test if the FastMCP server part runs without errors. Approve or request changes.

5.  **Task 1.5: Milestone Review - Scaffolding Complete**
    *   **[Human Reviewer]:** Confirm all criteria for "Milestone – Scaffolding Complete" are met.
        *   Repository set up.
        *   `README.md` with basic info.
        *   API contract documented.
        *   FastAPI server runs locally.
        *   `GET /health` works.
        *   `POST /stylize_image` (stubbed) works.
        *   `GET /styles` (stubbed) works.
        *   FastMCP server initialized with a dummy tool.
        *   Project structure and baseline code are clear and correct.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 2.

---

**Phase 2: Infrastructure Provisioning (Terraform IaC)**
*Milestone Criteria: Terraform applies cleanly, all cloud resources created. Cloud Run service (placeholder) can connect to Redis, Firestore, Secret Manager. CI pipeline in place. Human engineer reviews Terraform scripts and connectivity.*

1.  **Task 2.1: Terraform Project Initialization & GCP Provider**
    *   **[AI Agent]:** In `infra/`:
        *   Create `main.tf`, `variables.tf`, `outputs.tf`, `versions.tf`.
        *   Configure `versions.tf` for required Terraform version and Google Cloud provider (e.g., `hashicorp/google`).
        *   In `variables.tf`, define `gcp_project_id`, `gcp_region`, `gcp_zone`.
        *   In `main.tf`, configure the Google Cloud provider block.
    *   **[AI Agent]:** Create `terraform.tfvars.example` with placeholders for `gcp_project_id`, `gcp_region`.
    *   **[AI Agent]:** Run `terraform init`.
    *   **[AI Agent]:** Commit and push changes.
    *   **[Human Reviewer]:** Review Terraform project setup and provider configuration. Ensure `terraform.tfvars` is in `.gitignore`.

2.  **Task 2.2: Networking Resources**
    *   **[AI Agent]:** Create `infra/network.tf`.
    *   **[AI Agent]:** Define resources for:
        *   VPC Network (`google_compute_network`).
        *   Subnet for Serverless VPC Access Connector (`google_compute_subnetwork`, e.g., `10.8.0.0/28`).
        *   Serverless VPC Access Connector (`google_vpc_access_connector`).
        *   Cloud Router (`google_compute_router`).
        *   Cloud NAT (`google_compute_router_nat`) configured for the subnet and router.
    *   **[AI Agent]:** Output relevant network IDs/names in `outputs.tf`.
    *   **[AI Agent]:** Run `terraform fmt` and `terraform validate`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `network.tf` for correctness, CIDR ranges, and dependencies.

3.  **Task 2.3: Service Account**
    *   **[AI Agent]:** Create `infra/iam.tf`.
    *   **[AI Agent]:** Define `google_service_account` for `stylize-mcp-sa`.
    *   **[AI Agent]:** Define `google_project_iam_member` bindings for `stylize-mcp-sa` with roles:
        *   `roles/storage.objectAdmin` (for GCS)
        *   `roles/datastore.user` (for Firestore)
        *   `roles/vision.user` (for Vision API)
        *   `roles/pubsub.publisher` (for Pub/Sub, if `stylize-analytics` topic is included)
        *   `roles/secretmanager.secretAccessor` (for Secret Manager)
    *   **[AI Agent]:** Run `terraform fmt` and `terraform validate`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `iam.tf` to ensure adherence to the principle of least privilege for the defined roles.

4.  **Task 2.4: Storage and Database Resources**
    *   **[AI Agent]:** Create `infra/storage.tf`.
    *   **[AI Agent]:** Define GCS buckets (`google_storage_bucket`):
        *   `stylize-originals-<project_id_suffix>`
        *   `stylize-variants-<project_id_suffix>`
        *   Configure uniform bucket-level access.
    *   **[AI Agent]:** Define Memorystore for Redis instance (`google_redis_instance`):
        *   Smallest practical tier (e.g., BASIC, 1GB).
        *   Connect to the created VPC network.
        *   Specify region.
    *   **[AI Agent]:** (Optional for MVP analytics) Define Pub/Sub topic (`google_pubsub_topic`) `stylize-analytics`.
    *   **[AI Agent]:** Note in `docs/manual_setup_steps.md` (create if not exists) that "Cloud Firestore API must be enabled for the GCP project, and Firestore database initialized in Native mode (if not already done via console)."
    *   **[AI Agent]:** Output Redis host/port, GCS bucket names in `outputs.tf`.
    *   **[AI Agent]:** Run `terraform fmt` and `terraform validate`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `storage.tf` for bucket configurations, Redis instance settings, and Pub/Sub topic (if included).

5.  **Task 2.5: API Enablement and Secrets**
    *   **[AI Agent]:** Create `infra/apis_secrets.tf`.
    *   **[AI Agent]:** Define `google_project_service` resources to enable:
        *   `run.googleapis.com` (Cloud Run)
        *   `cloudbuild.googleapis.com` (Cloud Build)
        *   `firestore.googleapis.com` (Firestore)
        *   `vision.googleapis.com` (Vision API)
        *   `redis.googleapis.com` (Memorystore for Redis)
        *   `vpcaccess.googleapis.com` (Serverless VPC Access)
        *   `secretmanager.googleapis.com` (Secret Manager)
        *   `pubsub.googleapis.com` (Pub/Sub, if topic included)
        *   `artifactregistry.googleapis.com` (Artifact Registry for Docker images)
    *   **[AI Agent]:** Define `google_secret_manager_secret` for `OPENAI_API_KEY`.
    *   **[AI Agent]:** Define `google_secret_manager_secret_version` for `OPENAI_API_KEY` with placeholder data like "dummy-key" (actual key to be added manually to the first version in GCP Console for security, or via a secure CI variable if the human prefers).
    *   **[AI Agent]:** Document in `docs/manual_setup_steps.md` how to manually add the actual OpenAI API key to the Secret Manager if not done via CI.
    *   **[AI Agent]:** Run `terraform fmt` and `terraform validate`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `apis_secrets.tf` for the list of APIs and Secret Manager configuration. Decide on the method for populating the initial secret value.

6.  **Task 2.6: CI/CD Pipeline (Cloud Build) and Cloud Run Service (Placeholder)**
    *   **[AI Agent]:** Create `cloudbuild.yaml` at the root of the repository:
        *   Step 1: Build Docker image (using `Dockerfile` from next step).
        *   Step 2: Push image to Artifact Registry (e.g., `REGION-docker.pkg.dev/PROJECT_ID/stylize-repo/stylize-mcp-server:$COMMIT_SHA`).
        *   Step 3: Deploy to Cloud Run using `gcloud run deploy stylize-mcp-server --image=... --region=... --allow-unauthenticated --platform=managed --service-account=stylize-mcp-sa@... --vpc-connector=... --set-env-vars=...` (include placeholders for env vars like `REDIS_HOST`, `REDIS_PORT`, `GCP_PROJECT_ID`, `OPENAI_API_KEY_SECRET_PATH`).
    *   **[AI Agent]:** Create a basic `Dockerfile` in the root:
        *   `FROM python:3.10-slim` (or preferred version)
        *   `WORKDIR /app`
        *   `COPY requirements.txt .`
        *   `RUN pip install --no-cache-dir -r requirements.txt`
        *   `COPY app/ ./app/`
        *   `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]`
    *   **[AI Agent]:** In `infra/services.tf` (create if not exists):
        *   Define `google_cloud_run_v2_service` for `stylize-mcp-server`.
        *   Set a placeholder image initially (e.g., `gcr.io/cloudrun/hello`).
        *   Configure `service_account`, `vpc_access` (with connector), environment variables (pointing to Secret Manager for OpenAI key, Redis host/port from Terraform outputs).
        *   Add `lifecycle { ignore_changes = [template.containers.image] }` if Cloud Build will manage image updates directly via `gcloud run deploy`.
    *   **[AI Agent]:** Configure Cloud Build trigger in GCP Console (or describe steps for human) to connect to the GitHub repo and run `cloudbuild.yaml` on pushes to `main`.
    *   **[AI Agent]:** Document IAM roles needed for Cloud Build service account (e.g., Cloud Run Admin, Artifact Registry Writer, Service Account User for deploying with `stylize-mcp-sa`, Secret Manager Secret Accessor if build needs secrets).
    *   **[AI Agent]:** Run `terraform fmt` and `terraform validate`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `cloudbuild.yaml`, `Dockerfile`, Cloud Run Terraform definition (`services.tf`), and trigger setup. Verify Cloud Build SA permissions.

7.  **Task 2.7: Terraform Apply and Initial Verification**
    *   **[Human Reviewer]:** Create `terraform.tfvars` with actual project ID and region.
    *   **[AI Agent]:** Run `terraform plan -out=tfplan`.
    *   **[Human Reviewer]:** Review `terraform plan` output carefully.
    *   **[Both]:** If plan is acceptable, **[AI Agent]** (or Human) runs `terraform apply tfplan`.
    *   **[Human Reviewer]:** Verify resource creation in GCP console.
    *   **[AI Agent]:** Update `app/main.py` to attempt connections (on startup or via a test endpoint):
        *   Read `OPENAI_API_KEY` from Secret Manager (via env var set by Cloud Run).
        *   Connect to Redis (read host/port from env vars).
        *   Perform a simple Firestore operation (e.g., write/read a dummy document).
    *   **[AI Agent]:** Trigger a Cloud Build run to deploy this test application.
    *   **[Human Reviewer]:** Check Cloud Run logs for successful connections and secret retrieval.
    *   **[Human Reviewer]:** Confirm all criteria for "Milestone – Infrastructure Ready" are met. Provide go-ahead for Phase 3.

---

**Phase 3: Core Feature – `stylize_image` Endpoint Implementation**
*Milestone Criteria: `stylize_image` endpoint takes an image and style, returns a stylized image URL from GCS via DALL·E 3. `GET /styles` works. Human engineer reviews OpenAI integration, storage, and overall flow.*

1.  **Task 3.1: Image Input Handling and Validation**
    *   **[AI Agent]:** In `app/main.py` (`POST /stylize_image` handler):
        *   Ensure robust parsing of `multipart/form-data` for `image` (file) and `style_id` (string).
        *   Validate uploaded file:
            *   Is it present?
            *   Content type (e.g., `image/jpeg`, `image/png`).
            *   Size limit (e.g., 5MB, configurable via env var).
        *   Return HTTP 400 with clear JSON error if validation fails.
    *   **[AI Agent]:** Add unit tests for input validation logic (using `pytest` and `httpx`).
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review code for input handling, validation, and error responses. Review unit tests.

2.  **Task 3.2: Style Catalog Loading and `GET /styles` Endpoint**
    *   **[AI Agent]:** Create `app/styles.json` with the defined structure: `id`, `name`, `description`, `prompt_fragment`.
        *   Include at least 3-5 diverse styles, with some from "UI Elements" and "Icons & Logos" categories (e.g., "van_gogh", "pixel_art", "flat_ui_icon", "neumorphic_button").
    *   **[AI Agent]:** Implement logic in `app/main.py` (or a helper module) to load `styles.json` at application startup into an in-memory dictionary or list.
    *   **[AI Agent]:** Implement the actual `GET /styles` endpoint to return the content of the loaded style catalog.
    *   **[AI Agent]:** In `POST /stylize_image` handler, after receiving `style_id`, check if it exists in the loaded catalog. Return HTTP 400 if not found, perhaps listing available style IDs.
    *   **[AI Agent]:** Add unit tests for style catalog loading and the `GET /styles` endpoint.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review `styles.json` content. Review code for catalog loading, `GET /styles` implementation, and style validation in `POST /stylize_image`. Review unit tests.

3.  **Task 3.3: Basic Prompt Templating**
    *   **[AI Agent]:** Define a strategy for prompt templating. For MVP:
        *   User can optionally provide a `user_prompt: str` field in the `POST /stylize_image` request (form data).
        *   If `user_prompt` is provided: final prompt = `f"{user_prompt}, {style['prompt_fragment']}"`.
        *   If `user_prompt` is not provided: final prompt = `style['prompt_fragment']` (assuming the style prompt is self-sufficient for generating an image, or describes a transformation on a generic subject).
    *   **[AI Agent]:** Implement this logic within the `POST /stylize_image` handler.
    *   **[AI Agent]:** Log the final generated prompt (for debugging).
    *   **[AI Agent]:** Add unit tests for prompt templating logic.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review prompt templating logic and its flexibility for MVP. Review unit tests. Acknowledge the "Note for MVP: one style per call" and "Note on Architecture: direct DALL-E call" from the plan.

4.  **Task 3.4: OpenAI DALL·E 3 API Integration**
    *   **[AI Agent]:** Add `openai` to `requirements.txt`. Install.
    *   **[AI Agent]:** Create a service/helper function (e.g., `app/openai_service.py`) to encapsulate DALL·E 3 calls.
    *   **[AI Agent]:** Retrieve OpenAI API key (from environment variable, set by Cloud Run from Secret Manager).
    *   **[AI Agent]:** Implement the DALL·E 3 API call:
        *   Use `client.images.generate()` with the final prompt.
        *   Specify model (e.g., `dall-e-3`), size (e.g., `1024x1024`), quality, n=1.
        *   DALL·E 3's API typically returns a URL to the generated image or base64 data. For MVP, plan to fetch the image data from this URL server-side to then store in GCS.
    *   **[AI Agent]:** Implement error handling for OpenAI API calls (e.g., `openai.APIError`, rate limits, content policy violations from OpenAI). Return appropriate HTTP errors (e.g., 503 if OpenAI is down, 400 if prompt rejected by OpenAI).
    *   **[AI Agent]:** Add unit tests for the OpenAI service, mocking the `openai` client.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review OpenAI API integration code, focusing on API key handling (ensure it's not hardcoded/logged), request parameters, error handling, and the strategy for getting image data. Review unit tests.

5.  **Task 3.5: GCS Integration for Originals and Variants**
    *   **[AI Agent]:** Add `google-cloud-storage` to `requirements.txt`. Install.
    *   **[AI Agent]:** Create a service/helper function (e.g., `app/gcs_service.py`).
    *   **[AI Agent]:** Implement function to upload original image:
        *   Input: image file bytes/stream, unique ID (e.g., UUID).
        *   Upload to `stylize-originals` GCS bucket with name `original_id/original_filename`.
    *   **[AI Agent]:** Implement function to upload generated stylized image:
        *   Input: generated image bytes, original ID, style ID.
        *   Upload to `stylize-variants` GCS bucket with name `original_id/style_id.png` (or appropriate extension).
    *   **[AI Agent]:** Ensure GCS client uses Application Default Credentials (via the Cloud Run service account).
    *   **[AI Agent]:** Set appropriate `content_type` metadata on GCS objects.
    *   **[AI Agent]:** In `POST /stylize_image` handler:
        *   Generate a unique ID for the request (e.g., `request_id = str(uuid.uuid4())`).
        *   Store original image to GCS using `request_id`.
        *   After DALL·E 3 generates image data, store stylized image to GCS using `request_id` and `style_id`.
    *   **[AI Agent]:** Add unit tests for GCS service, mocking the `google-cloud-storage` client.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review GCS integration code, naming conventions for stored objects, and error handling. Review unit tests.

6.  **Task 3.6: Response Construction with Signed URL**
    *   **[AI Agent]:** In `app/gcs_service.py`, implement a function to generate a GCS signed URL for a given object in the `stylize-variants` bucket.
        *   Set TTL to 1 hour for MVP.
    *   **[AI Agent]:** In `POST /stylize_image` handler, after successful stylization and GCS storage:
        *   Generate signed URL for the stylized variant.
        *   Construct the JSON response: `{"original_id": request_id, "style": style_id, "stylized_image_url": signed_url}`.
    *   **[AI Agent]:** Log key details of the successful operation (request ID, style, time taken).
    *   **[AI Agent]:** Add unit tests for signed URL generation.
    *   **[AI Agent]:** Commit and push. Trigger CI/CD deployment.
    *   **[Human Reviewer]:** Review signed URL generation logic and response construction. Perform an end-to-end test by uploading an image and style via Postman/curl to the deployed Cloud Run service. Verify the image appears in GCS and the signed URL works.

7.  **Task 3.7: Milestone Review - Core Stylization Functionality**
    *   **[Human Reviewer]:** Confirm all criteria for "Milestone – Core Stylization Functionality" are met.
        *   `POST /stylize_image` accepts image and valid style_id.
        *   `GET /styles` returns the style catalog.
        *   OpenAI DALL·E 3 is called correctly.
        *   Original and stylized images are stored in GCS.
        *   Response contains a working signed URL to the stylized image.
        *   Basic error handling for invalid inputs and API failures is in place.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 4.

---
*(Continue this detailed breakdown for Phases 4 through 9, following the same pattern: AI Agent implements, Human Reviewer reviews/approves/tests, specific deliverables, and milestone checks.)*

---

**Phase 4: Safety Filtering with Cloud Vision SafeSearch**
*Milestone Criteria: Disallowed images rejected before OpenAI call. Human engineer verifies with test inputs.*

1.  **Task 4.1: Integrate Cloud Vision API Client**
    *   **[AI Agent]:** Add `google-cloud-vision` to `requirements.txt`. Install.
    *   **[AI Agent]:** Create a service/helper function (e.g., `app/vision_service.py`) to call SafeSearch.
        *   Input: image bytes or GCS URI of the original image.
        *   Output: SafeSearch annotation results.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review basic Vision API client setup.

2.  **Task 4.2: Implement SafeSearch Check on Inputs**
    *   **[AI Agent]:** In `POST /stylize_image` handler, *before* calling OpenAI:
        *   Call Vision API SafeSearch on the uploaded original image.
        *   Define policy: if `adult`, `violence`, or `racy` is `LIKELY` or `VERY_LIKELY`, reject.
        *   If rejected:
            *   Return HTTP 400/403 with a message like "Image content not allowed by safety policy."
            *   Do NOT proceed to OpenAI.
            *   (Optional for MVP, but good: Delete original from GCS if already uploaded).
    *   **[AI Agent]:** Log SafeSearch decisions (image blocked/allowed and reason).
    *   **[AI Agent]:** Add unit tests for SafeSearch logic, mocking the Vision API client.
    *   **[AI Agent]:** Commit and push. Trigger CI/CD deployment.
    *   **[Human Reviewer]:** Review SafeSearch integration logic, policy definition, and error handling.

3.  **Task 4.3: Test SafeSearch Functionality**
    *   **[Human Reviewer]:** Prepare test images:
        *   One clearly safe image.
        *   One image likely to trigger `adult` or `violence` (use a non-offensive but clearly classifiable test image, e.g., from a SafeSearch test dataset if available, or a drawing).
    *   **[Human Reviewer]:** Test the deployed service with these images.
        *   Verify safe image is processed.
        *   Verify unsafe image is rejected with the correct error and no OpenAI call is made (check logs/OpenAI usage).
    *   **[Human Reviewer]:** Approve or request adjustments to the SafeSearch policy/implementation.

4.  **Task 4.4: (Optional MVP) SafeSearch on Outputs**
    *   **[Both]:** Decide if SafeSearch on DALL·E 3 outputs is strictly needed for MVP. The plan lists it as optional. If yes:
        *   **[AI Agent]:** After receiving image from OpenAI and before returning to user, run SafeSearch on the generated variant. If flagged, return error and don't store/return the variant.
        *   **[AI Agent]:** Add unit tests.
        *   **[AI Agent]:** Commit and push.
        *   **[Human Reviewer]:** Review and test.
    *   **[Both]:** If skipping for MVP, create a ticket/issue for post-MVP consideration.

5.  **Task 4.5: Milestone Review - Safety Checks**
    *   **[Human Reviewer]:** Confirm input SafeSearch reliably filters content before stylization.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 5.

---

**Phase 5: Caching with Redis (Memorystore)**
*Milestone Criteria: Repeated requests served from cache, no OpenAI call. Human engineer verifies Redis usage and TTL.*

1.  **Task 5.1: Integrate Redis Client and Connect**
    *   **[AI Agent]:** Add `redis` (e.g., `redis-py`) to `requirements.txt`. Install.
    *   **[AI Agent]:** Create `app/cache_service.py`.
    *   **[AI Agent]:** Implement Redis connection logic using host/port from env vars (set by Cloud Run from Terraform outputs).
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review Redis client setup and connection logic.

2.  **Task 5.2: Implement Caching Key Design and Logic**
    *   **[AI Agent]:** In `POST /stylize_image` handler:
        *   After receiving image and `style_id`:
            *   Compute image hash (SHA-256 of image bytes, stream for large files).
            *   Form cache key: `f"stylize:{image_hash}:{style_id}"`.
        *   Check Redis for this key using `cache_service.get(cache_key)`.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review cache key generation.

3.  **Task 5.3: Implement Cache Hit and Miss Logic**
    *   **[AI Agent]:** If cache hit (key exists in Redis):
        *   Retrieve GCS path/signed URL of the stylized image from cache value.
        *   (Optional: verify object still exists in GCS).
        *   Return response directly, bypassing OpenAI, SafeSearch (for original), GCS uploads.
        *   Log "Cache hit".
    *   **[AI Agent]:** If cache miss:
        *   Proceed with normal flow (SafeSearch, OpenAI, GCS uploads).
        *   After successfully storing stylized image in GCS and getting its path/URL:
            *   Store `gcs_path_of_stylized_image` in Redis: `cache_service.set(cache_key, gcs_path_of_stylized_image, ttl=86400)` (1 day TTL for MVP).
        *   Log "Cache miss".
    *   **[AI Agent]:** Add unit tests for caching logic, mocking Redis client.
    *   **[AI Agent]:** Commit and push. Trigger CI/CD.
    *   **[Human Reviewer]:** Review cache hit/miss logic and TTL setting.

4.  **Task 5.4: Test Caching Functionality**
    *   **[Human Reviewer]:** Test the deployed service:
        *   Stylize an image with a style for the first time. Note time taken and check logs for "Cache miss" and OpenAI call.
        *   Stylize the *exact same image* with the *exact same style* again.
        *   Verify the second response is much faster.
        *   Check logs for "Cache hit" and confirm NO new OpenAI call was made.
        *   (Optional: Connect to Redis instance via `redis-cli` through a bastion/test VM in the VPC to inspect keys).
    *   **[Human Reviewer]:** Approve or request adjustments.

5.  **Task 5.5: Milestone Review - Caching Operational**
    *   **[Human Reviewer]:** Confirm cache hits correctly short-circuit generation and Redis is used with TTL.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 6.

---

**Phase 6: Cost Guardrails (Daily Caps & Per-User Quotas)**
*Milestone Criteria: Service enforces daily global and per-user limits. Human engineer verifies with small test quotas.*

1.  **Task 6.1: Define Quota Policy and Firestore Structure**
    *   **[AI Agent]:** Add `google-cloud-firestore` to `requirements.txt`. Install.
    *   **[AI Agent]:** Create `app/quota_service.py`.
    *   **[AI Agent]:** Define Firestore structure for quotas:
        *   Global: Document `usage_quotas/global_daily_cap`. Fields: `date` (YYYY-MM-DD), `count`.
        *   Per-user: Collection `user_daily_usage`. Document ID `YYYY-MM-DD_{user_identifier}`. Fields: `count`. (User identifier: client IP for unauth MVP, or API key/user ID if implemented).
    *   **[AI Agent]:** Configure default global cap (e.g., 100) and per-user cap (e.g., 10) as environment variables (with defaults).
    *   **[Human Reviewer]:** Review Firestore structure and default quota values.

2.  **Task 6.2: Implement Global Counter Logic**
    *   **[AI Agent]:** In `quota_service.py`:
        *   Function `check_and_increment_global_quota()`:
            *   Use Firestore transaction.
            *   Read `usage_quotas/global_daily_cap`.
            *   If `date` field is not today's date, reset `count` to 0 and update `date`.
            *   If `count` >= global daily cap, return `False` (quota exceeded).
            *   Increment `count`. Write back. Return `True`.
    *   **[AI Agent]:** In `POST /stylize_image` (after cache miss, before OpenAI call):
        *   Call `check_and_increment_global_quota()`. If it returns `False`, return HTTP 429/403 "Global daily quota exceeded."
    *   **[AI Agent]:** Add unit tests, mocking Firestore client.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review global quota logic, especially Firestore transaction and date reset.

3.  **Task 6.3: Implement Per-User Counter Logic**
    *   **[AI Agent]:** In `quota_service.py`:
        *   Function `check_and_increment_user_quota(user_identifier)`:
            *   Determine `user_identifier` (e.g., from request.client.host for FastAPI).
            *   Document key: `f"{today_date}_{user_identifier}"` in `user_daily_usage` collection.
            *   Use Firestore transaction. Read doc.
            *   If doc doesn't exist or its date implies reset, initialize count.
            *   If `count` >= per-user cap, return `False`.
            *   Increment `count`. Write back. Return `True`.
    *   **[AI Agent]:** In `POST /stylize_image` (after global quota check passes):
        *   Call `check_and_increment_user_quota()`. If `False`, return HTTP 429/403 "Per-user daily quota exceeded."
    *   **[AI Agent]:** Add unit tests, mocking Firestore client.
    *   **[AI Agent]:** Commit and push. Trigger CI/CD.
    *   **[Human Reviewer]:** Review per-user quota logic, user identification method for MVP, and Firestore transactions.

4.  **Task 6.4: Test Quota Behavior**
    *   **[Human Reviewer]:** Temporarily set very low quotas via env vars for the deployed service (e.g., global=2, per-user=1).
    *   **[Human Reviewer]:** Test global quota: Make 3 requests. The 3rd should be blocked.
    *   **[Human Reviewer]:** Test per-user quota: As one "user" (IP), make 2 requests. The 2nd should be blocked. Try from a different IP; first request should pass.
    *   **[Human Reviewer]:** Check Firestore data to verify counts and resets (e.g., after date changes).
    *   **[Human Reviewer]:** Restore original quota values. Approve or request adjustments.

5.  **Task 6.5: Milestone Review - Cost Guardrails Active**
    *   **[Human Reviewer]:** Confirm service enforces limits and Firestore checks are efficient.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 7.

---

**Phase 7: Usage Analytics and Monitoring**
*Milestone Criteria: Basic usage analytics (e.g., stylizations, cache hits) can be retrieved from logs/Firestore. Human engineer verifies data recording.*

1.  **Task 7.1: Leverage Cloud Logging and Monitoring**
    *   **[AI Agent]:** Ensure important events are already being logged with appropriate severity from previous phases (request received, cache hit/miss, OpenAI call, image stored, errors, SafeSearch decisions, quota enforcement). Add any missing crucial log points.
    *   **[AI Agent]:** Review standard Cloud Run metrics available in Cloud Monitoring.
    *   **[AI Agent]:** Create `docs/monitoring_analytics.md`. Document how to view basic logs and metrics in GCP console.
    *   **[Human Reviewer]:** Review existing logging points for completeness. Review documentation.

2.  **Task 7.2: Implement Custom Analytics Data Collection (Firestore for MVP)**
    *   **[AI Agent]:** For MVP, choose Firestore for custom analytics.
        *   Define Firestore collection `stylize_analytics_events`.
        *   Each document represents a processed request (or significant event).
        *   Fields: `timestamp`, `user_identifier` (IP for MVP), `style_id_requested`, `was_successful` (boolean), `was_cached` (boolean), `error_type` (if any, e.g., "safesearch_block", "quota_exceeded", "openai_error"), `processing_time_ms`.
    *   **[AI Agent]:** In `POST /stylize_image`, at the end of processing (or in `finally` block):
        *   Asynchronously log an event document to `stylize_analytics_events`. (Use `async def` and `await` if calling from async FastAPI, or run in background task if synchronous Firestore client is easier).
    *   **[AI Agent]:** Add unit tests for analytics event creation, mocking Firestore.
    *   **[AI Agent]:** Commit and push. Trigger CI/CD.
    *   **[Human Reviewer]:** Review analytics data structure and Firestore logging implementation. Discuss async vs. background task.

3.  **Task 7.3: Test Analytics Recording**
    *   **[Human Reviewer]:** Make several diverse requests to the deployed service (success, cache hit, SafeSearch block, quota block if possible).
    *   **[Human Reviewer]:** Check Firestore `stylize_analytics_events` collection to verify events are recorded correctly with appropriate data.
    *   **[Human Reviewer]:** Document in `docs/monitoring_analytics.md` how to query this Firestore collection for basic stats (e.g., "How many images stylized today?", "Cache hit percentage?").

4.  **Task 7.4: Milestone Review - Analytics & Monitoring**
    *   **[Human Reviewer]:** Confirm basic usage data is flowing and can be queried.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 8.

---

**Phase 8: MCP FastMCP Protocol Support**
*Milestone Criteria: `stylize_image` tool accessible via MCP client. Human engineer verifies with test client, ensuring REST API remains functional.*

1.  **Task 8.1: Refactor Core Logic for Shared Use**
    *   **[AI Agent]:** Identify the core stylization logic currently in the `POST /stylize_image` HTTP handler (input validation, style lookup, SafeSearch, prompt templating, cache check, OpenAI call, GCS storage, quota checks).
    *   **[AI Agent]:** Refactor this core logic into a reusable internal function or service class (e.g., `app/stylize_service.py` function `async def process_stylization(image_bytes: bytes, style_id: str, user_prompt: Optional[str], user_identifier: str) -> StylizationResult`).
    *   **[AI Agent]:** Update the `POST /stylize_image` HTTP handler to call this new service function.
    *   **[AI Agent]:** Ensure all existing unit tests pass after refactoring. Add tests for the new service function.
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review the refactoring carefully. Ensure no functionality is broken and the core logic is cleanly separated. Verify REST API still works as before.

2.  **Task 8.2: Implement MCP Tool (`stylize_image_tool`)**
    *   **[AI Agent]:** Update the placeholder `stylize_image_mcp_tool` defined in Phase 1.4.
    *   **[AI Agent]:** The MCP tool function should:
        *   Accept parameters like `image_bytes: bytes`, `style_id: str`, (optionally `user_prompt: str`).
        *   Determine `user_identifier` (e.g., from MCP context if available, or default to "mcp_user").
        *   Call the refactored `process_stylization` service function.
        *   Return the `stylized_image_url` as a string, or a descriptive string like "Image stylized and stored at <URL>".
    *   **[AI Agent]:** Update the docstring of the MCP tool to accurately describe its function, parameters, and return value for MCP client discovery.
    *   **[AI Agent]:** Ensure FastMCP server is correctly configured to expose this tool (e.g., via SSE endpoint like `/mcp/sse`).
    *   **[AI Agent]:** Commit and push.
    *   **[Human Reviewer]:** Review MCP tool implementation, parameter handling, and how it calls the shared core logic.

3.  **Task 8.3: Test MCP Tool with a Client**
    *   **[AI Agent]:** Provide a simple Python script using `fastmcp` client library to connect to the local/deployed server's MCP SSE endpoint and invoke the `stylize_image_tool` with test image bytes and a style ID.
    *   **[AI Agent]:** Document how to run this test client script in `docs/mcp_testing.md`.
    *   **[Human Reviewer]:** Run the test MCP client against the deployed service.
        *   Verify successful invocation and a correct response (stylized image URL).
        *   Check logs to ensure the stylization process (OpenAI call, GCS storage, etc.) occurred.
        *   Verify that quotas and analytics are also applied to MCP tool usage.
    *   **[Human Reviewer]:** Ensure the REST API (`POST /stylize_image`) continues to function correctly in parallel.
    *   **[Human Reviewer]:** Approve or request adjustments.

4.  **Task 8.4: Milestone Review - MCP Support**
    *   **[Human Reviewer]:** Confirm MCP tool is functional, documented, and REST API is not broken.
    *   **[Human Reviewer]:** Provide go-ahead for Phase 9.

---

**Phase 9: Final Testing and QA**
*Milestone Criteria: All MVP features verified. CI/CD deploys functional code. Documentation updated. Human engineer does final review and approves MVP launch readiness.*

1.  **Task 9.1: Comprehensive Functional Testing (Test Suite)**
    *   **[AI Agent]:** Create a functional test plan document (`docs/functional_tests_mvp.md`) covering:
        1.  Stylize success path (various images, styles).
        2.  `GET /styles` correctness.
        3.  SafeSearch blocking (input images).
        4.  Quota exceeded (global and per-user).
        5.  Cache hit behavior.
        6.  Invalid inputs (non-image file, unsupported style ID, oversized image).
        7.  MCP tool invocation success.
        8.  Error responses (format, codes).
    *   **[AI Agent]:** Where possible, write automated functional tests using `pytest` and `httpx` that can run against a deployed instance (potentially using a dedicated test GCP project or specific test flags to mock external calls like OpenAI to save cost in CI). For MVP, some manual steps might be needed for visual checks.
    *   **[Human Reviewer]:** Review the test plan. Execute all tests (manual and automated) on the deployed service. Report any bugs or issues.
    *   **[AI Agent]:** Fix any reported bugs from functional testing. Commit and redeploy.
    *   **[Human Reviewer]:** Re-test fixed bugs.

2.  **Task 9.2: Basic Performance & Load Testing (Manual)**
    *   **[Human Reviewer]:** Perform basic checks:
        *   Time a few stylization requests. Note average latency.
        *   Send a few (e.g., 3-5) requests in parallel to check concurrency handling.
        *   Monitor Cloud Run memory/CPU usage during these tests. Default 512MiB/1GiB should be fine.
    *   **[Human Reviewer]:** Document findings in `docs/performance_notes_mvp.md`. Note any obvious bottlenecks (unlikely for MVP scope if DALL-E is the main latency).

3.  **Task 9.3: Security Review (Checklist)**
    *   **[Human Reviewer]:** Perform a final security check based on the plan:
        *   OpenAI API key only in Secret Manager, not logged or exposed. Confirmed.
        *   GCS Signed URLs used. Confirmed.
        *   Service Account keys not embedded. Confirmed (using IAM roles).
        *   External calls use HTTPS. Confirmed.
        *   Consider Cloud Run authentication (for MVP, unauthenticated + quotas is per plan, note risk).
        *   Review IAM roles for least privilege.
    *   **[Human Reviewer]:** Document review in `docs/security_review_mvp.md`.

4.  **Task 9.4: Documentation Finalization**
    *   **[AI Agent]:** Update `README.md` to be comprehensive:
        *   Final overview.
        *   Link to API contract, usage examples (curl for HTTP, snippet for MCP).
        *   Available styles (or link to `GET /styles`).
        *   Safety and quota limits.
        *   Known limitations for MVP.
        *   Local development setup.
        *   Deployment info (CI/CD).
    *   **[AI Agent]:** Ensure all documents in `docs/` are up-to-date.
    *   **[Human Reviewer]:** Review all documentation for accuracy, clarity, and completeness.

5.  **Task 9.5: CI/CD Pipeline Verification**
    *   **[AI Agent]:** Make a small, non-breaking code change (e.g., update a log message).
    *   **[AI Agent]:** Commit and push to `main`.
    *   **[Human Reviewer]:** Verify the Cloud Build CI/CD pipeline triggers, builds, and deploys the new version to Cloud Run successfully. Test the minor change.

6.  **Task 9.6: Milestone Review – MVP Complete (Ready for Launch)**
    *   **[Human Reviewer]:** Perform a final holistic review of the system: code quality, infrastructure configuration, functionality against MVP scope, documentation.
    *   **[Human Reviewer]:** Confirm all previous milestone criteria have been met and verified.
    *   **[Human Reviewer]:** Resolve or explicitly defer any outstanding minor issues.
    *   **[Human Reviewer]:** Declare the MVP "done" and ready for its intended use/audience.

---

**Phase 10 & 11: Post-MVP Considerations & Pitfall Monitoring**

1.  **Task 10.1: Document Pitfalls and Post-MVP Items**
    *   **[AI Agent]:** Ensure "Potential Pitfalls and Mitigations" (Plan Section 10) and "Key Post-MVP Considerations from Vision" (Plan Section 11, formerly 10) are well-documented in `docs/` or a project wiki/issue tracker.
    *   **[Human Reviewer]:** Review these documents and create initial backlog items/tickets for post-MVP work (e.g., GDPR compliance, Vertex AI integration, batch processing).

---

This detailed task list should provide a clear roadmap for both the AI agent and the human reviewer, facilitating efficient development and ensuring all aspects of the implementation plan are covered. Remember to use a proper issue tracker (like GitHub Issues) to manage these tasks and their statuses.