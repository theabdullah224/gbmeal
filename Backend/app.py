# Import necessary modules from Flask framework and other libraries
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import bcrypt
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import base64
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta  # Added import
from models import db, User, initialize_database
# import openai
from openai import OpenAI

import stripe
from flask import Flask
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from models import db, User
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import stripe
import random
import random
import string
from datetime import datetime, timedelta
from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import logging
import bcrypt
from flask_jwt_extended import JWTManager
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask import Blueprint, jsonify, request
from models import User, db
from datetime import timedelta
from datetime import datetime, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import re
import pdfkit

from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
# pdf = pdfkit.from_string(html_content, False, configuration=config)
# Load environment variables from a .env file
load_dotenv()

# Initialize the Flask application
app = Flask(__name__)
stripe.api_key = os.getenv('STRIPEAPIKEY')
app.config['JWT_SECRET_KEY'] = os.getenv('JWTSECRET')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(days=30) 
jwt = JWTManager(app)
# Enable Cross-Origin Resource Sharing (CORS) to allow requests from any origin
# CORS(app, resources={r"/": {"origins": "*"}})
CORS(app)
api = Blueprint('api', __name__)
from flask_migrate import Migrate

# migrate = Migrate(app, db)

# Set up logging for debugging purposes
logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directly use the PostgreSQL connection string as in models.py
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_POOL_SIZE'] = 10
app.config['SQLALCHEMY_MAX_OVERFLOW'] = 20
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 30
app.config['SQLALCHEMY_POOL_RECYCLE'] = 299

app.config['SQLALCHEMY_POOL_PRE_PING'] = True
# Initialize database and migration
db.init_app(app)
migrate = Migrate(app, db)

# SMTP (Email) server configuration using environment variables
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT', 465))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

# Set up OpenAI client with API key from environment variables
client = OpenAI()
client.api_key = os.getenv('OPENAI_API_KEY')
#Payment Route:
# Payment route
@app.route('/payment', methods=['POST'])
def create_payment():
    try:
        data = request.get_json()
        plan_type = data.get('planType')
        email = data.get('email')

        logging.info(f"Creating payment for plan: {plan_type}, email: {email}")

        plan_mapping = {
            'pro': {
                'price_id': 'price_1PuTKXJIHZe9tvecdtUCk4B3',
                'amount': 699
            },
            'ultra_pro': {
                'price_id': 'price_1PuTMLJIHZe9tvecikAUEJ6W',
                'amount': 6900
            }
        }

        if plan_type not in plan_mapping:
            return jsonify({'error': 'Invalid plan type'}), 400

        price_id = plan_mapping[plan_type]['price_id']

        # Create a Checkout Session with a 30-day trial
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url='https://www.gbmeals.com/welcome',
            cancel_url='https://www.gbmeals.com/',
            subscription_data={
                'trial_period_days': 30,
            },
            customer_email=email,
        )

        logging.info(f"Payment session created: {session.id}")
        return jsonify({'url': session.url})

    except stripe.error.StripeError as e:
        logging.error(f'Stripe error: {e.user_message}')
        return jsonify({'error': e.user_message}), 400
    except Exception as e:
        logging.error(f'Error creating payment session: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500




@app.route('/cancel-plan', methods=['POST'])
def cancel_plan():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        if user.subscription_status not in ['pro', 'ultra_pro']:
            return jsonify({'error': 'No active paid subscription found for this user'}), 400

        # Find the customer in Stripe
        customers = stripe.Customer.list(email=email)
        if not customers.data:
            return jsonify({'error': 'No customer found in Stripe with this email'}), 404

        customer = customers.data[0]

        # Cancel the subscription in Stripe
        subscriptions = stripe.Subscription.list(customer=customer.id, status='active')
        if subscriptions.data:
            for subscription in subscriptions.data:
                canceled_subscription = stripe.Subscription.delete(subscription.id)
                logging.info(f"Subscription canceled: {canceled_subscription.id}")

        # Update user's subscription status in the database
        user.subscription_status = 'inactive'
        user.subscription_end_date = None
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Subscription canceled successfully. You can now delete your card if desired.',
        })

    except stripe.error.StripeError as e:
        logging.error(f'Stripe error: {e.user_message}')
        return jsonify({'error': e.user_message}), 400
    except Exception as e:
        logging.error(f'Error canceling subscription: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/delete-card', methods=['POST'])
def delete_card():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Check if user is on a paid plan
        if user.subscription_status in ['pro', 'ultra_pro']:
            return jsonify({'error': 'Please cancel your plan before deleting the card'}), 400

        # Find the customer in Stripe
        customers = stripe.Customer.list(email=email)
        if not customers.data:
            return jsonify({'error': 'No customer found in Stripe with this email'}), 404

        customer = customers.data[0]

        # Get the last 4 digits of the card before deleting
        payment_methods = stripe.PaymentMethod.list(customer=customer.id, type="card")
        card_last4 = None
        if payment_methods.data:
            card_last4 = payment_methods.data[0].card.last4

        # Delete the payment methods (cards)
        for payment_method in payment_methods.data:
            stripe.PaymentMethod.detach(payment_method.id)

        # Update user's subscription status if they're on a free trial
        if user.subscription_status == 'trial':
            user.subscription_status = 'inactive'
            user.subscription_end_date = None
            db.session.commit()

        message = 'Card deleted successfully.'
        if card_last4:
            message += f' Card ending in {card_last4} has been removed.'

        return jsonify({
            'status': 'success',
            'message': message,
        })

    except stripe.error.StripeError as e:
        logging.error(f'Stripe error: {e.user_message}')
        return jsonify({'error': e.user_message}), 400
    except Exception as e:
        logging.error(f'Error deleting card: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/update-card', methods=['POST'])
def update_card():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Find the customer in Stripe
        customers = stripe.Customer.list(email=email)
        if not customers.data:
            return jsonify({'error': 'No customer found in Stripe with this email'}), 404

        customer = customers.data[0]

        # Check if the customer has any payment methods
        payment_methods = stripe.PaymentMethod.list(
            customer=customer.id,
            type="card"
        )

        if not payment_methods.data:
            return jsonify({'error': 'No card found. Please subscribe to a plan first.'}), 400

        # Create a new Checkout Session for updating the card
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='setup',
            customer=customer.id,
            success_url='https://www.gbmeals.com/',
            cancel_url='https://www.gbmeals.com/',
        )

        return jsonify({'url': session.url})

    except stripe.error.StripeError as e:
        logging.error(f'Stripe error: {e.user_message}')
        return jsonify({'error': e.user_message}), 400
    except Exception as e:
        logging.error(f'Error updating card: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500


@app.route('/check-subscription', methods=['POST'])
def check_subscription():
    try:
        data = request.get_json()
        email = data.get('email')

        logger.info(f"Checking subscription for email: {email}")

        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            logger.warning(f"User not found for email: {email}")
            return jsonify({"error": "User not found"}), 404

        is_subscribed = user.is_subscription_active()
        can_generate_pdf = user.can_generate_pdf()

        logger.info(f"User details: status={user.subscription_status}, end_date={user.subscription_end_date}, free_used={user.free_plan_used}")
        logger.info(f"Subscription check result: is_subscribed={is_subscribed}, can_generate_pdf={can_generate_pdf}")

        return jsonify({
            "isSubscribed": is_subscribed,
            "canGeneratePDF": can_generate_pdf,
            "subscriptionStatus": user.subscription_status
        })

    except Exception as e:
        logger.error(f"Error checking subscription status: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred. Please try again later."}), 500
# temp route to check user details ..debugging...
@app.route('/check-user/<email>', methods=['GET'])
def check_user(email):
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({
            'email': user.email,
            'subscription_status': user.subscription_status,
            'subscription_end_date': str(user.subscription_end_date) if user.subscription_end_date else None,
            'free_plan_used': user.free_plan_used
        }), 200
    return jsonify({'error': 'User not found'}), 404


@app.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('WEBHOOKENDPOINTSECRET')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError as e:
        logger.error(f'Invalid payload: {str(e)}')
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f'Invalid signature: {str(e)}')
        return jsonify({'error': 'Invalid signature'}), 400

    logger.info(f"Received Stripe event: {event['type']}")
    logger.info(f"Event data: {event['data']}")

    if event['type'] == 'invoice.payment_succeeded':
        customer_id = event['data']['object']['customer']
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.email

        logger.info(f"Processing payment for email: {email}")
        user = User.query.filter_by(email=email).first()
        if user:
            try:
                plan_type = event['data']['object']['lines']['data'][0]['price']['product']
                logger.info(f"Received plan type: {plan_type}")
                
                if plan_type == 'prod_Qm1NSZX9ObY4mC':  # pro plan
                    user.subscription_status = 'pro'
                elif plan_type == 'prod_Qm1PPuGYmN2DDq':  # ultra pro plan
                    user.subscription_status = 'ultra_pro'
                else:
                    user.subscription_status = 'active'
                
                user.subscription_end_date = datetime.utcnow() + timedelta(days=30)
                db.session.commit()
                logger.info(f"Updated subscription for user {email}: status={user.subscription_status}, end_date={user.subscription_end_date}")
                
                # Send Welcome Email if the user has subscribed to pro or ultra_pro
                if user.subscription_status in ['pro', 'ultra_pro']:
                    send_welcome_email(user.email, user.name, user.subscription_status)
                    logger.info(f"Welcome email sent to {user.email} for {user.subscription_status} plan")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error updating subscription: {str(e)}")
        else:
            logger.warning(f"User not found for email: {email}")

    return jsonify({'status': 'success'}), 200

# Function to send welcome email with hardcoded SMTP credentials
def send_welcome_email(email, name, plan_type):
    try:
        msg = MIMEMultipart()
        msg['From'] = 'lann8552@gmail.com'
        msg['To'] = email
        msg['Subject'] = "Welcome to GBMeals - Subscription Active!"

        # Email body content based on plan type
        body = f"""
        Hello {name},

        Welcome to GBMeals, and thank you for subscribing to our {plan_type.capitalize()} Plan!

        With your {plan_type.capitalize()} Plan, you'll have access to personalized meal plans tailored to your preferences. 
        Start planning your meals today and enjoy delicious, healthy meals made just for you.

        If you have any questions, feel free to contact our support team.

        Best regards,
        The GBMeals Team
        """

        msg.attach(MIMEText(body, 'plain'))

        # Send the email via SMTP with hardcoded credentials
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login('lann8552@gmail.com', 'gaytwyanzdxasqnl')
            server.sendmail('lann8552@gmail.com', email, msg.as_string())

        logger.info(f"Welcome email sent to {email}")

    except Exception as e:
        logger.error(f"Error sending welcome email to {email}: {str(e)}")


# pdf cout-------------------------------------------------------------
@app.route('/api/users/<int:user_id>/pdf_stats', methods=['GET'])
def get_user_pdf_stats(user_id):
    try:
        # PDFs generated in the last week
        pdf_count_last_week = get_pdf_count_last_week(user_id)
        
        # PDFs generated in the last month
        pdf_count_last_month = get_pdf_count_last_month(user_id)
        
        # PDFs generated per month in the current year
        pdf_count_per_month = get_pdf_count_per_month(user_id)
        month_stats = [
            {
                'month': month.strftime('%B %Y'),
                'pdf_count': count
            } for month, count in pdf_count_per_month
        ]
        
        # PDFs generated per year
        pdf_count_per_year = get_pdf_count_per_year(user_id)
        year_stats = [
            {
                'year': year.strftime('%Y'),
                'pdf_count': count
            } for year, count in pdf_count_per_year
        ]
        
        # Total PDFs generated by the user
        total_pdf_count = get_total_pdf_count(user_id)
        
        # Return all the data in one response
        return jsonify({
            'user_id': user_id,
            'pdf_count_last_week': pdf_count_last_week,
            'pdf_count_last_month': pdf_count_last_month,
            'pdf_count_per_month': month_stats,
            'pdf_count_per_year': year_stats,
            'total_pdf_count': total_pdf_count
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Failed to fetch PDF stats', 'message': str(e)}), 500






@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        users = User.query.all()  # Fetch all users from the database
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'phone': user.phone,
                'subject': user.subject,
                'subscription_status': user.subscription_status,
                'subscription_end_date': user.subscription_end_date,
                'free_plan_used': user.free_plan_used,
                'verification_code': user.verification_code,
                'verification_code_expiry': user.verification_code_expiry
            })
        return jsonify(users_list), 200  # Return the list as a JSON response with HTTP 200 status
    except Exception as e:
        return jsonify({'error': 'Failed to fetch users', 'message': str(e)}), 500


@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        email = data.get('email')

        if not email:
            return jsonify({"error": "Email is required"}), 400

        user = User.query.filter_by(email=email).first()

        if not user:
            return jsonify({"error": "User not found"}), 404

        verification_code = ''.join(random.choices(string.digits, k=6))
        
        user.verification_code = verification_code
        user.verification_code_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Create a token that includes the user's ID
        token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=10))

        # Send email (implementation remains the same)
        # ...
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Your Password Reset Verification Code"
        body = f"Your verification code to reset your password is {verification_code}. The code will expire in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, msg.as_string())

        return jsonify({"message": "Verification code sent to your email", "token": token}), 200

    except Exception as e:
        logging.error(f"Error in forgot password: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route('/verify-code', methods=['POST'])
@jwt_required()
def verify_code():
    try:
        data = request.get_json()
        verification_code = data.get('verification_code')

        if not verification_code:
            return jsonify({"error": "Verification code is required"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        if user.verification_code != verification_code:
            return jsonify({"error": "Invalid verification code"}), 400

        if datetime.utcnow() > user.verification_code_expiry:
            return jsonify({"error": "Verification code has expired"}), 400

        # Create a new token for password reset
        reset_token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=10))

        return jsonify({"message": "Verification successful. You can now reset your password.", "reset_token": reset_token}), 200

    except Exception as e:
        logging.error(f"Error in verifying code: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset-password', methods=['POST'])
@jwt_required()
def reset_password():
    try:
        data = request.get_json()
        new_password = data.get('new_password')

        if not new_password:
            return jsonify({"error": "New password is required"}), 400

        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())

        user.password = hashed_password.decode('utf-8')
        user.verification_code = None
        user.verification_code_expiry = None
        db.session.commit()

        return jsonify({"message": "Password updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error in resetting password: {str(e)}")
        return jsonify({"error": str(e)}), 500





@app.route('/initiate-delete-account', methods=['POST'])
def initiate_delete_account():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Check if the user exists and the password is correct
        user = User.query.filter_by(email=email).first()
        if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            return jsonify({"error": "Invalid email or password"}), 401

        # Generate a 6-digit verification code
        verification_code = ''.join(random.choices(string.digits, k=6))

        # Set verification code and expiry time
        user.verification_code = verification_code
        user.verification_code_expiry = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()

        # Send the verification code to the user's email
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Account Deletion Verification Code"
        body = f"Your verification code to delete your account is {verification_code}. The code will expire in 10 minutes."
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, msg.as_string())

        # Generate and return a JWT token
        token = create_access_token(identity=user.id, expires_delta=timedelta(minutes=10))
        return jsonify({"message": "Verification code sent to your email", "token": token}), 200

    except Exception as e:
        logging.error(f"Error in initiating account deletion: {str(e)}")
        return jsonify({"error": str(e)}), 500





@app.route('/confirm-delete-account', methods=['POST'])
@jwt_required()
def confirm_delete_account():
    try:
        data = request.get_json()
        verification_code = data.get('verification_code')

        if not verification_code:
            return jsonify({"error": "Verification code is required"}), 400

        # Get the user's ID from the JWT token
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Check if the verification code matches and is not expired
        if user.verification_code != verification_code:
            return jsonify({"error": "Invalid verification code"}), 400

        if datetime.utcnow() > user.verification_code_expiry:
            return jsonify({"error": "Verification code has expired"}), 400

        # Delete the user account
        db.session.delete(user)
        db.session.commit()

        # Optionally: Blacklist or revoke the current token here to prevent further use
        # e.g., adding the current JWT to a blacklist or invalidating it

        return jsonify({"message": "Account deleted successfully"}), 200

    except SQLAlchemyError as e:
        logging.error(f"Database error in confirming account deletion: {str(e)}")
        db.session.rollback()  # Rollback in case of a database error
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logging.error(f"Error in confirming account deletion: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/deleteuser/<email>', methods=['DELETE'])
def deleteuser(email):
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        db.session.delete(user)
        db.session.commit()

        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        logging.error('Error during user deletion: %s', str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/adduser', methods=['POST'])
def adduser():
    try:
        data = request.json
        name = data.get('Your Name')
        email = data.get('Email Address')
        password = data.get('Password')
        subscription_status = data.get('status')

        
        if not email or not password:
            return jsonify({"error": "Invalid input: Name, email, and password are required."}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(name=name, email=email, password=hashed_password.decode('utf-8'), subscription_status=subscription_status)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({"message": "User registered successfully", "id": new_user.id}), 201

    except Exception as e:
        logging.error('Error during signup: %s', str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/submit', methods=['POST'])
def submit_contact_form():
    data = request.get_json()

    # Ensure all required fields are provided
    if not data or not all(k in data for k in ("name", "email", "message")):
        return jsonify({"error": "Invalid input: 'name', 'email', and 'message' are required."}), 400

    name = data['name']
    email = data['email']
    message = data['message']

    try:
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = "team@gbmeals.com"  # Replace with your recipient email
        msg['Subject'] = "User Contact Email"

        # Create the email body
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"
        msg.attach(MIMEText(body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        # Return a success message
        return jsonify({"message": "Your message has been sent successfully!"}), 200

    except Exception as e:
        # Log any errors and return an error message to the client
        app.logger.error('Error sending email: %s', str(e))
        return jsonify({"error": f"An error occurred while sending your message. Details: {str(e)}"}), 500


# Route to get a list of questions (currently returns an empty list)
@app.route('/questions', methods=['GET'])
def get_questions():
    questions = [
        {
            "category": "Food Allergies",
            "description": "Tell Us About Your Food Allergies",
            "details": "We want to make sure your meal plan is tailored to your needs. Let us know if you have any food allergies so we can provide you with delicious and safe recipes.",
            "options": [
                {"icon": "eggs.svg", "label": "Egg"},
                {"icon": "cheese.svg", "label": "Cheese"},
                {"icon": "tofu.svg", "label": "Tufo"},  # Note: Corrected typo from 'tufo' to 'tofu'
                {"icon": "butter.svg", "label": "Butter"},
                {"icon": "coconut.svg", "label": "Coconut"},
                {"icon": "plusc.svg", "label": "Add"}
            ]
        },
        {
            "category": "Food Dislikes",
            "description": "Tell us about the food you dislike",
            "details": "Tell us about the food you dislike",
            "options": [
                {"icon": "Chicken.svg", "label": "Chicken"},
                {"icon": "pork.svg", "label": "Pork"},
                {"icon": "beef.svg", "label": "Beef"},
                {"icon": "fish.svg", "label": "Fish"},
                {"icon": "mashroom.svg", "label": "Mushrooms"},  # Note: Corrected typo from 'mashroom' to 'mushroom'
                {"icon": "plusc.svg", "label": "Add"}
            ]
        },
        {
            "category": "Meal Plan Preferences",
            "description": "Choose Your Preferred/Popular Meal Plan",
            "details": "Select from popular dietary preferences to tailor your meal plan.",
            "options": [
                {"icon": "lowcarbs.svg", "label": "Low carb"},
                {"icon": "balanceddiet.svg", "label": "Balanced diet"},
                {"icon": "cornivorediet.svg", "label": "Carnivore diet"},  # Note: Corrected typo from 'carnivore' to 'cornivore'
                {"icon": "paleodiet.svg", "label": "Paleo diet"},
                {"icon": "plusc.svg", "label": "Add"}
            ]
        },
        {
            "category": "Dietary Restrictions",
            "description": "Choose Your Dietary Restrictions",
            "details": "Select any dietary restrictions that apply to you.",
            "options": [
                {"icon": "glotenfree.svg", "label": "Gluten free"},  # Note: Corrected typo from 'glotenfree' to 'glutenfree'
                {"icon": "diaryfree.svg", "label": "Dairy free"}   # Note: Corrected typo from 'diaryfree' to 'dairy free'
            ]
        },
        {
            "category": "Servings",
            "description": "How Many Servings Do You Need?",
            "details": "Select the number of servings you need per meal.",
            "options": [
                {"icon": "servings.svg", "label": "1 serving"},
                {"icon": "servings.svg", "label": "2 servings"},
                {"icon": "servings.svg", "label": "3 servings"},
                {"icon": "servings.svg", "label": "4+ servings"},
                {"icon": "plusc.svg", "label": "Add"}
            ]
        }
    ]

    return jsonify(questions)


# Route to test if CORS is working
@app.route('/test-cors', methods=['GET'])
def test_cors():
    response = jsonify({"message": "CORS is working"})
    response.headers.add('Access-Control-Allow-Origin', '*')  # Allow any origin to access this resource
    return response



@app.route('/generate', methods=['OPTIONS', 'POST'])
def generate_meal_plan():
    if request.method == 'OPTIONS':
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response

    try:
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>{title}</title>
        </head>
        <body>
            <img src="https://www.gbmeals.com/static/media/logo2.2cc494b3c43bf1131ac7.png" 
                 alt="Logo" 
                 style="display: block; margin: 10px auto; width: 100px; height: auto;" />
            {content}
        </body>
        </html>
        """
        
        data = request.get_json()
        food_preferences = data.get('preferredMeal')
        allergies = data.get('allergies', [])
        dislikes = data.get('dislikes', [])
        dietary_restrictions = data.get('dietaryRestrictions', [])
        servings = data.get('servings')
        total_calories = data.get('total_calories')

        print(total_calories,"---------------------------------------------------")
        match = re.match(r"^(\d+)", servings)
        if match:
            servings = int(match.group(1))
        else:
            raise ValueError("Unexpected serving size format")

        if not dietary_restrictions or not servings:
            return jsonify({"error": "Invalid input: preferredMeal and servings are required."}), 400


        meal_plan = ""  # Initialize an empty string to store the meal plan

       

        
        data = """
              h1{text-align: center; color: #2d3748; font-size: 24px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 0.1em;}
        .maindiv{width: 100%; margin: 0 auto; padding: 15px; box-sizing: border-box;}
        .firsttable{width: 100%; border-collapse: separate; border-spacing: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 40px;}
        .firsttable thead tr th{
            width: 33.33%; background-color: #738065; color: white; text-transform: uppercase; letter-spacing: 0.05em; padding: 16px 12px; font-size: 14px; border-right: 1px solid rgba(255, 255, 255, 0.2);
        }
        .firstcolumn{padding: 20px 16px; border-right: 1px solid #e5e7eb; background-color: white; font-size: 13px; vertical-align: top;}
        .firstcolumndiv{background-color: #f8fafc; padding: 12px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);}
        .meal{font-size: 13px; color: #313131; font-weight: 600; display: block; margin-bottom: 4px;}
        .maindish{font-size: 16px; font-weight: 600; color: #313131; margin: 8px 0 4px 0;}
        .sidedish{font-size: 14px; font-weight: 500; color: #666; font-style: italic; margin: 4px 0 8px 0;}
        .timetable{width: 100%; margin: 16px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); border-collapse: collapse; background-color: #f8fafc;}
        .timetable thead tr th{background-color: #A6AE9D; color: #313131; font-size: 14px; padding: 8px; border: 1px solid #d1d5db; width: 33%;}
        .timetable tbody tr td{font-size: 14px; text-align: center; padding: 8px; border: 1px solid #d1d5db;}
        h5{font-size: 14px; font-weight: 600; color: #313131; margin: 12px 0 8px 0; background-color: #f3f4f6; padding: 8px; border-radius: 6px;}
        .nutritable{width: 100%; margin: 8px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); border-collapse: collapse; background-color: #f8fafc;}
        .nutritable thead tr th{background-color: #A6AE9D; color: #313131; font-size: 14px; padding: 8px; border: 1px solid #d1d5db; width: 25%;}
        .nutritable tbody tr td{font-size: 14px; text-align: center; padding: 8px; border: 1px solid #d1d5db;}
        .secondcolumn{padding: 20px 16px; border-right: 1px solid #e5e7eb; background-color: white; font-size: 13px; vertical-align: top;}
        .secondcolumn div{background-color: #f3f4f6; padding: 16px; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);}
        .secondcolumn h6{margin: 0 0 12px 0; font-size: 14px; color: #313131; font-weight: 600;}
        .secondcolumn ol{padding-left: 20px; color: #4a5568; margin: 0;}
        .secondcolumn li {margin-bottom: 8px; font-size: 14px;}
        .secondcolumn p{color: #4a5568; line-height: 1.6; margin: 0; font-size: 14px;}
        .tabletwo{width: 100%; border-collapse: separate; border-spacing: 0; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);}
        .tabletwo thead tr th{padding: 16px; text-align: left;  background-color: #738065; color: white; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; width: 20%; border-right: 1px solid rgba(255, 255, 255, 0.2);}
        .tabletwo tbody tr td{padding: 15px;}
        .tablethree{width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);}
        .tablethree thead tr th{padding: 12px; text-align: left;  border-bottom: 1px solid #d1d5db; font-size: 13px; color: #ffffff;}
        .tablethree tbody tr td{padding: 12px; color: #4a5568; border-bottom: 1px solid #e5e7eb; font-size: 13px;}

        .container {max-width: 800px;margin: auto;}
.section {margin-bottom: 20px;}
.section h2 {font-size: 1.2em;margin-bottom: 10px;font-weight: bold;}

        ul {
            list-style-type: disc;
            padding-left: 20px;
            margin: 0;
        }"""
        for i in range(servings):
            prompt = ( 
                    f""" 
    Create a detailed meal plan for a {dietary_restrictions} diet with exactly {servings} distinct meals.
- Each meal should follow the structure provided, and you must include a shopping list.
-Must avoid extra spaces on start dont repeat the headers (MEALS INGREDIENTS INSTRUCTIONS) on each page it should be only first 
- Ensure that the generated meals take into account the following restrictions:
  - Must avoid these allergies: {', '.join(allergies)}.
  - Must exclude these disliked foods: {', '.join(dislikes)}.
- The {servings} servings refer to the number of **distinct meals to generate**.
- Generate the meal plan in pure HTML format without any additional information or formatting characters like "\\n" or "\\".
- Use only the following HTML structure for each meal, and ensure you repeat this for each of the {servings} meals.
-IMPORTANT: Total meals: {servings} servings must equal {total_calories} calories means each meal should contain that much coloreis that should be equal the the {total_calories} .
for example if there is 2 meals or 2 sevings and coloreis are  (Recomended (2000 - 2500 calories)) then two meals total colories should equal to the (2000 to 2500) 
-Please use detail and max content in the instructions
-each meal should be populate on 1 'A4' page size (means use max details)
-include each and every ingredients in the meal should list in the nutrition information each and every even little ingredients should show in the nutrition information 











  <div >
    
            <!-- Meal Plan Section -->
             <style>
        {data}
    </style>
    <h1>Meal Plan</h1>
    <div class="maindiv">
     
        <table class="firsttable">
        [never repeat this header this should be only on first page not on others page]
            <thead>
                <tr>
                    <th ><b>Meals</b></th>
                    <th ><b>Ingredients</b></th>
                    <th ><b>Instructions</b></th>
                </tr>
            </thead>
            <tbody>
                <tr >
                    [Repeat this <tr> block for {servings} time for each meal]
                        {''.join(f'''
                    <td class="firstcolumn">
                        <!-- Meal Info Section -->
                        <div class="firstcolumndiv">
                            <span class="meal">Meal {i+1}</span>
                            <h3 class="maindish" >[Main Dish Name]</h3>
                            <h4  class="sidedish">[Side Dish Name]</h4>
                        </div>

                        <!-- Time Table -->
                        <table class="timetable">
                            <thead>
                                <tr>
                                    <th >Prep</th>
                                    <th >Cook</th>
                                    <th >Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td >[Prep time]</td>
                                    <td >[Cook time]</td>
                                    <td >[Total time]</td>
                                </tr>
                            </tbody>
                        </table>

                        <!-- Nutrition Table -->
                        <div style="margin-top: 16px;">
                            <h5 >Nutritional Information</h5>
                            [repeat for all the detailed nutrition like protien carb iron vitamin colories... etc as much as in the meal and repeat the tr for each nutrition as much as nutrition present in the meal pick all of them and show here]
                            [IMPORTANT: Total meals: {servings} servings must equal {total_calories} calories means each meal should contain that much coloreis that should be equal the the total {total_calories}]
                            <table class="nutritable">
                                <thead>
                                    <tr>
                                        <th ></th>
                                        <th >Main</th>
                                        <th >Side</th>
                                        <th >Total</th>
                                    </tr>
                                </thead>
                                <tbody>
                                [include every single nutrition here that are availible in the meal dont miss any add minimum 10, like Vitamin A,Vitamin b,Vitamin c,Vitamin d,Vitamin e,Zinc,iron,Dietary Fiber,Omega-3 Fatty Acids and more that are availible in the meal means minimum add 10, these are just for example you have to add that are availible in the  meal also make sure you add 100% accurate (use only international units that can be understand by simple user)]
                                    <tr>
                                        <td >[Nutrition]</td>
                                        <td >[Value]</td>
                                        <td>[Value]</td>
                                        <td >[Value]</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </td>
                    
                    <!-- Ingredients Column -->
                    <td class="secondcolumn">
                        <div >
                            <h6 >Main Dish Ingredients</h6>
                            [Provide detail ingredients to make that dish]
                            <ol>
                                <li >[Ingredient]</li>
                            </ol>
                        </div>
                        <div >
                            <h6>Side Dish Ingredients</h6>
                            [Provide detail ingredients to make that dish]
                            <ol >
                                <li >[Ingredient]</li>
                            </ol>
                        </div>
                    </td>

                    <!-- Instructions Column -->
                    [main dish and side dish instructions should not be exceeded ]
                    <td class="secondcolumn">
                        <div >
                            <h6 >Main Dish Instructions</h6>
                            [Provide detail Instructions to make that dish as a user who didnot even know cooking can easily make this dish (provide detailed recipes)]
                            <p >[Instructions (detailed recipes, use maximum lines)]</p>
                        </div>
                        <div >
                            <h6>Side Dish Instructions</h6>
                            [Provide detail Instructions to make that dish as a user who didnot even know cooking can easily make this dish (provide detailed recipes)]
                            <p >[Instructions (detailed recipes) ]</p>
                        </div>
                    </td>
                </tr>
                ''' for i in range(servings))}
            </tbody>
        </table>


        <!-- Shopping List Section -->
         <h1 >Weekly Shopping List</h1>
         [Plese provide detailed shopping list according to the meals never miss single items ]
    [NEVER remove style tag and its content from here]
    [only and only use the international units , like kg,g,mg, litters,dozen etc.. NEVER USE quantity like i.e: 4 chicken , always use the international units like kg,g,mg, litters,dozen etc..]
    <style>
      body """"{font-family: Arial, sans-serif;background-color: #fff;color: #333;margin: 0;padding: 20px;}""""
      h1 {text-align: center;color: #333;font-size: 2rem;margin-bottom: 20px;}
      .container {display: flex;flex-wrap: wrap;gap: 30px;max-width: 900px;margin: 0 auto;}
      .column {flex: 1;min-width: 250px;}
      .category {margin-bottom: 20px;}
      .category h5 {font-size: 1.3rem;color: #333;font-weight: bold;margin: 0 0 10px;}
      .category ul {
        list-style-type: disc;
        padding-left: 20px;
        margin: 0;
      }
      .category li {
        font-size: 0.9rem;
        margin-bottom: 5px;
      }
    </style>
    [Must Generate a Complete "Weekly" Shopping List:Please provide a detailed
    shopping list for a full week of meals, ensuring it includes all necessary
    ingredients for each meal.]

    <div class="container">
      <div class="column">
        <div class="category">
          <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
          <ul>
            <li>
              [items name and weekly quantity(please provide the weekly quantity
              means that one multiply to 7 to get weekly quantity of each i.e if
              in meal we use 1 kg oil then you have to multiply 1 with 7 to get
              weekly quantity [you dont have to show the calculations , just
              show the value of weekly quantity] please use the international
              units that any one can understand )]
            </li>
          </ul>
        </div>

        <div class="category">
          <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
          <ul>
            <li>
              [items name and weekly quantity(please provide the weekly quantity
              means that one multiply to 7 to get weekly quantity of each i.e if
              in meal we use 1 kg oil then you have to multiply 1 with 7 to get
              weekly quantity [you dont have to show the calculations , just
              show the value of weekly quantity] please use the international
              units that any one can understand )]
            </li>
          </ul>
        </div>
      </div>

      <div class="column">
        <div class="category">
          <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
          <ul>
            <li>
              [items name and weekly quantity(please provide the weekly quantity
              means that one multiply to 7 to get weekly quantity of each i.e if
              in meal we use 1 kg oil then you have to multiply 1 with 7 to get
              weekly quantity [you dont have to show the calculations , just
              show the value of weekly quantity] please use the international
              units that any one can understand )]
            </li>
          </ul>
        </div>

        <div class="category">
          <h5>[items type i.e Vegetables,Fruits,Meat,Seafood etc]</h5>
          <ul>
            <li>
              [items name and weekly quantity(please provide the weekly quantity
              means that one multiply to 7 to get weekly quantity of each i.e if
              in meal we use 1 kg oil then you have to multiply 1 with 7 to get
              weekly quantity [you dont have to show the calculations , just
              show the value of weekly quantity] please use the international
              units that any one can understand )]
            </li>
          </ul>
        </div>
      </div>
    </div>

       
      
    </div>
</div>
    </div>
</div>

    """

        
    )

        response = client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"""
You are a meal planning assistant. Provide the meal plan in HTML format only, with no additional commentary. The plan should be for {servings} servings, where each (total serving's) total calories must  equals to {total_calories} for example the servings are {servings} and demanding calories are {total_calories} so you have to design the meal plan as where the total sevings/meals calories should be equal to the {total_calories}. Design a balanced meal plan that includes lean protein, healthy fats, whole grains, and vegetables. Each recipe should list precise ingredient measurements to meet the calorie goal. Ensure a good macronutrient balance in each dish, with a clear calorie breakdown per meal and per ingredient where possible.
"""

                        f"Ensure the meal plan consists of exactly {servings} meals, each corresponding to one serving. "
                        "Follow the provided structure and do not include any additional information, headers, or categories like 'breakfast' or 'lunch'. "
                        "Avoid using escape characters such as '\\n' or '\\'. Only use the specified HTML tags."
                    )
                },
                {"role": "user", "content": prompt}
            ],
        )
        
        meal_plan_content = response.choices[0].message.content.replace('```html', '').replace('```', '').strip()
        
        
        # Split content at the shopping list header
        split_marker = '<h1>Weekly Shopping List</h1>'
        parts = meal_plan_content.split(split_marker)

        # Generate meal plan PDF
        meal_plan_html = html_template.replace("{content}", parts[0]).replace("{title}", "Meal Plan")
        meal_plan_pdf = pdfkit.from_string(meal_plan_html, False, configuration=config)
        meal_plan_base64 = base64.b64encode(meal_plan_pdf).decode('utf-8')

        # Generate shopping list PDF
        shopping_list_html = html_template.replace("{content}", split_marker + parts[1]).replace("{title}", "Shopping List")
        shopping_list_pdf = pdfkit.from_string(shopping_list_html, False, configuration=config)
        shopping_list_base64 = base64.b64encode(shopping_list_pdf).decode('utf-8')

        return jsonify({
            "meal_plan_pdf": meal_plan_base64,
            "shopping_list_pdf": shopping_list_base64
        })
        
    except Exception as e:
        error_message = str(e)
        logging.error('Error generating response: %s', error_message)
        return jsonify({"error": error_message}), 500



# Route to serve the homepage
@app.route('/')
def home():
    return "Welcome to the MealPlannerDB!"

# Route to insert new user documents into the database
@app.route('/insert', methods=['POST'])
def insert_documents():
    try:
        data = request.form  # Parse form data from the request
        name = data.get('Your Name')
        email = data.get('Email Address')
        phone = data.get('Phone')
        subject = data.get('Subject')
        # Hash the user's password for security before storing it in the database
        password = bcrypt.hashpw(data.get('Password').encode('utf-8'), bcrypt.gensalt())

        if not name or not email or not phone or not subject:
            # If required fields are missing, return an error message
            return jsonify({"error": "Invalid input: Name, email, phone, and subject are required."}), 400

        # Check if a user with the same email already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"message": "Document with this email already exists"}), 400

        # Create a new user record and add it to the database
        new_user = User(name=name, email=email, phone=phone, subject=subject, password=password.decode('utf-8'))
        db.session.add(new_user)
        db.session.commit()

        # Return a success message along with the new user's ID
        return jsonify({"message": "Document inserted", "id": new_user.id})

    except Exception as e:
        # Log any errors and return an error message to the client
        logging.error('Error inserting document: %s', str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/show', methods=['GET'])
def show_user_data():
    user_id = request.headers.get('Authorization')
    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    try:
        # Use db.session.get() instead of User.query.get()
        user = db.session.get(User, int(user_id))
        if user:
            user_data = {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "phone": user.phone,
                "subject": user.subject,
                "subscription_status": user.subscription_status,
                "subscription_end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
                "free_plan_used": user.free_plan_used,
                "preferred_meal": user.preferred_meal,  # Changed from "family members"
                "dietary_restriction": user.dietary_restriction,  # Fixed typo
                "food_allergy": user.food_allergy,
                "servings": user.servings,
                "dislikes": user.dislikes,
                "total_calories": user.total_calories
            }
            # Note: We're not including the password field for security reasons
            return jsonify(user_data)
        else:
            return jsonify({"error": "User not found"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# update the data
@app.route('/update', methods=['PUT'])
def update_user_data():
    user_id = request.headers.get('Authorization')
    if not user_id:
        return jsonify({"error": "No user ID provided"}), 400

    try:
        user = db.session.get(User, int(user_id))
        if not user:
            return jsonify({"error": "User not found"}), 404

        data = request.json

        # Update fields if they are present in the request
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        if 'phone' in data:
            user.phone = data['phone']
        if 'subject' in data:
            user.subject = data['subject']
        if 'subscription_status' in data:
            user.subscription_status = data['subscription_status']
        if 'subscription_end_date' in data:
            user.subscription_end_date = datetime.strptime(data['subscription_end_date'], '%Y-%m-%d')
        if 'free_plan_used' in data:
            user.free_plan_used = data['free_plan_used']
        if 'preferred_meal' in data:
            user.preferred_meal = data['preferred_meal']
        if 'dietary_restriction' in data:
            user.dietary_restriction = data['dietary_restriction']
        if 'food_allergy' in data:
            user.food_allergy = data['food_allergy']
        if 'servings' in data: 
            user.servings = data['servings']
        if 'dislikes' in data:
            user.dislikes = data['dislikes']
        if 'total_calories' in data:
            user.total_calories = data['total_calories']

        db.session.commit()

        return jsonify({"message": "User data updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

# insert food pref into db
@app.route('/add_meal_preference', methods=['POST'])
def add_meal_preference():
    try:
        # Extract data from the request
        data = request.json
        preferred_meal = data.get('preferred_meal')
        dietary_restriction = data.get('dietary_restriction')
        food_allergy = data.get('food_allergy')
        servings = data.get('servings')
        dislikes = data.get('dislikes')
        total_calories = data.get('total_calories')

        # Validate that the user ID is provided
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "User ID is required."}), 400
        
        # Fetch the user from the database
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Update the user's meal preferences
        user.preferred_meal = preferred_meal
        user.dietary_restriction = dietary_restriction
        user.food_allergy = food_allergy
        user.servings = servings
        user.dislikes = dislikes
        user.total_calories = total_calories

        # Commit the changes
        db.session.commit()

        return jsonify({"message": "Meal preferences updated successfully"}), 200

    except Exception as e:
        logging.error('Error updating meal preference: %s', str(e))
        return jsonify({"error": str(e)}), 500


@app.route('/signup', methods=['POST'])
def signup():
    try:
        data = request.json
        name = data.get('Your Name')
        email = data.get('Email Address')
        password = data.get('Password')
        phone = data.get('Phone')
        subject = data.get('Subject')
        preferred_meal = data.get('preferredMeal')
        dietary_restriction = data.get('dietaryRestriction')
        food_allergy = data.get('foodAllergy')
        servings = data.get('servings')
        dislikes = data.get('dislikes')
        total_calories = data.get('totalCalories')

        if not name or not email or not password:
            return jsonify({"error": "Invalid input: Name, email, and password are required."}), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({"error": "User with this email already exists"}), 400

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            name=name,
            email=email,
            password=hashed_password.decode('utf-8'),
            phone=phone,
            subject=subject,
            preferred_meal=preferred_meal,
            dietary_restriction=dietary_restriction,
            food_allergy=food_allergy,
            servings=servings,
            dislikes=dislikes,
            total_calories=total_calories
        )
        db.session.add(new_user)
        db.session.commit()
        send_html_email(email, "Welcome to gbMeals!", html_content)
        return jsonify({"message": "User registered successfully", "id": new_user.id}), 201

    except Exception as e:
        logging.error('Error during signup: %s', str(e))
        return jsonify({"error": str(e)}), 500


# Admin credentials
# Admin credentials
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin_password"

# Route to handle user login
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        # Handle preflight CORS request
        response = jsonify({})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        # Handle actual login request
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        logging.debug(f"Login attempt for email: {email}")
        
        if not email or not password:
            logging.warning("Email or password missing in request")
            return jsonify({"error": "Email and password are required"}), 400
        
        # Check if the admin is trying to log in
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            logging.debug("Admin login successful")
            access_token = create_access_token(identity={"user_id": 0, "is_admin": True})
            return jsonify({
                "message": "Admin login successful",
                "access_token": access_token,
                "user_id": 0,
                "name": "Admin",
                "email": ADMIN_EMAIL,
                "is_admin": True,
                "redirect": "https://www.gbmeals.com/admin"
            }), 200
        
        # Find the user by email in the database
        user = User.query.filter_by(email=email).first()
        if not user:
             # If user is None, prompt to sign up
            logging.warning("Email not found. Please sign up.")
            return jsonify({"error": "Email not found. Please sign up."}), 404


        if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            logging.debug("Password check successful")
            access_token = create_access_token(identity={"user_id": user.id, "is_admin": False})
            return jsonify({
                "message": "Login successful",
                "access_token": access_token,
                "user_id": user.id,
                "name": user.name,
                "email": user.email,
                "redirect": "/"
            }), 200
        else:
            logging.warning("Invalid email or password")
            return jsonify({"error": "Invalid email or password"}), 401
    
    except Exception as e:
        logging.error(f'Error during login: {str(e)}', exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200




# @app.route('/send-pdf', methods=['POST'])
# def send_pdf():
#     data = request.json
#     email = data.get('email')
#     meal_plan_pdf = data.get('meal_plan_pdf')
#     shopping_list_pdf = data.get('shopping_list_pdf')
#     message = data.get('message', None)

#     user = User.query.filter_by(email=email).first()

#     if not user:
#         return jsonify({'error': 'User not found'}), 404

#     try:
#         # Process meal plan PDF
#         if isinstance(meal_plan_pdf, str) and ',' in meal_plan_pdf:
#             meal_plan_content = base64.b64decode(meal_plan_pdf.split(',')[1])
#         else:
#             meal_plan_content = base64.b64decode(meal_plan_pdf)

#         # Process shopping list PDF
#         if isinstance(shopping_list_pdf, str) and ',' in shopping_list_pdf:
#             shopping_list_content = base64.b64decode(shopping_list_pdf.split(',')[1])
#         else:
#             shopping_list_content = base64.b64decode(shopping_list_pdf)

#         msg = MIMEMultipart()
#         msg['From'] = SMTP_USER
#         msg['To'] = email
#         msg['Subject'] = "Your Meal Plan and Shopping List"

#         # Attach meal plan PDF
#         meal_plan_part = MIMEApplication(meal_plan_content, Name="meal_plan.pdf")
#         meal_plan_part['Content-Disposition'] = 'attachment; filename="meal_plan.pdf"'
#         msg.attach(meal_plan_part)

#         # Attach shopping list PDF
#         shopping_list_part = MIMEApplication(shopping_list_content, Name="shopping_list.pdf")
#         shopping_list_part['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
#         msg.attach(shopping_list_part)

#         # Add a text body to the email with optional message
#         email_body = "Please find attached your meal plan and shopping list PDFs."
#         if message:
#             email_body += f"\n\n{message}"

#         msg.attach(MIMEText(email_body, 'plain'))

#         # Send email
#         with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
#             server.login(SMTP_USER, SMTP_PASS)
#             server.sendmail(SMTP_USER, email, msg.as_string())

#         return jsonify({"message": "PDFs sent successfully"}), 200
#     except Exception as e:
#         logging.error('Error sending PDFs: %s', str(e))
#         return jsonify({"error": str(e)}), 500


html_contenttosend = """
<html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="und"><head><meta http-equiv="Content-Security-Policy" content="script-src 'none'; connect-src 'none'; object-src 'none'; form-action https://cdn.ampproject.org https://amp.stripo.email;"><meta charset="UTF-8"><meta content="width=device-width, initial-scale=1" name="viewport"><meta name="x-apple-disable-message-reformatting"><meta http-equiv="X-UA-Compatible" content="IE=edge"><meta content="telephone=no" name="format-detection"><title></title>
 <!--[if (mso 16)]>
      <style type="text/css"> a {text-decoration: none;} 
</style>
      <![endif]--><!--[if gte mso 9]>
      <style>sup { font-size: 100% !important; }</style>
      <![endif]--><!--[if gte mso 9]>
      <noscript>
         <xml>
           <o:OfficeDocumentSettings>
           <o:AllowPNG></o:AllowPNG>
           <o:PixelsPerInch>96</o:PixelsPerInch>
           </o:OfficeDocumentSettings>
         </xml>
      </noscript>
      <![endif]--><style type="text/css">.rollover:hover .rollover-first { max-height:0px!important; display:none!important;}.rollover:hover .rollover-second { max-height:none!important; display:block!important;}.rollover span { font-size:0px;}u + .body img ~ div div { display:none;}#outlook a { padding:0;}span.MsoHyperlink,span.MsoHyperlinkFollowed { color:inherit; mso-style-priority:99;}a.es-button { mso-style-priority:100!important; text-decoration:none!important;}a[x-apple-data-detectors],#MessageViewBody a { color:inherit!important; text-decoration:none!important; font-size:inherit!important; font-family:inherit!important; font-weight:inherit!important; line-height:inherit!important;}.es-desk-hidden { display:none; float:left; overflow:hidden; width:0; max-height:0; line-height:0; mso-hide:all;}@media only screen and (max-width:600px) {.es-m-p15b { padding-bottom:15px!important } .es-m-p20b { padding-bottom:20px!important } .es-m-p20r { padding-right:20px!important } .es-m-p20l { padding-left:20px!important } .es-p-default { } *[class="gmail-fix"] { display:none!important } p, a { line-height:150%!important } h1, h1 a { line-height:120%!important } h2, h2 a { line-height:120%!important } h3, h3 a { line-height:120%!important } h4, h4 a { line-height:120%!important } h5, h5 a { line-height:120%!important } h6, h6 a { line-height:120%!important } .es-header-body p { } .es-content-body p { } .es-footer-body p { } .es-infoblock p { } h1 { font-size:30px!important; text-align:left } h2 { font-size:24px!important; text-align:left } h3 { font-size:20px!important; text-align:left } h4 { font-size:24px!important; text-align:left } h5 { font-size:20px!important; text-align:left } h6 { font-size:16px!important; text-align:left } .es-header-body h1 a, .es-content-body h1 a, .es-footer-body h1 a { font-size:30px!important } .es-header-body h2 a, .es-content-body h2 a, .es-footer-body h2 a { font-size:24px!important } .es-header-body h3 a, .es-content-body h3 a, .es-footer-body h3 a { font-size:20px!important } .es-header-body h4 a, .es-content-body h4 a, .es-footer-body h4 a { font-size:24px!important } .es-header-body h5 a, .es-content-body h5 a, .es-footer-body h5 a { font-size:20px!important } .es-header-body h6 a, .es-content-body h6 a, .es-footer-body h6 a { font-size:16px!important } .es-menu td a { font-size:14px!important } .es-header-body p, .es-header-body a { font-size:14px!important } .es-content-body p, .es-content-body a { font-size:14px!important } .es-footer-body p, .es-footer-body a { font-size:14px!important } .es-infoblock p, .es-infoblock a { font-size:12px!important } .es-m-txt-c, .es-m-txt-c h1, .es-m-txt-c h2, .es-m-txt-c h3, .es-m-txt-c h4, .es-m-txt-c h5, .es-m-txt-c h6 { text-align:center!important } .es-m-txt-r, .es-m-txt-r h1, .es-m-txt-r h2, .es-m-txt-r h3, .es-m-txt-r h4, .es-m-txt-r h5, .es-m-txt-r h6 { text-align:right!important } .es-m-txt-j, .es-m-txt-j h1, .es-m-txt-j h2, .es-m-txt-j h3, .es-m-txt-j h4, .es-m-txt-j h5, .es-m-txt-j h6 { text-align:justify!important } .es-m-txt-l, .es-m-txt-l h1, .es-m-txt-l h2, .es-m-txt-l h3, .es-m-txt-l h4, .es-m-txt-l h5, .es-m-txt-l h6 { text-align:left!important } .es-m-txt-r img, .es-m-txt-c img, .es-m-txt-l img { display:inline!important } .es-m-txt-r .rollover:hover .rollover-second, .es-m-txt-c .rollover:hover .rollover-second, .es-m-txt-l .rollover:hover .rollover-second { display:inline!important } .es-m-txt-r .rollover span, .es-m-txt-c .rollover span, .es-m-txt-l .rollover span { line-height:0!important; font-size:0!important; display:block } .es-spacer { display:inline-table } a.es-button, button.es-button { font-size:18px!important; padding:10px 20px 10px 20px!important; line-height:120%!important } a.es-button, button.es-button, .es-button-border { display:inline-block!important } .es-m-fw, .es-m-fw.es-fw, .es-m-fw .es-button { display:block!important } .es-m-il, .es-m-il .es-button, .es-social, .es-social td, .es-menu { display:inline-block!important } .es-adaptive table, .es-left, .es-right { width:100%!important } .es-content table, .es-header table, .es-footer table, .es-content, .es-footer, .es-header { width:100%!important; max-width:600px!important } .adapt-img { width:100%!important; height:auto!important } .es-mobile-hidden, .es-hidden { display:none!important } .es-desk-hidden { width:auto!important; overflow:visible!important; float:none!important; max-height:inherit!important; line-height:inherit!important } tr.es-desk-hidden { display:table-row!important } table.es-desk-hidden { display:table!important } td.es-desk-menu-hidden { display:table-cell!important } .es-menu td { width:1%!important } table.es-table-not-adapt, .esd-block-html table { width:auto!important } .h-auto { height:auto!important } .img-7815 { width:332px!important } .img-8866 { width:277px!important } .img-5775 { height:48px!important } .es-text-7275 .es-text-mobile-size-24, .es-text-7275 .es-text-mobile-size-24 * { font-size:24px!important; line-height:150%!important } .es-text-9724 .es-text-mobile-size-24, .es-text-9724 .es-text-mobile-size-24 * { font-size:24px!important; line-height:150%!important } .es-text-9031 .es-text-mobile-size-14, .es-text-9031 .es-text-mobile-size-14 * { font-size:14px!important; line-height:150%!important } .es-text-8700 .es-text-mobile-size-20, .es-text-8700 .es-text-mobile-size-20 * { font-size:20px!important; line-height:150%!important } .es-text-2740 .es-text-mobile-size-20, .es-text-2740 .es-text-mobile-size-20 * { font-size:20px!important; line-height:150%!important } }@media screen and (max-width:384px) {.mail-message-content { width:414px!important } }</style>
 <style>*{scrollbar-width: thin;scrollbar-color: #888 transparent;}/* Chrome, Edge, Safari */::-webkit-scrollbar {width: 10px;height: 10px;}::-webkit-scrollbar-track {background: transparent;}::-webkit-scrollbar-thumb {background: #888;border-radius: 6px;border: 2px solid transparent;}::-webkit-scrollbar-thumb:hover {box-shadow: inset 0 0 6px rgba(0,0,0,0.3);}textarea::-webkit-scrollbar-track {margin: 15px;}</style></head>
 <body class="body" style="width:100%;height:100%;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;padding:0;Margin:0"><div dir="ltr" class="es-wrapper-color" lang="und" style="background-color:#EEEEEE"><!--[if gte mso 9]>
 <v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
   <v:fill type="tile"  color="#eee" origin="0.5, 0" position="0.5, 0"></v:fill>
 </v:background>
<![endif]--><table width="100%" cellspacing="0" cellpadding="0" class="es-wrapper" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;padding:0;Margin:0;width:100%;height:100%;background-repeat:repeat;background-position:center top;background-color:#EEEEEE"><tbody><tr><td valign="top" style="padding:0;Margin:0"><table cellspacing="0" cellpadding="0" align="center" class="es-header" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top"><tbody><tr><td align="center" bgcolor="#eeeeee" style="padding:0;Margin:0;background-color:#eeeeee"><table cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" class="es-header-body" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:600px"><tbody><tr><td align="left" style="padding:0;Margin:0;padding-top:5px"><table width="100%" cellpadding="0" cellspacing="0" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:600px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;padding-top:20px;padding-bottom:25px;font-size:0"><a target="_blank" href="https://www.gbmeals.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/12.png" alt="" height="51" class="img-5775" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a>
</td></tr><tr><td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank" href="https://www.gbmeals.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/banner_2_final_design_2_oXk.png" alt="" width="600" class="adapt-img" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td></tr><tr><td align="center" bgcolor="#000000" style="Margin:0;padding-top:35px;padding-right:70px;padding-bottom:20px;padding-left:70px"><span style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';color:#ffffff">Hi!</span>
 <p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"></p><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"></p><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"></p></td></tr>
 <tr><td align="center" bgcolor="#000000" style="padding:0;Margin:0;padding-bottom:20px;padding-right:60px;padding-left:60px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">It’s time to make meal planning easy for another week! Attached is your meal plan and shopping list for the week, designed to save you time and effort in the kitchen.</p></td></tr>
 <tr><td align="center" bgcolor="#000000" style="padding:0;Margin:0;padding-bottom:35px"><span class="es-button-border" style="border-style:solid;border-color:#2CB543;background:#ffffff;border-width:0px 0px 2px 0px;display:inline-block;border-radius:5px;width:auto;border-bottom:2px solid #738065"><a href="https://www.gbmeals.com/" target="_blank" class="es-button" style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#000000;font-size:14px;padding:10px 20px 10px 20px;display:inline-block;background:#ffffff;border-radius:5px;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #ffffff">Discover Now</a></span></td></tr></tbody></table>
</td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>
 <table cellspacing="0" cellpadding="0" align="center" class="es-content" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important"><tbody><tr><td align="center" bgcolor="#eeeeee" style="padding:0;Margin:0;background-color:#eeeeee"><table cellspacing="0" cellpadding="0" bgcolor="#000" align="center" class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#000;width:600px" role="none"><tbody><tr><td align="left" style="padding:0;Margin:0;padding-top:10px;padding-right:20px;padding-left:20px"><table width="100%" cellpadding="0" cellspacing="0" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:560px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" class="es-m-p15b es-text-9724" style="Margin:0;padding-right:70px;padding-left:70px;padding-top:15px;padding-bottom:10px"><h1 class="es-m-txt-c" style="Margin:0;font-family:arial, 'helvetica neue', helvetica, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:30px;font-style:normal;font-weight:normal;line-height:36px;color:#ffffff"><span class="es-text-mobile-size-24" style="font-size:24px;line-height:28.8px !important"> </span><strong> <span style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'">Here’s What’s Included</span> </strong><span class="es-text-mobile-size-24" style="line-height:28.8px !important;font-size:24px"> </span></h1>
</td></tr></tbody></table></td></tr></tbody></table></td></tr><tr><td align="left" style="padding:0;Margin:0;padding-right:20px;padding-left:20px"><table cellpadding="0" cellspacing="0" width="100%" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:560px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;font-size:0"><img width="35" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/underline.png" alt="" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></td></tr></tbody></table></td></tr></tbody></table></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-right:20px;padding-left:20px;padding-top:15px"><!--[if mso]><table style="width:560px" cellpadding="0" cellspacing="0"><tr><td style="width:160px" valign="top"><![endif]--><table cellpadding="0" cellspacing="0" align="left" class="es-left" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left"><tbody><tr><td align="left" class="es-m-p20b" style="padding:0;Margin:0;width:160px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank" href="https://www.gbmeals.com/tryfreefor30-days" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img width="160" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/pic_1.png" alt="" class="adapt-img" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a>
</td></tr></tbody></table></td></tr></tbody></table>
 <!--[if mso]></td><td style="width:20px"></td><td style="width:380px" valign="top"><![endif]--><table align="right" cellpadding="0" cellspacing="0" class="es-right" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right"><tbody><tr><td align="left" style="padding:0;Margin:0;width:380px"><table width="100%" role="presentation" cellpadding="0" cellspacing="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" class="es-text-8700" style="padding:0;Margin:0;padding-top:15px"><h2 class="es-text-mobile-size-20" style="Margin:0;font-family:arial, 'helvetica neue', helvetica, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:normal;line-height:24px;color:#ffffff"><strong>Weekly Meal Plan</strong></h2></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-top:10px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">&ZeroWidthSpace;A breakdown of meals for each day, so you can relax knowing your meals are sorted.</p></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-bottom:25px;padding-top:15px"><span class="es-button-border" style="border-style:solid;border-color:#2CB543;background:transparent;border-width:0px 0px 2px 0px;display:inline-block;border-radius:5px;width:auto;border-top:2px solid #ffffff;border-right:2px solid #ffffff;border-bottom:2px solid #ffffff;border-left:2px solid #ffffff"><a href="https://www.gbmeals.com/tryfreefor30-days" target="_blank" class="es-button" style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#ffffff;font-size:14px;padding:10px 20px 10px 20px;display:inline-block;background:transparent;border-radius:5px;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid transparent">Learn More</a>
 </span></td></tr></tbody></table></td></tr></tbody></table><!--[if mso]></td></tr></table><![endif]--></td></tr></tbody></table></td></tr></tbody></table>
 <table cellspacing="0" cellpadding="0" align="center" class="es-content" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important"><tbody><tr><td align="center" bgcolor="#eeeeee" style="padding:0;Margin:0;background-color:#eeeeee"><table cellspacing="0" cellpadding="0" bgcolor="#000" align="center" class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#000;width:600px" role="none"><tbody><tr><td align="left" style="Margin:0;padding-bottom:25px;padding-top:10px;padding-right:20px;padding-left:20px"><!--[if mso]><table style="width:560px" cellpadding="0" cellspacing="0"><tr><td style="width:160px" valign="top"><![endif]--><table cellpadding="0" cellspacing="0" align="left" class="es-left" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left"><tbody><tr><td align="left" class="es-m-p20b" style="padding:0;Margin:0;width:160px"><table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank" href="https://www.gbmeals.com/tryfreefor30-days" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/pic_2.png" alt="" width="160" class="adapt-img" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a>
</td></tr></tbody></table></td></tr></tbody></table>
 <!--[if mso]></td><td style="width:20px"></td><td style="width:380px" valign="top"><![endif]--><table cellpadding="0" cellspacing="0" align="right" class="es-right" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right"><tbody><tr><td align="left" style="padding:0;Margin:0;width:380px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" class="es-text-2740" style="padding:0;Margin:0;padding-top:15px"><h2 class="es-text-mobile-size-20" style="Margin:0;font-family:arial, 'helvetica neue', helvetica, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:normal;line-height:24px;color:#78856A"><strong> <span style="color:#ffffff">Shopping List</span> </strong></h2></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-top:10px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">A comprehensive list of ingredients, organized for a quick and efficient shopping experience.</p></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-bottom:25px;padding-top:15px"><span class="es-button-border" style="border-style:solid;border-color:#2CB543;background:transparent;border-width:0px 0px 2px 0px;display:inline-block;border-radius:5px;width:auto;border-top:2px solid #ffffff;border-right:2px solid #ffffff;border-bottom:2px solid #ffffff;border-left:2px solid #ffffff"><a href="https://www.gbmeals.com/tryfreefor30-days" target="_blank" class="es-button" style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#ffffff;font-size:14px;padding:10px 20px;display:inline-block;background:transparent;border-radius:5px;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid transparent">Learn More</a>
 </span></td></tr></tbody></table></td></tr></tbody></table><!--[if mso]></td></tr></table><![endif]--></td></tr></tbody></table></td></tr></tbody></table>
 <table align="center" cellspacing="0" cellpadding="0" class="es-content" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important"><tbody><tr><td align="center" bgcolor="#eeeeee" style="padding:0;Margin:0;background-color:#eeeeee"><table align="center" cellspacing="0" cellpadding="0" bgcolor="#000" class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#000;width:600px" role="none"><tbody><tr><td align="left" style="padding:0;Margin:0"><table cellpadding="0" cellspacing="0" width="100%" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:600px"><table width="100%" role="presentation" cellpadding="0" cellspacing="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" class="es-text-7275 es-m-p20l es-m-p20r es-m-p15b" style="padding:0;Margin:0;padding-top:15px;padding-bottom:10px"><h1 class="es-m-txt-c" style="Margin:0;font-family:arial, 'helvetica neue', helvetica, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:30px;font-style:normal;font-weight:normal;line-height:36px;color:#333333"><span class="es-text-mobile-size-24" style="line-height:28.8px !important;font-size:24px"> </span><strong> <span style="color:#ffffff">How to Customize Your Plan</span> </strong><span class="es-text-mobile-size-24" style="font-size:24px;line-height:28.8px !important"> </span></h1>
</td></tr><tr><td align="center" style="padding:0;Margin:0;font-size:0"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/underline.png" alt="" width="35" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></td></tr><tr><td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank" href="https://www.gbmeals.com/tryfreefor30-days" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/banner2_1.gif" alt="" width="600" class="adapt-img" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td></tr>
 <tr><td align="center" bgcolor="#000000" style="Margin:0;padding-top:20px;padding-bottom:35px;padding-right:45px;padding-left:45px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">Remember, you can customize your meal plan at any time! Simply log into your account on our website to change your preferences and update your plan to better suit your tastes. Simply download the attached PDF, head to the store, and you’re ready to go!</p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>
 <table cellspacing="0" cellpadding="0" align="center" class="es-footer" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top"><tbody><tr><td align="center" bgcolor="#eeeeee" style="padding:0;Margin:0;background-color:#eeeeee"><table cellspacing="0" cellpadding="0" bgcolor="#000000" align="center" class="es-footer-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#000000;width:600px" role="none"><tbody><tr><td align="left" style="padding:0;Margin:0"><table width="100%" cellspacing="0" cellpadding="0" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td valign="top" align="center" style="padding:0;Margin:0;width:600px"><table width="100%" cellspacing="0" cellpadding="0" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" class="es-text-9031" style="padding:0;Margin:0;padding-top:15px;padding-right:35px;padding-left:35px"><p class="es-text-mobile-size-14" style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">If you have any preferences or changes for future plans, feel free to let us know. We’re always here to help you get the most out of your GBMeal experience.</p>
<p class="es-text-mobile-size-14" style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><br></p><p class="es-text-mobile-size-14" style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px">Enjoy your week ahead!</p><p style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><br></p></td></tr>
 <tr><td align="center" style="padding:0;Margin:0;padding-right:55px;padding-bottom:15px;padding-left:55px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><strong> </strong></p><p style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><strong>Warm regards,</strong></p><p style="Margin:0;mso-line-height-rule:exactly;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol';line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><strong>The GBMeal Team</strong></p>
<p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#ffffff;font-size:14px"><strong> </strong></p></td></tr></tbody></table></td></tr></tbody></table></td></tr>
 <tr><td align="left" style="padding:0;Margin:0;padding-right:20px;padding-left:20px"><table cellspacing="0" width="100%" cellpadding="0" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:560px"><table cellpadding="0" cellspacing="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;font-size:0"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/bg_feI.png" alt="" width="400" class="adapt-img img-7815" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></td></tr></tbody></table></td></tr></tbody></table></td></tr>
 <tr><td align="left" bgcolor="#000000" style="padding:0;Margin:0;padding-top:5px;padding-right:20px;padding-left:20px;background-color:#000000"><table width="100%" cellpadding="0" cellspacing="0" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="left" style="padding:0;Margin:0;width:560px"><table width="100%" role="presentation" cellpadding="0" cellspacing="0" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" style="padding:0;Margin:0;padding-top:25px;font-size:0"><table cellpadding="0" cellspacing="0" class="es-table-not-adapt es-social" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td align="center" valign="top" style="padding:0;Margin:0;padding-right:18px"><a target="_blank" href="https://www.facebook.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/facebooklogo_49052.png" alt="Fb" width="25" height="25" title="Facebook" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a>
</td><td align="center" valign="top" style="padding:0;Margin:0;padding-right:18px"><a target="_blank" href="https://www.twitter.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img title="X" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/twitter_5968958.png" alt="X" width="25" height="25" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td>
 <td valign="top" align="center" style="padding:0;Margin:0;padding-right:18px"><a target="_blank" href="https://www.instagram.com/gbmeals/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img title="Instagram" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/instagram_1384031.png" alt="Ig" width="25" height="25" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td>
 <td align="center" valign="top" style="padding:0;Margin:0;padding-right:18px"><a target="_blank" href="https://www.youtube.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img alt="Yt" width="25" height="25" title="YouTube" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/youtube_1384028.png" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td>
 <td align="center" valign="top" style="padding:0;Margin:0"><a target="_blank" href="https://www.linkedin.com/" style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img title="LinkedIn" src="https://fnzaeju.stripocdn.email/content/guids/CABINET_9d51d0cb43d7215811c5045a243cd2f8867c5aa07c9879c4bb732f8814b45f47/images/linkedin_3128219.png" alt="In" width="25" height="25" style="display:block;font-size:14px;border:0;outline:none;text-decoration:none"></a></td></tr></tbody></table></td></tr>
 <tr><td align="center" style="padding:0;Margin:0;padding-bottom:20px;padding-top:15px"><p style="Margin:0;mso-line-height-rule:exactly;font-family:arial, 'helvetica neue', helvetica, sans-serif;line-height:21px;letter-spacing:0;color:#333333;font-size:14px"><span style="color:#ffffff"> </span><span style="color:#ffffff;font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol'">© 2024 gbmeals. All rights reserved.</span><span style="color:#ffffff"> </span></p></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table>
 <table class="es-footer es-content" cellspacing="0" cellpadding="0" align="center" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top"><tbody><tr><td align="center" style="padding:0;Margin:0"><table class="es-content-body" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:transparent;width:600px" cellspacing="0" cellpadding="0" align="center" bgcolor="#00000000" role="none"><tbody><tr><td align="left" style="padding:0;Margin:0;padding-right:20px;padding-left:20px"><table cellspacing="0" cellpadding="0" width="100%" role="none" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td valign="top" align="center" style="padding:0;Margin:0;width:560px"><table cellspacing="0" cellpadding="0" width="100%" role="presentation" style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px"><tbody><tr><td class="es-infoblock made_with" align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank" href="https://stripo.email/?utm_source=user-template" style="mso-line-height-rule:exactly;text-decoration:underline;color:#CCCCCC;font-size:12px"><img src="https://ety.stripocdn.email/content/guids/CABINET_9df86e5b6c53dd0319931e2447ed854b/images/64951510234941531.png" alt="" width="125" style="display:block;font-size:14px;border:0;outline:none;</tbody></table></td></tr></tbody></table></div></body></html>
"""

@app.route('/send-pdf', methods=['POST'])
def send_pdf():
    data = request.json
    email = data.get('email')
    meal_plan_pdf = data.get('meal_plan_pdf')
    shopping_list_pdf = data.get('shopping_list_pdf')
    message = data.get('message', None)
    html_content =html_contenttosend# New parameter for HTML content

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    try:
        # Process meal plan PDF
        if isinstance(meal_plan_pdf, str) and ',' in meal_plan_pdf:
            meal_plan_content = base64.b64decode(meal_plan_pdf.split(',')[1])
        else:
            meal_plan_content = base64.b64decode(meal_plan_pdf)

        # Process shopping list PDF
        if isinstance(shopping_list_pdf, str) and ',' in shopping_list_pdf:
            shopping_list_content = base64.b64decode(shopping_list_pdf.split(',')[1])
        else:
            shopping_list_content = base64.b64decode(shopping_list_pdf)

        msg = MIMEMultipart('alternative')  # Changed to 'alternative' for HTML support
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Your Meal Plan and Shopping List"

        # Create plain text version
        text_body = "Please find attached your meal plan and shopping list PDFs."
        if message:
            text_body += f"\n\n{message}"

        # Create HTML version
        if html_content:
            html_body = html_content
        else:
            html_body = f"""
            <html>
                <body>
                    <p>Please find attached your meal plan and shopping list PDFs.</p>
                    {f'<p>{message}</p>' if message else ''}
                </body>
            </html>
            """

        # Attach both plain text and HTML versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Create a new MIMEMultipart for mixed content (attachments)
        mixed_msg = MIMEMultipart('mixed')
        # Copy the headers
        for key in msg.keys():
            mixed_msg[key] = msg[key]
        # Attach the message body
        mixed_msg.attach(msg)

        # Attach meal plan PDF
        meal_plan_part = MIMEApplication(meal_plan_content, Name="meal_plan.pdf")
        meal_plan_part['Content-Disposition'] = 'attachment; filename="meal_plan.pdf"'
        mixed_msg.attach(meal_plan_part)

        # Attach shopping list PDF
        shopping_list_part = MIMEApplication(shopping_list_content, Name="shopping_list.pdf")
        shopping_list_part['Content-Disposition'] = 'attachment; filename="shopping_list.pdf"'
        mixed_msg.attach(shopping_list_part)

        # Send email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, mixed_msg.as_string())

        return jsonify({"message": "PDFs sent successfully"}), 200
    except Exception as e:
        logging.error('Error sending PDFs: %s', str(e))
        return jsonify({"error": str(e)}), 500

# Route to send a custom email with a PDF attachment
@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.get_json()  # Parse JSON data from the request
    
    # Ensure all required fields are provided
    if not data or not all(k in data for k in ("to", "subject", "body", "pdf_data", "pdf_name")):
        return jsonify({"error": "Invalid input: 'to', 'subject', 'body', 'pdf_data', and 'pdf_name' are required."}), 400
    
    to_address = data['to']
    subject = data['subject']
    body = data['body']
    pdf_data = data['pdf_data']
    pdf_name = data['pdf_name']
    
    try:
        # Decode base64-encoded PDF data
        pdf_content = base64.b64decode(pdf_data)

        # Create an email message with the PDF attached
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Attach the PDF to the email
        pdf_part = MIMEApplication(pdf_content, Name=pdf_name)
        pdf_part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
        msg.attach(pdf_part)

        # Send the email via SMTP
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_address, msg.as_string())

        # Return a success message
        return jsonify({"message": "Email sent successfully"}), 200

    except Exception as e:
        # Log any errors and return an error message to the client
        logging.error('Error sending email: %s', str(e))
        return jsonify({"error": str(e)}), 500


html_content = """
<html dir="ltr" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office" lang="und">

<head>
  <meta http-equiv="Content-Security-Policy"
    content="script-src 'none'; connect-src 'none'; object-src 'none'; form-action https://cdn.ampproject.org https://amp.stripo.email;">
  <meta charset="UTF-8">
  <meta content="width=device-width, initial-scale=1" name="viewport">
  <meta name="x-apple-disable-message-reformatting">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta content="telephone=no" name="format-detection">
  <title></title>
  <!--[if (mso 16)]>
     <style type="text/css"> a {text-decoration: none;} 
 </style>
     <![endif]--><!--[if gte mso 9]><style>sup { font-size: 100% !important; }</style><![endif]--><!--[if gte mso 9]>
 <noscript>
          <xml>
            <o:OfficeDocumentSettings>
            <o:AllowPNG></o:AllowPNG>
            <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
          </xml>
       </noscript>
 <![endif]--><!--[if !mso]><!-->
  <link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Roboto:400,400i,700,700i"><!--<![endif]-->
  <style type="text/css">
    .rollover:hover .rollover-first {
      max-height: 0px !important;
      display: none !important;
    }

    .rollover:hover .rollover-second {
      max-height: none !important;
      display: block !important;
    }

    .rollover span {
      font-size: 0px;
    }

    u+.body img~div div {
      display: none;
    }

    #outlook a {
      padding: 0;
    }

    span.MsoHyperlink,
    span.MsoHyperlinkFollowed {
      color: inherit;
      mso-style-priority: 99;
    }

    a.es-button {
      mso-style-priority: 100 !important;
      text-decoration: none !important;
    }

    a[x-apple-data-detectors],
    #MessageViewBody a {
      color: inherit !important;
      text-decoration: none !important;
      font-size: inherit !important;
      font-family: inherit !important;
      font-weight: inherit !important;
      line-height: inherit !important;
    }

    .es-desk-hidden {
      display: none;
      float: left;
      overflow: hidden;
      width: 0;
      max-height: 0;
      line-height: 0;
      mso-hide: all;
    }

    @media only screen and (max-width:600px) {
      .es-m-p20b {
        padding-bottom: 20px !important
      }

      .es-m-p20l {
        padding-left: 20px !important
      }

      .es-m-p0t {
        padding-top: 0px !important
      }

      .es-m-p20r {
        padding-right: 20px !important
      }

      .es-m-p35b {
        padding-bottom: 35px !important
      }

      .es-m-p0r {
        padding-right: 0px !important
      }

      .es-m-p15t {
        padding-top: 15px !important
      }

      .es-p-default {}

      *[class="gmail-fix"] {
        display: none !important
      }

      p,
      a {
        line-height: 150% !important
      }

      h1,
      h1 a {
        line-height: 120% !important
      }

      h2,
      h2 a {
        line-height: 120% !important
      }

      h3,
      h3 a {
        line-height: 120% !important
      }

      h4,
      h4 a {
        line-height: 120% !important
      }

      h5,
      h5 a {
        line-height: 120% !important
      }

      h6,
      h6 a {
        line-height: 120% !important
      }

      .es-header-body p {}

      .es-content-body p {}

      .es-footer-body p {}

      .es-infoblock p {}

      h1 {
        font-size: 28px !important;
        text-align: center
      }

      h2 {
        font-size: 20px !important;
        text-align: left
      }

      h3 {
        font-size: 20px !important;
        text-align: left
      }

      h4 {
        font-size: 24px !important;
        text-align: left
      }

      h5 {
        font-size: 20px !important;
        text-align: left
      }

      h6 {
        font-size: 16px !important;
        text-align: left
      }

      .es-header-body h1 a,
      .es-content-body h1 a,
      .es-footer-body h1 a {
        font-size: 28px !important
      }

      .es-header-body h2 a,
      .es-content-body h2 a,
      .es-footer-body h2 a {
        font-size: 20px !important
      }

      .es-header-body h3 a,
      .es-content-body h3 a,
      .es-footer-body h3 a {
        font-size: 20px !important
      }

      .es-header-body h4 a,
      .es-content-body h4 a,
      .es-footer-body h4 a {
        font-size: 24px !important
      }

      .es-header-body h5 a,
      .es-content-body h5 a,
      .es-footer-body h5 a {
        font-size: 20px !important
      }

      .es-header-body h6 a,
      .es-content-body h6 a,
      .es-footer-body h6 a {
        font-size: 16px !important
      }

      .es-menu td a {
        font-size: 14px !important
      }

      .es-header-body p,
      .es-header-body a {
        font-size: 14px !important
      }

      .es-content-body p,
      .es-content-body a {
        font-size: 16px !important
      }

      .es-footer-body p,
      .es-footer-body a {
        font-size: 14px !important
      }

      .es-infoblock p,
      .es-infoblock a {
        font-size: 12px !important
      }

      .es-m-txt-c,
      .es-m-txt-c h1,
      .es-m-txt-c h2,
      .es-m-txt-c h3,
      .es-m-txt-c h4,
      .es-m-txt-c h5,
      .es-m-txt-c h6 {
        text-align: center !important
      }

      .es-m-txt-r,
      .es-m-txt-r h1,
      .es-m-txt-r h2,
      .es-m-txt-r h3,
      .es-m-txt-r h4,
      .es-m-txt-r h5,
      .es-m-txt-r h6 {
        text-align: right !important
      }

      .es-m-txt-j,
      .es-m-txt-j h1,
      .es-m-txt-j h2,
      .es-m-txt-j h3,
      .es-m-txt-j h4,
      .es-m-txt-j h5,
      .es-m-txt-j h6 {
        text-align: justify !important
      }

      .es-m-txt-l,
      .es-m-txt-l h1,
      .es-m-txt-l h2,
      .es-m-txt-l h3,
      .es-m-txt-l h4,
      .es-m-txt-l h5,
      .es-m-txt-l h6 {
        text-align: left !important
      }

      .es-m-txt-r img,
      .es-m-txt-c img,
      .es-m-txt-l img {
        display: inline !important
      }

      .es-m-txt-r .rollover:hover .rollover-second,
      .es-m-txt-c .rollover:hover .rollover-second,
      .es-m-txt-l .rollover:hover .rollover-second {
        display: inline !important
      }

      .es-m-txt-r .rollover span,
      .es-m-txt-c .rollover span,
      .es-m-txt-l .rollover span {
        line-height: 0 !important;
        font-size: 0 !important;
        display: block
      }

      .es-spacer {
        display: inline-table
      }

      a.es-button,
      button.es-button {
        font-size: 16px !important;
        padding: 0px 0px 0px 0px !important;
        line-height: 120% !important
      }

      a.es-button,
      button.es-button,
      .es-button-border {
        display: inline-block !important
      }

      .es-m-fw,
      .es-m-fw.es-fw,
      .es-m-fw .es-button {
        display: block !important
      }

      .es-m-il,
      .es-m-il .es-button,
      .es-social,
      .es-social td,
      .es-menu {
        display: inline-block !important
      }

      .es-adaptive table,
      .es-left,
      .es-right {
        width: 100% !important
      }

      .es-content table,
      .es-header table,
      .es-footer table,
      .es-content,
      .es-footer,
      .es-header {
        width: 100% !important;
        max-width: 600px !important
      }

      .adapt-img {
        width: 100% !important;
        height: auto !important
      }

      .es-mobile-hidden,
      .es-hidden {
        display: none !important
      }

      .es-desk-hidden {
        width: auto !important;
        overflow: visible !important;
        float: none !important;
        max-height: inherit !important;
        line-height: inherit !important
      }

      tr.es-desk-hidden {
        display: table-row !important
      }

      table.es-desk-hidden {
        display: table !important
      }

      td.es-desk-menu-hidden {
        display: table-cell !important
      }

      .es-menu td {
        width: 1% !important
      }

      table.es-table-not-adapt,
      .esd-block-html table {
        width: auto !important
      }

      .h-auto {
        height: auto !important
      }

      .img-5080 {
        width: 200px !important
      }

      .img-1224 {
        width: 280px !important
      }

      .es-text-3613 .es-text-mobile-size-16,
      .es-text-3613 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-9870 .es-text-mobile-size-16,
      .es-text-9870 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-9610 .es-text-mobile-size-16,
      .es-text-9610 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-5700 .es-text-mobile-size-16,
      .es-text-5700 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-3855 .es-text-mobile-size-16,
      .es-text-3855 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-3485 .es-text-mobile-size-16,
      .es-text-3485 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }

      .es-text-4228 .es-text-mobile-size-16,
      .es-text-4228 .es-text-mobile-size-16 * {
        font-size: 16px !important;
        line-height: 150% !important
      }
    }

    @media screen and (max-width:384px) {
      .mail-message-content {
        width: 414px !important
      }
    }
  </style>
  <style>
    * {
      scrollbar-width: thin;
      scrollbar-color: #888 transparent;
    }

    /* Chrome, Edge, Safari */
    ::-webkit-scrollbar {
      width: 10px;
      height: 10px;
    }

    ::-webkit-scrollbar-track {
      background: transparent;
    }

    ::-webkit-scrollbar-thumb {
      background: #888;
      border-radius: 6px;
      border: 2px solid transparent;
    }

    ::-webkit-scrollbar-thumb:hover {
      box-shadow: inset 0 0 6px rgba(0, 0, 0, 0.3);
    }

    textarea::-webkit-scrollbar-track {
      margin: 15px;
    }
  </style>
</head>

<body class="body"
  style="width:100%;height:100%;-webkit-text-size-adjust:100%;-ms-text-size-adjust:100%;padding:0;Margin:0">
  <div dir="ltr" class="es-wrapper-color" lang="und" style="background-color:#EEEEEE"><!--[if gte mso 9]>
  <v:background xmlns:v="urn:schemas-microsoft-com:vml" fill="t">
    <v:fill type="tile"  color="#eeeeee" origin="0.5, 0" position="0.5, 0"></v:fill>
  </v:background>
 <![endif]-->
    <table width="100%" cellspacing="0" cellpadding="0" class="es-wrapper" role="none"
      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;padding:0;Margin:0;width:100%;height:100%;background-repeat:repeat;background-position:center top;background-color:#EEEEEE">
      <tbody>
        <tr>
          <td valign="top" style="padding:0;Margin:0">
            <table cellspacing="0" cellpadding="0" align="center" class="es-header" role="none"
              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top">
              <tbody>
                <tr>
                  <td align="center" style="padding:0;Margin:0">
                    <table cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" class="es-header-body"
                      role="none"
                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:600px">
                      <tbody>
                        <tr>
                          <td align="left" style="padding:0;Margin:0;padding-top:35px">
                            <table cellspacing="0" width="100%" cellpadding="0" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:600px">
                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;padding-bottom:35px;font-size:0">
                                            <a target="_blank" href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/logo22cc494b3c43bf1131ac7.png"
                                                alt="" width="280" class="img-1224"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/welcomebanner1_sSP.gif"
                                                alt="" width="600" class="adapt-img"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td align="left" bgcolor="#000000"
                            style="padding:0;Margin:0;padding-top:5px;padding-bottom:40px;background-color:#000000">
                            <table cellpadding="0" cellspacing="0" width="100%" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:600px">
                                    <table width="100%" role="presentation" cellpadding="0" cellspacing="0"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;padding-bottom:15px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:21px;letter-spacing:0;color:#606060;font-size:14px">
                                              <strong><span style="color:#ffffff">Hi!</span><a target="_blank"
                                                  style="mso-line-height-rule:exactly;text-decoration:underline;color:#ffffff;font-size:14px"
                                                  href=""></a></strong></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" bgcolor="#000000" class="es-text-3613"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-right:30px;padding-left:30px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#ffffff;font-size:14px">
                                              <strong> </strong><span class="es-text-mobile-size-16"
                                                style="font-size:16px">Welcome to GBMeal! We’re thrilled to have you on
                                                board. You’ve just made the first step toward simplifying your weekly
                                                meal planning and ensuring that you have delicious, nutritious meals
                                                ready every week.</span><strong> </strong></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0"><span class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#ffffff;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto;border-top:14px solid #ffffff;border-right:44px solid #ffffff;border-bottom:14px solid #ffffff;border-left:44px solid #ffffff"><a
                                                href="https://www.gbmeals.com/" target="_blank" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#738065;font-size:14px;padding:0px;display:inline-block;background:#ffffff;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:bold;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #ffffff">Discover
                                                Now</a></span></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td align="left" style="padding:0;Margin:0;padding-top:35px">
                            <table cellspacing="0" width="100%" cellpadding="0" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:600px">
                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;padding-bottom:5px">
                                            <h1
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:28px;font-style:normal;font-weight:bold;line-height:33.6px;color:#313131">
                                              What You Can <span style="color:#738065">Expect From Us</span></h1>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0"><img alt=""
                                              width="35"
                                              src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/underline.png"
                                              style="display:block;font-size:16px;border:0;outline:none;text-decoration:none">
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <tr class="es-mobile-hidden">
                          <td align="left" style="padding:0;Margin:0;padding-top:5px;padding-bottom:20px">
                            <!--[if mso]><table style="width:600px" cellpadding="0" cellspacing="0"><tr><td style="width:200px" valign="top"><![endif]-->
                            <table cellspacing="0" cellpadding="0" align="left" class="es-left" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left">
                              <tbody>
                                <tr>
                                  <td valign="top" align="center" class="es-m-p20b"
                                    style="padding:0;Margin:0;width:200px">
                                    <table width="100%" cellspacing="0" cellpadding="0" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" class="es-m-txt-l"
                                            style="padding:0;Margin:0;padding-left:25px;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/image1.png"
                                                alt="" width="175"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                            <!--[if mso]></td><td style="width:20px"></td><td style="width:380px" valign="top"><![endif]-->
                            <table cellspacing="0" cellpadding="0" align="right" class="es-right" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:380px">
                                    <table width="100%" cellspacing="0" cellpadding="0" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="left"
                                            style="Margin:0;padding-top:15px;padding-right:10px;padding-bottom:10px;padding-left:10px">
                                            <h2
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:bold;line-height:24px;color:#738065">
                                              Weekly Meal Plans</h2>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-text-5700"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-left:10px;padding-right:25px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:14px">
                                              <span class="es-text-mobile-size-16" style="font-size:16px">Each week,
                                                you’ll receive a personalize&ZeroWidthSpace;d meal plan with a detailed
                                                shopping list. Say goodbye to the daily "What’s for dinner?" dilemma!
                                                Your curated plan makes it easy to stay organized and
                                                well-prepared.</span></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" style="padding:0;Margin:0;padding-left:10px"><span
                                              class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#738065;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto"><a
                                                href="https://www.gbmeals.com/" target="_blank" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#FFFFFF;font-size:14px;padding:0px;display:inline-block;background:#738065;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #738065">Learn
                                                More</a></span></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table><!--[if mso]></td></tr></table><![endif]-->
                          </td>
                        </tr>
                        <!--[if !mso]><!-->
                        <tr class="es-desk-hidden"
                          style="display:none;float:left;overflow:hidden;width:0;max-height:0;line-height:0;mso-hide:all">
                          <td align="left" style="padding:0;Margin:0;padding-top:10px">
                            <table align="left" cellspacing="0" cellpadding="0" class="es-left" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left">
                              <tbody>
                                <tr>
                                  <td valign="top" align="center" class="es-m-p20b"
                                    style="padding:0;Margin:0;width:200px">
                                    <table width="100%" cellspacing="0" cellpadding="0" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" class="es-m-txt-l es-m-p20l"
                                            style="padding:0;Margin:0;padding-left:25px;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                width="175"
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/image1.png"
                                                alt=""
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                            <table cellpadding="0" align="right" cellspacing="0" class="es-right" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:380px">
                                    <table width="100%" cellspacing="0" cellpadding="0" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="left" class="es-m-p20l es-m-p0t"
                                            style="Margin:0;padding-top:15px;padding-right:10px;padding-bottom:10px;padding-left:10px">
                                            <h2
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:bold;line-height:24px;color:#738065">
                                              Weekly Meal Plans</h2>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-text-3855 es-m-p20l es-m-p20r"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-left:10px;padding-right:25px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:14px">
                                              <span class="es-text-mobile-size-16" style="font-size:16px">Each week,
                                                you’ll receive a personalize&ZeroWidthSpace;d meal plan with a detailed
                                                shopping list. Say goodbye to the daily "What’s for dinner?" dilemma!
                                                Your curated plan makes it easy to stay organized and
                                                well-prepared.</span></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-m-p20l es-m-p35b"
                                            style="padding:0;Margin:0;padding-left:10px"><span class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#738065;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto"><a
                                                href="" target="_blank" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#FFFFFF;font-size:14px;padding:0px;display:inline-block;background:#738065;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #738065">Learn
                                                More</a></span></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <!--<![endif]--><!--[if !mso]><!-->
                        <tr class="es-desk-hidden"
                          style="display:none;float:left;overflow:hidden;width:0;max-height:0;line-height:0;mso-hide:all">
                          <td align="left" style="padding:0;Margin:0;padding-bottom:35px">
                            <table cellpadding="0" cellspacing="0" align="left" class="es-left" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:219px">
                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" class="es-m-txt-l es-m-p20l es-m-p0r"
                                            style="padding:0;Margin:0;padding-right:25px;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/image2.png"
                                                alt="" width="194"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                            <table cellpadding="0" cellspacing="0" align="right" class="es-right" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:361px">
                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="left" class="es-m-p15t"
                                            style="Margin:0;padding-left:25px;padding-right:10px;padding-bottom:10px;padding-top:25px">
                                            <h2
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:bold;line-height:24px;color:#738065">
                                              Smart Shopping Lists</h2>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-text-9870 es-m-p20l"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-left:25px;padding-right:15px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:14px">
                                              <span class="es-text-mobile-size-16" style="font-size:16px"> </span></p>
                                            <p class="es-text-mobile-size-16"
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:16px">
                                              Save time and shop smarter! Our curated shopping lists ensure you have
                                              everything you need, making your trips to the grocery store faster and
                                              more efficient.</p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-m-p20l"
                                            style="padding:0;Margin:0;padding-left:25px"><span class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#738065;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto"><a
                                                target="_blank" href="https://www.gbmeals.com/" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#FFFFFF;font-size:14px;padding:0px;display:inline-block;background:#738065;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #738065">Learn
                                                More</a></span></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <!--<![endif]-->
                        <tr class="es-mobile-hidden">
                          <td align="left" style="padding:0;Margin:0;padding-bottom:35px">
                            <!--[if mso]><table style="width:600px" cellpadding="0" cellspacing="0"><tr><td style="width:361px" valign="top"><![endif]-->
                            <table cellpadding="0" cellspacing="0" align="left" class="es-left" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:left">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:361px">
                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="left"
                                            style="Margin:0;padding-left:25px;padding-right:10px;padding-bottom:10px;padding-top:25px">
                                            <h2
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:20px;font-style:normal;font-weight:bold;line-height:24px;color:#738065">
                                              Smart Shopping Lists</h2>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" class="es-text-9610"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-left:25px;padding-right:15px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:14px">
                                              <span class="es-text-mobile-size-16" style="font-size:16px"> </span></p>
                                            <p class="es-text-mobile-size-16"
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:16px">
                                              Save time and shop smarter! Our curated shopping lists ensure you have
                                              everything you need, making your trips to the grocery store faster and
                                              more efficient.</p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="left" style="padding:0;Margin:0;padding-left:25px"><span
                                              class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#738065;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto"><a
                                                href="https://www.gbmeals.com/" target="_blank" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#FFFFFF;font-size:14px;padding:0px;display:inline-block;background:#738065;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:normal;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #738065">Learn
                                                More</a></span></td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                            <!--[if mso]></td><td style="width:20px"></td><td style="width:219px" valign="top"><![endif]-->
                            <table cellpadding="0" cellspacing="0" align="right" class="es-right" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;float:right">
                              <tbody>
                                <tr>
                                  <td align="left" class="es-m-p20b" style="padding:0;Margin:0;width:219px">
                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;padding-right:25px;font-size:0">
                                            <a target="_blank" href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/image2.png"
                                                alt="" width="194"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table><!--[if mso]></td></tr></table><![endif]-->
                          </td>
                        </tr>
                      
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
            <table cellspacing="0" cellpadding="0" align="center" class="es-content" role="none"
              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important">
              <tbody>
                <tr>
                  <td align="center" style="padding:0;Margin:0">
                    <table cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" class="es-content-body"
                      role="none"
                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:600px">
                      <tbody>
                        <tr>
                          <td align="left" style="padding:0;Margin:0;padding-top:35px">
                            <table width="100%" cellspacing="0" cellpadding="0" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td valign="top" align="center" style="padding:0;Margin:0;width:600px">
                                    <table width="100%" cellspacing="0" cellpadding="0" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center"
                                            style="padding:0;Margin:0;padding-bottom:5px;padding-right:15px;padding-left:15px">
                                            <h1
                                              style="Margin:0;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;mso-line-height-rule:exactly;letter-spacing:0;font-size:28px;font-style:normal;font-weight:bold;line-height:33.6px;color:#313131">
                                              <strong>Tasty, Nutritious Recipes</strong></h1>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0"><img
                                              src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/underline.png"
                                              alt="" width="35"
                                              style="display:block;font-size:16px;border:0;outline:none;text-decoration:none">
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#738065;font-size:16px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/top_image1_KNO.png"
                                                alt="" width="600" class="adapt-img"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" bgcolor="#738065"
                                            style="Margin:0;padding-bottom:15px;padding-right:30px;padding-left:30px;padding-top:15px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#ffffff;font-size:16px">
                                              From wholesome breakfasts to satisfying dinners, we’ve got you covered
                                              with balanced and easy-to-make meals.</p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" bgcolor="#738065"
                                            style="padding:0;Margin:0;padding-bottom:35px;padding-left:25px"><span
                                              class="es-button-border"
                                              style="border-style:solid;border-color:#738065;background:#ffffff;border-width:14px 35px 14px 35px;display:inline-block;border-radius:8px;width:auto;border-top:14px solid #ffffff;border-right:34px solid #ffffff;border-bottom:14px solid #ffffff;border-left:34px solid #ffffff"><a
                                                href="https://www.gbmeals.com/" target="_blank" class="es-button"
                                                style="mso-style-priority:100 !important;text-decoration:none !important;mso-line-height-rule:exactly;color:#738065;font-size:14px;padding:0px;display:inline-block;background:#ffffff;border-radius:8px;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;font-weight:bold;font-style:normal;line-height:16.8px;width:auto;text-align:center;letter-spacing:0;mso-padding-alt:0;mso-border-alt:10px solid #ffffff">Learn
                                                More</a></span></td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0"><a target="_blank"
                                              href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#738065;font-size:16px"><img
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/offer_image_fIC.png"
                                                alt="" width="600" class="adapt-img"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
            <table cellspacing="0" cellpadding="0" align="center" class="es-footer" role="none"
              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top">
              <tbody>
                <tr>
                  <td align="center" style="padding:0;Margin:0">
                    <table cellspacing="0" cellpadding="0" bgcolor="#ffffff" align="center" class="es-footer-body"
                      role="none"
                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;background-color:#FFFFFF;width:600px">
                      <tbody>
                        <tr>
                          <td align="left" style="padding:0;Margin:0;padding-top:35px">
                            <table width="100%" cellpadding="0" cellspacing="0" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:600px">
                                    <table cellpadding="0" cellspacing="0" width="100%" role="presentation"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" class="es-text-3485"
                                            style="padding:0;Margin:0;padding-bottom:15px;padding-right:35px;padding-left:35px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#606060;font-size:14px">
                                              <span class="es-text-mobile-size-16" style="font-size:16px">If you have
                                                any questions or need assistance, feel free to reply to this email.
                                                We're here to help!&nbsp; Looking forward to helping you make meal
                                                planning easier. </span></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" class="es-text-4228"
                                            style="padding:0;Margin:0;padding-right:35px;padding-left:35px;padding-bottom:30px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:24px;letter-spacing:0;color:#333333;font-size:14px">
                                              <strong class="es-text-mobile-size-16" style="font-size:16px"> Warm
                                                regards, </strong></p>
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:21px;letter-spacing:0;color:#333333;font-size:14px">
                                              <strong> The GBMeal Team</strong></p>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;padding-bottom:35px;font-size:0">
                                            <a target="_blank" href="https://www.gbmeals.com/"
                                              style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                width="200"
                                                src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/logo22cc494b3c43bf1131ac7.png"
                                                alt="" class="img-5080"
                                                style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                        <tr>
                          <td align="left" bgcolor="#000000"
                            style="padding:0;Margin:0;padding-top:25px;padding-bottom:25px;background-color:#000000">
                            <table width="100%" cellpadding="0" cellspacing="0" role="none"
                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                              <tbody>
                                <tr>
                                  <td align="left" style="padding:0;Margin:0;width:600px">
                                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%"
                                      style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                      <tbody>
                                        <tr>
                                          <td align="center" style="padding:0;Margin:0;font-size:0">
                                            <table cellpadding="0" cellspacing="0" class="es-table-not-adapt es-social"
                                              role="presentation"
                                              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px">
                                              <tbody>
                                                <tr>
                                                  <td align="center" valign="top"
                                                    style="padding:0;Margin:0;padding-right:20px"><img alt="Fb"
                                                      width="23" height="23" title="Facebook"
                                                      src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/facebooklogo_49052.png"
                                                      style="display:block;font-size:16px;border:0;outline:none;text-decoration:none">
                                                  </td>
                                                  <td align="center" valign="top"
                                                    style="padding:0;Margin:0;padding-right:20px"><img width="23"
                                                      height="23" title="X"
                                                      src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/twitter_5968958.png"
                                                      alt="X"
                                                      style="display:block;font-size:16px;border:0;outline:none;text-decoration:none">
                                                  </td>
                                                  <td align="center" valign="top"
                                                    style="padding:0;Margin:0;padding-right:20px"><a target="_blank"
                                                      href="https://www.instagram.com/gbmeals/"
                                                      style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                        alt="Ig" width="23" height="23" title="Instagram"
                                                        src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/instagram_1384031.png"
                                                        style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                                  </td>
                                                  <td align="center" valign="top"
                                                    style="padding:0;Margin:0;padding-right:20px"><img title="YouTube"
                                                      src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/youtube_1384028.png"
                                                      alt="Yt" width="23" height="23"
                                                      style="display:block;font-size:16px;border:0;outline:none;text-decoration:none">
                                                  </td>
                                                  <td valign="top" align="center" style="padding:0;Margin:0"><a
                                                      target="_blank" href="https://www.gbmeals.com/"
                                                      style="mso-line-height-rule:exactly;text-decoration:underline;color:#2CB543;font-size:14px"><img
                                                        height="23" title="LinkedIn"
                                                        src="https://enjobkh.stripocdn.email/content/guids/CABINET_d4c7cf3d3287f63d3fd8ef8a939741b5964691d841a9e4036865138946aa62b4/images/linkedin_3128219.png"
                                                        alt="In" width="23"
                                                        style="display:block;font-size:16px;border:0;outline:none;text-decoration:none"></a>
                                                  </td>
                                                </tr>
                                              </tbody>
                                            </table>
                                          </td>
                                        </tr>
                                        <tr>
                                          <td align="center"
                                            style="padding:0;Margin:0;padding-bottom:5px;padding-top:20px">
                                            <p
                                              style="Margin:0;mso-line-height-rule:exactly;font-family:roboto, 'helvetica neue', helvetica, arial, sans-serif;line-height:21px;letter-spacing:0;color:#333333;font-size:14px">
                                              <span style="color:#ffffff">© 2024 gbmeals. All rights reserved.</span>
                                            </p>
                                          </td>
                                        </tr>
                                      </tbody>
                                    </table>
                                  </td>
                                </tr>
                              </tbody>
                            </table>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </td>
                </tr>
              </tbody>
            </table>
            <table class="es-footer es-content" cellspacing="0" cellpadding="0" align="center" role="none"
              style="mso-table-lspace:0pt;mso-table-rspace:0pt;border-collapse:collapse;border-spacing:0px;width:100%;table-layout:fixed !important;background-color:transparent;background-repeat:repeat;background-position:center top">
            </table>
  </div>
</body>

</html>
"""

def send_html_email(to_email, subject, html_content):
    # Create the email message
    message = MIMEMultipart()
    message['From'] = SMTP_USER
    message['To'] = to_email
    message['Subject'] = subject

    # Attach HTML content to the email
    message.attach(MIMEText(html_content, 'html'))

    try:
        # Connect to the SMTP server and send the email
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, message.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Error sending email: {e}")





def send_subscription_ending_email(email, name, end_date, subscription_status):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = email
        msg['Subject'] = "Your Subscription is Ending Soon!"

        # Determine the plan name based on the subscription status
        if subscription_status == 'pro':
            plan_name = "Starter"
        elif subscription_status == 'ultra_pro':
            plan_name = "Premium"
        else:
            plan_name = "Unknown"

        body = f"""
        Hello {name},

        We hope you've been enjoying your {plan_name} subscription with us!

        This is a friendly reminder that your subscription is set to end on {end_date.strftime('%Y-%m-%d')}.

        To continue enjoying our {plan_name} features, please renew your subscription before it expires`.

        If you have any questions or need assistance with renewal, please don't hesitate to contact our support team.

        Thank you for being a valued member of our community!

        Best regards,
        Team gb meals
        """
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, email, msg.as_string())

        logging.info(f"Subscription ending email sent to {email}")
    except Exception as e:
        logging.error(f"Error sending subscription ending email to {email}: {str(e)}")

def send_subscription_ending_emails():
    with app.app_context():
        three_days_from_now = datetime.now() + timedelta(days=3)
        users = User.query.filter(
            User.subscription_status.in_(['pro', 'ultra_pro']),
            User.subscription_end_date == three_days_from_now.date()
        ).all()

        if users:
            for user in users:
                send_subscription_ending_email(user.email, user.name, user.subscription_end_date, user.subscription_status)
        else:
            logging.info("No users with subscriptions ending in 3 days.")



def check_subscription_status():
    # Ensure we are inside the application context
    with app.app_context():  # This will provide the app context for the query
        # Query users with any subscription status that could be active (pro, ultra_pro)
        users = User.query.filter(User.subscription_status.in_(['pro', 'ultra_pro'])).all()

        for user in users:
            # Check if the plan has expired
            if user.subscription_end_date and datetime.now() > user.subscription_end_date:
                # Set subscription status to inactive
                user.subscription_status = 'inactive'
                user.subscription_end_date = None  # Set subscription_end_date to None
                db.session.commit()  # Commit changes to the database

        print("Checked and updated subscription statuses.")
def start_scheduler2():
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(check_subscription_status, 'interval', minutes=1)  # Run every minute
    scheduler.start()

    # To capture job execution and errors for debugging
    def job_listener(event):
        if event.exception:
            print(f"Job {event.job_id} failed")
        else:
            print(f"Job {event.job_id} completed successfully")

    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)  # Add the listener here


def start_scheduler():
    scheduler = BackgroundScheduler()
    # Schedule the email sending function to run daily
    scheduler.add_job(func=send_subscription_ending_emails, trigger="cron", hour=0)
    scheduler.start()
    logging.info("Scheduler started for sending subscription ending emails.")
# Run the application
if __name__ == '__main__':
    start_scheduler()
    start_scheduler2()
    initialize_database()  # Initialize the database before starting the server
    app.run(debug=False, host="0.0.0.0", port="5000")  # Run the app on port 5000 with debugging disabled