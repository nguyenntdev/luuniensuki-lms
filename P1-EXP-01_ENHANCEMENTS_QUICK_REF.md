# P1-EXP-01 Enhancement Quick Reference

## What Changed

### 1. Experiment Model - New Fields

**File:** `backend/models.py` (Experiment class)

```python
# NEW: Track who created the experiment
created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    PG_UUID(as_uuid=True),
    ForeignKey("users.id", ondelete="SET NULL"),
    nullable=True,
)

# NEW: Targeting rules for audience segmentation
target_audience: Mapped[Optional[dict[str, Any]]] = mapped_column(
    JSONB, nullable=True
)

# NEW: Relationship to creator
created_by: Mapped[Optional["User"]] = relationship(
    "User",
    foreign_keys=[created_by_id],
)
```

### 2. User Model - New Relationship

**File:** `backend/models.py` (User class)

```python
# NEW: Track experiments created by this user
created_experiments: Mapped[list["Experiment"]] = relationship(
    back_populates="created_by",
    foreign_keys="Experiment.created_by_id",
    cascade="all, delete-orphan",
)
```

### 3. Service Functions - Updated Signatures

**File:** `backend/services/experiments.py`

```python
def create_experiment(
    db: Session,
    key: str,
    name: str,
    variants: list[dict[str, Any]],
    description: Optional[str] = None,
    target_audience: Optional[dict[str, Any]] = None,  # NEW
    is_active: bool = False,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    created_by_id: Optional[UUID] = None,  # NEW
) -> Experiment:
    ...

def update_experiment(
    db: Session,
    experiment_id: UUID,
    name: Optional[str] = None,
    description: Optional[str] = None,
    variants: Optional[list[dict[str, Any]]] = None,
    target_audience: Optional[dict[str, Any]] = None,  # NEW
    is_active: Optional[bool] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> Optional[Experiment]:
    ...
```

### 4. Schemas - New Fields

**File:** `backend/schemas.py`

```python
class ExperimentOut(BaseSchema):
    id: UUID
    key: str
    name: str
    description: Optional[str] = None
    variants: list[dict[str, Any]]
    target_audience: Optional[dict[str, Any]] = None  # NEW
    is_active: bool
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_by_id: Optional[UUID] = None  # NEW
    created_at: datetime

class ExperimentCreateIn(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    variants: list[dict[str, Any]] = Field(...)
    target_audience: Optional[dict[str, Any]] = Field(  # NEW
        None,
        description="Optional targeting rules for audience segmentation"
    )
    is_active: bool = Field(default=False)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class ExperimentUpdateIn(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    variants: Optional[list[dict[str, Any]]] = None
    target_audience: Optional[dict[str, Any]] = None  # NEW
    is_active: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
```

### 5. API Endpoints - Updated

**File:** `backend/main.py`

**POST /api/v1/admin/experiments:**
```python
experiment = experiments.create_experiment(
    db=db,
    key=payload.key,
    name=payload.name,
    variants=payload.variants,
    description=payload.description,
    target_audience=payload.target_audience,  # NEW
    is_active=payload.is_active,
    start_date=payload.start_date,
    end_date=payload.end_date,
    created_by_id=current_user.id,  # NEW - auto-populated
)
```

**PUT /api/v1/admin/experiments/{experiment_id}:**
```python
experiment = experiments.update_experiment(
    db=db,
    experiment_id=experiment_id,
    name=payload.name,
    description=payload.description,
    variants=payload.variants,
    target_audience=payload.target_audience,  # NEW
    is_active=payload.is_active,
    start_date=payload.start_date,
    end_date=payload.end_date,
)
```

### 6. Database Migration

**File:** `migrations/versions/0036_experiment_enhancements.py`

```python
def upgrade():
    # Add created_by_id column
    op.add_column('experiments', sa.Column('created_by_id', 
        postgresql.UUID(as_uuid=True), nullable=True))
    
    # Add target_audience column
    op.add_column('experiments', sa.Column('target_audience', 
        postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    
    # Create foreign key constraint
    op.create_foreign_key(
        'fk_experiments_created_by_id_users',
        'experiments', 'users',
        ['created_by_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index
    op.create_index('idx_experiments_created_by', 
        'experiments', ['created_by_id'])
```

## Example Usage

### Creating an Experiment with Target Audience

```bash
curl -X POST http://localhost:8000/api/v1/admin/experiments \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "onboarding_flow_test",
    "name": "Onboarding Flow A/B Test",
    "description": "Testing simplified vs detailed onboarding",
    "variants": [
      {"key": "control", "name": "Current Flow", "weight": 50},
      {"key": "simplified", "name": "Simplified Flow", "weight": 50}
    ],
    "target_audience": {
      "new_users_only": true,
      "min_age": 13,
      "countries": ["VN", "US", "UK"]
    },
    "is_active": true
  }'
```

### Updating Target Audience

```bash
curl -X PUT http://localhost:8000/api/v1/admin/experiments/{id} \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_audience": {
      "new_users_only": true,
      "min_age": 18,
      "countries": ["VN"],
      "premium_only": false
    }
  }'
```

## Migration Command

```bash
cd /Users/nguyennt/Documents/luuniensuki-lms
alembic upgrade head
```

## Files Changed

- ✅ `backend/models.py` - Added 2 fields + 1 relationship to Experiment
- ✅ `backend/models.py` - Added 1 relationship to User
- ✅ `backend/services/experiments.py` - Updated 2 functions
- ✅ `backend/schemas.py` - Enhanced 3 schemas
- ✅ `backend/main.py` - Updated 2 endpoints
- ✅ `migrations/versions/0036_experiment_enhancements.py` - New migration

## Backwards Compatibility

✅ All new fields are OPTIONAL (nullable=True)
✅ Existing experiments will work without changes
✅ Old API calls without new fields will still work
✅ created_by_id is auto-populated for new experiments
