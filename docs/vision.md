# Stylize MCP Server – Project Vision Document

## 1. Executive Summary
Stylize is a Model‑Context‑Protocol (MCP) server that lets any MCP‑aware agent transform a user‑supplied image into multiple, high‑quality, style‑specific variants in a single call. The service orchestrates premium generative‑image APIs (OpenAI DALL·E 3 and Vertex AI Imagen) while adding value through a curated style bank, template‑driven prompt engineering, content‑safety filtering, caching, usage‑based cost guards, and Google Cloud‑native scalability. With over 1.6 million MCP server downloads tracked across ~4,000 servers (PulseMCP, 2025), and image generation servers among the most popular categories, Stylize is positioned to capture significant market share in this growing ecosystem.

## 2. Problem Statement & Opportunity
* **Today**: Developers must chain raw image‑generation APIs, hand‑craft prompts, manage costs, and enforce safety.
* **Gap**: No turnkey MCP server bundles these concerns into one frictionless tool, especially for practical UI elements, icons, and logos that developers specifically request.
* **Opportunity**: Become the default "style orchestrator" in the Cline, Windsurf, and Copilot MCP marketplaces—owning the long tail of product‑design, marketing, and creative agents. Particularly valuable as MCP-aware platforms like Windsurf now support "drag & drop images" and design tool integration.
* **Market Validation**: Multiple community-built image generators have gained significant traction, with one Stability AI-powered generator showing over 22,000 uses and 166 upvotes on PulseMCP, and a DALL-E generator with 17,000+ uses (PulseMCP, 2025).

## 3. Target Users & Personas
| Persona | Needs | Pain Points |
|---|---|---|
| **Indie dev / designer** | Fast image variants for mock‑ups, icons, logos | Limited GPU/credits, prompt fatigue, needs specific UI elements |
| **Marketing automation agent** | Bulk on‑brand asset generation | Brand consistency, throughput |
| **Enterprise creative team** | Governed, auditable generation pipeline | Compliance, spend tracking |
| **Code-to-Design bridge user** | Convert wireframes to styled UI mockups | Integration with IDE workflow, consistency across outputs |

## 4. Value Proposition
* **One‑call stylization** – `stylize_image` accepts an image URL + style names; returns signed URLs for each variant.
* **Curated style catalog** – 100+ ready‑to‑use looks (Vaporwave, Zen‑Ink, Mid‑Century Modern, etc.) with specialized collections for UI elements, icons, and logos.
* **Project context analysis** – Intelligently analyze project documentation, code, and branding to automatically suggest relevant icon and logo styles aligned with the project's domain and aesthetic.
* **Cost guard‑rails** – Daily spend caps, per‑user quotas, and cache hits on duplicate requests to control API costs which constitute ~80% of operational expenses.
* **Enterprise‑grade safety** – NSFW / violent / political filters and audit logs.
* **Google Cloud‑native** – Auto‑scales via Cloud Run, monitored with Cloud Logging & Cloud Trace.
* **IDE Integration** – Seamless integration with Windsurf, Cline, and Copilot Studio, leveraging their evolving image capabilities.

## 5. Differentiation vs Existing MCP Servers
| Capability | Stylize | DALL‑E MCP | SD‑XL MCP |
|---|---|---|---|
| Multi‑engine orchestration | ✅ | ❌ | ❌ |
| Template prompt bank | ✅ | ❌ | ⚠️ basic |
| Caching & cost caps | ✅ | ❌ | ❌ |
| Safety pipeline | ✅ | ⚠️ minimal | ⚠️ |
| Google Cloud deployment | ✅ | n/a | n/a |
| UI/Icon-specific styles | ✅ | ❌ | ❌ |
| IDE-native integration | ✅ | ⚠️ limited | ❌ |

## 6. High‑Level Architecture (Google Cloud‑First)
```
Client (MCP Agent)
   │  WebSocket JSON‑RPC (FastMCP)
   ▼
Cloud Run  ───► Firestore (metadata)
  │           │
  │           └─ Memorystore (Redis) – style & hash cache
  │
  ├─ Pub/Sub queue  ─► Cloud Functions (worker pool)
  │                         ├─ Vertex AI Imagen API
  │                         └─ OpenAI DALL·E 3 API via private egress
  │
  ├─ Cloud Vision SafeSearch API (content filter)
  └─ Cloud Storage bucket (originals + variants, signed URLs)
```
* All HTTP egress exits through Cloud NAT to whitelist external APIs.
* Identity & Access via IAM service accounts; secrets in Secret Manager.
* CI/CD: Cloud Build triggers on GitHub pushes, deploys to Cloud Run and Functions.

## 7. Core Feature Set
1. **Stylize Image** (`stylize_image`) – MVP.
2. **List Styles** (`list_styles`) – returns style catalog.
3. **Add Custom Style** (`add_style`) – saves prompt template per user (premium tier).
4. **Batch Stylize** – accepts up to 50 images/500 variants async via Pub/Sub.
5. **Progress Events** – `notifications/progress` stream.
6. **Admin Dashboard** – Firebase Hosting single‑page app for quotas, logs, billing.
7. **Project Context Analysis** (`analyze_project`) – Analyzes project context to recommend styles.

## 7.5 Comprehensive Feature List

### Core API Features
| Feature | Description | Tier | MVP |
|---|---|---|:---:|
| **Image Stylization** | Transform input images into styled variants | All | ✅ |
| **Style Catalog** | Browse and select from pre-defined styles | All | ✅ |
| **Custom Styles** | Create and save custom style definitions | Pro, Enterprise | ❌ |
| **Batch Processing** | Process multiple images in one request | Pro, Enterprise | ❌ |
| **Progress Tracking** | Real-time updates on job status | All | ❌ |
| **Project Context Analysis** | Auto-suggest styles based on project context | Pro, Enterprise | ❌ |

### Style Categories
| Category | Description | Examples | Tier | MVP |
|---|---|---|---|:---:|
| **UI Elements** | Styles optimized for interface components | Material Design, Neumorphic, Glassmorphic | All | ✅ |
| **Icons & Logos** | Styles for brand assets and navigation | Minimal Flat, 3D Isometric, Neon Glow | All (limited) / Pro (full) | ✅ |
| **Illustrations** | Artistic styles for rich graphics | Watercolor, Line Art, Retro | Pro, Enterprise | ❌ |
| **Industry-Specific** | Styles tailored to specific sectors | Medical, Finance, Gaming | Pro, Enterprise | ❌ |
| **Brand Kits** | Style collections that maintain brand consistency | Custom enterprise packages | Enterprise | ❌ |

### Intelligence Features
| Feature | Description | Tier | MVP |
|---|---|---|:---:|
| **Project Analysis** | Scan project files to understand context | Pro, Enterprise | ❌ |
| **Style Recommendations** | AI-suggested styles based on project | All (basic) / Pro (advanced) | ❌ |
| **Asset Detection** | Identify existing assets to maintain consistency | Pro, Enterprise | ❌ |
| **Brand Pattern Recognition** | Detect and maintain brand style patterns | Enterprise | ❌ |
| **Domain-Specific Suggestions** | Tailored recommendations by industry | Pro, Enterprise | ❌ |

### Integration Features
| Feature | Description | Tier | MVP |
|---|---|---|:---:|
| **MCP Protocol Support** | Full FastMCP integration | All | ✅ |
| **IDE Plugins** | Direct integration with Windsurf, Cline, etc. | All | ❌ |
| **Design Tool Connectors** | Figma, Sketch integration | Pro, Enterprise | ❌ |
| **API Access** | Headless access for custom integrations | Pro, Enterprise | ❌ |
| **Custom Webhooks** | Event notifications to external systems | Enterprise | ❌ |

### Management Features
| Feature | Description | Tier | MVP |
|---|---|---|:---:|
| **Usage Analytics** | Track usage patterns and costs | All (basic) / Pro (detailed) | ✅ |
| **Team Management** | Multi-user accounts with permissions | Enterprise | ❌ |
| **Access Controls** | Role-based permissions and style access | Enterprise | ❌ |
| **Audit Logging** | Comprehensive activity tracking | Enterprise | ❌ |
| **Cost Management** | Budget controls and alerts | All (basic) / Pro, Enterprise (advanced) | ✅ |

### Infrastructure Features
| Feature | Description | Tier | MVP |
|---|---|---|:---:|
| **High Performance** | Optimized for speed and quality | All (standard) / Pro (priority) | ✅ |
| **Caching** | Intelligent result caching | All (limited) / Pro (enhanced) | ✅ |
| **Safety Filters** | Content moderation and safety checks | All | ✅ |
| **Redundancy** | Multi-engine fallback support | Pro, Enterprise | ❌ |
| **Custom Deployment** | Self-hosted or private cloud options | Enterprise | ❌ |

## 8. Non‑Functional Requirements
* **Latency**: < 6 s P95 for single‑style 1024×1024 variant.
* **Scale**: 500 concurrent stylizations without prep‑warm.
* **Availability**: 99.5 % monthly SLO.
* **Cost ceiling**: <$0.08 per 1k style calls (infra only, excl. model API fees).

## 9. Security & Compliance
* Signed URLs (7‑day TTL) prevent hotlink abuse.
* Content safety: Cloud Vision SafeSearch scores ≥ "Likely" in adult/violence → block.
* GDPR & CCPA: delete originals after 30 days; user‑initiated purge API.
* Audit logs in Cloud Logging; BigQuery sink retained 1 year.

## 10. Google Cloud Service Map
| Concern | Service | Notes |
|---|---|---|
| Compute (stateless) | Cloud Run | Containerised FastMCP server |
| Async workers | Cloud Functions + Pub/Sub | Burstable processing |
| Object storage | Cloud Storage | Standard + lifecycle rules |
| Cache | Memorystore (Redis) | 1 GB tier |
| Metadata DB | Firestore in Native mode | Per‑user usage + style defs |
| Secrets | Secret Manager | API keys, daily cap values |
| Monitoring | Cloud Logging, Error Reporting, Cloud Trace | Alerting via Cloud Monitoring |
| Networking | Cloud NAT + VPC Serverless | Static egress IP list |

## 11. Tech Stack & Tools
* **Lang/Runtime**: Python 3.11, FastAPI + FastMCP.
* **Libraries**: `aiohttp`, `pydantic`, `tortoise‑orm` (Firestore adapter), `redis‑async`.
* **DevOps**: Docker, Cloud Build, GitHub Actions, Terraform (infra‑as‑code).
* **Testing**: Pytest, Locust for load, Guardrails AI for output policy tests.

## 12. Roadmap & Milestones
| Phase | Deliverables |
|---|---|
| **Initial Prep** | Terraform baseline, repo scaffolding |
| **MVP** | `stylize_image`, GCS storage, DALL·E 3 API integration |
| **Enhancement** | Caching, Cloud Vision safety, style catalog |
| **GA Release** | Vertex AI Imagen integration, admin dashboard, billing hooks |
| **Future Expansion** | Batch API, custom styles, progress events, marketplace launch |

## 13. Monetization Strategy
Based on market research of comparable AI SaaS products (PulseMCP, 2025), Stylize will operate on a freemium model, with the following tiers:

* **Free**: Limited to 20 style calls per day (comparable to Playground AI's 50/day and more generous than ChatGPT's 2/day), with standard resolution outputs, watermarked results, and limited style selection.
* **Pro**: $19.99/month (aligned with industry benchmarks of $15-25/month), with 1,000 style calls per month, HD/4K resolution options, no watermarks, full style catalog access, and priority processing.
* **Enterprise**: Custom pricing for large teams and organizations, with dedicated support, customized solutions, and volume discounts.

Expected conversion rate from free to paid is 2-5% based on SaaS industry benchmarks, targeting 250-300 paying users to reach sustainability milestone of $5k MRR.

Revenue will be generated through subscription fees, with additional revenue streams from:
* **API fees**: Pass-through fees for external API calls (e.g. OpenAI, Vertex AI).
* **Custom style development**: Offer custom style development services for clients.
* **Partnerships**: Partner with design and marketing agencies to offer bundled solutions.
* **Referral program**: Free users who refer others receive additional credits, with bonus incentives when referred users upgrade to paid plans.

## 14. Team & Responsibilities
| Role | Headcount | Core Duties |
|---|---|---|
| Human Product Owner | 1 | Vision, roadmap, marketplace strategy |
| AI Agent (Engineering) | 1 | End-to-end implementation, infrastructure management, style curation, content safety monitoring, and comprehensive documentation maintenance. The agent will maintain detailed logs of all development activities, update technical documentation as the system evolves, and ensure all code is well-documented with comments and explanatory notes. |

## 15. Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| API cost spike | Med | High | Daily spend cap env var + alerts |
| Margin compression | High | High | Implement aggressive caching, explore bulk API discounts, consider self-hosted models for high-volume styles |
| NSFW false‑negatives | Low | Med | Ensemble safety (Vision + model-native filter), selective moderation to control costs |
| Marketplace churn | Med | Med | Multi‑platform launch (Cline + MCPMarket + BytePlus) |
| External API downtime | Low | Med | Multi‑engine fallback (DALL·E ⇄ Vertex AI) |
| User quota abuse | Med | High | Implement fair use policies, rate limiting, and usage anomaly detection |
| Pricing model issues | Med | Med | Plan to test and adjust pricing within first 3-6 months based on usage patterns |

## 16. Open Questions
* Enterprise SSO demand? (workload identity federation)
* Do we need on‑prem GPU for privacy‑sensitive clients?
* When should we transition to self-hosted models for cost optimization?
* How can we best integrate with emerging creative MCP servers (like "Short Video Maker")?

## 17. Appendix
### 17.1 Style JSON Schema (excerpt)
```json
{
  "id": "zen‑ink‑enso‑minimal",
  "prompt": "Minimalist zen enso circle painted with black sumi‑ink brush strokes, circle slightly open…",
  "negative_prompt": "blurry, artifacts, watermark",
  "model_preference": "dall‑e‑3"
}
```

### 17.2 Implementation Strategy
The implementation will follow a phased approach:
1. **Primary API**: OpenAI DALL·E 3 will serve as the primary image generation API due to its robust capabilities, recent price reductions (from $0.020 to $0.016 per standard image), and expanded features including Ultra HD resolution (4K) options.
2. **Secondary API**: Google Vertex AI Imagen will be integrated as a secondary API for redundancy and potentially different stylization capabilities.
3. **Feature Evolution**: The system will begin with core stylization and gradually incorporate advanced capabilities like animation and extended editing tools as they become available in the underlying APIs.
4. **Project Context Analysis**: Implementation will leverage AI to analyze different project components:
   - **Code Analysis**: Scan repositories to detect application type, UI frameworks, and color schemes
   - **Documentation Parsing**: Extract domain information, terminology, and brand guidelines from project docs
   - **Asset Inventory**: Catalog existing images, logos, and design elements to ensure consistency
   - **Style Recommendation Engine**: Use extracted context to suggest appropriate styles from the catalog
   - **Auto-Generation Pipeline**: Create tailored assets based on project context (icons, UI elements, logos)

### 17.3 MCP Tool Schemas
* `stylize_image` – Accepts an image URL and one or more style names, provides options for resolution and quality settings, and returns signed URLs for each generated style variant. Includes safety checks and usage tracking.
* `list_styles` – returns catalog w/ description & recommended model.
* `add_style` – Auth‑gated; user provides prompt template.
* `analyze_project` – Analyzes project files, documentation, and existing assets to understand context and suggest appropriate styles or generate project-specific assets automatically.

### 17.4 Cost Structure & Optimization
The primary cost drivers for Stylize are:

* **AI Generation APIs (~80% of costs)**: OpenAI's image APIs cost roughly $0.02-0.04 per standard quality image, meaning 100k image variants would cost $2,000-$4,000 per month.
* **Content Moderation**: Vision API costs approximately $1.50 per 1,000 images for SafeSearch, potentially adding $150/month for 100k images unless selectively applied.
* **Infrastructure**: Cloud Run, Storage, Pub/Sub and other GCP services contribute only minor costs (estimated <$200/month for 100k images) with many falling under free tier allocations.
* **Caching**: Memorystore (Redis) fixed cost of ~$35/month regardless of scale (until higher tiers needed).

To optimize costs and improve margins:
1. **Aggressive caching** of common style requests to reduce duplicate API calls
2. **Selective content moderation** using OpenAI's free moderation API when possible
3. **Resolution tiering** with lower resolution for free users
4. **Explore self-hosted models** on GPUs if volume justifies the infrastructure investment

### 17.5 Growth Strategy
1. **Initial user acquisition**: Seek featured placement in Windsurf, Cline, and Copilot marketplaces
2. **User referral program**: Incentivize free users to refer others with bonus credits
3. **Partner ecosystem**: Integrate with complementary MCP servers like "Short Video Maker"
4. **Platform expansion**: Prioritize IDE platforms actively incorporating image capabilities
5. **Target milestone**: 250-300 paying Pro users ($20/month) to reach $5k MRR sustainability

References:
- PulseMCP ecosystem statistics and image server usage data (2025)
- Playground AI, ChatGPT, and Leonardo AI pricing benchmarks (2025)
- SaaS conversion rate industry benchmarks (2-5% free-to-paid)
