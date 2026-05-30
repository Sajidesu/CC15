from fastapi import FastAPI, Depends, HTTPException, status
import mysql.connector
import random
import string
from datetime import datetime
from typing import Optional

from database import get_db
from schemas import EmployeeLogin, AdminLogin, UserSignUp, ClockAction

app = FastAPI(title="General Attendance API")

# ==========================================
# CACHE MEMORY (List of Tuples)
# ==========================================
attendance_cache = []
cache_needs_refresh = True 

# ==========================================
# HELPER: ID GENERATOR
# ==========================================
def generate_unique_id(role: str, cursor) -> str:
    prefix = "ADM" if role.lower() == "admin" else "EMP"
    while True:
        random_suffix = ''.join(random.choices(string.digits, k=4))
        new_id = f"{prefix}-{random_suffix}"
        
        cursor.execute("SELECT special_id FROM users WHERE special_id = %s", (new_id,))
        if not cursor.fetchone():
            return new_id 

# ==========================================
# 1. AUTHENTICATION & REGISTRATION
# ==========================================
@app.post("/api/signup")
def register_user(user: UserSignUp, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor()
    try:
        generated_id = generate_unique_id(user.role, cursor)

        final_password = user.password if user.role.lower() == "admin" else None

        user_query = "INSERT INTO users (special_id, first_name, password, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(user_query, (generated_id, user.firstName, final_password, user.role))
        new_user_id = cursor.lastrowid

        info_query = """
            INSERT INTO employee_info (user_id, first_name, last_name, email, phone_number, birth_date, category, department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(info_query, (
            new_user_id, 
            user.firstName, 
            user.lastName, 
            user.email, 
            user.phoneNumber, 
            user.dateOfBirth, 
            user.category, 
            user.department
        ))
        db.commit()
        
        return {
            "success": True, 
            "message": "User verified and stored in database.",
            "assigned_id": generated_id 
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/api/login/employee")
def login_employee(user_data: EmployeeLogin, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT user_id, special_id, first_name, role FROM users WHERE special_id = %s AND role = 'employee'"
        cursor.execute(query, (user_data.specialId,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Special ID")
        return {"success": True, "message": "Login successful", "user": user}
    finally:
        cursor.close()

@app.post("/api/login/admin")
def login_admin(admin_data: AdminLogin, db: mysql.connector.MySQLConnection = Depends(get_db)):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT user_id, special_id, first_name, role 
            FROM users 
            WHERE special_id = %s AND CAST(password AS CHAR) = %s AND role = 'admin'
        """
        cursor.execute(query, (admin_data.specialId, admin_data.password))
        admin = cursor.fetchone()
        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Admin Credentials")
        return {"success": True, "message": "Admin login successful", "user": admin}
    finally:
        cursor.close()

# ==========================================
# 2. EMPLOYEE TIME TRACKING
# ==========================================
@app.post("/api/attendance/clock")
def clock_in_out(action: ClockAction, db: mysql.connector.MySQLConnection = Depends(get_db)):
    global cache_needs_refresh 
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.user_id, i.first_name, i.last_name, i.department, i.category
            FROM users u
            JOIN employee_info i ON u.user_id = i.user_id
            WHERE u.special_id = %s
        """, (action.specialId,))
        employee = cursor.fetchone()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        cursor.execute("""
            SELECT log_id, time_out FROM employee_logs 
            WHERE user_id = %s ORDER BY time_in DESC LIMIT 1
        """, (employee['user_id'],))
        last_record = cursor.fetchone()
        current_time = datetime.now()

        if not last_record or last_record['time_out'] is not None:
            insert_query = """
                INSERT INTO employee_logs (user_id, first_name, last_name, department, log_date, time_in, category) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                employee['user_id'], employee['first_name'], employee['last_name'],
                employee['department'], current_time.date(), current_time, employee['category']
            ))
            db.commit()
            cache_needs_refresh = True 
            return {"success": True, "action": "timed in", "message": f"{employee['first_name']} has successfully timed in"}

        elif last_record['time_out'] is None:
            cursor.execute("UPDATE employee_logs SET time_out = %s WHERE log_id = %s", (current_time, last_record['log_id']))
            db.commit()
            cache_needs_refresh = True
            return {"success": True, "action": "timed out", "message": f"{employee['first_name']} has successfully timed out"}
    finally:
        cursor.close()

# ==========================================
# 3. ADMIN DASHBOARD (CACHED WITH TUPLES)
# ==========================================
@app.get("/api/admin/attendance")
def get_attendance(searchQuery: Optional[str] = None, filterDate: Optional[str] = None, db: mysql.connector.MySQLConnection = Depends(get_db)):
    global attendance_cache
    global cache_needs_refresh

    data_source = "Python List of Tuples"

    if cache_needs_refresh:
        data_source = "MySQL Database"
        cursor = db.cursor() 
        try:
            query = """
                SELECT l.first_name, l.last_name, u.special_id, l.department, l.category, 
                       l.log_date, l.time_in, l.time_out, l.hours_worked, l.status
                FROM employee_logs l
                JOIN users u ON l.user_id = u.user_id
                ORDER BY l.log_date DESC, l.time_in DESC
            """
            cursor.execute(query)
            attendance_cache = cursor.fetchall()
            cache_needs_refresh = False 
        finally:
            cursor.close()

    filtered_data = attendance_cache

    if searchQuery:
        search = searchQuery.lower()
        filtered_data = [
            row for row in filtered_data 
            if search in str(row[0]).lower() 
            or search in str(row[1]).lower() 
            or search in str(row[2]).lower()
        ]
        
    if filterDate:
        filtered_data = [row for row in filtered_data if str(row[5]) == filterDate]

    formatted_data = [
        {
            "first_name": row[0], "last_name": row[1], "special_id": row[2],
            "department": row[3], "category": row[4], "log_date": row[5],
            "time_in": row[6], "time_out": row[7], "hours_worked": row[8], "status": row[9]
        }
        for row in filtered_data
    ]

    return {
        "success": True, 
        "source": data_source, 
        "data": formatted_data
    }
