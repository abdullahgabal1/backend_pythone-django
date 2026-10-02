# Daary AI Backend — Complete API Reference
> **Base URL:** `http://localhost:8000/api/v1/`
> **Version:** 1.0 | **Last Updated:** October 2, 2026

---

## 📁 Files to Share

| File | Purpose |
|------|---------|
| `schema.yml` | Import into **Postman** (File → Import → select this file) |
| `API_REFERENCE.md` | This file — give to the **frontend developer** |

---

## 🔑 Authentication

The backend uses **two separate auth systems**:

| System | Who | Token Format | Header |
|--------|-----|-------------|--------|
| **JWT (Buyer App)** | Mobile/Web buyers | `Bearer <access_token>` | `Authorization: Bearer eyJ...` |
| **Token (Developer Dashboard)** | Developer accounts | `Token <key>` | `Authorization: Token abc123...` |

---

## 1. 🔐 Buyer Authentication (`/api/v1/auth/`)

### `GET /auth/challenge/`
> Get auth challenge (public)
- **Auth:** None
- **Response:** `200` challenge data

### `POST /auth/send-otp/`
> Send OTP to phone number (public)
- **Auth:** None
- **Body:**
```json
{ "phone": "01012345678" }
```
- **Response:** `200` `{ "detail": "OTP sent successfully" }`

### `POST /auth/verify-otp/`
> Verify OTP and get JWT tokens (public)
- **Auth:** None
- **Body:**
```json
{
  "phone": "01012345678",
  "otp": "123456",
  "name": "أحمد محمد",
  "birthday": "1995-03-15"
}
```
- **Response:** `200`
```json
{
  "access": "eyJ...",
  "refresh": "eyJ...",
  "user": { "id": 1, "phone": "01012345678", "name": "أحمد محمد" }
}
```

### `POST /auth/token/refresh/`
> Refresh expired access token
- **Auth:** None
- **Body:** `{ "refresh": "eyJ..." }`
- **Response:** `200` `{ "access": "eyJ..." }`

### `POST /auth/logout/`
> Blacklist refresh token
- **Auth:** `Bearer <access_token>`
- **Body:** `{ "refresh": "eyJ..." }`
- **Response:** `200`

---

## 2. 👤 Buyer Account (`/api/v1/account/`)

### `GET /account/me/`
> Get current user profile
- **Auth:** `Bearer <access_token>`
- **Response:** `200`
```json
{
  "id": 1,
  "phone": "01012345678",
  "name": "أحمد محمد",
  "birthday": "1995-03-15",
  "role": "buyer"
}
```

### `PATCH /account/me/`
> Update user profile
- **Auth:** `Bearer <access_token>`
- **Body:** `{ "name": "أحمد علي" }`
- **Response:** `200` updated user object

---

## 3. 🏠 Properties (`/api/v1/properties/`)

### `GET /properties/`
> List all properties (public, paginated)
- **Auth:** None
- **Query Params:** `?page=1&page_size=20`
- **Response:** `200`
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/v1/properties/?page=2",
  "results": [
    {
      "id": 1,
      "title": "شقة فاخرة في التجمع الخامس",
      "description": "...",
      "location": "التجمع الخامس",
      "price": "2500000.00",
      "price_suffix": "جنيه",
      "area_sqm": 180,
      "beds": 3,
      "baths": 2,
      "property_type": "apartment",
      "completion_status": "ready",
      "furnishing": "furnished",
      "payment_method": "cash",
      "parking": 1,
      "is_featured": true,
      "view_count": 42,
      "agent": { "id": 1, "name": "محمد أحمد", "phone": "01098765432" },
      "images": [
        { "id": 1, "image": "https://...", "order": 0, "is_cover": true }
      ],
      "amenities": [
        { "id": 1, "name": "مسبح" },
        { "id": 2, "name": "أمن وحراسة" }
      ]
    }
  ]
}
```

### `GET /properties/{id}/`
> Get single property detail (public)
- **Auth:** None
- **Response:** `200` full property object (same shape as above)

---

## 4. 🔍 Search (`/api/v1/search/`)

### `GET /search/`
> Search & filter properties (public)
- **Auth:** None
- **Query Params:**
  - `?q=التجمع` — text search (location, title, description)
  - `?property_type=apartment`
  - `?completion_status=ready`
  - `?min_price=1000000&max_price=5000000`
  - `?min_area=100&max_area=300`
  - `?beds=3`
  - `?furnishing=furnished`
  - `?payment_method=cash`
  - `?ordering=-price` or `?ordering=price`
- **Response:** `200` paginated property list (same shape as `/properties/`)

---

## 5. ❤️ Favorites (`/api/v1/favorites/`)

### `GET /favorites/`
> List buyer's favorite properties
- **Auth:** `Bearer <access_token>`
- **Response:** `200` list of favorited properties

### `POST /favorites/{property_id}/toggle/`
> Add or remove a property from favorites
- **Auth:** `Bearer <access_token>`
- **Response:** `201` `{ "status": "added" }` or `200` `{ "status": "removed" }`

---

## 6. 📩 Inquiries (`/api/v1/inquiries/`)

### `POST /inquiries/`
> Submit an inquiry about a property
- **Auth:** `Bearer <access_token>`
- **Body:**
```json
{
  "property": 1,
  "message": "أريد الاستفسار عن هذه الشقة"
}
```
- **Response:** `201` inquiry object

### `GET /inquiries/my/`
> List buyer's own inquiries
- **Auth:** `Bearer <access_token>`
- **Response:** `200` list of inquiries

### `GET /inquiries/{id}/`
> Get inquiry detail
- **Auth:** `Bearer <access_token>`
- **Response:** `200` inquiry object

---

## 7. 🤖 AI Survey (`/api/v1/ai/survey/`) ⭐ CORE FEATURE

### `POST /ai/survey/start/`
> Start a new AI recommendation survey (public)
- **Auth:** Optional `Bearer <access_token>`
- **Response:** `200`
```json
{
  "session_id": "a1b2c3d4-...",
  "question": {
    "id": 1,
    "key": "budget_max",
    "text": "What is your maximum budget in Egyptian pounds?",
    "question_type": "currency",
    "options": [],
    "required": true,
    "order": 1
  }
}
```

### `POST /ai/survey/answer/`
> Answer a survey question (returns next question or top 3 results)
- **Auth:** Optional `Bearer <access_token>`
- **Body:**
```json
{
  "session_id": "a1b2c3d4-...",
  "question_key": "budget_max",
  "answer": 3000000
}
```
- **Response (next question):** `200`
```json
{
  "session_id": "a1b2c3d4-...",
  "completed": false,
  "question": {
    "id": 2,
    "key": "financing_needed",
    "text": "Which payment method do you prefer?",
    "question_type": "single_choice",
    "options": ["cash", "installment", "mortgage", "any"],
    "required": true,
    "order": 2
  }
}
```
- **Response (survey complete — TOP 3 RESULTS):** `200`
```json
{
  "session_id": "a1b2c3d4-...",
  "completed": true,
  "result": {
    "session_id": "a1b2c3d4-...",
    "top_properties": [
      {
        "property": { /* full property object */ },
        "property_id": 5,
        "title": "فيلا في الشيخ زايد",
        "match_percentage": 92,
        "score": 92.0,
        "tags": ["ضمن الميزانية", "الموقع المفضل", "استلام فوري"],
        "reasons": [
          "سعر العقار يقع تماماً ضمن ميزانيتك المحددة",
          "يقع في المنطقة المفضلة لديك: الشيخ زايد",
          "الوحدة جاهزة للاستلام الفوري بدون انتظار"
        ]
      },
      { /* 2nd best match */ },
      { /* 3rd best match */ }
    ],
    "created_at": "2026-10-02T05:30:00Z"
  }
}
```

### `GET /ai/survey/{session_id}/results/`
> Retrieve results of a completed survey
- **Auth:** Optional `Bearer <access_token>`
- **Response:** `200` same result object as above

---

## 8. 📍 Locations (`/api/v1/locations/`)

### `GET /locations/`
> List all available locations (public)
- **Auth:** None
- **Response:** `200` list of location objects

---

## 9. 📞 Marketing / Contact (`/api/v1/contact/`)

### `POST /contact/lead/`
> Submit a marketing lead (public)
- **Auth:** None
- **Body:**
```json
{
  "name": "أحمد",
  "phone": "01012345678",
  "message": "أريد معرفة المزيد"
}
```
- **Response:** `201` lead object

---

## 10. 🏢 Developer Authentication (`/api/v1/developer/`)

### `POST /developer/login/`
> Login developer
- **Auth:** None
- **Body:** `{ "email": "dev@company.com", "password": "securepassword123" }`
- **Response:** `200` `{ "token": "abc123...", "user": {...} }`

### `POST /developer/logout/`
> Logout developer & delete token
- **Auth:** `Token <developer_token>`
- **Response:** `200` `{ "detail": "تم تسجيل الخروج بنجاح." }`

### `POST /developer/register/`
> Register a new developer account (Primary user gets all permissions)
- **Auth:** None
- **Body:** `{ "company_name": "الشركة العقارية", "email": "dev@company.com", "password": "securepassword123", "first_name": "...", "last_name": "..." }`
- **Response:** `201` `{ "token": "abc123...", "user": {...} }`

---

## 11. 🏢 Developer Account (`/api/v1/developer/account/`)

### `GET /developer/account/`
> Get developer account details
- **Auth:** `Token <developer_token>`
- **Response:** `200` user object

### `PUT /developer/account/`
> Update developer profile
- **Auth:** `Token <developer_token>`
- **Body:** `{ "first_name": "...", "email": "...", "current_password": "...", "new_password": "..." }`
- **Response:** `200` updated user object

### `DELETE /developer/account/`
> Delete developer account (Only Primary Account Owner)
- **Auth:** `Token <developer_token>`
- **Response:** `204` No content

---

## 12. 👥 Developer Team (`/api/v1/developer/team/`)

### `GET /developer/team/`
> List team members
- **Auth:** `Token <developer_token>`
- **Response:** `200` Paginated list of team members with their permissions

### `POST /developer/team/invite/`
> Invite a new team member
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_team`
- **Body:** `{ "email": "...", "first_name": "...", "last_name": "...", "password": "...", "permission_ids": [1, 2] }`
- **Response:** `201` Created team member object

### `PUT /developer/team/{id}/`
> Update team member roles/status
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_team`
- **Body:** `{ "status": "active", "permission_ids": [1, 2, 3] }`
- **Response:** `200` Updated team member

### `DELETE /developer/team/{id}/`
> Soft-delete team member (deactivates account)
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_team`
- **Response:** `204` No content

---

## 13. 📊 Developer Projects (`/api/v1/developer/projects/`)

### `GET /developer/projects/`
> List developer's projects
- **Auth:** `Token <developer_token>`
- **Query Params:** `?status=active&project_type=residential&search=Nile`
- **Response:** `200` Paginated projects

### `POST /developer/projects/`
> Create a new project (Multipart Form)
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_projects`
- **Response:** `201` Full project detail

### `GET /developer/projects/{id}/`
> Get project detail
- **Auth:** `Token <developer_token>`
- **Response:** `200` Full project detail with gallery

### `PUT /developer/projects/{id}/`
> Update project (Multipart Form)
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_projects`
- **Response:** `200` Updated project detail

### `DELETE /developer/projects/{id}/`
> Delete project
- **Auth:** `Token <developer_token>`
- **Permission Required:** `manage_projects`
- **Response:** `204` No content

### `GET /developer/projects/{id}/stats/`
> Get project statistics
- **Auth:** `Token <developer_token>`
- **Response:** `200` `{ "gallery_count": 5, "marketing_leads": 12, "total_views": 340 }`

---

## 14. 📈 Developer Dashboard (`/api/v1/developer/dashboard/`)

### `GET /developer/dashboard/overview/`
> Get dashboard statistics
- **Auth:** `Token <developer_token>`
- **Permission Required:** `view_leads`
- **Response:** `200`
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

## 15. 📋 Developer Leads (`/api/v1/developer/leads/`)

### `GET /developer/leads/`
> List all leads for this developer
- **Auth:** `Token <developer_token>`
- **Permission Required:** `view_leads`
- **Query Params:** `?type=marketing&project_id=1&source=facebook&rating=hot&status=new`

### `GET /developer/leads/{id}/`
> Get lead detail
- **Auth:** `Token <developer_token>`
- **Permission Required:** `view_leads`

### `PATCH /developer/leads/{id}/`
> Update lead status & rating
- **Auth:** `Token <developer_token>`
- **Permission Required:** `rate_leads`
- **Body:** `{ "status": "contacted", "rating": "hot" }`

### `GET /developer/leads/export/`
> Export leads as CSV file
- **Auth:** `Token <developer_token>`
- **Permission Required:** `export_excel`
- **Response:** `200` `.csv` file download

---

## 16. 🔐 Permission System (Developer Dashboard)

| ID | Codename | Arabic Name | Controls |
|----|----------|-------------|----------|
| 1 | `view_leads` | عرض العملاء المحتملين | View leads list, dashboard overview |
| 2 | `rate_leads` | تقييم العملاء المحتملين | Update lead status/rating |
| 3 | `export_excel` | تصدير الإكسيل | Export leads CSV |
| 4 | `manage_team` | إدارة الفريق | Invite/edit/remove team members |
| 5 | `manage_projects` | إدارة المشاريع | Create/edit/delete projects |

> **Note**: The Primary Account Owner gets all permissions automatically. Team members get permissions assigned via `permission_ids` array when invited or updated.

---

## 📚 Interactive API Documentation

When the server is running, you can also access:
- **Swagger UI:** [http://localhost:8000/api/docs/swagger-ui/](http://localhost:8000/api/docs/swagger-ui/)
- **ReDoc:** [http://localhost:8000/api/docs/redoc/](http://localhost:8000/api/docs/redoc/)
- **Raw OpenAPI Schema:** [http://localhost:8000/api/docs/schema/](http://localhost:8000/api/docs/schema/)

---

## ⚡ Quick Setup for Frontend Developer

```javascript
// src/api/client.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

// Automatically attach auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;

// Usage:
// const { data } = await api.get('/properties/');
// const { data } = await api.post('/ai/survey/start/');
```
