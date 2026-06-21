import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
from callbacks import register_callbacks
from layout import make_layout

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.layout = make_layout()

register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=False)