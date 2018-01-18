from flask import Flask, flash, render_template, request, redirect, session
import os, random
app = Flask(__name__)
#app.secret_key = os.urandom(24)
app.config['SESSION_TYPE'] = 'memcached'
app.config['SECRET_KEY'] = os.urandom(24)


def setSession():
    session['num'] = random.randint(1,100)


@app.route('/')
def index():
    session['num'] = session.get('num',None)
    if session['num'] == None:
        setSession()
    else:
	pass
    print session['num']
    return render_template('index.html')

@app.route('/guess', methods=['POST'])
def checkNumber():
    error = None
    success = None
    guess = request.form['guess']
    if request.method == 'POST':
      if guess.isdigit():
        numguess = int(guess)
        if numguess == session['num']:
            flash('Correct', 'success')
            return redirect('/')
        elif numguess > session['num']:
            flash('High', 'TryAgain')
        elif numguess < session['num']:
            flash('Low', 'TryAgain')
      else:
        flash('Not a valid guess', 'TryAgain') 
    elif isinstance(guess, str):
        flash('Not a valid guess', 'TryAgain')
    else:
        flash('Not a valid guess', 'TryAgain')
    
    return redirect('/')


@app.route('/reset', methods=['GET', 'POST'])
def reset():
    setSession()
    return redirect('/')

app.run(host='0.0.0.0',port=9090,debug=True)

      

