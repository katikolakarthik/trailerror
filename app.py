from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import mysql.connector
from flask_mail import Mail, Message
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'katikolakarthik@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'Karthik@4477'  # Replace with your app password

mail = Mail(app)

# Database connection function
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",        # e.g., "localhost" or your server IP
            user="root",           # Database username
            password="",       # Database password
            database="exam_responses"       # Database name
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Error connecting to database: {e}")
        return None

# Save responses to phpMyAdmin database
def save_to_phpmyadmin(response_data):
    connection = connect_to_db()
    if connection is None:
        print("Failed to connect to the database.")
        return

    try:
        cursor = connection.cursor()

        # SQL query to insert responses
        insert_query = """
            INSERT INTO responses (username, question, selected_answer, correct_answer)
            VALUES (%s, %s, %s, %s)
        """

        for response in response_data:
            cursor.execute(insert_query, (
                response['Username'],
                response['Question'],
                response['Selected Answer'],
                response.get('Correct Answer', None)
            ))

        connection.commit()  # Commit the transaction
        print("Responses saved to phpMyAdmin database successfully.")
    except mysql.connector.Error as e:
        print(f"Error inserting data: {e}")
    finally:
        cursor.close()
        connection.close()

# Save responses to Google Sheets (Optional)
def save_to_google_sheets(response_data):
    pass  # Placeholder if Google Sheets is required in the future

# Function to send responses via email (Optional)
def send_responses_via_email(response_data):
    try:
        msg = Message('User Responses', sender=app.config['MAIL_USERNAME'], recipients=['admin@example.com'])
        msg.body = "\n".join([f"{resp['Question']}: {resp['Selected Answer']}" for resp in response_data])
        mail.send(msg)
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")

# Route for login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        # Load credentials from Excel
        try:
            credentials_df = pd.read_excel("credentials.xlsx")
            credentials_df['Username'] = credentials_df['Username'].fillna('').str.lower()
            credentials_df['Password'] = credentials_df['Password'].fillna('')

            user_data = credentials_df[credentials_df['Username'] == username]
            if not user_data.empty:
                stored_password = user_data.iloc[0]['Password']
                if password == stored_password:
                    session["username"] = username
                    return redirect(url_for("questions"))
                else:
                    flash("Invalid password.", "error")
            else:
                flash("Username not found.", "error")
        except Exception as e:
            flash(f"Error reading credentials: {str(e)}", "error")

    return render_template("login.html")

# Route for questions
@app.route("/questions", methods=["GET", "POST"])
def questions():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    if request.method == "POST":
        try:
            # Collect responses from form
            responses = request.form.to_dict()
            response_data = [
                {
                    "Username": username,
                    "Question": q,
                    "Selected Answer": a,
                    "Correct Answer": None  # Add correct answers if available
                } for q, a in responses.items()
            ]

            # Save responses to phpMyAdmin database
            save_to_phpmyadmin(response_data)

            # Optional: Send email or save to Google Sheets
            # send_responses_via_email(response_data)
            # save_to_google_sheets(response_data)

            flash("Responses submitted successfully!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error saving responses: {str(e)}", "error")

    try:
        # Load questions from Excel
        questions_df = pd.read_excel("questions.xlsx")
        questions = questions_df.to_dict(orient="records")
        return render_template("questions.html", questions=questions)
    except Exception as e:
        flash(f"Error loading questions: {str(e)}", "error")
        return redirect(url_for("login"))

