# User Service

The User Service handles user management, authentication, and authorization for the microservices platform.

## What You'll Learn (Progressive Phases)

### ✅ Phase 2 (Current): Basic Service
- FastAPI application setup
- RESTful API endpoints (CRUD operations)
- Request/Response validation with Pydantic
- API documentation with Swagger/ReDoc
- Health check endpoints
- In-memory storage (for learning)

### 🔄 Phase 3 (Next): Database Integration
- PostgreSQL connection with SQLAlchemy
- Database models and migrations (Alembic)
- Repository pattern for data access
- Async database operations

### 🔄 Phase 4: Authentication
- Password hashing with bcrypt
- JWT token generation and validation
- Login and registration endpoints
- Token refresh mechanism

### 🔄 Phase 5: Event-Driven
- Kafka producer setup
- Publishing user events (created, updated, deleted)
- Event schemas

## Architecture

```
user-service/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── core/
│   │   └── config.py        # Service configuration
│   ├── api/
│   │   └── routes/
│   │       ├── health.py    # Health check endpoints
│   │       └── users.py     # User CRUD endpoints
│   ├── models/             # Database models (Phase 3)
│   ├── db/                 # Database setup (Phase 3)
│   └── services/           # Business logic (Phase 3)
├── Dockerfile
├── requirements.txt
└── README.md
```

## API Endpoints

### Health Checks
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Basic health check |
| GET | `/health/ready` | Readiness check (dependencies) |
| GET | `/health/live` | Liveness check |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/users` | Create new user |
| GET | `/api/v1/users` | List users (paginated) |
| GET | `/api/v1/users/{id}` | Get user by ID |
| PUT | `/api/v1/users/{id}` | Update user |
| DELETE | `/api/v1/users/{id}` | Delete user |

## Running the Service

### Option 1: Run Locally (Development)

1. **Install dependencies:**
```bash
cd services/user-service
pip install -r requirements.txt
```

2. **Run the service:**
```bash
python -m app.main
```

Or with uvicorn directly:
```bash
uvicorn app.main:app --reload --port 8001
```

3. **Access the service:**
- API: http://localhost:8001
- Swagger Docs: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Option 2: Run with Docker

1. **Build the image:**
```bash
docker build -t user-service:latest .
```

2. **Run the container:**
```bash
docker run -p 8001:8001 user-service:latest
```

## Testing the API

### Using cURL

**Create a user:**
```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "full_name": "John Doe",
    "password": "SecurePass123"
  }'
```

**Get all users:**
```bash
curl http://localhost:8001/api/v1/users
```

**Get specific user:**
```bash
curl http://localhost:8001/api/v1/users/{user_id}
```

**Update user:**
```bash
curl -X PUT http://localhost:8001/api/v1/users/{user_id} \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Smith"
  }'
```

**Delete user:**
```bash
curl -X DELETE http://localhost:8001/api/v1/users/{user_id}
```

### Using the Swagger UI

1. Navigate to http://localhost:8001/docs
2. Click "Try it out" on any endpoint
3. Fill in the parameters and click "Execute"
4. View the response

## Current Limitations (Will fix in Phase 3)

- ⚠️ Uses in-memory storage (data lost on restart)
- ⚠️ Passwords stored in plain text
- ⚠️ No authentication/authorization
- ⚠️ No database persistence
- ⚠️ No event publishing

## What We're Learning

### 1. FastAPI Basics
- Application setup and configuration
- Route definition and HTTP methods
- Request/response models with Pydantic
- Path and query parameters
- Exception handling

### 2. RESTful API Design
- Resource-based URLs
- HTTP status codes
- CRUD operations
- Pagination

### 3. API Documentation
- Automatic OpenAPI schema generation
- Swagger UI for interactive testing
- Request/response examples

### 4. Error Handling
- HTTP exceptions
- Validation errors
- Custom error responses

## Next Steps

Once you're comfortable with this phase:

1. **Test all endpoints** using Swagger UI or cURL
2. **Read the code** and understand how it works
3. **Experiment** - try adding a new field to the user
4. **Move to Phase 3** - Add database persistence

## Questions to Consider

1. What happens to the data when you restart the service?
2. How does FastAPI validate the request data?
3. What's the difference between `/health`, `/health/ready`, and `/health/live`?
4. Why do we use UUID for user IDs instead of integers?
5. What's the purpose of `skip` and `limit` parameters?

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [REST API Best Practices](https://restfulapi.net/)
