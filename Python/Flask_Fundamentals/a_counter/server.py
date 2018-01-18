from flask import Flask, render_template, request, redirect, session
import os
app = Flask(__name__)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    session["count"] = session.get("count",0) + 1
    return render_template('index.html', count=session['count'])

@app.route('/increment', methods=['POST'])
def increment_by_two():
    session['count']
    return redirect('/')

@app.route('/clear', methods=['POST'])
def clear():
    session['count'] = 0
    return redirect('/')



app.run(host='0.0.0.0',port=9090,debug=True)

