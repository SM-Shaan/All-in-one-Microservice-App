# Phase 3: Database & Repository Pattern ✅

## What You've Learned

Congratulations! You've upgraded from in-memory storage to a real PostgreSQL database with professional patterns.

### New Concepts Implemented

1. **SQLAlchemy ORM** - Object-Relational Mapping
2. **Async Database Operations** - Non-blocking database queries
3. **Repository Pattern** - Clean separation of data access logic
4. **Password Hashing** - Secure password storage with bcrypt
5. **Database Migrations** - Alembic for schema versioning
6. **Connection Pooling** - Efficient database connection management

## Architecture

```
Route Handler
     ↓
Repository (Data Access Layer)
     ↓
SQLAlchemy (ORM)
     ↓
PostgreSQL Database
```

## Key Files Created/Modified

### Database Models
- `app/models/domain/user.py` - SQLAlchemy User model
- `app/db/base.py` - Base class for all models

### Repository Pattern
- `app/db/repositories/user_repository.py` - User data access layer
- Methods: create, get_by_id, get_by_email, list, update, delete, count

### Database Session
- `app/db/session.py` - Connection pool, session management
- `get_db()` - Dependency injection for routes
- `init_db()` / `close_db()` - Lifecycle management

### Security
- `app/core/security.py` - Password hashing utilities
- `hash_password()` - Bcrypt hashing
- `verify_password()` - Password verification

### API Schemas
- `app/models/schemas/user_schemas.py` - Pydantic models
- UserCreate, UserUpdate, UserResponse, UserListResponse

### Database Migrations
- `alembic.ini` - Alembic configuration
- `app/db/migrations/env.py` - Migration environment
- `app/db/migrations/script.py.mako` - Migration template

### Updated Files
- `app/api/routes/users.py` - Now uses database instead of memory
- `app/main.py` - Initializes database on startup

## How to Run Phase 3

### Step 1: Start PostgreSQL

```bash
# From project root
cd E:\microservices-platform

# Start PostgreSQL (and other infrastructure)
docker-compose up -d postgres
```

Wait for PostgreSQL to be ready (~10 seconds).

### Step 2: Install Dependencies

```bash
cd services/user-service
pip install -r requirements.txt
```

### Step 3: Run the Service

```bash
python run.py
```

You should see:
```
============================================================
🚀 Starting user-service v1.0.0
============================================================
📍 Running on http://0.0.0.0:8001
📚 API Docs: http://0.0.0.0:8001/docs

🔄 Initializing database...
✅ Database tables created
✅ Database initialized successfully
============================================================
✅ Service is ready to accept requests!
============================================================
```

### Step 4: Test the Database Integration

Open http://localhost:8001/docs and try creating a user:

```json
{
  "email": "alice@example.com",
  "full_name": "Alice Johnson",
  "password": "SecurePass123"
}
```

**Now the magic happens:**
1. Stop the service (Ctrl+C)
2. Start it again (`python run.py`)
3. Go to Swagger UI and list users
4. **Your data is still there!** 🎉

## Understanding the Code

### 1. SQLAlchemy Model (Database Layer)

```python
# app/models/domain/user.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

This maps to a PostgreSQL table:
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Repository Pattern (Data Access Layer)

```python
# app/db/repositories/user_repository.py
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        return user

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
```

**Why Repository Pattern?**
- Separates database logic from business logic
- Makes testing easier (can mock the repository)
- Centralizes all database queries
- Provides clean API for data access

### 3. Dependency Injection (Route Layer)

```python
# app/api/routes/users.py
@router.post("/")
async def create_user(
    user_data: UserCreate,
    repo: UserRepository = Depends(get_user_repo)
):
    # repo is automatically injected by FastAPI
    user = await repo.create(user_data)
    return user
```

**How it works:**
1. FastAPI sees `Depends(get_user_repo)`
2. Calls `get_user_repo()` which needs a `db` session
3. FastAPI sees `db: AsyncSession = Depends(get_db)`
4. Creates a database session
5. Passes it to `UserRepository`
6. Injects repository into route handler
7. Automatically closes session after request

### 4. Password Hashing

```python
# app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Why bcrypt?**
- Specifically designed for password hashing
- Slow by design (prevents brute force attacks)
- Automatically includes salt (prevents rainbow table attacks)
- Configurable work factor (can increase as computers get faster)

Example:
```python
>>> password = "SecurePass123"
>>> hashed = hash_password(password)
>>> print(hashed)
$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU2dVXK7aGMW

>>> verify_password("SecurePass123", hashed)
True
>>> verify_password("WrongPassword", hashed)
False
```

## Database Migrations with Alembic

Alembic tracks database schema changes over time.

### Create a New Migration

When you change your models:

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add phone_number to users"
```

This creates a migration file in `app/db/migrations/versions/`.

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# See migration history
alembic history

# See current version
alembic current
```

### Example Migration File

```python
def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))

def downgrade() -> None:
    op.drop_column('users', 'phone_number')
```

## Testing the Features

### 1. Create Users

```bash
curl -X POST http://localhost:8001/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "bob@example.com",
    "full_name": "Bob Smith",
    "password": "SecurePass123"
  }'
```

### 2. List Users with Pagination

```bash
# First page (10 users)
curl "http://localhost:8001/api/v1/users?skip=0&limit=10"

# Second page
curl "http://localhost:8001/api/v1/users?skip=10&limit=10"

# Only active users
curl "http://localhost:8001/api/v1/users?active_only=true"
```

### 3. Get User by Email

```bash
curl "http://localhost:8001/api/v1/users/email/bob@example.com"
```

### 4. Update User

```bash
curl -X PUT http://localhost:8001/api/v1/users/{user_id} \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Robert Smith"
  }'
```

### 5. Check Database Directly

```bash
# Connect to PostgreSQL
docker exec -it microservices-postgres psql -U postgres -d users

# Query users
SELECT id, email, full_name, is_active, created_at FROM users;

# Check password is hashed
SELECT email, hashed_password FROM users LIMIT 1;

# Exit
\q
```

## Common Issues and Solutions

### Issue: "Connection refused" to PostgreSQL

**Problem:** PostgreSQL not running

**Solution:**
```bash
docker-compose up -d postgres
docker ps  # Verify it's running
```

### Issue: "Table already exists"

**Problem:** Tables created but Alembic not tracking

**Solution:**
```bash
# Drop all tables
docker exec -it microservices-postgres psql -U postgres -d users -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

# Restart service (will recreate tables)
python run.py
```

### Issue: Import errors

**Problem:** Python can't find modules

**Solution:**
```bash
# Make sure you're in the right directory
cd services/user-service

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "asyncpg.exceptions.InvalidCatalogNameError"

**Problem:** Database doesn't exist

**Solution:**
```bash
# Create the database
docker exec -it microservices-postgres psql -U postgres -c "CREATE DATABASE users;"
```

## Comparing Phase 2 vs Phase 3

| Feature | Phase 2 | Phase 3 |
|---------|---------|---------|
| Storage | In-memory dict | PostgreSQL |
| Data Persistence | Lost on restart | Permanent |
| Password Storage | Plain text | Bcrypt hashed |
| Architecture | Simple routes | Repository pattern |
| Database | None | SQLAlchemy ORM |
| Migrations | N/A | Alembic |
| Connection Pooling | N/A | Built-in |
| Production Ready | ❌ | ✅ (for database layer) |

## Key Takeaways

1. **ORM Benefits**: SQLAlchemy lets you work with Python objects instead of SQL
2. **Repository Pattern**: Separates data access from business logic
3. **Async Operations**: Non-blocking database calls for better performance
4. **Security**: Never store passwords in plain text
5. **Migrations**: Track database schema changes over time
6. **Dependency Injection**: Clean way to provide dependencies to routes

## Questions to Consider

1. What happens if two requests try to create a user with the same email?
2. How does the connection pool improve performance?
3. Why do we separate SQLAlchemy models from Pydantic models?
4. What would happen if we didn't use `await` for database operations?
5. How does bcrypt make brute-force attacks slower?

## Experiments to Try

1. **Add a field:**
   - Add `phone_number` to the User model
   - Create a migration with Alembic
   - Apply it and test

2. **Test transactions:**
   - What happens if an error occurs mid-update?
   - The session rollback ensures data consistency!

3. **Performance test:**
   - Create 100 users with a script
   - Test pagination performance
   - Check connection pool usage

4. **Database exploration:**
   - Connect to PostgreSQL with a GUI (pgAdmin, DBeaver)
   - Explore the schema
   - Run custom SQL queries

## Next Phase Preview

In **Phase 4**, you'll add:
- JWT authentication (login/logout)
- Token-based authorization
- Protected endpoints
- Current user dependency
- Password change functionality

Ready to continue? Let me know!

## Resources

- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Bcrypt Explained](https://en.wikipedia.org/wiki/Bcrypt)
- [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
