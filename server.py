# server restful api for the ticketing project
# author : yousef javaherian
import tornado.web
import tornado.ioloop
import mysql.connector
from tornado.options import define, options
import os
from binascii import hexlify

define("port", default=4001, help="server port", type=int)
define("mysql_host", default="localhost", help="mysql server ip and port")
define("mysql_database", default="ticketing_api_db", help="application database name ")
define("mysql_user", default="root", help="database user name")
define("mysql_password", default="77yousef", help="database password")


# our api class inherited from tornado web application:
class Application(tornado.web.Application):
    def __init__(self):
        # all handlers are query string request handlers:
        handlers = [
                    (r"/signup", SignupHandler),
                    (r"/login", LoginHandler),
                    (r"/logout", LogoutHandler),
                    (r"/sendticket", SendTicketHandler),
                    (r"/sendrespond", SendResHandler),
                    (r"/getticket", GetTicketHandler),
                    (r"/getrespond", GetResHandler),
                    (r"/editticketstatus", EditTicketHandler),
                    (r"/getmyinfo", GetMyInfoHandler),
                    (r".*", DefaultHandler)
                    ]
        super().__init__(handlers)
        # a wrapper around sql database:
        self.db = mysql.connector.connect(host=options.mysql_host, database=options.mysql_database,
                                          user=options.mysql_user, passwd=options.mysql_password)
        self.cursor = self.db.cursor()
        # self.db = torndb.Connection(
        #   host=options.mysql_host, database=options.mysql_database,
        #   user=options.mysql_user, password=options.mysql_password)
        # a dynamic dictionary containing tokens of active users:
        # key = token , val = user_name
        self.token_dict = {}

# handlers :


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    @property
    def cursor(self):
        return self.application.cursor

    @property
    def token_dict(self):
        return self.application.token_dict


class SignupHandler(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        firstname = self.get_argument("firstname")
        lastname = self.get_argument("lastname")
        # check for username in database:
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user_name})
        result = self.cursor.fetchall()
        if len(result) > 0:
            output = {'msg': "this user_name is already taken out please enter another username.",
                      'status': 'Duplicate Username'}
            self.write(output)
            return
        # creating the user:
        insert_stmt = "INSERT INTO users (first_name, last_name, user_name, password, access_level) " \
                      "VALUES (%s,%s,%s,%s,%s)"
        val = (firstname, lastname, user_name, password, 'USER')
        self.cursor.execute(insert_stmt, val)
        self.db.commit()
        output = {'msg': "user created successfully.",
                  'status': 'OK'}
        self.write(output)


class LoginHandler(BaseHandler):
    def get(self):
        user_name = self.get_argument("username")
        password = self.get_argument("password")
        # check for username in database:
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s AND password = %(password)s", {'user_name': user_name, "password":password})
        result = self.cursor.fetchall()
        if len(result) == 0:
            output = {'msg': "invalid credentials please try again",
                      'status': 'Invalid'}
            self.write(output)
            return
        # check for multiple logins:
        if user_name in self.token_dict.values():
            output = {'msg': "you have already logged in.",
                      'status': 'Multiple Logins'}
            self.write(output)
            return

        # creating a unique token for this user:
        token = str(hexlify(os.urandom(16)))
        while token in self.token_dict:
            token = str(hexlify(os.urandom(16)))
        self.token_dict[token] = user_name

        output = {'msg': "logged in successfully",
                  'token': token,
                  'status': 'OK'}
        self.write(output)


class LogoutHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        # check for token in dict:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return
        # deleting the token in dict:
        self.token_dict.pop(token)

        output = {'msg': "logged out successfully",
                  'status': 'OK'}
        self.write(output)


class SendTicketHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        subject = self.get_argument("subject")
        body = self.get_argument("body")
        # checking that the token is valid:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return
        # checking that the user is not admin
        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user})
        row = self.cursor.fetchall()[0]
        if row[4] == 'ADMIN':
            output = {'msg': "sorry admins can't send tickets.",
                      'status': 'Invalid Request'}
            self.write(output)
            return
        # creating a ticket:
        insert_stmt = "INSERT INTO tickets (subject, body, status, from_user) " \
                      "VALUES (%s,%s,%s,%s)"
        val = (subject, body, 'open', row[2])
        self.cursor.execute(insert_stmt, val)
        self.db.commit()
        output = {'msg': "ticket was send successfully.",
                  'status': 'OK'}
        self.write(output)
        return


class SendResHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        ticket_id = self.get_argument("ticket_id")
        body = self.get_argument("body")
        # checking that the token is valid:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return
        # checking that the user is admin
        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user})
        row = self.cursor.fetchall()[0]
        if row[4] == 'USER':
            output = {'msg': "sorry only admins can send responds.",
                      'status': 'Invalid Request'}
            self.write(output)
            return
        # checking that this is the only respond to the ticket:
        self.cursor.execute("SELECT * FROM responds WHERE ticket_id = %(ticket_id)s", {'ticket_id': ticket_id})
        result = self.cursor.fetchall()
        if len(result) > 0:
            output = {'msg': "sorry the ticket with this id has been already responded by admin with username {}"
                .format(result[0][1]), 'status': 'Invalid Request'}
            self.write(output)
            return
        # checking that a ticket with this id exist:
        self.cursor.execute("SELECT * FROM tickets WHERE ticket_id = %(ticket_id)s", {'ticket_id': ticket_id})
        result = self.cursor.fetchall()
        if len(result) == 0:
            output = {'msg': "sorry there is no ticket with this id.", 'status': 'Invalid Request'}
            self.write(output)
            return
        # creating a respond:
        insert_stmt = "INSERT INTO responds (body, from_admin, ticket_id) " \
                      "VALUES (%s,%s,%s)"
        val = (body, row[2], ticket_id)
        self.cursor.execute(insert_stmt, val)
        self.db.commit()
        output = {'msg': "respond was send successfully.",
                  'status': 'OK'}
        self.write(output)
        return


class GetTicketHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        # checking that the token is valid:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return
        # checking the user access level:
        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user})
        row = self.cursor.fetchall()[0]
        access_level = row[4]
        if access_level == 'ADMIN':
            # admins can view all the tickets:
            self.cursor.execute("SELECT * FROM tickets")
        elif access_level == 'USER':
            self.cursor.execute("SELECT * FROM tickets WHERE from_user = %(user_name)s", {"user_name": row[2]})

        # fetching the tickets:
        tickets = self.cursor.fetchall()
        output = {'msg': "tickets were retrieaved successfully",
                  'tickets': tickets,
                  'status': 'OK'}
        self.write(output)
        return


class GetResHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        # checking that the token is valid:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return

        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user})
        row = self.cursor.fetchall()[0]
        access_level = row[4]
        # gathering all tickets that this user has send:
        self.cursor.execute("SELECT ticket_id FROM tickets WHERE from_user = %(user_name)s", {'user_name': user})
        result = self.cursor.fetchall()
        tickets = []
        for itr in result:
            tickets.append(itr[0])
        # checking the user access level:
        if access_level == 'ADMIN':
            # admins can view all the responds:
            self.cursor.execute("SELECT * FROM responds")
            responds = self.cursor.fetchall()
            output = {'msg': "all of the responds were retrieaved successfully",
                      'responds': responds,
                      'status': 'OK'}

        elif access_level == 'USER':
            responds = []
            for ticket in tickets:
                self.cursor.execute("SELECT * FROM responds WHERE ticket_id = %(id)s", {"id": ticket})
                responds.extend(self.cursor.fetchall())
            output = {'msg': "all of the responds related to your sent tickets were retrieaved successfully"
                , 'responds': responds, 'status': 'OK'}
        self.write(output)
        return


class EditTicketHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        ticket_id = self.get_argument("ticket_id")
        new_status = self.get_argument("new_status")

        # checking that the token is valid:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return

        # checking the user access level:
        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {'user_name': user})
        row = self.cursor.fetchall()[0]
        access_level = row[4]
        if access_level == 'USER':
            output = {'msg': "sorry!, only admins can change a ticket status.",
                      'status': 'Invalid Request'}
            self.write(output)
            return

        # getting the ticket:
        self.cursor.execute("SELECT * FROM tickets WHERE ticket_id = %(id)s", {"id": ticket_id})
        ticket = self.cursor.fetchall()
        if len(ticket) == 0:
            output = {'msg': "there exist no ticket with this id",
                      'status': 'Bad Request'}
            self.write(output)
            return
        # checking the new status:
        if new_status != 'open' and new_status != 'closed' and new_status != 'in progress':
            output = {'msg': "new status can only be from the set {'open' , 'closed' , 'in progress'}",
                      'status': 'Bad Request'}
            self.write(output)
            return
        # changing the ticket:
        self.cursor.execute("UPDATE tickets SET status = %(new_status)s WHERE ticket_id = %(ticket_id)s",
                            {'new_status': new_status, 'ticket_id': ticket_id})
        self.db.commit()
        output = {'msg': "ticket status was successfully changed to {}".format(new_status),
                  'status': 'OK'}
        self.write(output)
        return


class GetMyInfoHandler(BaseHandler):
    def get(self):
        token = self.get_argument("token")
        # check for token in dict:
        if token not in self.token_dict:
            output = {'msg': "invalid token please input a valid token.",
                      'status': 'Invalid'}
            self.write(output)
            return
        user = self.token_dict[token]
        self.cursor.execute("SELECT * FROM users WHERE user_name = %(user_name)s", {"user_name": user})
        user_info = self.cursor.fetchall()[0]
        output = {'msg': "user information was retrieaved successfully",
                  'info': user_info,
                  'status': 'OK'}
        self.write(output)
        return

class DefaultHandler(BaseHandler):
    def get(self):
        self.write("welcome to the ticketing service !!"
                   "\n you can query this directories for the related tasks:"
                   "\n /signup , query parameters:firstname,lastname,username,password"
                   "\n /login , query parameters:username,password"
                   "\n /logout , query parameters:token"
                   "\n /sendticket , query parameters:token, subject, body"
                   "\n /sendrespond , query parameters:token ,ticket_id, body"
                   "\n /getticket , query parameters:token"
                   "\n /getrespond , query parameters:token"
                   "\n /editticketstatus , query parameters:token, ticket_id , new_status"
                   "\n /getmyinfo , query parameters:token")
        return


if __name__ == "__main__":
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    print("I'm listening on port {}".format(options.port))
    tornado.ioloop.IOLoop.current().start()