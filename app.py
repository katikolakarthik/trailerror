from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import pandas as pd
import os
import threading
import time

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key"

# Directory for storing responses per branch
RESPONSES_DIR = "responses"
os.makedirs(RESPONSES_DIR, exist_ok=True)

# Branch-specific configuration
BRANCH_CONFIG = {
    "datascience": {"credentials": "datasciencecredentials.xlsx", "questions": "datasciencequestions.xlsx"},
    "csm": {"credentials": "csmcredentials.xlsx", "questions": "csmquestions.xlsx"},
    "cse": {"credentials": "csecredentials.xlsx", "questions": "csequestions.xlsx"},
    "it": {"credentials": "itcredentials.xlsx", "questions": "itquestions.xlsx"},
    "ece": {"credentials": "ececredentials.xlsx", "questions": "ecequestions.xlsx"},
    "eee": {"credentials": "eeecredentials.xlsx", "questions": "eeequestions.xlsx"},
    "ce": {"credentials": "cecredentials.xlsx", "questions": "cequestions.xlsx"}
}

# Timer for automatic submission
def start_timer(username, branch):
    def submit_after_timeout():
        time.sleep(300)  # 5 minutes timer
        try:
            # Auto-submit responses
            questions_file = BRANCH_CONFIG[branch]["questions"]
            questions_df = pd.read_excel(questions_file)
            questions = questions_df.to_dict(orient="records")
            response_data = []

            for question in questions:
                response_data.append({
                    "Username": username,
                    "Question": question["Question"],
                    "Selected Answer": "Not Answered",
                    "Correct Answer": question.get("Correct Answer", None),
                    "Is Correct": False
                })

            # Save to branch-specific file
            response_file = os.path.join(RESPONSES_DIR, f"{branch}_responses.xlsx")
            if os.path.exists(response_file):
                existing_df = pd.read_excel(response_file)
                new_df = pd.DataFrame(response_data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(response_file, index=False)
            else:
                pd.DataFrame(response_data).to_excel(response_file, index=False)

            print(f"Responses for {username} in branch {branch} auto-submitted.")
        except Exception as e:
            print(f"Error during auto-submit: {str(e)}")

    thread = threading.Thread(target=submit_after_timeout)
    thread.start()

# Route for login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip().lower()
        password = request.form["password"].strip()

        # Determine the branch based on the username
        branch = None
        for b, config in BRANCH_CONFIG.items():
            try:
                credentials_df = pd.read_excel(config["credentials"])
                credentials_df['Username'] = credentials_df['Username'].fillna('').str.lower()
                credentials_df['Password'] = credentials_df['Password'].fillna('')

                user_data = credentials_df[credentials_df['Username'] == username]
                if not user_data.empty:
                    stored_password = user_data.iloc[0]['Password']
                    if password == stored_password:
                        branch = b
                        break
            except Exception as e:
                flash(f"Error reading credentials for {b}: {str(e)}", "error")

        if branch:
            session["username"] = username
            session["branch"] = branch
            start_timer(username, branch)  # Start the timer for auto-submission
            return redirect(url_for("questions"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")

# Route for questions
@app.route("/questions", methods=["GET", "POST"])
def questions():
    if "username" not in session or "branch" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    branch = session["branch"]
    questions_file = BRANCH_CONFIG[branch]["questions"]

    if request.method == "POST":
        try:
            # Load correct answers from the branch-specific questions file
            questions_df = pd.read_excel(questions_file)
            correct_answers = questions_df.set_index('Question')['Correct Answer'].to_dict()

            # Collect responses from the form
            responses = request.form.to_dict()
            total_marks = 0

            # Validate and calculate total marks
            response_data = []
            for question, selected_answer in responses.items():
                correct_answer = correct_answers.get(question, None)
                is_correct = (selected_answer == correct_answer)
                if is_correct:
                    total_marks += 1
                response_data.append({
                    "Username": username,
                    "Question": question,
                    "Selected Answer": selected_answer,
                    "Correct Answer": correct_answer,
                    "Is Correct": is_correct
                })

            # Add total marks to each row
            for row in response_data:
                row["Total Marks"] = total_marks

            # Save responses to branch-specific file
            response_file = os.path.join(RESPONSES_DIR, f"{branch}_responses.xlsx")
            if os.path.exists(response_file):
                existing_df = pd.read_excel(response_file)
                new_df = pd.DataFrame(response_data)
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df.to_excel(response_file, index=False)
            else:
                pd.DataFrame(response_data).to_excel(response_file, index=False)

            flash("Responses submitted successfully!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error processing responses: {str(e)}", "error")
            return redirect(url_for("login"))

    try:
        # Load branch-specific questions
        questions_df = pd.read_excel(questions_file)
        questions = questions_df.to_dict(orient="records")
        return render_template("questions.html", questions=questions)
    except Exception as e:
        flash(f"Error loading questions for {branch}: {str(e)}", "error")
        return redirect(url_for("login"))

# Route to download responses file for a specific branch
@app.route("/download-responses/<branch>")
def download_responses(branch):
    if branch not in BRANCH_CONFIG:
        flash("Invalid branch.", "error")
        return redirect(url_for("login"))

    try:
        response_file = os.path.join(RESPONSES_DIR, f"{branch}_responses.xlsx")
        if os.path.exists(response_file):
            return send_file(response_file, as_attachment=True)
        else:
            flash(f"No responses file available for {branch}.", "error")
            return redirect(url_for("login"))
    except Exception as e:
        flash(f"Error downloading file for {branch}: {str(e)}", "error")
        return redirect(url_for("login"))
