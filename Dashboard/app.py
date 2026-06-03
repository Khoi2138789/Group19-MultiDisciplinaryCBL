import dash
from callbacks import register_callbacks

# Import the specific f/unction from your layout.py file
from layout import make_layout

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# 1. Set the layout by CALLING the function we imported
app.layout = make_layout()

# 2. Register the callbacks
register_callbacks(app)

# 3. Run the server
if __name__ == '__main__':
    app.run(debug=False)