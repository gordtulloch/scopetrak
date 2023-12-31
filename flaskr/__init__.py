from flask import  Flask, request, url_for, redirect, render_template
import os

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def home():
        return render_template("index.html")
    
    @app.route('/start', methods=['GET'])
    def start_page():
            return render_template('start.html')

    @app.route('/end', methods=['GET'])
    def end_page():
            return render_template('end.html')
    
    @app.route('/config', methods=['GET'])
    def config_form():
            return render_template('config.html')
    
    @app.route('/saveconfig', methods=['GET','POST'])
    def config_form():
            return render_template('saveconfig.html')
    from . import db
    db.init_app(app)

    return app




if __name__ == "__main__":
    app.run(debug=True)