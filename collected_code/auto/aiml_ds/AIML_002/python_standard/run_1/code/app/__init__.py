from flask import Flask

app = Flask(__name__)

from routes import predict

app.register_blueprint(predict.bp)
