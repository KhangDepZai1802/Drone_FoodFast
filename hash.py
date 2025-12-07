from passlib.context import CryptContext

# Cấu hình giống hệt file main.py của bạn
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Kiểm tra thử hash cũ trong file SQL xem có đúng là 123456 không
old_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4h/j.8h9.e"
print(f"Hash cũ có khớp '123456' không? -> {pwd_context.verify('123456', old_hash)}")

# 2. Tạo hash mới
new_hash = pwd_context.hash("123456")
print(f"Hash MỚI cho '123456' là: {new_hash}")