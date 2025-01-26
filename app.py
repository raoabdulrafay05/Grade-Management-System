from flask import Flask, render_template, request, redirect, url_for, session, flash
import pandas as pd
import json

app = Flask(_name_)
app.secret_key = '123'

# Store users in a dictionary (in a real app, use a database)
users = {
    "u20230573@giki.edu.pk": {"password": "1234", "name": "Default User"}
}

@app.route('/')
def index():
    return render_template('index.html', error=None)

@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    
    # Basic validation
    if not name or not email or not password:
        return render_template('index.html', error="All fields are required.")
    
    if password != confirm_password:
        return render_template('index.html', error="Passwords do not match.")
    
    if email in users:
        return render_template('index.html', error="Email already exists.")
    
    # Store user credentials
    users[email] = {
        "password": password,
        "name": name
    }
    
    # Redirect to login with success message
   
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():

    email = request.form['email']
    password = request.form['password']
    
    # Check if user exists and password matches
    if email in users and users[email]['password'] == password:
        session['logged_in'] = True
        session['user_email'] = email
        session['user_name'] = users[email]['name']
        return redirect(url_for('main_menu'))
    else:
        return render_template('index.html', error="Invalid login credentials.")
    

@app.route('/main_menu')
def main_menu():
    if 'logged_in' not in session:
        return redirect(url_for('index'))
    
    # Get data from session if it exists
    data = None
    if 'data' in session:
        data = pd.DataFrame(session['data']).to_dict('records')
    
    return render_template('main_menu.html', data=data, user_name=session.get('user_name', 'User'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file part", "error")
            return redirect(url_for('upload'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash("No selected file", "error")
            return redirect(url_for('upload'))
        
        if file and file.filename.endswith('.csv'):
            try:
                # Read the CSV file into a DataFrame
                df = pd.read_csv(file)
                
                # Convert DataFrame to a format that can be stored in session
                session['data'] = df.to_dict('records')
                
                # Store column names separately
                session['columns'] = list(df.columns)
                
                flash("File uploaded successfully!", "success")
                return redirect(url_for('main_menu'))
                
            except Exception as e:
                flash(f"Error processing file: {str(e)}", "error")
                return redirect(url_for('upload'))
    
    return render_template('upload.html')

@app.route('/create', methods=['GET', 'POST'])
def create():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        student_name = request.form['name'].strip()
        marks_input = request.form['marks']
        
        try:
            student_marks = float(marks_input)
            if student_marks < 0 or student_marks > 100:
                raise ValueError("Marks must be between 0 and 100.")
            
            # Get existing data or create new list
            data = session.get('data', [])
            
            # Add new record
            data.append({"Name": student_name, "Marks": student_marks})
            
            # Update session
            session['data'] = data
            
            flash("Student record added successfully!", "success")
            return redirect(url_for('main_menu'))
            
        except ValueError as e:
            flash(f"Invalid input: {str(e)}", "error")
    
    return render_template('create.html')

@app.route('/apply_absolute_grading')
def apply_absolute_grading():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    if 'data' not in session or not session['data']:
        flash("No data available to apply grading. Please add records first.", "error")
        return redirect(url_for('main_menu'))
    
    try:
        df = pd.DataFrame(session['data'])
        df['Grade'] = pd.cut(
            df['Marks'],
            bins=[0, 50, 60, 70, 80, 100],
            labels=['F', 'D', 'C', 'B', 'A'],
            include_lowest=True
        )
        
        # Update session with new data
        session['data'] = df.to_dict('records')
        flash("Absolute grading applied successfully!", "success")
        
    except Exception as e:
        flash(f"Error applying grading: {str(e)}", "error")
    
    return redirect(url_for('main_menu'))

@app.route('/apply_relative_grading')
def apply_relative_grading():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    if 'data' not in session or not session['data']:
        flash("No data available to apply grading. Please add records first.", "error")
        return redirect(url_for('main_menu'))
    
    try:
        df = pd.DataFrame(session['data'])
        df['Grade'] = pd.qcut(df['Marks'], q=5, labels=['F', 'D', 'C', 'B', 'A'])
        
        # Update session with new data
        session['data'] = df.to_dict('records')
        flash("Relative grading applied successfully!", "success")
        
    except Exception as e:
        flash(f"Error applying grading: {str(e)}", "error")
    
    return redirect(url_for('main_menu'))

@app.route('/save_grades')
def save_grades():
    if 'logged_in' not in session:
        return redirect(url_for('index'))

    if 'data' not in session or not session['data']:
        flash("No data available to save. Please add records first.", "error")
        return redirect(url_for('main_menu'))
    
    try:
        df = pd.DataFrame(session['data'])
        
        # Print the columns to debug
        print("Available columns:", df.columns.tolist())
        
        # Check and standardize column names
        df.columns = df.columns.str.strip().str.title()
        
        # Reorder columns to desired format: Name, Marks, Grade
        columns_to_save = []
        if 'Name' in df.columns:
            columns_to_save.append('Name')
        if 'Marks' in df.columns:
            columns_to_save.append('Marks')
        if 'Grade' in df.columns:
            columns_to_save.append('Grade')
            
        if not columns_to_save:
            raise ValueError("Required columns (Name, Marks) not found in the data")
            
        df = df[columns_to_save]
        
        # Save to CSV
        df.to_csv('grades.csv', index=False)
        flash("Grades saved to 'grades.csv' successfully!", "success")
        
    except Exception as e:
        flash(f"Error saving grades: {str(e)}", "error")
        print(f"Debug - Error details: {str(e)}")  # For debugging
    
    return redirect(url_for('main_menu'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('index'))

@app.route('/reset-password', methods=['POST'])
def reset_password():
    # Placeholder for password reset functionality
    flash("Password reset link sent to your email.", "success")
    return render_template('index.html')

if _name_ == '_main_':
    app.run(debug=True)
