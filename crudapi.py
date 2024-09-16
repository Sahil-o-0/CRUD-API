from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
import mysql.connector

app1 = FastAPI()

class User(BaseModel):
    name: str
    email: EmailStr

    @field_validator('email')
    def check_email_domain(cls, v):
        if not v.endswith("@skill-mine.com"):
            raise ValueError("Email domain must be @skill-mine.com")
        return v

class UserSearchRequest(BaseModel):
    name: str

class UpdateUser(BaseModel):
    name: str
    email: EmailStr

    @field_validator('email')
    def check_email_domain(cls, v):
        if not v.endswith("@skill-mine.com"):
            raise ValueError("Email domain must be @skill-mine.com")
        return v

def get_db_connection():
    conn = mysql.connector.connect(
        host="127.0.0.1",
        user="root",
        password="Sahil1234",
        database="datatry1"
    )
    return conn


@app1.post("/users")
async def create_user(user: User):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.callproc('check_email_exists', [user.email])
        for result in cursor.stored_results():
            if result.fetchone() is not None:
                raise HTTPException(status_code=400, detail="Email address already exists")
            
        cursor.callproc('AddUser', [user.name, user.email]) 
        conn.commit()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Database error: " + str(e))  
    finally:
        cursor.close()
        conn.close()

    return {"message": "User created successfully"}


@app1.get("/users")
async def read_users():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.callproc('GetAllUsers') 
    for result in cursor.stored_results():
        users = result.fetchall()

    cursor.close()
    conn.close()

    return users


@app1.get("/users/{user_id}")
async def read_user_by_id(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.callproc('GetUserById', [user_id])
    for result in cursor.stored_results():
        user = result.fetchone()

    cursor.close()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@app1.put("/users/update/{user_id}")
async def update_user(user_id: int, user: UpdateUser):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.callproc('GetUserById', [user_id])
    existing_user = None
    for result in cursor.stored_results():
        existing_user = result.fetchone()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.callproc('UpdateUser', [user_id, user.name, user.email])  
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "User updated successfully"}


@app1.delete("/users/delete/{user_id}")
async def delete_user(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.callproc('GetUserById', [user_id])
    existing_user = None
    for result in cursor.stored_results():
        existing_user = result.fetchone()

    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    cursor.callproc('DeleteUser', [user_id]) 
    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "User deleted successfully"}

@app1.post("/users/search")
async def search_user_by_name(user_search_request: UserSearchRequest):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.callproc('SearchUserByName', [user_search_request.name])
        for result in cursor.stored_results():
            users = result.fetchall()
        cursor.close()
        conn.close()
        if not users:
            raise HTTPException(status_code=404, detail="User not found") 
        return {"users": users}
    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
