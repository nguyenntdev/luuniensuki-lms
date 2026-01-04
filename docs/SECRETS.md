# Secrets va cau hinh nhay cam

Tat ca secrets/credentials nen duoc luu trong `.env.prod` (khong commit) va TLS key trong `certbot/conf/`.

## 1) File `.env.prod`

Luu o goc project. Nen set quyen file:

```bash
chmod 600 .env.prod
```

### Secrets bat buoc

- `POSTGRES_PASSWORD` - mat khau DB
- `JWT_SECRET_KEY` - khoa ky JWT

### Cau hinh lien quan

- `POSTGRES_DB`, `POSTGRES_USER` - thong tin DB
- `JWT_ALGORITHM` - mac dinh `HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- `LOG_LEVEL`, `INTERACTION_TOLERANCE_MULTIPLIER`
- `NEXT_PUBLIC_API_BASE_URL` - de trong cho production (same-origin)
- `MODEL_BASE_URL` - mac dinh `/assets/models`

### Tao gia tri ngau nhien

```bash
# DB password
openssl rand -hex 16

# JWT secret
openssl rand -hex 32
```

### Mau `.env.prod`

```bash
POSTGRES_DB=luuniensuki
POSTGRES_USER=postgres
POSTGRES_PASSWORD=CHANGE_ME

JWT_SECRET_KEY=CHANGE_ME
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

LOG_LEVEL=info
INTERACTION_TOLERANCE_MULTIPLIER=1.25

NEXT_PUBLIC_API_BASE_URL=
MODEL_BASE_URL=/assets/models
```

## 2) TLS certificates

- Cert va private key duoc luu trong `certbot/conf/live/cuudinh.histolab.icu/`.
- Khong copy key ra ngoai neu khong can thiet.
- Khi cap nhat cert, nho restart nginx container.

## 3) Luu y

- Tuyet doi khong commit file `.env.prod` len git.
- Neu can chia se secrets, dung password manager/secret manager.
