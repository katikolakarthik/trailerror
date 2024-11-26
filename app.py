from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
from flask_mail import Mail, Message

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'katikolakarthik@gmail.com'  # Replace with your email
app.config['MAIL_PASSWORD'] = 'Karthik@4477'  # Replace with your email password

mail = Mail(app)

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
            response_data = [{"Question": q, "Selected Answer": a} for q, a in responses.items()]

            # Save responses to an Excel file
            responses_df = pd.DataFrame(response_data)
            responses_df.to_excel("User_Responses.xlsx", index=False)

            # Send responses via email
            send_responses_via_email(response_data)

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

# Function to send responses via email
def send_responses_via_email(response_data):
    try:
        msg = Message('User Responses', sender=app.config['MAIL_USERNAME'], recipients=['admin@example.com'])
        msg.body = "\n".join([f"{resp['Question']}: {resp['Selected Answer']}" for resp in response_data])
        mail.send(msg)
    except Exception as e:
        print(f"Error sending email: {e}")


