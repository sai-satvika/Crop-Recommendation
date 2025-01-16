from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
import pandas as pd
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Load the dummy dataset
DATA_FILE = "Dummy_Farming_Data.xlsx"

# File to store user credentials
USER_FILE = "users.json"

# Load or initialize user data
if not os.path.exists(USER_FILE):
    with open(USER_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USER_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        users = load_users()

        if username in users and users[username] == password:
            session['username'] = username
            flash("Login successful!", "success")
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "danger")

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        users = load_users()

        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))

        if username in users:
            flash("Username already exists!", "danger")
            return redirect(url_for('signup'))

        # Add new user
        users[username] = password
        save_users(users)
        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out!", "info")
    return redirect(url_for('login'))

@app.route('/index')
def index():
    if 'username' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    if 'username' not in session:
        flash("Please log in first!", "warning")
        return redirect(url_for('login'))

    # Load the dataset
    data = pd.read_excel(DATA_FILE)

    # Parse user input from the request
    user_input = request.get_json()
    location = user_input.get("location")
    crop_type = user_input.get("crop_type")
    soil_type = user_input.get("soil_type")
    field_size = float(user_input.get("field_size", 1))  # Default to 1 acre
    irrigation_system = user_input.get("irrigation_system")

    # Filter the data based on user inputs
    filtered_data = data[
        (data["Crop Type"] == crop_type) &
        (data["Soil Type"] == soil_type) &
        (data["Irrigation Type"] == irrigation_system)
    ]

    # If no exact match is found, broaden the filter by removing one condition at a time
    if filtered_data.empty:
        filtered_data = data[(data["Crop Type"] == crop_type)]

    # Get the first matching row
    recommendation_row = filtered_data.iloc[0]

    # Extract relevant details and convert to appropriate types
    profit_per_acre = float(recommendation_row["Profit Estimate (₹ per acre)"])
    water_per_acre = float(recommendation_row["Water Quantity (liters per acre)"])
    n_fertilizer = float(recommendation_row["Fertilizer N (kg per acre)"])
    p_fertilizer = float(recommendation_row["Fertilizer P (kg per acre)"])
    k_fertilizer = float(recommendation_row["Fertilizer K (kg per acre)"])

    # Calculate total values based on field size
    total_profit = profit_per_acre * field_size
    total_water = water_per_acre * field_size
    total_n_fertilizer = n_fertilizer * field_size
    total_p_fertilizer = p_fertilizer * field_size
    total_k_fertilizer = k_fertilizer * field_size

    # Create the recommendation response
    recommendation = {
        "profit": f"₹{total_profit:.2f}",
        "water_requirement": f"{total_water:.2f} liters for {field_size} acres",
        "fertilizers": {
            "N": f"{total_n_fertilizer:.2f} kg",
            "P": f"{total_p_fertilizer:.2f} kg",
            "K": f"{total_k_fertilizer:.2f} kg",
        },
        "details": {
            "Days to Grow": int(recommendation_row["Days to Grow"]),
            "Watering Schedule": recommendation_row["Watering Schedule"],
            "Pesticides": recommendation_row["Pesticides"],
            "Storage Duration": recommendation_row["Storage Duration"],
        }
    }

    # Return the JSON response
    return jsonify(recommendation)
if __name__ == "__main__":
    app.run(debug=True)