from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import login_user, login_required, logout_user, current_user
import random
from string import ascii_uppercase
from flask_socketio import join_room, leave_room, send
from .models import Event, User
from . import db
import os
from werkzeug.utils import secure_filename

views = Blueprint('views', __name__)

@views.route('/')
@login_required
def home():
    return render_template('home.html', user=current_user)


@views.route('/profile')
@login_required
def profile():
    user = db.session.query(User).filter_by(id=current_user.id).first()
    print(f"Database profile_pic value: {user.profile_pic}") 
    print(f"Current profile_pic value: {current_user.profile_pic}")
    return render_template('profile.html', user=current_user)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@views.route('/update_profile_pic', methods=['POST'])
@login_required
def update_profile_pic():
    file = request.files.get('profile-pic')
    
    if file and file.filename != '' and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = secure_filename(file.filename)
        
        # Generate relative file path to save in the database
        relative_filepath = f"images/profile_pics/user_{current_user.id}_{filename}"
        
        # Get the absolute path to the 'static' folder
        static_folder = os.path.join(current_app.root_path, 'static')
        
        # Generate the full file path where the image will be saved
        full_filepath = os.path.join(static_folder, relative_filepath)
        print(f"Saving profile pic to: {full_filepath}")
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(full_filepath), exist_ok=True)
        
        # Save the file to the server
        file.save(full_filepath)

        # Update the user's profile_pic field in the database with the relative path
        current_user.profile_pic = relative_filepath
        db.session.commit()

        print(f"Updated profile_pic in database: {current_user.profile_pic}")

        # Refresh the current_user
        login_user(current_user)

        flash('Profile picture updated!', 'success')
    else:
        flash('Invalid file format or no file selected.', 'danger')

    return redirect(url_for('views.profile'))


@views.route('/chat')
@login_required
def chat():
    return render_template('chat.html', user=current_user)


rooms_dict = {}
def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)

        if code not in rooms_dict:
            break
    return code


@views.route('/rooms', methods=['GET', 'POST'])
@login_required
def rooms():
    session.clear()



    if request.method == 'POST':
        name = request.form.get('name')
        code = request.form.get('code')
        join = request.form.get('join', False)
        create = request.form.get('create', False)

        if not name:
            return render_template('rooms.html', user=current_user, error='Name is required.', code=code, name=name)
        if join != False and not code:
            return render_template('rooms.html', user=current_user, error='Code is required.', code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms_dict[room] = {'members': 0, 'messages': []}
        elif code not in rooms_dict:
            return render_template('rooms.html', user=current_user, error='Room does not exist.', code=code, name=name)
        
        session['room'] = room
        session['name'] = name
        return redirect(url_for('views.meeting'))
    return render_template('rooms.html', user=current_user)


























@views.route('/meeting')
@login_required
def meeting():
    room = session.get('room')
    if room is None or session.get("name") is None or room not in rooms_dict:
        return redirect(url_for('views.rooms'))
    return render_template('meeting.html', user=current_user, code=room, messages=rooms_dict[room]['messages'])

def init_socketio(socketio):

    @socketio.on('message')
    def message(data):
        room = session.get('room')
        if room not in rooms_dict:
            return
        
        content = {
            "name": session.get('name'),
            "message": data['data']
        }
        send(content, to=room)
        rooms_dict[room]['messages'].append(content) 
        print(f"(session.get('name')) said: {data['data']}")  

    #store date somewhere here (on the server)
    #data will be lost because we're storing in RAM, not in a database. We need to update to store in db



    @socketio.on('connect')
    def connect(auth):
        print("Connect event triggered")  
        room = session.get('room')
        name = session.get('name')
        print(f"Session room: {room}, name: {name}")  

        if not room or not name:
            print("Room or name not found in session") 
            return
        if room not in rooms_dict:
            print(f"Room {room} not found in rooms_dict")  
            leave_room(room)
            return
    
        join_room(room)
        send({"name": name, "message": "joined the room."}, to=room)
        rooms_dict[room]['members'] += 1
        print(f"{name} joined {room}")

    @socketio.on('disconnect')
    def disconnect():
        room = session.get('room')
        name = session.get('name')
        leave_room(room)

        if room in rooms_dict:
            rooms_dict[room]['members'] -= 1
            if rooms_dict[room]['members'] <= 0:
                del rooms_dict[room]
        send({"name": name, "message": "left the room."}, to=room)
        print(f"{name} left {room}")
















@views.route('/settings')
def settings():
    return render_template('settings.html', user=current_user)


@views.route('/edit_profile')
@login_required
def edit_profile():
    return render_template('edit_profile.html', user=current_user)



@views.route('/update-profile', methods=['POST'])
@login_required
def update_profile():
    # Get form data
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    username = request.form['username']
    email = request.form['email']

    # Update user details
    user = db.session.query(User).filter_by(id=current_user.id).first()
    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.email = email

    #commit
    db.session.commit()

    #flash message
    flash('Profile updated successfully!', 'success')


    return render_template('profile.html', user=current_user)