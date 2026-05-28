from fastapi import FastAPI, Depends, HTTPException, status
import mysql.connector
from datetime import datetime
from typing import Optional
from database import get_db
from schemas import EmployeeLogin, AdminLogin, UserSignUp, ClockAction

app = FastAPI(title="General Attendance API")

# ==========================================
# 1. AUTHENTICATION & REGISTRATION ROUTES
# ==========================================

@app.post("/api/signup")
def register_user(
    user: UserSignUp, 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor()
    try:
        # 1. Check if special_id already exists
        cursor.execute("SELECT * FROM users WHERE special_id = %s", (user.specialId,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="User with this Special ID already exists")

        # 2. Insert into `users` table first
        user_query = """
            INSERT INTO users (special_id, first_name, password, role) 
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(user_query, (user.specialId, user.firstName, user.password, user.role))
        
        # Grab the newly generated user_id
        new_user_id = cursor.lastrowid

        # 3. Insert the rest into `employee_info` table
        info_query = """
            INSERT INTO employee_info (user_id, first_name, last_name, email, category, department)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(info_query, (
            new_user_id, user.firstName, user.lastName, 
            user.email, user.category, user.department
        ))
        
        db.commit()
        return {"success": True, "message": "User verified and stored in database."}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()

@app.post("/api/login/employee")
def login_employee(
    user_data: EmployeeLogin, 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        query = "SELECT user_id, special_id, first_name, role FROM users WHERE first_name = %s AND special_id = %s AND role = 'employee'"
        cursor.execute(query, (user_data.firstName, user_data.specialId))
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid First Name or Special ID")
        return {"success": True, "message": "Login successful", "user": user}
    finally:
        cursor.close()

@app.post("/api/login/admin")
def login_admin(
    admin_data: AdminLogin, 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        # We use CAST because the password column is VARBINARY
        query = """
            SELECT user_id, special_id, first_name, role 
            FROM users 
            WHERE first_name = %s AND special_id = %s AND CAST(password AS CHAR) = %s AND role = 'admin'
        """
        cursor.execute(query, (admin_data.firstName, admin_data.specialId, admin_data.password))
        admin = cursor.fetchone()

        if not admin:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Admin Credentials")
        return {"success": True, "message": "Admin login successful", "user": admin}
    finally:
        cursor.close()

# ==========================================
# 2. EMPLOYEE TIME TRACKING ROUTES
# ==========================================

@app.post("/api/attendance/clock")
def clock_in_out(
    action: ClockAction, 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        # 1. Get the user's full details needed for the logs
        cursor.execute("""
            SELECT u.user_id, i.first_name, i.last_name, i.department, i.category
            FROM users u
            JOIN employee_info i ON u.user_id = i.user_id
            WHERE u.special_id = %s
        """, (action.specialId,))
        employee = cursor.fetchone()

        if not employee:
            raise HTTPException(status_code=404, detail="Employee not found")

        # 2. Find the user's most recent log entry
        cursor.execute("""
            SELECT log_id, time_out FROM employee_logs 
            WHERE user_id = %s ORDER BY time_in DESC LIMIT 1
        """, (employee['user_id'],))
        last_record = cursor.fetchone()

        current_time = datetime.now()

        # Logic: Time IN
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
            return {"success": True, "action": "timed in", "message": f"{employee['first_name']} has successfully timed in"}

        # Logic: Time OUT
        elif last_record['time_out'] is None:
            cursor.execute("""
                UPDATE employee_logs SET time_out = %s WHERE log_id = %s
            """, (current_time, last_record['log_id']))
            db.commit()
            return {"success": True, "action": "timed out", "message": f"{employee['first_name']} has successfully timed out"}

    finally:
        cursor.close()

# ==========================================
# 3. ADMIN DASHBOARD ROUTES
# ==========================================

@app.get("/api/admin/attendance")
def get_attendance(
    searchQuery: Optional[str] = None, 
    filterDate: Optional[str] = None, 
    db: mysql.connector.MySQLConnection = Depends(get_db)
):
    cursor = db.cursor(dictionary=True)
    try:
        query = """
            SELECT l.first_name, l.last_name, u.special_id, l.department, l.category, 
                   l.log_date, l.time_in, l.time_out, l.hours_worked, l.status
            FROM employee_logs l
            JOIN users u ON l.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        if searchQuery:
            query += " AND (l.first_name LIKE %s OR l.last_name LIKE %s OR u.special_id = %s)"
            params.extend([f"%{searchQuery}%", f"%{searchQuery}%", searchQuery])
        
        if filterDate:
            query += " AND l.log_date = %s"
            params.append(filterDate)
            
        query += " ORDER BY l.log_date DESC, l.time_in DESC"

        cursor.execute(query, tuple(params))
        records = cursor.fetchall()

        return {"success": True, "data": records}
    finally:
        cursor.close()