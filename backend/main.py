import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import db
from firebase_admin import auth
from google.cloud import storage

import flask
from flask import request
from flask import send_file

import traceback
import os
import json


# Check if db activating first time
if not len(firebase_admin._apps):

    # Fetch the service account key JSON file contents
    cred = credentials.Certificate('cred.json')

    # Initialize the app with a service account, granting admin privileges
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://mcc-fall-2019-g5-258415.firebaseio.com/'
    })

    # Credentials for google cloud storage
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "cred.json"

ref = db.reference('/')


import firebase_interaction as bfi
import FB_functions
import report_generate
import image_functions as img_func


app = flask.Flask(__name__)
app.config["IMAGE_UPLOADS"] = "img/uploads"


def get_uid_from(id_token):
    '''
    Function verifying token from client.
    Returns uid which can be used for user identifying.
    '''

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        return decoded_token

    except:
        return 'ERROR: Authenfication failed.'


def user_validate(uid):
    return True


def get_uid_from(id_token):
    '''
    Function verifying token from client.
    Returns uid which can be used for user identifying.
    '''

    try:
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']

        return uid

    except:
        return 'ERROR: Authenfication failed.'


@app.route('/')
def default_route():
    return 'Hello world!'

@app.route('/first_set_data', methods=['GET'])
def first_set_data():
    bfi.table_fill()
    return 'INFO::Table filling is done.'


@app.route('/update_data')
def update_data():
    pass


# TODO: Fix this function to post according to new requirements
@app.route('/project/<project_id>/upload_image', methods=['POST'])
def upload_image_to_project(project_id):

    image = request.files["image"]

    try:

        # user_id = get_uid_from(data['id_token']) # add user checking
        user_id = 'uid'
        filename = image.filename

        # Save image locally
        # image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        image.save('img/' + filename)
        images_names = img_func.image_resize('img/', filename)

        save_to_fb_dir = 'attachments/' + project_id + '/'

        img_func.image_upload('img/', save_to_fb_dir, images_names)

        for element in images_names:
            FB_functions.add_attachment(
                    project_id,
                    filename,
                    save_to_fb_dir + element,
                    'image')
            os.remove('img/{}'.format(element))

        return 'INFO: Image uploaded.'

    except Exception as e:
        print(traceback.format_exc())
        return 'ERROR: Image was not uploaded.\nException: {}\n{}'.format(e, traceback.print_exc())


# TODO: Fix this function to post according to new requirements
@app.route('/project/<project_id>/set_icon', methods=['POST'])
def upload_project_icon(project_id):

    image = request.files["image"]

    try:
        # user_id = get_uid_from(data['id_token']) # add user checking
        user_id = 'uid'
        filename = image.filename

        # Save image locally
        # image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        image.save('img/' + filename)
        images_names = img_func.image_resize('img/', filename)

        save_to_fb_dir = 'attachments/' + project_id + '/icon/'

        img_func.image_upload('img/', save_to_fb_dir, images_names)

        FB_functions.update_project(project_id, 'image_url', save_to_fb_dir)

        for element in images_names:
            FB_functions.add_attachment(
                    project_id,
                    filename,
                    save_to_fb_dir + element,
                    'project_icon')
            os.remove('img/{}'.format(element))

        return 'INFO: Image uploaded.'

    except Exception as e:
        print(traceback.format_exc())
        return 'ERROR: Project icon was not uploaded.\nException: {}\n{}'.format(e, traceback.print_exc())


# TODO: Fix this function to post according to new requirements
@app.route('/user/set_icon', methods=['POST'])
def upload_user_icon():

    data = request.args
    image = request.files["image"]

    try:
        # user_id = get_uid_from(data['id_token']) # add user checking
        user_id = 'uid'
        filename = image.filename

        # Save image locally
        # image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        image.save('img/' + filename)
        images_names = img_func.image_resize('img/', filename)

        save_to_fb_dir = 'attachments/' + user_id + '/'

        img_func.image_upload('img/', save_to_fb_dir, images_names)

        for element in images_names:
            os.remove('img/{}'.format(element))

        return 'INFO: User icon uploaded.'

    except Exception as e:
        print(traceback.format_exc())
        return 'ERROR: Project icon was not uploaded.\nException: {}\n{}'.format(e, traceback.print_exc())


# TODO: Fix this function to post according to new requirements
@app.route('/upload_image', methods=['POST'])
def upload_image():

    try:
        data = request.args
        image = request.files["image"]

        user_id = get_uid_from(data['id_token']) # add user checking
        project_id = data['project_id']
        filename = image.filename

        # Save image locally
        image.save(os.path.join(app.config["IMAGE_UPLOADS"], filename))
        images_names = img_func.image_resize(filename, 'img/')

        save_to_fb_dir = 'attachments/' + project_id + '/'

        attachment_id = img_func.image_upload('img/', save_to_fb_dir, images_names)

        return 'INFO: Image uploaded.'

    except:
        'ERROR: Image was not uploaded.'


# TODO: Fix this function to post according to new requirements
@app.route('/get_image/<path>/<filename>', methods=['GET'])
def get_image(path, filename):

    data = request.args
    quality = data['quality']

    img_func.image_download(path + '/', filename, quality)

    return 'INFO::Image downloaded'


#?? what about settings of profile and what profile is
@app.route('/users/<user_id>/get_profile_settings')
def get_profile_settings():
    return "This is get_profile_settings method. returns profile info"

@app.route('/users/create_user')
def create_user():
    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    FB_functions.create_user(uid_response,request.args["name"],request.args["email"],request.args["image_url"])
    return "OK"

@app.route('/set_profile_settings')
def set_profile_settings():
    return "This is set_profile_settings method. returns fails or not"


@app.route('/create_project', methods=['POST'])
def create_project():

    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    if(not(FB_functions.verify_user(uid_response))):
        return "ERROR: Not such user."

    data = request.args
    project_id = FB_functions.create_project(
            data['title'],
            data['is_shared'],
            data['key_words'],
            data['creator_id'],
            data['deadline'],
            data['description'],
            data['image_url'],
            data['last_modified'],
            data['is_media_available']
    )
    return project_id


@app.route('/project/<project_id>/delete', methods=['DELETE'])
def delete_project(project_id):

    # TODO: Add user check (if user admin or not)
    # if data.TOKEN is valid (check with firebase)
    #check for valid token
    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    #check that user exists
    if(not(FB_functions.verify_user(uid_response))):
        return "ERROR: Not such user."
    #check that user in the project
    user_id = uid_response
    if(not(FB_functions.does_user_in_project(user_id, project_id))):
        return "Error: User not in project"
    #check if user admin
    if (FB_functions.does_user_admin_of_project(user_id, project_id)):
        return FB_functions.delete_project(project_id)
    else:
        return "ERROR: user does not have rights to delete project"

    return "ERROR: Wrong project id."


@app.route('/project/<project_id>/add_members', methods=['POST'])
def add_members_to_project(project_id):

    #check for valid token
    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    #check that user exists
    if(not(FB_functions.verify_user(uid_response))):
        return "ERROR: Not such user."
    #check that user in the project
    user_id = uid_response
    if(not(FB_functions.does_user_in_project(user_id, project_id))):
        return "Error: User not in project"

    return FB_functions.add_members_to_project(users_id, project_id)


@app.route('/project/<project_id>/members')
def get_members_of_project(project_id):
    '''
    Returns dict of members which consist of user_id, project_id and role_id
    '''
    #check for valid token
    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    #check that user exists
    if(not(FB_functions.verify_user(uid_response))):
        return "ERROR: Not such user."
    #check that user in the project
    user_id = uid_response
    if(not(FB_functions.does_user_in_project(user_id, project_id))):
        return "Error: User not in project"

    members = FB_functions.get_members_of_project(project_id)

    return json.dumps(members)


@app.route('/project/<project_id>/add_task', methods=['POST'])
def set_task_to_project(project_id):

    #check for valid token
    id_token = request.headers["id_token"]
    uid_response = get_uid_from(id_token)
    if(uid_response == "ERROR: Authenfication failed."):
        return "ERROR: Authenfication failed."
    #check that user exists
    if(not(FB_functions.verify_user(uid_response))):
        return "ERROR: Not such user."
    #check that user in the project
    user_id = uid_response
    if(not(FB_functions.does_user_in_project(user_id, project_id))):
        return "Error: User not in project"

    data=request.args
    task_id = FB_functions.add_task_to_project(
            project_id,
            data["creater_id"],
            data["description"],
            data["status"],
            data["taskname"]
    )

    return json.dumps(task_id)


@app.route('/project/<project_id>/update', methods=['POST'])
def project_update(project_id):

    data=request.args

    param_name = data['parameter']
    param_value = data['value']

    res = FB_functions.update_project(project_id, param_name, param_value)

    return str(res)


@app.route('/task/<task_id>/status_update', methods=['PUT'])
def update_task_status(task_id):
    data=request.args
    FB_functions.update_task(task_id, data["task_status"])
    return "OK"


@app.route('/task/<task_id>/assign_to_user', methods=['POST'])
def assign_task_to_users(task_id):
    data=request.args
    FB_functions.assign_task_to_users(task_id, data["user_ids"])
    return "OK"


@app.route('/project/<project_id>/tasks')
def get_tasks_of_project(project_id):
    '''
    Get_tasks_of_project method.
    Returns list of tasks.
    '''

    tasks = FB_functions.get_tasks_of_project(project_id)

    return json.dumps(tasks)


# @app.route('/convert_image_to_task')
# def convert_image_to_task():
#     return "This is convert_image_to_task method. returns fails or not"


@app.route('/project/<project_id>/add_attachments', methods=['POST'])
def add_attachments_to_project(project_id):
    return "This is add_attachments_to_project method. returns fails or not"


@app.route('/project/<project_id>/generate_report')
def generate_project_report(project_id):
    '''
    This is generate_project_report method.
    Returns report file.
    '''

    report_name = report_generate.generate_project_report(project_id)

    # print(report_name)
    # if not report_name:
    #     return 'ERROR: Project not exist'

    # return report_name
    return send_file(report_name)


@app.route('/get_projects', methods=['GET'])
def get_list_of_projects():
    '''
    Get_list_of_projects method.
    Returns list of projects with all provided information.
    '''

    list_of_projects = FB_functions.get_list_of_projects_implementation(request.args["user_id"])

    return json.dumps(list_of_projects)


@app.route('/project/<project_id>/search', methods=['GET'])
def search_for_project(project_id):
    '''
    Search_for_project method. Searching for single project.
    Returns json with all information about project.
    '''

    project = FB_functions.search_for_project_implementation(project_id)

    return json.dumps(project)


@app.route('/get_image_resolution')
def get_image_resolution():
    return "This is get_image_resolution method. returns a new image"


@app.route('/send_notification')
def send_notification():
    return "This is send_notification method. sends a notification"


if __name__ == "__main__":

    app.run(host='0.0.0.0', debug = True, port = 8080)