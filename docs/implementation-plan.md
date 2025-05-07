Great, I’ll now prepare an actionable and prioritized implementation plan focused on delivering the Stylize MCP MVP based on your vision. I’ll organize the tasks by functional area, dependencies, and sequencing so the engineering process can begin smoothly.


# Stylize MCP Server MVP Implementation Plan

This plan outlines the steps to build the **MVP version of the Stylize MCP Server**. It covers all required features, infrastructure setup, task sequencing, milestone criteria, and potential pitfalls. The implementation will be executed primarily by the AI agent (end-to-end coding, infra, docs), with the human engineer providing code review and oversight at key milestones.

## 1. Project Setup and Scaffolding

* **Choose Tech Stack & Repo Setup:**

  * Use a high-level web framework (e.g. **Python FastAPI** or **Node.js Express**) for the HTTP API. Python is preferred to leverage FastMCP’s Python library and Google Cloud client libraries.
  * Initialize a GitHub repository for the project. Set up a clear directory structure: e.g. `app/` for code, `infra/` for Terraform, `docs/` for documentation.
  * Add a README with an overview of the service and the MVP goals. Include instructions for local development (how to run the server, etc.).

* **Define API Contract:**

  * Design the `stylize_image` REST endpoint (e.g. `POST /stylize_image`). Document its request/response format (input: image file + style identifier, output: stylized image URL or binary).
  * If needed, define a simple authentication/ID mechanism for users (for per-user quotas). For MVP, this could be an API key or a user ID passed in headers or request (to identify usage per user). If no auth, treat all requests under a single global user context.

* **Baseline Application Skeleton:**

  * Scaffold the web service with a minimal route for `stylize_image` (returning a placeholder response initially). Ensure the server runs locally.
  * Implement basic logging for each request (this will aid debugging and later usage analytics). Include request ID logging for traceability.
  * Set up error handling middleware to return JSON errors gracefully (will be used for e.g. SafeSearch violations or quota exceedance).

* **MCP Server Initialization:**

  * Install the **FastMCP** library (if using Python) and verify basic usage. Initialize an MCP server instance in the code (e.g. `mcp = FastMCP("StylizeServer")`).
  * Define a placeholder MCP **Tool** for `stylize_image` (e.g. `@mcp.tool()` decorator in Python) that for now just returns a static message or echo. This hooks the function into the MCP protocol as an available action.
  * Ensure the MCP server can run alongside the HTTP API. (If using FastMCP’s built-in server, it may handle HTTP internally. Alternatively, plan to expose MCP via a special endpoint or SSE stream on the same web server. We'll refine this in a later step.)

* **Milestone – Scaffolding Complete:**
  **Criteria:** The repository is set up with a running server that exposes `GET /health` (or similar) and `POST /stylize_image` (stubbed). The FastMCP server is initialized with a dummy tool. The human engineer reviews the project structure and baseline code for clarity and correctness. No real functionality yet – this just verifies that the development environment is ready and code style/configuration meets standards.

## 2. Infrastructure Provisioning (Terraform IaC)

* **Terraform Project Initialization:**

  * Write Terraform configuration in `infra/` to provision all required cloud resources. Break the config into logical files/modules (e.g. `main.tf`, `network.tf`, `storage.tf`, `services.tf`, etc.) for clarity.
  * Configure the Google Cloud provider in Terraform (ensure the GCP project and credentials are set up). This allows automated provisioning of GCP resources.

* **Networking and Access Setup:**

  * **VPC and Serverless Connector:** Create a VPC network and a **Serverless VPC Access Connector** for Cloud Run to enable private resource access. Use a /28 CIDR (e.g. 10.8.0.0/28) for the connector’s subnet.
  * **Cloud NAT:** Provision a Cloud Router and Cloud NAT on the VPC to allow the Cloud Run service egress to the internet (for calling external APIs like OpenAI). This ensures that with the VPC connector, external traffic routes through NAT.
  * **Service Account:** Create a dedicated service account for the Cloud Run service (e.g. `stylize-mcp-sa`). Grant it necessary IAM roles: Storage Object Admin (for GCS access), Firestore User, Vision API User, Pub/Sub Publisher (if used for analytics), and Secret Manager Accessor (to read API keys). Principle of least privilege is applied.

* **Storage and Database:**

  * **Google Cloud Storage (GCS):** Create two buckets for images (or one bucket with separate prefixes): e.g. `stylize-originals` and `stylize-variants`. These will store uploaded original images and generated stylized images respectively. Apply appropriate access control (the Cloud Run service account can have read/write, public access is disabled by default).
  * **Firestore:** Enable Cloud Firestore in Native mode for the project (if not already). No specific Terraform resource exists to create Firestore (it’s an API enablement), but ensure the API is enabled in project and secure rules are in place. Firestore will be used to store the **style catalog** and possibly **usage records/quotas**.
  * **Redis (Memorystore):** Provision a Memorystore for Redis instance (likely a small **Redis** instance, e.g. 1GB, tier standard or basic). Place it in the same region and VPC network. Terraform `google_redis_instance` resource can create this. Note the Redis connection IP/port for use in the app.
  * **Pub/Sub (for analytics):** Create a Pub/Sub topic (e.g. `stylize-analytics`) for usage events. This can be optional in MVP (if we decide to log events to Pub/Sub for future processing). If included, grant publish permission to the Cloud Run service account on this topic.

* **API Enablement and Secrets:**

  * **APIs:** Ensure Terraform (or pre-run steps) enables all needed GCP APIs: Cloud Run, Cloud Build, Firestore, Vision API, Memorystore, VPC Access, Secret Manager, Pub/Sub. This avoids runtime errors when the service tries to use them.
  * **Secret Manager:** Store the OpenAI API key (for DALL·E 3) in Secret Manager (e.g. secret name `OPENAI_API_KEY`). Terraform can provision the secret and set its value (or the value can be manually added out-of-band for security). Grant the Cloud Run service account **Secret Manager Secret Accessor** permission to this secret.
  * *(Optional)* Also store other config in Secret Manager if desired (for example, a map of daily quota values or other sensitive config), or use environment variables for non-sensitive configs.

* **CI/CD Pipeline (Cloud Build) Setup:**

  * Configure a **Cloud Build trigger** connected to the GitHub repo (using GitHub App integration). This trigger should run on commits to the main branch (and optionally PRs for testing).
  * Write a `cloudbuild.yaml` script in the repo for the CI pipeline. Include steps to:

    1. Build the Docker image for the Stylize server (using a Dockerfile or Buildpacks).
    2. Run unit tests (later, after implementing features, we will add tests).
    3. Push the image to Container Registry or Artifact Registry.
    4. Deploy the new image to Cloud Run (either by calling `gcloud run deploy` or by running `terraform apply` with the new image reference).
  * Secure the Cloud Build pipeline: use a substitution or Secret Manager integration to fetch the OpenAI API key for testing if needed, but **do not hardcode secrets**. The deploy step should reference the secret by name so that Cloud Run loads it via Secret Manager at runtime (not at build time).
  * Ensure Cloud Build has necessary IAM to deploy to Cloud Run and run Terraform (e.g. add Cloud Build service account roles for Cloud Run Admin, Storage Admin, etc., or use a separate deploy service account).

* **Milestone – Infrastructure Ready:**
  **Criteria:** Terraform applies cleanly, creating all cloud resources. We have: a Cloud Run service (initially can be a placeholder image) connected to a VPC, Redis instance available, Firestore enabled, GCS buckets created, Vision API enabled, Secret Manager populated, and CI pipeline in place. The human engineer should review the Terraform scripts and maybe do a dry-run. Successful completion is when the Cloud Run service (even if a dummy app) can start and connect to Redis (test a simple GET/SET), access Firestore (test a simple query), and retrieve the secret from Secret Manager. All plumbing is verified before building core features.

## 3. Core Feature – `stylize_image` Endpoint Implementation

* **Image Input Handling:**

  * Implement file upload handling in the `POST /stylize_image` route. The request may contain a binary image file (e.g. multipart form-data) or a URL to an image. For MVP, assume the client uploads an image file. Use a library to parse the incoming file stream.
  * Validate the input: ensure it’s an image format we support (JPEG/PNG) and below a size limit (define a max file size, e.g. 5MB, to prevent abuse). If invalid, respond with HTTP 400 error.

* **Style Parameter:**

  * The request should also include a style identifier (e.g. a string or ID referencing a style in our catalog). Accept a style ID or name and check it against the loaded style catalog (to ensure it’s a supported style).
  * If the style is not recognized, return a clear error message listing available style options.
  * **Note for MVP:** The `stylize_image` endpoint will process **one style identifier per API call**. Handling multiple style names in a single call is a post-MVP enhancement, aligning with a streamlined MVP approach.

* **Style Catalog Loading:**

  * For MVP, the style catalog (mapping style IDs/names to DALL·E 3 prompt fragments and descriptions) will be stored in a simple **JSON file** (`styles.json`) packaged with the application. This is easy to manage initially.
  * The server will load this JSON at startup.
  * *Future enhancement:* Move this to Firestore for dynamic updates without redeploying.
  * The catalog should define for each style:
    * `id`: A unique string identifier (e.g., "van_gogh", "pixel_art").
    * `name`: A human-readable name (e.g., "Van Gogh", "Pixel Art").
    * `description`: A short description of the style.
    * `prompt_fragment`: The actual text to be appended or used in the DALL·E 3 prompt to achieve this style.
  * An endpoint (`GET /styles`) **must be implemented as part of the MVP** to list all available styles from the catalog. This is a core feature as per the vision document.
  * The initial `styles.json` for the MVP **will include representative styles from "UI Elements" and "Icons & Logos" categories**, in addition to other artistic styles.

* **Basic Prompt Templating:**

  * Implement logic to build the final prompt for the OpenAI API. For MVP, a simple approach: use the style’s prompt template as the basis. If we have a way to describe the original image’s content, insert it; otherwise, just rely on the style prompt.
  * *Example:* If style prompt is `"in the style of Monet's watercolor landscape"`, and if the user’s image is a portrait of a dog, ideally we’d combine to instruct DALL·E accordingly (e.g. "A portrait of a dog, in the style of Monet's watercolor landscape"). If automatic content description is too complex, we might require the user to provide a brief description of their image as input for the MVP. This detail should be clarified: **for MVP, we can assume the user provides a text prompt or the style inherently implies the transformation on the same content**.
  * In summary, prepare variables: the style prompt and possibly the original image description (if available). Combine them to form the text that will be sent to DALL·E 3.

* **Call OpenAI DALL·E 3 API:**

  * Integrate the OpenAI API client. Use the OpenAI Python library or direct HTTP calls. Retrieve the API key from Secret Manager (the library can load from env var).
  * Call the DALL·E 3 API (text-to-image if image-to-image via API is not readily available/documented for direct use, or requires complex input preparation. If image-to-image is simple, use that). The Vision document mentions DALL·E 3 supports image variations, which is ideal.
  * Handle API errors from OpenAI (e.g. rate limits, invalid requests, content policy violations from their end).
  * **Note on Architecture:** For the MVP, the Cloud Run service will call the DALL·E 3 API directly. This is a simplification of the Pub/Sub + Cloud Functions architecture shown in the vision document's high-level diagram. The asynchronous worker architecture is planned for future scalability, batch processing, and multi-engine orchestration.

* **Storing Originals and Variants (GCS Integration):**

  * Upon receiving the request, store the original image file to GCS immediately (e.g. in `stylize-originals` bucket). Generate a unique ID or filename (could use a UUID or a hash of content + style for uniqueness). This is useful for record-keeping and possibly caching keys.
  * After generation, store the stylized image output to GCS (in `stylize-variants` bucket) with a name tied to the original image’s ID and style. For example, if original ID is `12345` and style `van_gogh`, the variant file could be `12345_van_gogh.jpg`.
  * Ensure the GCS upload is done using the service account (the code can use Google Cloud Storage client library, which will pick up credentials). The service account has permission to write to the bucket.
  * Set metadata on the stored images if needed (content-type, and maybe custom metadata like the style used, timestamp, etc., for future reference).

* **Response Construction:**

  * Return a response to the client with the result. For MVP, simplest is to return the **public URL or a signed URL** of the stylized image in GCS. Since the bucket is private, the server can generate a signed URL (valid for e.g. 1 hour for the MVP; the 7-day TTL mentioned in the vision document can be a post-MVP consideration for specific use cases).
  * Include in the JSON response: the `original_image_id` (or URL) and `stylized_image_url`, and possibly some metadata (style name, processing time, etc.). Example response:

    ```json
    {
      "original_id": "12345",
      "style": "van_gogh",
      "stylized_image_url": "https://storage.googleapis.com/stylize-variants/12345_van_gogh.jpg"
    }
    ```
  * Log the operation (original ID, style, time taken, user id if any) for analytics.

* **Milestone – Core Stylization Functionality:**
  **Criteria:** The `stylize_image` endpoint can take a real image and style and return a stylized image successfully. Test by uploading a sample image with a known style from the catalog; verify the OpenAI API is invoked and an image is returned and saved in GCS. For example, input a test image with style "Van Gogh" – the output image in GCS should visibly reflect Van Gogh’s style. The human engineer will review this implementation, focusing on correct use of the OpenAI API (no leakage of API key, error handling on failures) and proper storage of images. At this stage, the basic end-to-end flow (upload -> DALL·E -> output) is working.

## 4. Safety Filtering with Cloud Vision SafeSearch

* **Integrate SafeSearch on Inputs:**

  * Use the Google Cloud Vision API to check each original image for explicit content before sending it to generation. The Vision client library can be used to call SafeSearch Detection on the uploaded image file.
  * When a `stylize_image` request comes in, after storing the original to GCS (or before, if we prefer to scan pre-upload via memory), call the Vision API on that image. Check the SafeSearchAnnotation results: categories like *adult*, *violence*, *racy*, etc., with likelihood ratings.
  * Define a policy for rejection. For MVP, **if any of adult or violence or racy content is detected as LIKELY or VERY\_LIKELY**, we refuse to process the image. (We can be lenient on “medical” or “spoof” categories if they are not relevant.) This will prevent generating stylized versions of potentially disallowed content.
  * If the image is flagged, return an HTTP 400 or 403 error to the client with a message like "Image content not allowed by safety policy." Do **not** call the OpenAI API in this case (saving cost). Also, consider deleting the uploaded original from GCS to avoid storing unsafe content (or move it to a secure location for moderation review if needed, but for MVP, deletion is fine).

* **(Optional) SafeSearch on Outputs:**

  * DALL·E 3 itself has content moderation, but to be extra safe, we can also run SafeSearch on the generated image before returning it. This ensures that if the output unintentionally contains explicit elements, we catch it.
  * Implement a second SafeSearch scan on the generated variant. If it comes out with high likelihood of explicit content, do not return that image to the user. Instead, you could return an error "Stylized image deemed unsafe and was discarded." (This scenario should be rare if input was fine, but style prompts might conceivably add disturbing elements.)
  * In case of a flag, you might not store the unsafe variant or you store it and tag it. For MVP, simplest is to not store or to delete it, and just raise an error.

* **Test SafeSearch:**

  * Use a couple of test images known to trigger SafeSearch (e.g., a random explicit image or one with violence from a test dataset, or even an obviously inappropriate one if allowed). Ensure the service correctly identifies and blocks it. Also test a normal image to ensure it passes through.
  * Log the SafeSearch decisions (e.g. “Blocked image due to violence: VERY\_LIKELY”) for audit.

* **Milestone – Safety Checks:**
  **Criteria:** The system enforces content safety rules. If a user tries to stylize a disallowed image, the request is rejected with an appropriate message and no OpenAI call is made. This can be verified by the human engineer with test inputs that should be blocked (for example, an image with adult content results in a 400 error, whereas a benign image still works). The code implementing this should be reviewed to ensure it uses Vision API correctly and handles the various categories properly (e.g., not overly blocking harmless images). SafeSearch filtering is considered done when it reliably filters obvious adult/violent content before stylization.

## 5. Caching with Redis (Memorystore)

* **Rationale for Caching:** The DALL·E API calls are the most expensive and time-consuming part of the pipeline. We will cache recent results to avoid duplicate work. For example, if the same user sends the exact same image with the same style twice, we should return the already generated variant the second time (fast and free). Caching also helps if multiple users accidentally stylize the same popular image/style (though that’s less likely unless a demo image).

* **Caching Key Design:**

  * Define a strategy to uniquely identify a request for caching. A good key is a hash of the image content plus the style ID. Compute an **image hash** (e.g. SHA-256 or MD5) of the original image file bytes. Combine it with the style ID to form the cache key, e.g. `cache_key = SHA256(image_bytes) + ":" + style_id`.
  * We must store mapping from this key to the generated output. The output could be identified by the GCS path of the stylized image (which is effectively permanent storage). So the cache entry could be the GCS URL (or the object name).
  * Use Redis (via the Memorystore endpoint) to store this mapping. When a request comes in: compute key, do a Redis GET. If found, we have a cache hit – we can skip calling OpenAI and directly use that result. If not found, it’s a cache miss – proceed to call OpenAI and then store the result.

* **Implementing Cache Check:**

  * After receiving an image upload and style ID, compute the hash of the image (be mindful of memory – stream the file to hasher to handle large files).
  * Connect to Redis (the Redis endpoint/port from config). Use a Redis client library (e.g. `redis-py` for Python). The connection should be configured to use the VPC connector (which we set up) – in Cloud Run, the environment variable like `REDIS_HOST` and `REDIS_PORT` will point to the internal IP of the Redis instance.
  * Attempt to GET the key. If present:

    * Parse the stored value (e.g. GCS path). Verify that object exists in GCS (to avoid stale pointer, though if we never delete, it should exist).
    * Directly return a response pointing to that stored image (no OpenAI call). We should still log that we served from cache (for analytics).
  * If not present (cache miss): continue the normal flow (SafeSearch -> prompt -> OpenAI -> store image). Once the new stylized image is in GCS, do a Redis SET for the key to the value (with an appropriate TTL).

    * Set a TTL (time-to-live) for the cache entries, perhaps a day or week. We don’t want unbounded growth of the cache if many unique images come in. A TTL of 24 hours or 7 days is reasonable, as users are unlikely to repeat after a long time.
    * Alternatively, since we store variants in GCS permanently, the cache just prevents recomputation. If storage cost is not an issue, we could keep cache entries longer. For MVP, a shorter TTL (like 1 day) is fine to balance new content vs. repeated tests.

* **Considerations:**

  * Ensure thread-safety if multiple requests for the same new image come in simultaneously. Two instances might miss the cache at the same time. We might accept that race (both generate and last one wins in cache) for MVP, or implement a locking mechanism in Redis (advanced). Probably not needed initially due to low traffic assumption.
  * The cache is global across users. This means if different users upload identical images (or one user repeats), they get the same stylized result from cache. This is usually fine (the image content dictates output). There’s a minor privacy consideration that one user might unknowingly get an image generated from another user’s input if they had the same exact image. This scenario is rare and acceptable for MVP; we can document it as a known behavior.

* **Milestone – Caching Operational:**
  **Criteria:** Repeated stylization requests are served faster and without calling OpenAI again. To test, take an image and a style, stylize it once (note the time or logs showing an OpenAI API call), then stylize the same image/style again. The second time, confirm via logs that no OpenAI request was made and the result was returned from cache (and the response image is the same). The human engineer will verify that Redis is being used (perhaps by directly querying the Redis instance for the key or checking metrics) and that cache entries expire as configured. This feature is done when cache hits successfully short-circuit the generation and the service still returns correct data.

## 6. Cost Guardrails (Daily Caps & Per-User Quotas)

* **Define Quota Policy:**

  * Establish a daily global cap on how many stylizations or how much cost the service will allow. For example, **global daily cap**: 100 image generations per day (or a dollar equivalent, e.g. \$2/day if each image \~\$0.02). This prevents runaway costs in case of abuse.
  * Establish a **per-user daily quota** as well, say 10 images per user per day for free usage. This ensures one user cannot exhaust the entire day’s budget. (These numbers can be adjusted; for MVP we just need some reasonable limits to demonstrate the mechanism.)

* **Implement Global Counter:**

  * Decide where to store usage counts. Firestore is a good choice for persistent, multi-instance safe counting. We can use a simple document in Firestore like `usage/dailyTotals` with a field for the current date and count of images generated today. Alternatively, use Redis for quick incrementing and perhaps back it by Firestore for persistence at day boundary.
  * MVP approach: use Firestore transactions or the atomic increment feature. For each stylization request that is about to be processed, do a Firestore transaction: increment a counter in a doc for the current date. If the incremented value exceeds the cap, abort (roll back) and indicate quota exceeded.
  * We can key by date (e.g. document with key `2025-05-04` and a field `count`). Or a single doc with multiple date fields. Simpler: one doc with a field `count` and a field `date`. Each day, if the stored date != today’s date, reset the count to 0 and update date.
  * This check should occur **before calling OpenAI** (to avoid cost if over quota). Also, it should happen after a cache miss is confirmed (if it was a cache hit, we might decide not to count it towards the OpenAI quota since it didn’t incur cost – but it did use the service’s resources. We can choose to count cache hits separately or not at all for cost budgets. For cost guardrail, focus on actual API calls).

* **Implement Per-User Counter:**

  * Similar approach, but maintain a counter per user. This could be a Firestore document per user per day, e.g. collection `usage/{userId}` with fields for date and count, or a subcollection by date. If we have authenticated user IDs or API keys, use that. If not (public API), we might use the client IP address as a crude identifier for quota (not perfect, but something).
  * On each request, after global check, perform user-specific check. For user X, increment their count for today. If it exceeds the per-user cap, rollback and return an error "User quota exceeded, try tomorrow."
  * If using Firestore, these increments should ideally be in a transaction to avoid race conditions if multiple requests from same user at once. Firestore supports transaction or batch writes for increments. If using Redis, we could use `INCR` which is atomic, but Firestore persistence is valuable for daily resets. (We could combine: use Redis for quick count and sync to Firestore daily. But MVP simpler: just use Firestore, given likely low QPS.)

* **Quotas and Response:**

  * If a quota is exceeded, return an HTTP 429 Too Many Requests or 403 error code. Make the message clear (e.g. "Daily quota exceeded, please try again later.").
  * Also, once a quota is hit, we might short-circuit further calls. One idea: if global quota is hit, perhaps put the server in a “disabled” mode for the rest of the day. But given multiple instances, better to just have each request check and fail accordingly.
  * We should reset counts daily. This can be done by comparing date as mentioned, or simply rely on a new doc each day. Possibly implement a scheduled job or just handle on first request of a new day, the first request sees date mismatch and resets counts.

* **Testing Quota Behavior:**

  * Simulate the quota easily by temporarily lowering the limits in a test environment (e.g. set per-user cap to 1). Make two requests as the same user – the second should be rejected. Similarly, set a small global cap and ensure that after N requests, the (N+1)th gets blocked.
  * Ensure that the counting does not off-by-one or double-count on retries. If an OpenAI call fails (e.g. API error), decide whether to count it or not. Probably count it if the request was made to OpenAI (since cost incurred), or not count if we short-circuited before call.
  * The human reviewer will look at how the Firestore writes are done (e.g. using transactions to prevent race conditions and ensure correctness).

* **Milestone – Cost Guardrails Active:**
  **Criteria:** The service enforces daily usage limits globally and per user. After exceeding the set number of requests, further calls are blocked. This is verified by testing with a dummy small quota. Also, the implementation should not overly degrade performance – the Firestore check is quick and doesn’t cause a big latency (Firestore is pretty fast for single doc access). This feature is complete when the team is confident that runaway usage will be prevented in production (thus keeping costs in check). Documentation should note what the limits are and how to adjust them if needed.

## 7. Usage Analytics and Monitoring

* **Basic Logging & Monitoring:**

  * Leverage Cloud Run’s integration with Cloud Logging: ensure all important events (request received, cache hit/miss, OpenAI call made, image stored, errors, etc.) are logged with appropriate severity. This provides a baseline audit trail.
  * Enable Cloud Run metrics in Cloud Monitoring (requests count, latency, memory usage, etc., are auto-collected). Set up an alert for unusually high error rate or if traffic spikes beyond expectation (could hint at abuse).

* **Custom Analytics Data:**

  * Determine what usage stats are valuable. Likely: total number of stylizations over time, breakdown by style (which styles are popular), breakdown by user, and success vs failure rate.
  * We can use **Google Analytics** if this were a front-end app, but since this is a server, a better approach is to record events in a database or send to an analytics pipeline. For MVP, a simple method is to use Firestore or Pub/Sub to log events:

    * For example, create a Firestore collection `analytics` and add a document for each request (with fields: timestamp, user, style, success/failure, was\_cached). This is straightforward but could grow large. Since MVP traffic is low, this is acceptable.
    * Alternatively, publish a message to the `stylize-analytics` Pub/Sub topic for each completed request (including needed info). Later, one could connect this to BigQuery via Dataflow or a Cloud Function to aggregate statistics. Doing the Pub/Sub route decouples logging from processing (non-blocking for our service). For MVP we might implement the publish (which is quick) and not yet build the subscriber, just store the messages for future use.
  * In either case, ensure that analytics logging happens **after** the main work (so it doesn’t slow the user response). It can even be done asynchronously (in a background thread or just after sending response, since Cloud Run will wait for request handler to finish before terminating).

* **Analytics Examples:**

  * Track per-style usage: we can maintain counters in memory or Firestore to increment each time a style is used. E.g., a Firestore doc `analytics/styles/{styleId}` with a count. This helps see which styles are most popular.
  * Track errors: count how many requests were blocked by SafeSearch or by quotas. This can be in analytics logs as well (so we know if users are hitting limits often or trying disallowed content often).
  * If using Firestore for analytics, consider writing in batches or periodically if high frequency (but likely fine for MVP). If using Pub/Sub, just one publish per request.

* **Dashboard and Inspection:**

  * It’s useful to be able to view the analytics easily. For MVP, manual querying of Firestore or logs might suffice. But consider setting up a simple **Metrics Dashboard**: e.g., use Cloud Monitoring custom metrics. We could increment a custom metric for "Stylizations count" and "Cache hit count" using OpenCensus/Cloud client. This might be overkill; instead, use the built-in Cloud Run request count for total, and derive cache hit rate by subtracting OpenAI call count (OpenAI calls could be tracked via a metric or log counter).
  * At minimum, document how to retrieve the usage stats (maybe a script to query Firestore or instructions to use GCP’s log explorer to filter logs by labels).

* **Milestone – Analytics & Monitoring:**
  **Criteria:** The team can observe how the service is being used in real-time or via logs. For example, we should be able to answer “How many images were stylized today?” and “What percentage of requests were served from cache?” using our collected data. The human engineer verifies that analytics events are being recorded (by checking Firestore or receiving Pub/Sub messages) and that the data is coherent. This milestone is reached when basic usage analytics are flowing and documented, though a full dashboard is not required for MVP.

## 8. MCP FastMCP Protocol Support

* **Understand MCP Role:** The Model Context Protocol (MCP) allows AI agent systems (like VS Code Copilot or other LLM tools) to interact with external tools/servers in a standardized way. In our case, we want the Stylize server to be accessible as an MCP **tool** called, say, `"stylize_image"`. This will let an AI agent request image stylization via MCP.

* **Implement MCP Endpoint:**

  * Using the FastMCP library integrated earlier, formally define the `stylize_image` function as an MCP tool. For example, in Python:

    ```python
    @mcp.tool()
    def stylize_image_tool(image: bytes, style: str) -> str:
        """Stylize an image with the given style. Returns URL of stylized image."""
        # (This will call the same logic as our HTTP endpoint internally)
    ```

    Adjust the signature as needed; MCP tools can accept arguments. We might define it to accept a base64 string or image bytes and a style identifier. The tool’s docstring serves as description for the MCP client.
  * Ensure the MCP server is running. FastMCP can run an SSE (Server-Sent Events) or HTTP for MCP. We might configure it to run on a specific port or route. If using FastMCP standalone, it may spin up its own server loop – we need to ensure that doesn’t conflict with the FastAPI/Express server. One approach is to unify them: possibly use FastMCP’s ability to generate a FastAPI app or mount an endpoint for MCP. (FastMCP 2.0 mentions FastAPI integration.) If integration is complex, as a fallback, run the MCP server on a separate thread on a different port within the same container.
  * The MCP server should expose the **SSE endpoint** (for receiving tool invocation requests) at e.g. `/sse` or `/mcp`. Also, it might expose a metadata route (like an OpenAPI or JSON description of tools). Verify in FastMCP docs how clients discover the tools.

* **Bridge MCP Tool to Core Logic:**

  * Inside the MCP tool function, we don’t want to duplicate all logic. Instead, have it call the same code path as the HTTP request handler. We can refactor the core stylization logic (SafeSearch, caching, OpenAI call, etc.) into a internal function or service class that both the HTTP route and the MCP tool function call. This ensures consistency.
  * The MCP tool should take the input image (likely as bytes or base64) and style, and then call that internal function. It will then return the result (e.g. the URL or maybe directly the image bytes if MCP expects direct output).
  * Since MCP is designed for LLM consumption, returning a URL string is probably acceptable (the LLM or agent might follow up to fetch it). Alternatively, we could return a short text response like "Image stylized and stored at <URL>" to the agent, but the URL itself is crucial.

* **MCP Protocol Compliance:**

  * Confirm that the MCP server advertises the tool correctly. There might be a manifest or handshake when a client connects. For example, ensure the tool’s name and docstring appears so that an agent knows how to call it (the docstring “Stylize an image with the given style…” should be descriptive).
  * Test with an MCP client. Perhaps use a simple MCP client or the FastMCP client to call the tool locally. E.g., using the `fastmcp` CLI or a small Python snippet to connect to `localhost:port/sse` and invoke the tool with test data. This will validate that our server can handle MCP requests as expected.

* **FastMCP and Authentication:**

  * MCP connections may be local or from tools like Copilot. If we need to secure it (to not allow arbitrary internet use), we might restrict it via network (since Cloud Run can be set to only allow specific client or run privately). For MVP, no authentication on MCP beyond what’s inherent (if the server is not publicly accessible or behind an AI agent environment).

* **Milestone – MCP Support:**
  **Criteria:** The Stylize service is accessible through the MCP protocol. This means an AI agent (like a Copilot plugin or an MCP client script) can invoke the `stylize_image` tool and receive a result. The human engineer will verify this by running a test MCP client: sending an image and style through MCP and ensuring the response is correct. Also, ensure this doesn’t break the REST API (both interfaces should work in parallel). When the MCP tool is functional and documented (in the code docstring or a separate `OPENAPI.md` for MCP), we consider MCP integration complete.

## 9. Final Testing and QA

* **Functional Testing:**

  * Create a suite of functional tests (could be simple scripts or manual steps) to verify each feature end-to-end:

    1. **Stylize success path:** Upload a known image, use a style, get an output image. Visually check the output (it should reflect the style). Also verify the response JSON and that the image is indeed stored in GCS.
    2. **SafeSearch block:** Try an image that should be blocked. Confirm the API returns an error and nothing is generated/stored.
    3. **Quota exceeded:** If possible, simulate many requests (or temporarily set low quotas) to trigger the quota exceeded error. Confirm correct error response.
    4. **Cache hit:** Stylize the same image/style twice and ensure second response is fast and logged as cache hit.
    5. **Invalid inputs:** Try calling with a non-image file or an unsupported style ID. The API should handle gracefully with clear errors (no crash).
    6. **MCP invocation:** Use an MCP client to do a stylization and check that it goes through (this also tests that the internal refactoring didn’t break anything).
  * Automate what we can: possibly use a testing framework to simulate HTTP calls (e.g. pytest with HTTPX or Postman scripts). The AI agent can write these tests to run locally or in CI. However, note that testing the OpenAI call will actually spend credits – for automated tests, it might be wise to mock the OpenAI API. For MVP manual testing of OpenAI integration is fine, but for continuous integration, we might skip hitting OpenAI or use a dummy stub if possible.

* **Performance & Load Testing (Basic):**

  * Not a huge focus for MVP, but do a quick check: how long does a single request take on average? (Should be mostly the OpenAI latency, maybe a few seconds). Test concurrent requests by sending a few in parallel (Cloud Run should autoscale or handle concurrency if we set >1 concurrency). Ensure no obvious bottlenecks like excessive memory or slow hashing (we can hash \~5MB in a fraction of a second, so that’s fine).
  * Monitor Cloud Run’s memory usage during these tests. A DALL·E image data might be a few hundred KB. With caching and processing, a 512MB container should suffice. Ensure the Cloud Run service’s memory limit (set in Terraform) is adequate (maybe 1GiB to be safe if using Vision API etc., although likely 512MiB is enough). Also ensure we didn’t accidentally bloat memory (e.g. don’t load huge style catalog into memory beyond necessity).

* **Security Review:**

  * Ensure that the service is not exposing anything sensitive: the OpenAI API key is in Secret Manager and not returned anywhere. GCS URLs are signed (so not open to the world indefinitely). The service account keys are not embedded.
  * Check that all external calls (OpenAI, Vision) are properly authenticated and using HTTPS.
  * If the service is to be publicly accessible, consider enabling authentication on Cloud Run (maybe require an API key header for any request to deter random usage). For MVP, it might be open but with quotas it’s somewhat protected. This is noted as a risk if someone finds the endpoint – but quotas mitigate damage.

* **Documentation & Examples:**

  * Write or update the documentation (README or a separate docs file) with usage examples. Include how to call the HTTP API (curl example) and how to use the MCP tool (if an agent developer wants to integrate).
  * Document the style catalog (list the style options available in MVP).
  * Document the safety and quota limits in place for transparency to users (e.g. “Note: explicit images are not allowed and will be rejected. Each user is limited to 10 stylizations per day in this demo.”).
  * Include any known limitations (for instance, “the stylized image may not preserve the exact input content if using text-only generation” as discussed). This sets correct expectations and helps the human engineer and any stakeholders understand the MVP’s boundaries.

* **Milestone – MVP Complete (Ready for Launch):**
  **Criteria:** All features outlined in the vision document are implemented and verified: the `stylize_image` endpoint works with style templates, images are stored in GCS, OpenAI integration produces outputs, SafeSearch filtering and cost controls are enforced, caching improves performance, usage is tracked, and the MCP interface is available. The CI/CD pipeline is configured such that a push of new code triggers a deployment to Cloud Run (tested with a dummy update to ensure everything integrates). The human engineer does a final review of the entire system – reading through code, infra config, and documentation – ensuring quality and maintainability. Any outstanding issues or bugs discovered in testing are resolved. When the service runs stable and meets the defined acceptance tests, we declare the MVP “done.”

## 10. Potential Pitfalls and Mitigations

* **OpenAI API Reliability and Cost:** The DALL·E 3 API might be slow or have rate limits. If the AI agent fires too many requests quickly, we could hit OpenAI’s limits or run up cost. **Mitigation:** Use caching and quotas (as implemented) to curb overuse. Also implement exponential backoff retry for the API call in case of transient failures. Log any API errors for later debugging. Possibly configure a budget alert on the OpenAI API usage (outside of code) so we get notified if costs spike.

* **Image Handling Performance:** Handling large image files in memory could strain the container. **Mitigation:** Stream uploads to GCS (i.e., don’t load the entire file in RAM if possible). We can read in chunks and hash simultaneously, then upload that stream to GCS. Cloud Run has limited /tmp space, but small files can be handled there if needed for Vision API input. Also limit upload size to avoid out-of-memory scenarios.

* **Cloud Vision False Positives/Negatives:** The SafeSearch might occasionally flag innocuous images or miss something. This could annoy users if their image is wrongly blocked. **Mitigation:** For MVP, our thresholds are conservative (only block if likely/very likely). We can fine-tune if needed. Log the scores for future analysis. In case of false block, the human engineer can manually allow or adjust settings in future.

* **Concurrency and Data Consistency:** With Cloud Run scaling, two instances might simultaneously update Firestore usage counts or check Redis cache. There’s a risk of race conditions (e.g., two calls generating the same image in parallel, or two increments overshooting a quota by both seeing previous count). **Mitigation:** Using transactions in Firestore for counters will serialize those updates properly. For caching, a rare race could generate two images – which is not catastrophic, just some wasted cost. If needed, we could lock by cache key in Redis (e.g., set a temporary "lock" entry while generation in progress), but for MVP this complexity might be overkill. Document this possibility as something to monitor.

* **Terraform and Config Drift:** Managing infrastructure via Terraform means any manual changes in GCP could conflict. Also deploying new container images via CI vs Terraform image reference needs care. **Mitigation:** For MVP, once infra is created, we might treat the Cloud Run service updates as outside Terraform (CI directly deploys). We should then add `lifecycle { ignore_changes = [image] }` on the Terraform Cloud Run resource, so Terraform doesn’t override the updated image on next apply. The human engineer should be aware of this to avoid confusion. All secrets and config should remain in Terraform to avoid manual config that could be lost.

* **MCP Complexity:** Integrating FastMCP with our web server might introduce complexity or edge cases (like thread management, SSE endpoints). **Mitigation:** If FastMCP integration proves unstable, we could decouple it: e.g., run a separate lightweight MCP server that calls our REST API internally. That would isolate any issues. However, for MVP we aim to integrate directly. Thorough testing with the MCP client will reveal issues. Keep the MCP implementation simple (one tool) to reduce risk.

* **Secrets and Keys Management:** Losing the OpenAI key or exposing it is a security risk. **Mitigation:** We never log the key or include it in client responses. Using Secret Manager and not storing the key in the container image or repo ensures safety. Also rotate the key if needed. Similarly, ensure the GCP service account keys are not exposed (we use IAM roles directly).

* **Third-Party Dependencies:** Relying on OpenAI, Google APIs, and FastMCP means if any of those services have an outage or bug, our server might fail. **Mitigation:** Have fallbacks if possible: e.g., if OpenAI is down or returns error, return a graceful error to user ("Stylization service is currently unavailable, please try later"). The AI agent implementer should code defensively around external API calls. Also pin dependency versions in requirements to prevent unexpected changes.

By anticipating these pitfalls, the AI agent and human engineer can keep a close watch during implementation and testing. With this plan and careful execution, we aim to successfully deliver the Stylize MCP Server MVP with all the requested functionality.

## 10. Key Post-MVP Considerations from Vision

Beyond the defined MVP scope, the following item from the vision document is noted as an important post-MVP enhancement:

*   **Data Privacy and Deletion:** Full implementation of data lifecycle management as per GDPR & CCPA guidelines, including automated deletion of original images after 30 days and providing a user-initiated purge API.
