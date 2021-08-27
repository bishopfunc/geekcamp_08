from flask import *
from flask_sqlalchemy import SQLAlchemy, sqlalchemy
from sqlalchemy.exc import SQLAlchemyError

# from sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.config['SECRET_KEY'] = 'secret key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.sqlite'

db = SQLAlchemy(app)

class User(db.Model): 
  __tablename__ = 'user_table'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(32)) 
  internships = db.relationship('Internship', lazy=True, cascade='delete')

  def to_dict(self):
      return {
          'user_id': self.id,
          'user_name': self.name,
          'internships': [Internship.to_dict(internship) for internship in self.internships]
      }

class Internship(db.Model):
  __tablename__ = 'internship_table'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(32))
  memo = db.Column(db.String())
  priority = db.Column(db.Integer)
  user_id = db.Column(db.Integer, db.ForeignKey('user_table.id'), nullable=False)
  tasks = db.relationship('Task', lazy=True, cascade='delete')

  def to_dict(self):
      return {
          'internship_id': self.id,
          'internship_name': self.name,
          'memo': self.memo,
          'priority': self.priority,
          'tasks': [Task.to_dict(task) for task in self.tasks]
      }


class Task(db.Model):
  __tablename__ = 'task_table'

  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(32))
  start_date = db.Column(db.String(32))
  end_date = db.Column(db.String(32))
  is_complete = db.Column(db.Boolean, nullable=False, default=False)
  internship_id = db.Column(db.Integer, db.ForeignKey('internship_table.id'), nullable=False)

  def to_dict(self):
      return {
          'task_id': self.id,
          'task_name': self.name,
          'start_date': self.start_date,
          'end_date': self.end_date,
          'is_complete': self.is_complete,
      }

db.create_all()

    
test_json0 = {"req_num" : 0}
test_json1 = {
    "req_num": 1,
    "user_id": 2
}

test_json2 = {
    "req_num": 2,
    "user_id": 2,
    "internship_id": 0
}
test_json3 = {
    "req_num": 3,
    "user_id": 2,
    "internship_id": 1,
    "memo": "IT系、結構よさげ",
    "priority": 1,
    "tasks": [
        {"task_id": 3, "task_name": "応募", "start_date": "2021/08/27 00:00", "end_date": "2021/08/27 00:00", "is_complete": False},
        {"task_id": 4, "task_name": "面接本番", "start_date": "2021/08/27 00:00", "end_date": "2021/08/28 00:00", "is_complete": True}
    ]
}

test_json4 = {
    "req_num": 4,
    "user_id": 0,
    "internship_id": 0
}

@app.route('/test')
def index():
    user_ex = User(name='hogehoge')
    delete_user_all = db.session.query(User)
    db.session.add(user_ex)
    # db.session.commit()
    # db.session.delete(delete_user_all)
    db.session.commit()
    db.session.close()
    
    return jsonify({"data": [User.to_dict(user) for user in User.query.all()]})

@app.route('/', methods = ['POST', 'GET'])
def request_from_client():
    # for test_json in [test_json0, test_json3, test_json2, test_json1]:
        # if request.method == 'POST':
    test_json = test_json3
    if True:
        # json_from_client = request.json
        # data = request.data.decode('utf-8')
        # data = [ json.loads(s) for s in data if s != "" ]
        # json_from_client = json.loads(str(data))
        json_from_client = test_json
        app.logger.info('json_from_client: %s', json_from_client)
        req_num = json_from_client["req_num"]
        if req_num == 0:
            json_to_client = create_user(json_from_client)
        elif req_num == 1:
            json_to_client = internship_id_list(json_from_client)
        elif req_num == 2:
            json_to_client = internship_detail(json_from_client)
        elif req_num == 3:
            json_to_client = update_internship(json_from_client)
        elif req_num == 4:
            json_to_client = delete_internship(json_from_client)
        else:
            json_to_client = check_status() #TODO

    return jsonify(json_to_client)  
        # data = User.query.all()
    # return render_template('db_info.html', data=data)

    # return jsonify({"data": [User.to_dict(user) for user in User.query.all()]})
    # return redirect(url_for('index'))


def create_user(json):
    new_user = User()
    db.session.add(new_user)
    db.session.commit()
    db.session.close()
    new_user = db.session.query(User).first()
    new_json = {
        "status": check_status(),
        "user_id": new_user.id
    }
    
    return new_json

def internship_id_list(json):
    user_id = json["user_id"]
    internship_id_list = [internship.id for internship in Internship.query().filter(Internship.user_id==user_id).all()]
    new_json = {
        "status": check_status(),
        "internship_id": internship_id_list
    }
    return new_json

def internship_detail(json):
    user_id = json["user_id"]
    internship_id = json["internship_id"]
    my_internship = db.session.query(Internship).filter(Internship.user_id==user_id, Internship.id==internship_id)
    task_detail_list = [task.to_dict for task in Task.query().filter(Internship.user_id==user_id, Internship.id==internship_id)] #TODO
    new_json = {
        "status": check_status(),
        "memo": my_internship.memo,
        "priority": my_internship.priority,
        "tasks": task_detail_list
    }   
    return new_json

def update_internship(json):
    user_id = json["user_id"]
    internship_id = json["internship_id"]
    memo = json["memo"]
    priority =json["priority"]
    tasks = json["tasks"]
    
    #新規作成
    if internship_id == -1:
       internship_id = create_internship_id(user_id, internship_id)
    app.logger.info('internship_id: %s', internship_id)
    ###ここまで成功

    #制限して取得
    my_internship = db.session.query(Internship).filter(Internship.user_id==user_id, Internship.id==internship_id).one()    
    app.logger.info('Old')
    app.logger.info('my_internship: %s', my_internship)

    # app.logger.info('my_internship.memo: %s', my_internship.memo)
    # app.logger.info('my_internship.priority: %s', my_internship.priority)

    #DBの書き換え
    my_internship.memo = memo
    my_internship.priority = priority
    # task_list = update_tasks(user_id, internship_id, tasks)
    
    try:
        task_list = update_tasks(user_id, internship_id, tasks)
    except sqlalchemy.orm.exc.UnmappedInstanceError as e:
        # error = str(e.__dict__['orig'])
        # app.logger.info('error: %s', error)
        app.logger.info('e: %s', e)      

    app.logger.info('my_internship.memo: %s', my_internship.memo)
    app.logger.info('my_internship.priority: %s', my_internship.priority)

    app.logger.info('New')
    app.logger.info('my_internship: %s', my_internship)
    # try:
    db.session.add(my_internship)
    # except SQLAlchemyError as e:
    #     # error = str(e.__dict__['orig'])
    #     # app.logger.info('error: %s', error)
    #     app.logger.info('e: %s', e)       
        
    db.session.commit()
    db.session.close()

    new_json = {
        "status": check_status(),
        "internship_id": internship_id
    }   
    return new_json

def create_internship_id(user_id, internship_id):

    new_internship = Internship(user_id=user_id)
    db.session.add(new_internship)
    
    db.session.commit()
    db.session.close()
    internship_id = db.session.query(Internship).filter(Internship.user_id==user_id).first().id
    return internship_id

def update_tasks(user_id, internship_id, tasks):
    app.logger.info('user_id: %s', user_id)
    app.logger.info('internship_id: %s', internship_id)
    app.logger.info('tasks: %s', tasks)

    tasks_db = db.session.query(Task).filter(Task.internship_id==internship_id).all()
    if tasks_db is None:
        app.logger.info('tasks_db_None: %s', tasks_db)
    else:
        app.logger.info('tasks_db_Exist: %s', tasks_db)
        #TODO
        try:
            db.session.delete(tasks_db) 
            # ここエラーでる
        except :
            db.session.commit()
        #ここまでOK

    json_task_id_list = [task["task_id"] for task in tasks]
    app.logger.info('json_task_id_list: %s', json_task_id_list)
    # ここまでOK

    # for i in range(json_task_id_list[-1] + 1):
    for num, id in enumerate(json_task_id_list):
        new_task = Task(internship_id=internship_id,id=id) #この書き方は大丈夫？
    #   new_task = Task()
        app.logger.info('new_task: %s', new_task)
        app.logger.info('ここから心配')
    #   db.session.add(new_task)
    #   db.session.commit()

    #   new_task = db.session.query(Task).filter(Task.internship_id==internship_id).first() #書き換えとして扱う
    # idが書き換え不可能だからこうしてる？ 分岐させるのみ？

    #   new_task.id = [task["task_id"] for task in tasks] # id書き換え可能なのか？
    #   new_task.internship_id = [task["internship_id"] for task in tasks]
        new_task.name = tasks[num]["task_name"]
        new_task.start_date = tasks[num]["start_date"]
        new_task.end_date = tasks[num]["end_date"] 
        new_task.is_complete = tasks[num]["is_complete"] 
        app.logger.info('new_task.id : %s', new_task.id )
        app.logger.info('new_task.name: %s', new_task.name)
        app.logger.info('new_task.start_date: %s', new_task.start_date)
        app.logger.info('new_task.end_date: %s', new_task.end_date)
        app.logger.info('new_task.is_complete: %s', new_task.is_complete)

        db.session.add(new_task)
        app.logger.info('new_task: %s', new_task)
        #ここからか！
        try:
            db.session.commit()
        except:
            db.session.close()
    return [task.to_dict for task in Task.query().filter(Task.internship_id==internship_id).all()]

def delete_internship(json):
    user_id = json["user_id"]
    internship_id = json["internship_id"] 
    my_internship = db.session.query(Internship).filter(Internship.user_id==user_id, Internship.id==internship_id) 
    db.session.delete(my_internship)  
    
    new_json = {
        "status": check_status(),
    }
    return new_json

def check_status():
    status = 0
    return status 

# @app.route('/db')
# def show_table():
#     return jsonify({"data": [User.to_dict(user) for user in User.query.all()]})




if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=True)