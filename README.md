# IChatBox
IChatBox is a multi-website chatbox platform designed to be embedded into external websites via a license key. It provides a tenant admin UI to respond to chats in real time, and a super admin UI to manage all tenants.

## Specs
- `docs/SPECS.md`
- `docs/PACKAGES.md`

## Docker Compose (Recommended)
Run locally with PostgreSQL + Redis:
```bash
docker compose up --build
```

URLs:
- Tenant admin login: `http://127.0.0.1:8002/admin/login/`
- Tenant live chat: `http://127.0.0.1:8002/admin/chat/`
- Tenant widget settings: `http://127.0.0.1:8002/admin/profile/`
- Super admin (Django Admin): `http://127.0.0.1:8002/supper-admin/`

Database in compose uses PostgreSQL (persistent volume `postgres_data`).

## Run Without Docker (SQLite)
### 1. Clone the repository
```bash
git clone https://github.com/yourusername/IChatBox.git
cd IChatBox
```
### 2. Set up a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate # On Windows, use `venv\Scripts\activate`
```
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
### 4. Environment variables
Create a `.env` file in the repo root:

```bash
SECRET_KEY=change-me
DEBUG=True
```
### 5. Apply migrations
```bash
python manage.py migrate
```
### 6. Create a superuser (optional)
```bash
python manage.py createsuperuser
```
### 7. Run the development server
```bash
python manage.py runserver
```
### 8. Open the admin UI
- Tenant admin: `http://127.0.0.1:8002/admin/login/`
- Super admin: `http://127.0.0.1:8002/supper-admin/`

## Notes
- Widget endpoints are exposed under `/admin/widget-config/` and `/admin/widget-history/` and are designed to be embedded on external domains (CORS enabled).
- WebSocket endpoints are exposed under `/ws/user/chat/` (visitor) and `/ws/admin/chat/` (tenant admin).

## Widget Integration Snippet
You can integrate without writing inline JavaScript by using `data-*` attributes:
```html
<script
  src="https://yourdomain.com/static/ichatbox.js"
  data-api-key="YOUR_PUBLIC_LICENSE_KEY_UUID"
  data-username="Guest_123"
  defer>
</script>
```
Recommended attribute name is `data-widget-key` (aliases supported: `data-license-key`, `data-api-key`).
