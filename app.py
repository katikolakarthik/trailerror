from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import pandas as pd
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"

# File path for storing responses
RESPONSES_FILE = "responses.xlsx"

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

            # Save responses to an Excel file
            if os.path.exists(RESPONSES_FILE):
                existing_df = pd.read_excel(RESPONSES_FILE)
                new_df = pd.DataFrame(response_data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(RESPONSES_FILE, index=False)
            else:
                pd.DataFrame(response_data).to_excel(RESPONSES_FILE, index=False)

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

# Route to download responses file
@app.route("/download-responses")
def download_responses():
    try:
        if os.path.exists(RESPONSES_FILE):
            return send_file(RESPONSES_FILE, as_attachment=True)
        else:
            flash("No responses file available.", "error")
            return redirect(url_for("login"))
    except Exception as e:
        flash(f"Error downloading file: {str(e)}", "error")
        return redirect(url_for("login"))

