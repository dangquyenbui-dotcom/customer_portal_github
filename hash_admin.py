# hash_admin.py
from werkzeug.security import generate_password_hash

# Use a VERY simple password just for testing
my_password = "2L20o'£>+n,E[V8" 

new_hash = generate_password_hash(my_password)

print("\n" + "="*50)
print("COPY THIS HASH for the password 'admin':")
print("\n" + new_hash)
print("\n" + "="*50)