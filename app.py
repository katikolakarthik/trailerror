from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd

app = Flask(__name__)
app.secret_key = "your_secret_key"

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

@app.route("/questions", methods=["GET", "POST"])
def questions():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    if request.method == "POST":
        responses = request.form.to_dict()
        response_data = [{"Question": q, "Selected Answer": a} for q, a in responses.items()]
        pd.DataFrame(response_data).to_excel("User_Responses.xlsx", index=False)
        flash("Responses submitted successfully!", "success")
        return redirect(url_for("login"))

    try:
        questions_df = pd.read_excel("questions.xlsx")
        questions = questions_df.to_dict(orient="records")
        return render_template("questions.html", questions=questions)
    except Exception as e:
        flash(f"Error loading questions: {str(e)}", "error")
        return redirect(url_for("login"))
def submit_exam():
    response_data = []  # Initialize response_data as an empty list

    # Loop through the user's answers
    for idx, selected_answer in answers.items():
        if selected_answer.get() == "":
            messagebox.showwarning("Warning", f"Please answer Question {idx + 1}")
            return

        # Add the question and answer to response_data
        response_data.append({
            'Question': questions_df.iloc[idx]['Question'],
            'Selected Answer': selected_answer.get(),
            'Correct Answer': questions_df.iloc[idx]['Correct Answer'],
            'Username': username  # Use the username of the logged-in user
        })

    # Save the responses to an Excel file or database
    try:
        responses_df = pd.DataFrame(response_data)
        responses_df.to_excel("User_Responses.xlsx", index=False)
        messagebox.showinfo("Quiz Completed", "Your responses have been submitted!")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save responses: {str(e)}")

from flask_mail import Mail, Message
app = Flask(__name__)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = '22K91A6777@tkrcet.com'
app.config['MAIL_PASSWORD'] = 'tkrcet@2022'

mail = Mail(app)
def send_responses_via_email(response_data):
    msg = Message('User Responses', sender='your-email@gmail.com', recipients=['admin@example.com'])
    msg.body = str(response_data)  # Format responses as needed
    mail.send(msg)
send_responses_via_email(response_data)

