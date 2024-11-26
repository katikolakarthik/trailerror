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

if __name__ == "__main__":
    app.run(debug=True)
