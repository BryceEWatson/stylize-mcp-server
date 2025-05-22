# Infrastructure Costs and MVP Development Decisions for Stylize MCP Server

## Document Purpose

This document outlines the Google Cloud Platform (GCP) infrastructure components for the Stylize MCP Server MVP, the estimated costs associated with them, and the key decisions made to manage these costs during the active development phase. The goal is to maintain a functional development environment while minimizing unnecessary expenditure.

## Guiding Principles for Cost Management (MVP Development Phase)

1.  **Leverage Free Tiers:** Maximize the use of GCP's "always free" tiers for services like Cloud Run, Cloud Storage, Pub/Sub, and Secret Manager.
2.  **Minimize "Always-On" Services:** Services that incur costs simply by being provisioned (regardless of usage) are prime candidates for temporary removal or significant downscaling during periods where their specific functionality is not being actively developed or tested.
3.  **Develop Locally, Test Specifics in Cloud:** Encourage local development using Dockerized versions of stateful services (like Redis). Cloud resources for these services should be provisioned only when cloud-specific integration or performance testing is required.
4.  **`terraform destroy` for Inactivity:** For extended periods of non-development, destroying the entire development infrastructure via Terraform is the most effective way to eliminate all costs.
5.  **Billing Alerts:** GCP Billing Alerts are configured for the project to monitor spend and prevent surprises.

## Core Infrastructure Components (Always Provisioned for MVP Dev)

These components form the baseline for our MVP development environment and are designed to have minimal to zero idle cost, primarily utilizing free tiers.

| Service                      | GCP Resource(s)                                                                 | Estimated Idle Monthly Cost (us-central1) | Rationale / Notes                                                                                                                                                                                                                         |
| :--------------------------- | :------------------------------------------------------------------------------ | :---------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Compute Engine**           | `google_cloud_run_v2_service`                                                   | ~$0.00                                    | Cloud Run has a generous free tier for requests, vCPU-seconds, and GiB-seconds. Configured to scale to 0 instances when idle. Costs will only accrue with actual usage beyond the free tier. Placeholder "hello" image used initially.         |
| **Storage**                  | `google_storage_bucket` (x2: originals, variants)                               | ~$0.00                                    | Cloud Storage has a free tier (5 GB-months Standard Storage, plus free operations). Initial storage will be negligible. Lifecycle rules (30/60 days) are in place for eventual cleanup; operations for these are infrequent.                 |
| **Messaging**                | `google_pubsub_topic` (`stylize-analytics`)                                     | ~$0.00                                    | Pub/Sub has a free tier for message throughput (10 GiB/month). The topic itself incurs no cost when idle with no messages.                                                                                                        |
| **Security**                 | `google_secret_manager_secret` & `_version` (`OPENAI_API_KEY`)                  | ~$0.00                                    | Secret Manager has a free tier (6 active secret versions, 10,000 access ops/month). Our usage (1 secret, 1 version, infrequent access) fits well within this. Placeholder value used in Terraform; actual key set manually.        |
| **Identity & Access**      | `google_service_account` (`stylize-mcp-sa`), `google_project_iam_member` (x5) | $0.00                                     | Service accounts and IAM bindings do not have direct costs. Essential for security and least privilege.                                                                                                                                 |
| **API Management**           | `google_project_service` (x9 APIs)                                              | $0.00                                     | Enabling APIs does not incur costs; usage of specific APIs will. All necessary APIs for Cloud Run, GCS, Firestore, Vision, etc., are enabled.                                                                                         |
| **Networking (Basic VPC)** | `google_compute_network` (`stylize-mcp-vpc`), `google_compute_subnetwork`       | $0.00                                     | The VPC network and subnet resources themselves do not have direct costs. They are kept as foundational elements for potential future re-integration of VPC-connected services.                                                        |
| **CI/CD**                    | Cloud Build (Triggers, `cloudbuild.yaml`)                                       | Variable (Build Minutes)                  | Cloud Build has a daily free tier for build minutes (120 min/day). Costs accrue only if this is exceeded. This is not an "idle infrastructure" cost but a development activity cost.                                             |

## Temporarily Removed/Deferred Services for Cost Optimization (MVP Dev)

To significantly reduce immediate "always-on" idle costs during development, the following services, initially planned, have been **commented out** of the Terraform configuration. They can be re-introduced by uncommenting them and running `terraform apply` when their specific functionality needs to be developed or tested in the cloud environment.

| Service                           | GCP Resource(s)                                                                                   | Original Estimated Idle Monthly Cost (us-central1) | Reason for Temporary Removal / Impact                                                                                                                                                                                                                                                                                          |
| :-------------------------------- | :------------------------------------------------------------------------------------------------ | :------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Caching**                       | `google_redis_instance` (`stylize-mcp-redis`)                                                     | ~$35.77                                            | Memorystore for Redis incurs costs based on provisioned capacity and uptime. Removed to save significant costs. **Impact:** Server-side caching via Redis is disabled in the deployed dev environment. Caching logic should be developed/tested locally (e.g., with Dockerized Redis).                                                |
| **VPC Egress/Private Access**   | `google_vpc_access_connector` (`stylize-mcp-vpc-connector`)                                       | ~$15.00                                            | The Serverless VPC Access Connector incurs costs for its underlying VM instances. Primarily needed for Cloud Run to access Redis or other VPC-internal resources. **Impact:** Cloud Run cannot access resources within the VPC privately.                                                                                         |
| **Static Egress IP / NAT**      | `google_compute_router_nat` (`stylize-mcp-nat`), `google_compute_router` (`stylize-mcp-router`) | ~$35.04                                            | Cloud NAT and its router incur costs for gateway uptime and IP addresses. Needed for a static egress IP or to allow VPC-internal resources (connected via VPC Connector) to egress. **Impact:** Cloud Run will egress to the public internet using Google's shared IP pool. This is acceptable for calling the OpenAI API for MVP. |

**Total Estimated Immediate Monthly Idle Cost (Optimized MVP Dev Setup): ~ $0.00 - $5.00**
*(This assumes usage stays within free tiers. Small costs might accrue from minimal Cloud Storage operations or if Cloud Run has very brief activity beyond the absolute minimum. Any Cloud Build usage beyond the free tier is separate).*

**Total Estimated Monthly Savings from Optimization: ~ $85.81**

## Decision Rationale for Optimized Setup

*   **Focus on Core Application Logic:** The primary goal during early MVP development is to build and test the core image stylization functionality, API endpoints, and basic GCP integrations (GCS, Secret Manager). The removed services (Redis caching, specific VPC networking for Redis) are considered secondary features for initial development sprints.
*   **Cost vs. Benefit during Development:** The ongoing cost of Redis, VPC Connector, and NAT for a development environment that might not be in constant use was deemed too high relative to their immediate necessity for core feature development.
*   **Local Development Alternatives:** Features like caching can be effectively developed and unit-tested locally using tools like Docker Compose to run a local Redis instance.
*   **Phased Re-introduction:** When development focus shifts to implementing caching, or if a static egress IP becomes a hard requirement, these services can be uncommented from Terraform and re-provisioned. This allows for targeted spending only when needed.
*   **Application Code Adaptability:** The application code (in `app/`) is expected to be written to gracefully handle the absence of Redis configuration (e.g., by disabling caching features or using a no-op cache client if Redis environment variables are not set).

## Future Considerations (Post-MVP or for Staging/Production)

*   **Re-introducing Redis:** For performance and to reduce external API calls, Redis will be essential for caching.
*   **Re-introducing VPC Connector & NAT:** If Redis is re-introduced, the VPC Connector will be needed for Cloud Run to access it. Cloud NAT might be re-introduced if a static egress IP is required for integrations or security whitelisting.
*   **Dedicated Test Environment:** For more comprehensive integration testing, a separate staging/test environment that mirrors production more closely (including all services) will be necessary. Costs for such an environment will be higher.
*   **Cost Optimization for Production:** This includes right-sizing instances, exploring committed use discounts, and potentially using more cost-effective alternatives if applicable at scale.

## Review and Updates

This document should be reviewed periodically, especially when:
*   New GCP services are considered for the project.
*   The project moves from development to staging or production phases.
*   Significant changes in GCP pricing occur.
