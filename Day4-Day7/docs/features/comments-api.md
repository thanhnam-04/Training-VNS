# Comments API

Base path: /api/posts

## GET /{post_id}/comments

Mo ta:

- Lay danh sach comment cua mot post

## POST /{post_id}/comments

Mo ta:

- Tao comment moi
- Yeu cau dang nhap

Request body:

```json
{
  "content": "string"
}
```

## DELETE /{post_id}/comments/{comment_id}

Mo ta:

- Xoa comment
- Cho phep author hoac admin
