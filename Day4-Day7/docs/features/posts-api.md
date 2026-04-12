# Posts API

Base path: /api/posts

## GET /

Mo ta:

- Lay danh sach post da publish

Query:

- skip (mac dinh 0)
- limit (mac dinh 10 hoac 20 tuy service)

## POST /

Mo ta:

- Tao post moi

Header:

- Authorization: Bearer <access_token>

Request body:

```json
{
  "title": "string",
  "content": "string",
  "image_url": "string | null",
  "is_published": true
}
```

## PUT /{post_id}

Mo ta:

- Cap nhat post
- Cho phep owner hoac admin

## DELETE /{post_id}

Mo ta:

- Xoa post
- Cho phep owner hoac admin

## POST /upload-image

Mo ta:

- Upload image cho post
- Yeu cau dang nhap
