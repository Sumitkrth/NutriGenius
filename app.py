
import bcrypt
import razorpay
import pandas as pd
import MySQLdb.cursors
from functools import wraps
from dotenv import load_dotenv
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
from gemini_content import run_conversation
from yoga import find_yoga_poses, yoga_poses_df, detailed_procedures_df
from flask import Flask, render_template, jsonify, request, redirect, url_for, Blueprint, flash
from diet_planner.diet_all import get_response_diet as get_response_diet_all, input_prompt_diet_all
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from diet_planner.diet_lunch import get_response_diet as get_response_diet_lunch, input_prompt_diet_lunch
from diet_planner.diet_dinner import get_response_diet as get_response_diet_dinner, input_prompt_diet_dinner
from diet_planner.diet_breakfast import get_response_diet as get_response_diet_breakfast, input_prompt_diet_breakfast

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

app.secret_key = 'your_secret_key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'mydatabase'
app.config['RAZORPAY_KEY_ID'] = 'rzp_test_VVaYOc7j3B2yvD'
app.config['RAZORPAY_KEY_SECRET'] = 's5QqR03arhotrerRgsPnoADw'
mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth_bp.login'
auth_bp = Blueprint('auth_bp', __name__, template_folder='templates')
razorpay_client = razorpay.Client(auth=('rzp_test_VVaYOc7j3B2yvD', 's5QqR03arhotrerRgsPnoADw'))

class User(UserMixin):
    def __init__(self, id, username, email, subscription_status):
        self.id = id
        self.username = username
        self.email = email
        self.subscription_status = subscription_status

# Function to calculate BMR
def calculate_bmr(weight, height, age, gender):
    if gender == 'male':
        return 10 * weight + 6.25 * height - 5 * age + 5
    elif gender == 'female':
        return 10 * weight + 6.25 * height - 5 * age - 161
    else:
        return None

# Function to calculate daily calorie requirement based on BMR and activity level
def calculate_calories(bmr, activity_level):
    activity_multipliers = {
        'sedentary': 1.2,
        'lightly active': 1.375,
        'moderately active': 1.55,
        'very active': 1.725,
        'extra active': 1.9
    }
    return bmr * activity_multipliers.get(activity_level, 0) if activity_level in activity_multipliers else None

# Function to calculate default nutritional requirements based on daily calorie needs
def calculate_default_nutritional_requirements(calories):
    carbs = calories * 0.55 / 4
    fat = calories * 0.25 / 9
    protein = calories * 0.20 / 4
    return [
        carbs, fat, protein
    ]

# Function to print nutritional component values along with their names
def format_nutritional_components(components):
    nutritional_names = [
        'Carbohydrates', 'Total Fat', 'Protein'
    ]
    formatted = ""
    for name, value in zip(nutritional_names, components):
        formatted += f"{name}: {value}<br>"
    return formatted

# Function to find yoga poses based on user input
def find_yoga_poses(health_issues, user_contraindications):
    print(f"Health Issues: {health_issues}")
    print(f"User Contraindications: {user_contraindications}")

    all_matches = pd.DataFrame()
    for issue in health_issues:
        matches = yoga_poses_df[yoga_poses_df['Benefit'].str.contains(issue, case=False, na=False)]
        all_matches = pd.concat([all_matches, matches])

    print(f"All Matches: {all_matches}")

    # Filter out yoga poses that have contraindications matching any of the user's contraindications
    if not all_matches.empty:
        all_matches = all_matches.drop_duplicates().reset_index(drop=True)
        filtered_matches = []
        for index, row in all_matches.iterrows():
            contraindications_list = row['Contraindications'].split(', ') if isinstance(row['Contraindications'], str) else []
            if not any(contra in user_contraindications for contra in contraindications_list):
                filtered_matches.append(row)

        if filtered_matches:
            results = []
            for row in filtered_matches:
                pose = row['Pose']
                benefit = row['Benefit']
                procedure = detailed_procedures_df[detailed_procedures_df['Pose'] == pose]['Procedure'].values
                procedure_text = procedure[0] if len(procedure) > 0 else "Procedure not available."
                # Handle NaN values
                results.append({'pose': pose, 'benefit': benefit, 'procedure': procedure_text if pd.notna(procedure_text) else "Procedure not available."})
            print(f"Filtered Results: {results}")
            return results
        else:
            return "No matching yoga poses found for the given health issues."
    else:
        return "No matching yoga poses found for the given health issues."

@login_manager.user_loader
def load_user(user_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))
    user = cursor.fetchone()
    if user:
        cursor.execute('SELECT expiry_date FROM subscriptions WHERE email = %s ORDER BY expiry_date DESC LIMIT 1', (user['email'],))
        subscription = cursor.fetchone()
        subscription_status = False
        if subscription and subscription['expiry_date']:
            expiry_date = subscription['expiry_date']
            if expiry_date > datetime.now():
                subscription_status = True
        return User(id=user['id'], username=user['name'], email=user['email'], subscription_status=subscription_status)
    return None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        confirm_password = request.form['confirm_password'].encode('utf-8')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('auth_bp.register'))
        
        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s OR name = %s', (email, name))
        account = cursor.fetchone()
        
        if account:
            flash('Account already exists!', 'error')
            return redirect(url_for('auth_bp.register'))
        
        cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)', (name, email, hashed_password.decode('utf-8')))
        mysql.connection.commit()
        
        flash('Your account has been successfully created!', 'success')
        return redirect(url_for('auth_bp.login'))
    return render_template('register.html', form_type='register')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login_input']
        password = request.form['password'].encode('utf-8')
        
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s OR name = %s', (login_input, login_input))
        account = cursor.fetchone()
        
        if account and bcrypt.checkpw(password, account['password'].encode('utf-8')):
            cursor.execute('SELECT expiry_date FROM subscriptions WHERE email = %s ORDER BY expiry_date DESC LIMIT 1', (account['email'],))
            subscription = cursor.fetchone()
            subscription_status = False
            if subscription and subscription['expiry_date']:
                expiry_date = subscription['expiry_date']
                if expiry_date > datetime.now():
                    subscription_status = True
            user = User(id=account['id'], username=account['name'], email=account['email'], subscription_status=subscription_status)
            login_user(user)
            flash('Successfully logged in your account!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Incorrect name/email or password!', 'error')
            return redirect(url_for('auth_bp.login'))
    
    return render_template('register.html', form_type='login')


@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Successfully logged out!', 'success')
    return redirect(url_for('home'))

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        account = cursor.fetchone()
        if account:
            password = request.form['password'].encode('utf-8')
            confirm_password = request.form['confirm_password'].encode('utf-8')
            if password != confirm_password:
                flash('Passwords do not match!', 'error')
                return redirect(url_for('auth_bp.forgot_password'))
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            cursor.execute('UPDATE users SET password = %s WHERE email = %s', (hashed_password, email,))
            mysql.connection.commit()
            flash('Password has been successfully reset!', 'success')
            return redirect(url_for('auth_bp.login'))
        else:
            flash('Account does not exist!', 'error')
            return redirect(url_for('auth_bp.forgot_password'))
    return render_template('register.html', form_type='forgot_password')

def subscription_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.subscription_status:
           return render_template('subscription.html')    
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/dashboard')
@login_required
def dashboard():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT expiry_date FROM subscriptions WHERE email = %s ORDER BY expiry_date DESC LIMIT 1", (current_user.email,))
    subscription = cursor.fetchone()
    cursor.close()
    
    subscription_status = 'Inactive'
    subscription_expiry = 'N/A'
    
    if subscription and subscription['expiry_date']:
        expiry_date = subscription['expiry_date']
        subscription_expiry = expiry_date.strftime('%Y-%m-%d')
        if expiry_date > datetime.now():
            subscription_status = 'Active'
    
    return render_template('dashboard.html', 
                           name=current_user.username, 
                           email=current_user.email,
                           subscription_status=subscription_status,
                           subscription_expiry=subscription_expiry)

@app.route('/gemini_content', methods=['GET', 'POST'])
@login_required
@subscription_required
def gemini_content():
    return render_template("gemini_content.html")

@app.route('/yoga', methods=['GET', 'POST'])
@login_required
@subscription_required
def yoga():
    return render_template("yoga.html")

@app.route("/run_conversation", methods=["POST"])
def process_message_func1():
    msg = request.json['message']
    resp = run_conversation(msg)
    return jsonify({"response": resp})

@app.route('/diet_all', methods=['GET', 'POST'])
@login_required
def diet_all():
    response = None
    if request.method == 'POST':
        input_diet = request.form['input_diet']
        response = get_response_diet_all(input_prompt_diet_all, input_diet)
    return render_template('diet_all.html', response=response)

@app.route('/diet_breakfast', methods=['GET', 'POST'])
@login_required
def diet_breakfast():
    response = None
    if request.method == 'POST':
        input_diet = request.form['input_diet']
        response = get_response_diet_breakfast(input_prompt_diet_breakfast, input_diet)
    return render_template('diet_breakfast.html', response=response)

@app.route('/diet_lunch', methods=['GET', 'POST'])
@login_required
def diet_lunch():
    response = None
    if request.method == 'POST':
        input_diet = request.form['input_diet']
        response = get_response_diet_lunch(input_prompt_diet_lunch, input_diet)
    return render_template('diet_lunch.html', response=response)

@app.route('/diet_dinner', methods=['GET', 'POST'])
@login_required
def diet_dinner():
    response = None
    if request.method == 'POST':
        input_diet = request.form['input_diet']
        response = get_response_diet_dinner(input_prompt_diet_dinner, input_diet)
    return render_template('diet_dinner.html', response=response)


@app.route('/meal_index', methods=['GET', 'POST'])
@login_required
def meal_index():
    response = None
    if request.method == 'POST':
        input_diet = request.form['input_diet']
        response = get_response_diet_lunch(input_prompt_diet_lunch, input_diet)
    return render_template('meal_index.html', response=response)


@app.route('/nutrition_home')
@login_required
@subscription_required
def nutrition_home():
    return render_template('nutrition.html')

@app.route('/get_results', methods=['POST'])
def get_results():
    health_issues = request.form.getlist('health_issues[]')
    user_contraindications = request.form.getlist('contraindications[]')

    print(f"Selected Health Issues: {health_issues}")
    print(f"Selected Contraindications: {user_contraindications}")

    results = find_yoga_poses(health_issues, user_contraindications)
    return jsonify(results)

@app.route('/get_contraindications', methods=['POST'])
def get_contraindications():
    health_issues_input = request.form['healthIssues']
    more_issues_input = request.form.get('moreIssues', '')

    health_issues = [issue.strip() for issue in health_issues_input.split(',')]
    if more_issues_input:
        health_issues.extend([issue.strip() for issue in more_issues_input.split(',')])

    print(f"Health Issues Input: {health_issues_input}")
    print(f"More Issues Input: {more_issues_input}")
    print(f"Parsed Health Issues: {health_issues}")

    # Find all poses beneficial for the user's health issues
    all_matches = pd.DataFrame()
    for issue in health_issues:
        matches = yoga_poses_df[yoga_poses_df['Benefit'].str.contains(issue, case=False, na=False)]
        all_matches = pd.concat([all_matches, matches])

    # Gather unique contraindications from the matched poses
    contraindications_set = set()
    for index, row in all_matches.iterrows():
        contraindications_list = row['Contraindications'].split(', ') if isinstance(row['Contraindications'], str) else []
        contraindications_set.update(contraindications_list)

    print(f"Contraindications Set: {contraindications_set}")

    return jsonify(list(contraindications_set), health_issues)

@app.route('/get_detailed_procedures', methods=['POST'])
def get_detailed_procedures():
    try:
        yoga_pose_name = request.form['yoga_pose_name']

        if yoga_pose_name in detailed_procedures_df:
            detailed_procedures = detailed_procedures_df[yoga_pose_name]['Detailed Procedures']
            return jsonify(detailed_procedures)
        else:
            return jsonify({'error': 'Yoga pose not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/charge', methods=['POST'])
@login_required
def charge():
    if request.method == 'POST':
        amount = int(request.form['amount']) * 100  # Amount in paise (e.g., 19900 paise = 199 INR)
        
        # Create an order
        order = razorpay_client.order.create({'amount': amount, 'currency': 'INR', 'payment_capture': '1'})
        
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO subscriptions (name, email, amount, order_id, subscription_status, expiry_date) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (current_user.username, current_user.email, amount, order['id'], 'Pending', None))
        mysql.connection.commit()
        cursor.close()

        return render_template('payment.html', order_id=order['id'], key_id=app.config['RAZORPAY_KEY_ID'], amount=amount, payment_successful=False)

@app.route('/payment_success', methods=['POST'])
@login_required
def payment_success():
    response = request.form
    order_id = response.get('razorpay_order_id')
    payment_id = response.get('razorpay_payment_id')
    signature = response.get('razorpay_signature')

    print(f"Response: {response}")
    print(f"Order ID: {order_id}")
    print(f"Payment ID: {payment_id}")
    print(f"Signature: {signature}")

    # Verify payment signature
    try:
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        })
    except razorpay.errors.SignatureVerificationError as e:
        print(f"Signature verification failed: {e}")
        return "Payment verification failed"

    # Update subscription status, payment ID, and expiry date
    cursor = mysql.connection.cursor()
    try:
        cursor.execute("""
            UPDATE subscriptions 
            SET subscription_status=%s, payment_id=%s, expiry_date=%s 
            WHERE order_id=%s
        """, ('Success', payment_id, datetime.now() + timedelta(days=30), order_id))
        mysql.connection.commit()
    except Exception as e:
        print(f"Error updating subscription: {e}")
    finally:
        cursor.close()

    return render_template('payment.html', payment_successful=True, payment_id=payment_id)

@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        weight = float(request.form['weight'])
        height = float(request.form['height'])
        age = int(request.form['age'])
        gender = request.form['gender']
        activity_level = request.form['activity_level']
        num_diseases = int(request.form['num_diseases'])

        bmr = calculate_bmr(weight, height, age, gender)
        if bmr is None:
            return jsonify(result="Invalid gender input.")

        calories = calculate_calories(bmr, activity_level)
        if calories is None:
            return jsonify(result="Invalid activity level input.")

        if num_diseases == 0:
            default_nutrients = calculate_default_nutritional_requirements(calories)
            result = format_nutritional_components(default_nutrients)
        else:
            diseases = [request.form[f'disease_{i}'].title() for i in range(num_diseases)]
            try:
                df1 = pd.read_csv('final_diseases.csv')
                df2 = pd.read_csv('final_food_items.csv')
            except FileNotFoundError as e:
                return jsonify(result=f"File not found: {e.filename}")
            except pd.errors.EmptyDataError:
                return jsonify(result="One of the input files is empty.")

            nutritional_components = []
            for disease in diseases:
                row = df1.loc[df1['Disease'] == disease]
                if row.empty:
                    return jsonify(result=f"No data found for disease: {disease}")
                nutritional_components.append(list(row.iloc[:, 1:].values[0]))

            if not nutritional_components:
                return jsonify(result="No nutritional components found for the given diseases.")

            final_list = nutritional_components[0]
            for components in nutritional_components[1:]:
                for i, value in enumerate(components):
                    final_list[i] = min(final_list[i], value)

            result = format_nutritional_components(final_list)

        return jsonify(result=result)
    except ValueError as e:
        return jsonify(result=f"Invalid input. Error: {e}")
    except Exception as e:
        return jsonify(result=f"An error occurred: {e}")
    
if __name__ == '__main__':
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.run(debug=True)