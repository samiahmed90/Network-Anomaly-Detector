# Import Flask to create our web application.
# Import render_template to display HTML pages.
from flask import Flask, render_template

# Create the Flask application instance.
app = Flask(__name__)

# Define the homepage route.
# This function runs when someone visits the root URL (/).
@app.route("/")
def home():
    # Display the dashboard HTML page.
    return render_template("index.html")


# Start the Flask development server when this file is executed directly.
if __name__ == "__main__":
    # Listen on all network interfaces on port 5000.
    # Debug mode is enabled temporarily during development.
    app.run(host="0.0.0.0", port=5000, debug=True)
