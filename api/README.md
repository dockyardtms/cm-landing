## Landing API (Credomax Landing Site)

This `api/` folder started as a general-purpose FastAPI service but is now
focused on a lightweight Landing API that powers the
`https://api.landing.credomaxtrans.com` form endpoint.

### What is actually used now

- **Form Lambda**: `src/form_handler.py`
  - Deployed via `iac/api/template.yaml` as an AWS Lambda behind API Gateway.
  - Accepts `POST /form` with JSON `{ "name": "...", "phone": "..." }`.
  - Performs basic validation and logs submissions to CloudWatch.

- **Health endpoints**: `src/routers/health.py`
  - `GET /health` and `GET /health/detailed` return simple API health.

- **FastAPI app (optional)**: `src/app.py` / `src/main.py`
  - Provide a small FastAPI application named "Landing API".
  - Kept mainly for local development or future expansion.

### What was removed or stubbed

- The original workflow/run management logic and its dependencies from the
  previous project are **not used** anymore.
- `routers/workflows.py` and `routers/runs.py` are now **simple placeholders**
  that return a message indicating those APIs are not implemented for the
  Landing API.
- `services/health_service.py` has been simplified to avoid the original
  project’s dependency checks and now only reports basic API health.

### Configuration

Environment variables use a `LANDING_API_*` prefix. See the env files under
`api/env/` for examples:

- `env/local.env` – local development
- `env/dev.env` – development
- `env/stg.env` – staging
- `env/prod.env` – production

Key variables:

- `LANDING_API_DEBUG`
- `LANDING_API_RATE_LIMIT`
- `LANDING_API_ALLOWED_HOSTS`
- `LANDING_API_CORS_ORIGINS`

### Deployment

The Landing form Lambda and its custom domain are defined under `iac/api`:

- `iac/api/template.yaml` – SAM template for:
  - Regional API Gateway with custom domain `api.landing.credomaxtrans.com`.
  - Lambda function using `src.form_handler.handler`.
- `iac/api/samconfig.yaml` – deployment configuration (prod).

From `iac/api` you can deploy with:

```bash
sam build
sam deploy --config-env prod
```

After deployment, the landing page JavaScript posts to:

```text
POST https://api.landing.credomaxtrans.com/form
async def create_workflow(workflow_data: WorkflowCreateRequest, current_user: str = Depends(get_current_user))
```

**Run Router (`runs.py`):**
```python
@router.post("", response_model=RunResponse)
async def create_run(run_data: RunCreateRequest, current_user: str = Depends(get_current_user))
```

**Health Router (`health.py`):**
```python
@router.get("/health")
async def health_check(health_service: HealthService = Depends(HealthService))
```

#### 3. **Service Layer (`services/`)**
Business logic abstraction with dependency injection:

**Workflow Service:**
- Workflow CRUD operations
- Validation and schema checking
- Version management
- Access control

**Run Service:**
- Run lifecycle management
- SQS message publishing
- Status tracking
- Log aggregation

**Health Service:**
- Dependency health checks
- System status monitoring
- Performance metrics

#### 4. **Authentication System (`auth.py`)**
API key-based authentication with user context:
```python
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    # Validate API key
    # Extract user context
    # Return user identifier
```

**Security Features:**
- Bearer token authentication
- API key validation
- User context injection
- Rate limiting per user
- Request logging with user attribution

#### 5. **Exception Handling (`exceptions.py`)**
Structured error handling with consistent API responses:
```python
class LandingAPIException(Exception):
    def __init__(self, status_code: int, error_code: str, message: str, details: Optional[Dict] = None)
```

**Error Categories:**
- **Client Errors (4xx)**: Invalid requests, authentication failures
- **Server Errors (5xx)**: Internal failures, dependency issues
- **Business Logic Errors**: Workflow validation, concurrency limits
- **Infrastructure Errors**: Database connectivity, queue failures

### Design Patterns

#### 1. **Dependency Injection Pattern**
FastAPI's dependency injection system for clean architecture:
```python
@router.post("/workflows")
async def create_workflow(
    workflow_data: WorkflowCreateRequest,
    current_user: str = Depends(get_current_user),
    workflow_service: WorkflowService = Depends(WorkflowService)
):
```

#### 2. **Repository Pattern**
Service layer abstracts data access:
```python
class WorkflowService:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(settings.workflows_table)
```

#### 3. **Request/Response Pattern**
Pydantic models for type safety and validation:
```python
class WorkflowCreateRequest(BaseModel):
    name: str
    definition: Dict[str, Any]
    description: str = ""

class WorkflowResponse(BaseModel):
    id: str
    name: str
    version: str
    created_at: str
```

#### 4. **Middleware Pattern**
Cross-cutting concerns handled by middleware:
- Request logging
- Rate limiting
- CORS handling
- Error formatting

### API Design Principles

#### 1. **RESTful Design**
- Resource-based URLs (`/v1/workflows`, `/v1/runs`)
- HTTP methods for operations (GET, POST, PUT, DELETE)
- Consistent response formats
- Proper HTTP status codes

#### 2. **Versioning Strategy**
- URL-based versioning (`/v1/`)
- Backward compatibility maintenance
- Deprecation notices for old versions
- Migration guides for breaking changes

#### 3. **Pagination & Filtering**
```python
@router.get("/runs")
async def list_runs(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    workflow_id: Optional[str] = None
):
```

#### 4. **Error Response Format**
Consistent error structure across all endpoints:
```json
{
  "error": {
    "code": "WORKFLOW_NOT_FOUND",
    "message": "Workflow abc123 not found",
    "details": {
      "workflow_id": "abc123",
      "suggestions": ["Check workflow ID", "List available workflows"]
    }
  }
}
```

### Security Architecture

#### 1. **Authentication & Authorization**
- **API Key Authentication**: Bearer token in Authorization header
- **User Context**: API key mapped to user identity
- **Rate Limiting**: Per-user and per-IP rate limits
- **Request Validation**: All inputs validated with Pydantic

#### 2. **Input Validation**
- **Schema Validation**: Pydantic models for all request/response data
- **Workflow Validation**: Deep validation of workflow definitions
- **SQL Injection Prevention**: Parameterized queries (DynamoDB)
- **XSS Prevention**: Input sanitization and output encoding

#### 3. **Security Headers**
- **CORS**: Configurable cross-origin policies
- **Content Security Policy**: Prevent XSS attacks
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Request Size Limits**: Prevent large payload attacks

### Performance Optimizations

#### 1. **Async/Await Pattern**
All I/O operations are asynchronous:
```python
async def create_workflow(workflow_data: WorkflowCreateRequest) -> WorkflowResponse:
    workflow = await workflow_service.create_workflow(...)
    return WorkflowResponse(**workflow)
```

#### 2. **Connection Pooling**
- **AWS SDK**: Connection pooling for DynamoDB and SQS
- **HTTP Client**: Reuse connections for external API calls
- **Database Connections**: Efficient connection management

#### 3. **Caching Strategy**
- **Configuration Caching**: Settings cached during startup
- **Workflow Caching**: Frequently accessed workflows cached
- **Response Caching**: Cache headers for static content

#### 4. **Pagination & Limits**
- **Result Limits**: Maximum result set sizes to prevent memory issues
- **Streaming Responses**: Large datasets streamed to client
- **Lazy Loading**: On-demand loading of related data

### Monitoring & Observability

#### 1. **Structured Logging**
JSON-formatted logs with correlation IDs:
```python
logger.info("Workflow created", 
           workflow_id=workflow_id, 
           user_id=current_user,
           request_id=request.headers.get("X-Request-ID"))
```

#### 2. **Metrics & Monitoring**
- **Request Metrics**: Response times, error rates, throughput
- **Business Metrics**: Workflow creation rates, run success rates
- **Infrastructure Metrics**: CPU, memory, connection pool usage
- **Custom Dashboards**: Real-time monitoring dashboards

#### 3. **Health Checks**
Comprehensive health check endpoints:
- **Basic Health**: API availability and version
- **Detailed Health**: All dependencies (DynamoDB, SQS, etc.)
- **Readiness Probes**: Kubernetes readiness checks
- **Liveness Probes**: Application health monitoring

#### 4. **Error Tracking**
- **Exception Logging**: All exceptions logged with context
- **Error Aggregation**: Error patterns and trends
- **Alerting**: Real-time alerts for critical errors
- **Debug Information**: Detailed error context for troubleshooting
