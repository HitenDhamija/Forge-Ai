# Human-in-the-Loop Approval Gates

## Overview

The Approval Gates system provides controlled, auditable human oversight for execution steps. Every critical operation can require explicit human approval before proceeding, ensuring safety and compliance.

**Philosophy:** ForgeAI never bypasses human approval for critical operations. Every decision is logged, auditable, and reversible.

## Architecture

```
Execution Runtime
       ↓
Step requires_approval = true
       ↓
Approval Engine
       ↓
Create ApprovalRequest
       ↓
Polling / API
       ↓
Human Reviews (via ApprovalGate UI)
       ↓
Decision: Approved / Denied
       ↓
Execution Runtime continues or skips step
```

## Components

### Approval Engine

Core logic for managing approval requests and decisions:

```python
from app.approval import ApprovalEngine

engine = ApprovalEngine()

# Create request
request = await engine.create_request(
    ApprovalRequestCreate(
        execution_id="exec-123",
        step_id="step-1",
        request_type="auth",
        title="Approve: Implement JWT authentication",
        description="This step modifies authentication logic",
        context={"agent_type": "software_engineer"},
        risk_level="high",
        timeout_minutes=30,
    )
)

# Process decision
decision = await engine.decide(
    request.id,
    ApprovalDecisionCreate(
        decision="approved",
        reason="Looks good",
        decided_by="human",
    )
)

# Check status
is_approved = await engine.is_approved(request.id)
```

### Timeout Manager

Handles automatic timeouts for pending requests:

```python
from app.approval import TimeoutManager

manager = TimeoutManager(approval_engine)

# Register timeout callback
@manager.on_timeout
async def handle_timeout(request_id: str):
    print(f"Request timed out: {request_id}")

# Start checking
await manager.start()
```

### Approval Models

Database tables for persistence:

```sql
CREATE TABLE approval_requests (
    id VARCHAR PRIMARY KEY,
    execution_id VARCHAR NOT NULL,
    step_id VARCHAR NOT NULL,
    request_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    context JSON,
    risk_level VARCHAR DEFAULT 'medium',
    status VARCHAR DEFAULT 'pending',
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    decided_at TIMESTAMP,
    decided_by VARCHAR
);

CREATE TABLE approval_decisions (
    id VARCHAR PRIMARY KEY,
    request_id VARCHAR REFERENCES approval_requests(id),
    decision VARCHAR NOT NULL,
    reason TEXT,
    decided_by VARCHAR NOT NULL,
    decided_at TIMESTAMP,
    metadata JSON
);
```

## Timeout Configuration

Timeouts are configured per request type:

| Request Type | Timeout | Description |
|-------------|---------|-------------|
| `auth` | Never | Authentication changes require explicit approval |
| `database` | 30 min | Database migrations |
| `file_delete` | 15 min | File deletions |
| `dependency` | 20 min | Dependency updates |
| `file_modify` | 10 min | File modifications |
| `general` | 15 min | Default |

## Risk Levels

| Level | Score | Use Case |
|-------|-------|----------|
| `low` | 1 | Minor changes, documentation |
| `medium` | 2 | Feature implementation |
| `high` | 3 | Security, database, auth changes |
| `critical` | 4 | Deletions, destructive operations |

## API Endpoints

### Create Approval Request

```http
POST /api/v1/approval/request
Content-Type: application/json

{
  "execution_id": "exec-123",
  "step_id": "step-1",
  "request_type": "auth",
  "title": "Approve: Implement JWT authentication",
  "description": "This step modifies authentication logic",
  "context": {"agent_type": "software_engineer"},
  "risk_level": "high",
  "timeout_minutes": 30
}
```

### Decide on Approval

```http
POST /api/v1/approval/{request_id}/decide
Content-Type: application/json

{
  "decision": "approved",
  "reason": "Looks good",
  "decided_by": "human"
}
```

### Get Pending Approvals

```http
GET /api/v1/approval/pending/{execution_id}
```

### Get Approval Stats

```http
GET /api/v1/approval/stats
```

### Enable Auto-Approve

```http
POST /api/v1/approval/auto-approve?enabled=true
```

## Frontend Integration

### ApprovalGate Component

The `ApprovalGate` component provides a UI for reviewing and deciding on pending approvals:

```tsx
import { ApprovalGate } from "@/components/execution/ApprovalGate";

<ApprovalGate
  approvals={pendingApprovals}
  onApprove={handleApprove}
  onDeny={handleDeny}
  onCancel={handleCancel}
  loading={loading}
/>
```

### Features

- **Risk indicators** - Color-coded badges for risk levels
- **Type icons** - Visual indicators for request types
- **Expandable details** - View full context before deciding
- **Reason field** - Optional reason for decision
- **Loading states** - Prevents double-clicking

## Integration with Execution Runtime

The execution runtime automatically creates approval requests for steps with `requires_approval=True`:

```python
# In ExecutionRuntime._execute_step()
if step.requires_approval:
    request = await self.approval_engine.create_request(...)
    self._pending_approvals[step.step_id] = request.id
    
    # Wait for approval
    approved = await self._wait_for_approval(step.step_id)
    
    if approved:
        # Continue execution
    else:
        # Skip step
```

## Approval Flow

1. **Step requires approval** - Execution runtime detects `requires_approval=True`
2. **Create request** - Approval engine creates `ApprovalRequest`
3. **Poll for decision** - Frontend polls `/approval/pending/{execution_id}`
4. **Human reviews** - User sees `ApprovalGate` with details
5. **Decision made** - User clicks Approve or Deny
6. **API call** - Frontend calls `/approval/{request_id}/decide`
7. **Execution continues** - Runtime receives decision and proceeds

## Audit Trail

Every approval action is logged:

```json
{
  "request_id": "req-123",
  "execution_id": "exec-456",
  "step_id": "step-1",
  "decision": "approved",
  "reason": "Looks good",
  "decided_by": "human",
  "decided_at": "2026-07-01T12:00:00Z",
  "risk_level": "high",
  "request_type": "auth"
}
```

## Auto-Approval Mode

For development/testing, auto-approval can be enabled:

```python
# Enable auto-approve
approval_engine.set_auto_approve(True)

# Or via API
POST /api/v1/approval/auto-approve?enabled=true
```

**Warning:** Never enable auto-approval in production.

## Best Practices

1. **Set appropriate timeouts** - Don't let requests linger indefinitely
2. **Use risk levels** - Help prioritize review attention
3. **Provide context** - Include enough information for informed decisions
4. **Document reasons** - Always provide reasons for decisions
5. **Monitor stats** - Track approval rates and decision times
