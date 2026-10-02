# Developer Dashboard — Complete API Reference
> **Base URL:** `http://localhost:8000/api/v1`
> **Authorization:** `Authorization: Token <developer_token>` (**NOT** `Bearer`)

---

## ✅ All 22 Endpoints — Complete Reference

---

### 1. Authentication

#### `POST /developer/login/`
**Auth:** None

```json
{
  "email": "dev@example.com",
  "password": "password123"
}
```

**Response 200:**
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "dev@example.com",
    "first_name": "عبدالله",
    "last_name": "جمال",
    "avatar": null,
    "is_primary": true,
    "status": "active",
    "permissions": [
      {"id": 1, "codename": "view_leads", "name": "عرض العملاء المحتملين"},
      {"id": 2, "codename": "rate_leads", "name": "تقييم العملاء المحتملين"},
      {"id": 3, "codename": "export_excel", "name": "تصدير الإكسيل"},
      {"id": 4, "codename": "manage_team", "name": "إدارة الفريق"},
      {"id": 5, "codename": "manage_projects", "name": "إدارة المشاريع"}
    ],
    "created_at": "2026-10-01T12:00:00Z"
  }
}
```

---

#### `POST /developer/logout/`
**Auth:** `Token <developer_token>`

No request body needed.

**Response 200:**
```json
{
  "detail": "تم تسجيل الخروج بنجاح."
}
```

---

#### `POST /developer/register/`
**Auth:** None

```json
{
  "company_name": "شركة عقارات جمال",
  "email": "dev@example.com",
  "password": "password123",
  "first_name": "عبدالله",
  "last_name": "جمال"
}
```

**Response 201:**
```json
{
  "token": "abc123...",
  "user": { "...same as login response..." }
}
```

> **NOTE:** Primary user automatically gets ALL 5 permissions assigned.

---

### 2. Account Management

#### `GET /developer/account/`
**Auth:** `Token <developer_token>`

**Response 200:** Returns the same `user` object as login.

---

#### `PUT /developer/account/`
**Auth:** `Token <developer_token>`

```json
{
  "first_name": "عبدالله",
  "last_name": "جمال",
  "email": "new@example.com",
  "avatar": "<file upload>",
  "current_password": "old123",
  "new_password": "new123456"
}
```
> All fields are optional. `current_password` required only when changing password.

**Response 200:** Updated user object.

---

#### `DELETE /developer/account/`
**Auth:** `Token <developer_token>`
> **Only the primary account owner** can delete the account. Deletes the entire company account and all team members.

**Response 204:** No content.

---

### 3. Projects

#### `GET /developer/projects/`
**Auth:** `Token <developer_token>`

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `status` | `active` / `inactive` | Filter by status |
| `project_type` | `residential` / `commercial` / `medical` | Filter by type |
| `search` | string | Search by name |
| `page` | int | Page number |

**Response 200:**
```json
{
  "count": 10,
  "next": "http://...",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "مشروع النيل",
      "project_type": "residential",
      "location": {"id": 1, "name": "القاهرة الجديدة"},
      "price_per_meter": "15000.00",
      "status": "active",
      "main_image": "http://localhost:8000/media/project_images/...",
      "created_at": "2026-10-01T12:00:00Z"
    }
  ]
}
```

---

#### `POST /developer/projects/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_projects`
**Content-Type:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `name` | string | ✅ |
| `project_type` | `residential` / `commercial` / `medical` | ✅ |
| `location_id` | int (Location ID) | ✅ |
| `price_per_meter` | decimal | ✅ |
| `description` | string | ❌ |
| `status` | `active` / `inactive` | ❌ (default: active) |
| `main_image` | file | ✅ |
| `document` | file | ❌ |

**Response 201:** Full project detail object.

---

#### `GET /developer/projects/{id}/`
**Auth:** `Token <developer_token>`

**Response 200:** Full project detail with gallery.

---

#### `PUT /developer/projects/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_projects`
**Content-Type:** `multipart/form-data`

Same fields as POST, all optional (partial update).

**Response 200:** Updated project detail.

---

#### `DELETE /developer/projects/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_projects`

**Response 204:** No content.

---

#### `GET /developer/projects/{id}/stats/`
**Auth:** `Token <developer_token>`

**Response 200:**
```json
{
  "gallery_count": 5,
  "marketing_leads": 12,
  "total_views": 340
}
```

---

### 4. Dashboard Overview

#### `GET /developer/dashboard/overview/`
**Auth:** `Token <developer_token>`
**Permission Required:** `view_leads`

> ⚠️ **Frontend Fix:** The URL is `/developer/dashboard/overview/` NOT `/developer/stats/`

**Response 200:**
```json
{
  "projects": {
    "total": 5,
    "active": 3,
    "top_by_leads": [
      {"id": 1, "name": "مشروع النيل", "lead_count": 45}
    ]
  },
  "leads": {
    "total": 150,
    "marketing_total": 80,
    "inquiries_total": 70,
    "last_30_days": 35,
    "by_source": {
      "facebook": 40,
      "google": 30,
      "website": 10
    }
  },
  "location_medians": {}
}
```

---

### 5. Team Management

#### `GET /developer/team/`
**Auth:** `Token <developer_token>`

**Response 200:** Paginated list of team members with permissions.

---

#### `POST /developer/team/invite/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_team`

> ⚠️ **Frontend Fix:** The URL is `/developer/team/invite/` NOT `/developer/team/`

```json
{
  "email": "member@example.com",
  "first_name": "أحمد",
  "last_name": "محمد",
  "password": "password123",
  "permission_ids": [1, 2]
}
```

**Response 201:** Created team member object.

---

#### `PUT /developer/team/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_team`

```json
{
  "first_name": "أحمد",
  "last_name": "محمد",
  "permission_ids": [1, 2, 3],
  "status": "active"
}
```
> All fields optional.

**Response 200:** Updated team member.

---

#### `DELETE /developer/team/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `manage_team`

> **Soft delete** — sets status to `inactive`.

**Response 204:** No content.

---

### 6. Leads

#### `GET /developer/leads/`
**Auth:** `Token <developer_token>`
**Permission Required:** `view_leads`

**Query Params:**
| Param | Type | Description |
|-------|------|-------------|
| `type` | `marketing` | If set to `marketing`, returns ad campaign leads. Default: buyer inquiries |
| `project_id` | int | Filter by project |
| `source` | string | Filter by source |
| `rating` | string | Filter by rating (inquiries only) |
| `status` | string | Filter by status (inquiries only) |
| `page` | int | Page number |

---

#### `GET /developer/leads/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `view_leads`

**Response 200:** Lead detail object.

---

#### `PATCH /developer/leads/{id}/`
**Auth:** `Token <developer_token>`
**Permission Required:** `rate_leads`

```json
{
  "status": "contacted",
  "rating": "hot"
}
```

---

#### `GET /developer/leads/export/`
**Auth:** `Token <developer_token>`
**Permission Required:** `export_excel`

**Response:** CSV file download with all leads.

---

## 🔐 Permission System

### All 5 Permissions
| ID | Codename | Arabic Name | Controls |
|----|----------|-------------|----------|
| 1 | `view_leads` | عرض العملاء المحتملين | View leads list, dashboard overview |
| 2 | `rate_leads` | تقييم العملاء المحتملين | Update lead status/rating |
| 3 | `export_excel` | تصدير الإكسيل | Export leads CSV |
| 4 | `manage_team` | إدارة الفريق | Invite/edit/remove team members |
| 5 | `manage_projects` | إدارة المشاريع | Create/edit/delete projects |

### How Permissions Work
1. **Primary user** (account creator) → Gets ALL 5 permissions automatically on registration
2. **Team members** → Get only the permissions assigned via `permission_ids` during invite
3. **Removing a permission** → Update the team member with new `permission_ids` list (it REPLACES, not appends)
4. **Permission check** → Backend checks `user.permissions.filter(codename=...)` on every request

### To Change a Team Member's Permissions:
```
PUT /api/v1/developer/team/{id}/
{
  "permission_ids": [1, 2]   // REPLACES all permissions with these
}
```

---

## 📋 TypeScript Interfaces

```typescript
interface Permission {
  id: number;
  codename: string;
  name: string;
}

interface DeveloperUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  avatar: string | null;
  is_primary: boolean;
  status: "active" | "inactive";
  permissions: Permission[];
  created_at: string;
}

interface Project {
  id: number;
  name: string;
  project_type: "residential" | "commercial" | "medical";
  location: { id: number; name: string };
  price_per_meter: string;
  description: string;
  status: "active" | "inactive";
  main_image: string;
  document: string | null;
  created_at: string;
  updated_at: string;
}

interface ProjectStats {
  gallery_count: number;
  marketing_leads: number;
  total_views: number;
}

interface DashboardOverview {
  projects: {
    total: number;
    active: number;
    top_by_leads: { id: number; name: string; lead_count: number }[];
  };
  leads: {
    total: number;
    marketing_total: number;
    inquiries_total: number;
    last_30_days: number;
    by_source: Record<string, number>;
  };
  location_medians: Record<string, number>;
}

interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
```

---

## ⚠️ Frontend Fixes Needed

| Issue | Wrong | Correct |
|-------|-------|---------|
| Dashboard URL | `/developer/stats/` | `/developer/dashboard/overview/` |
| Team invite URL | `/developer/team/` (POST) | `/developer/team/invite/` (POST) |
| Account update | Mocked/hardcoded | Real `PUT /developer/account/` |
| Auth header | `Bearer <token>` | `Token <token>` |
