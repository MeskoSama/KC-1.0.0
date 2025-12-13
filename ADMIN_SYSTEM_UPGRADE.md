# 🔐 Admin System Upgrade - Complete Documentation

## ✅ Mission Completed

Upgraded from hardcoded admin usernames to a flexible role-based permission system without breaking existing features.

---

## 📋 What Changed

### 1. **Database Schema Updates**

**User Model - New Fields:**
```python
role: str = "user"  # user, admin, superadmin
banned: bool = False
```

**Migration Applied:**
- ✅ All 10 existing users migrated
- ✅ 2 users (TestMiner, meskop) set to "admin" role
- ✅ 8 regular users with "user" role
- ✅ All users have `banned: false` by default

---

### 2. **Authentication Changes**

**JWT Token Updates:**
```python
# OLD: Token included is_admin (boolean)
payload = {"user_id": ..., "username": ..., "is_admin": True/False}

# NEW: Token includes role (string)
payload = {"user_id": ..., "username": ..., "role": "user|admin|superadmin"}
```

**Login Response:**
```json
{
  "token": "...",
  "user": {
    "id": "...",
    "username": "meskop",
    "role": "admin",
    "is_admin": true  // Kept for backward compatibility
  }
}
```

---

### 3. **Authorization Dependencies**

**New Functions:**

```python
# Any authenticated user
async def require_user(user: dict = Depends(get_current_user))

# Admin or superadmin only
async def require_admin(user: dict = Depends(get_current_user))

# Superadmin only
async def require_superadmin(user: dict = Depends(get_current_user))
```

**Features:**
- ✅ Automatic ban check on login
- ✅ Banned users receive 403 error
- ✅ Role-based access control

---

### 4. **Hardcoded Admin List Removed**

**Before:**
```python
ADMIN_USERNAMES = ["TestMiner", "meskop"]  # ❌ Hardcoded
```

**After:**
```python
# ✅ No hardcoded list - roles stored in database
```

---

## 🎯 New Admin API Endpoints

### **1. Ban/Unban Users**
**Endpoint:** `POST /api/admin/users/ban`  
**Required Role:** Admin or Superadmin  
**Request Body:**
```json
{
  "user_id": "abc-123",
  "banned": true
}
```

**Protection:**
- ❌ Cannot ban superadmins
- ❌ Regular admins cannot ban other admins (only superadmins can)

---

### **2. Delete User**
**Endpoint:** `DELETE /api/admin/users/{user_id}`  
**Required Role:** Superadmin only  

**Protection:**
- ❌ Cannot delete superadmins (even by other superadmins)

---

### **3. Change User Role**
**Endpoint:** `PUT /api/admin/users/role`  
**Required Role:** Superadmin only  
**Request Body:**
```json
{
  "user_id": "abc-123",
  "new_role": "admin"
}
```

**Valid Roles:** `user`, `admin`, `superadmin`

---

### **4. Change User Currency**
**Endpoint:** `PUT /api/admin/users/currency`  
**Required Role:** Admin or Superadmin  
**Request Body:**
```json
{
  "user_id": "abc-123",
  "new_currency_type": "GRP"
}
```

**Valid Currencies:** `NIM`, `GRP`, `VDD`, `KKD`

---

### **5. Update User Balance**
**Endpoint:** `PUT /api/admin/user/balance`  
**Required Role:** Admin or Superadmin (using existing endpoint)  
**Request Body:**
```json
{
  "user_id": "abc-123",
  "currency": "GRP",
  "amount": 10000.0,
  "operation": "add"
}
```

**Operations:** `add` (increase) or `set` (replace)

---

### **6. List All Users**
**Endpoint:** `GET /api/admin/users/list?skip=0&limit=50`  
**Required Role:** Admin or Superadmin  

**Response:**
```json
{
  "users": [
    {
      "id": "...",
      "minecraft_username": "Player1",
      "role": "user",
      "banned": false,
      "balances": {...},
      // password_hash excluded for security
    }
  ],
  "total": 10,
  "skip": 0,
  "limit": 50
}
```

---

### **7. View Admin Logs**
**Endpoint:** `GET /api/admin/logs?limit=100`  
**Required Role:** Admin or Superadmin  

**Response:**
```json
{
  "logs": [
    {
      "id": "...",
      "admin_username": "meskop",
      "action": "User banned",
      "details": "User Player1 (ID: abc-123)",
      "timestamp": "2024-11-28T12:00:00Z"
    }
  ],
  "total": 5
}
```

---

## 🔒 Security Features

### **1. Role Hierarchy**
```
superadmin > admin > user
```

### **2. Protection Rules**

| Action | User | Admin | Superadmin |
|--------|------|-------|------------|
| View own data | ✅ | ✅ | ✅ |
| Ban regular users | ❌ | ✅ | ✅ |
| Ban admins | ❌ | ❌ | ✅ |
| Ban superadmins | ❌ | ❌ | ❌ |
| Delete users | ❌ | ❌ | ✅ |
| Delete superadmins | ❌ | ❌ | ❌ |
| Change user roles | ❌ | ❌ | ✅ |
| Change currencies | ❌ | ✅ | ✅ |
| Update balances | ❌ | ✅ | ✅ |
| View admin logs | ❌ | ✅ | ✅ |

### **3. Audit Trail**
- ✅ All admin actions logged to `admin_logs` collection
- ✅ Includes: admin username, action type, details, timestamp
- ✅ Cannot be edited (append-only)

### **4. Ban System**
- ✅ Banned users rejected at login with 403 error
- ✅ Banned users rejected at every API call
- ✅ Ban status checked in `get_current_user()` dependency

---

## 📁 Files Modified

### **1. `/app/backend/server.py`**
**Changes:**
- Removed `ADMIN_USERNAMES` hardcoded list (line 33)
- Updated `User` model with `role` and `banned` fields (lines 137-139)
- Added new Pydantic models: `UserRoleUpdate`, `UserBanUpdate`, `UserCurrencyUpdate` (lines 237-247)
- Updated `create_jwt_token()` to use role instead of is_admin (line 256)
- Enhanced `get_current_user()` with ban check (lines 265-277)
- Added new dependencies: `require_user`, `require_admin`, `require_superadmin` (lines 279-297)
- Updated `/auth/register` to set role="user" by default (lines 312-339)
- Updated `/auth/login` to check ban status and use role (lines 341-365)
- Added 6 new admin endpoints (lines 1817-1968)

### **2. `/app/backend/migrate_to_roles.py` (NEW)**
**Purpose:** One-time migration script
- Adds `role` field to existing users
- Adds `banned` field to existing users
- Converts old admin users to admin role
- Run once before deploying

### **3. `/app/ADMIN_SYSTEM_UPGRADE.md` (NEW)**
**Purpose:** This documentation file

---

## 🚀 How to Use

### **For Superadmins:**

**1. Promote User to Admin:**
```bash
curl -X PUT https://your-api.com/api/admin/users/role \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "new_role": "admin"}'
```

**2. Create Superadmin:**
```bash
# Manually update in MongoDB (for security):
db.users.updateOne(
  {minecraft_username: "YourUsername"},
  {$set: {role: "superadmin"}}
)
```

**3. Delete User:**
```bash
curl -X DELETE https://your-api.com/api/admin/users/user-123 \
  -H "Authorization: Bearer YOUR_SUPERADMIN_TOKEN"
```

### **For Admins:**

**1. Ban User:**
```bash
curl -X POST https://your-api.com/api/admin/users/ban \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "banned": true}'
```

**2. Change User Currency:**
```bash
curl -X PUT https://your-api.com/api/admin/users/currency \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user-123", "new_currency_type": "GRP"}'
```

**3. Update Balance:**
```bash
curl -X PUT https://your-api.com/api/admin/user/balance \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "currency": "GRP",
    "amount": 10000.0,
    "operation": "add"
  }'
```

**4. List Users:**
```bash
curl https://your-api.com/api/admin/users/list?skip=0&limit=50 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**5. View Logs:**
```bash
curl https://your-api.com/api/admin/logs?limit=100 \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

---

## 🎯 Current Admin Users

After migration:
- **TestMiner** - role: `admin`
- **meskop** - role: `admin`

To create a superadmin, manually update MongoDB:
```javascript
db.users.updateOne(
  {minecraft_username: "meskop"},
  {$set: {role: "superadmin"}}
)
```

---

## ✅ Safety Checklist

- ✅ Admins cannot edit source code (all operations via database)
- ✅ MongoDB is source of truth for permissions
- ✅ No hardcoded admin lists
- ✅ Cannot ban/delete superadmins
- ✅ Regular admins cannot ban other admins
- ✅ All admin actions logged
- ✅ Banned users blocked at authentication
- ✅ Role-based JWT tokens
- ✅ Password hashes excluded from API responses
- ✅ Existing features preserved (backward compatible)

---

## 🔄 Backward Compatibility

**Maintained:**
- ✅ `is_admin` field still returned in API responses (derived from role)
- ✅ Old JWT tokens still work (until expiry)
- ✅ Existing endpoints unchanged
- ✅ Database migrations non-destructive

**Deprecated:**
- ⚠️ `is_admin` boolean field (use `role` instead)
- ⚠️ `get_admin_user()` function (use `require_admin` instead)

---

## 📊 Database Collections

### **users**
```javascript
{
  "id": "abc-123",
  "minecraft_username": "Player1",
  "role": "user",  // NEW
  "banned": false,  // NEW
  "is_admin": false,  // DEPRECATED
  "balances": {...},
  "portfolio": {...},
  // ... other fields
}
```

### **admin_logs** (NEW)
```javascript
{
  "id": "log-456",
  "admin_username": "meskop",
  "action": "User banned",
  "details": "User Player1 (ID: abc-123)",
  "timestamp": "2024-11-28T12:00:00Z"
}
```

---

## 🎉 Mission Status: COMPLETE

All requirements implemented:
- ✅ User roles system (user, admin, superadmin)
- ✅ Banned field added
- ✅ JWT tokens include role
- ✅ Reusable authorization dependencies
- ✅ Admin endpoints (ban, delete, role change, balance, currency)
- ✅ Safety: admins operate via database only
- ✅ MongoDB as source of truth
- ✅ Migration script provided and executed
- ✅ No hardcoded admin logic
- ✅ All existing features preserved

**Ready for production use!** 🚀
