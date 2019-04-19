# simple command line client app for the ticketing project
# author : yousef javaherian
import requests
from enum import Enum
import time
import platform
import os


PORT = 4001
SERVER_ADDRESS = 'http://127.0.0.1:' + str(PORT) + '/'


class Methods(Enum):
    SIGNUP = SERVER_ADDRESS + 'signup?'
    LOGIN = SERVER_ADDRESS + 'login?'
    LOGOUT = SERVER_ADDRESS + 'logout?'
    SEND_TICKET = SERVER_ADDRESS + 'sendticket?'
    SEND_RESPOND = SERVER_ADDRESS + 'sendrespond?'
    GET_TICKET = SERVER_ADDRESS + 'getticket?'
    GET_RESPOND = SERVER_ADDRESS + 'getrespond?'
    EDIT_TICKET = SERVER_ADDRESS + 'editticketstatus?'
    GET_MY_INFO = SERVER_ADDRESS + 'getmyinfo?'


def options(options):
    while True:
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')
        for i in range(len(options)):
            print(str(i+1) + "." + options[i])
        cmd = input("Please input your operation number: ")
        if int(cmd) in range(1,len(options) + 1):
            return options[int(cmd) - 1]


def pretty_print_tickets_responds_user(tickets, responds):
    responded_tickets = {}
    for res in responds:
        responded_tickets[int(res[2])] = (res[0], res[1])
    if len(tickets) == 0:
        print("you have not send any tickets yet.")
    else:
        i = 0
        for itr in tickets:
            i += 1
            print("\n--------------------\nTicket#{} status:{}\nSubject:{}\n----------\n{}".format(i, itr[2], itr[0], itr[1]))
            if int(itr[4]) in responded_tickets:
                print("----------\nRespond from {}\n----------\n{}".
                      format(responded_tickets[itr[4]][1], responded_tickets[itr[4]][0]))


def pretty_print_tickets_responds_admin(tickets, responds):
    responded_tickets = {}
    for res in responds:
        responded_tickets[int(res[2])] = (res[0], res[1])
    if len(tickets) == 0:
        print("tickets database is empty!")
    else:
        i = 0
        for itr in tickets:
            i += 1
            print("\n--------------------\nTicket#{} status:{}\nId:{}\nFrom User:{}\nSubject:{}\n----------\n{}"
                  .format(i, itr[2], itr[4], itr[3], itr[0], itr[1]))
            if int(itr[4]) in responded_tickets:
                print("----------\nRespond from {}\n----------\n{}".format(responded_tickets[itr[4]][1],
                                                                         responded_tickets[itr[4]][0]))


def show_dashboard(token):
    # first lets see the access level of the user:
    response = requests.get(Methods.GET_MY_INFO.value + "token=" + token).json()
    access_level = response['info'][-1]
    firstname = response['info'][0]
    lastname = response['info'][1]
    print("Welcome to your Dashboard dear {} {}".format(firstname, lastname))
    if access_level == 'USER':
        while True:
            cmd = options(['Send a new Ticket', 'View your ticket/responds', 'Exit your dashboard'])
            if cmd == 'Send a new Ticket':
                print("Please fill out this fields to send your ticket:")
                subject = input("Subject:")
                body = input("BOdy:")
                response = requests.get(Methods.SEND_TICKET.value + "token=" + token + '&' +
                                        'subject=' + subject + '&' + 'body=' + body).json()
                print(response['msg'])
                time.sleep(2)
                continue
            if cmd == 'View your ticket/responds':
                response = requests.get(Methods.GET_TICKET.value + "token=" + token).json()
                tickets = response['tickets']
                response = requests.get(Methods.GET_RESPOND.value + "token=" + token).json()
                responds = response['responds']
                #########
                pretty_print_tickets_responds_user(tickets, responds)
                input("Type anything to go back to your dashboard...")
                continue
            if cmd == 'Exit your dashboard':
                print("Going back to Menu...")
                time.sleep(1)
                break

    if access_level == 'ADMIN':
        while True:
            cmd = options(['Send a Respond', 'View all of the ticket/responds', 'change a ticket status', 'Exit your dashboard'])

            if cmd == 'Send a Respond':
                print("Please fill out this fields to send your respond:")
                ticket_id = input("Ticket id:")
                body = input("Body:")
                response = requests.get(
                    Methods.SEND_RESPOND.value + "token=" + token + '&' + 'ticket_id=' + ticket_id + '&' + 'body=' + body).json()
                print(response['msg'])
                if response['status'] == 'OK':
                    # we need to close this ticket:
                    requests.get(Methods.EDIT_TICKET.value + "token=" + token + '&' + 'ticket_id=' + ticket_id + '&' + 'new_status=closed')
                time.sleep(2)
                continue

            if cmd == 'View all of the ticket/responds':
                response = requests.get(Methods.GET_TICKET.value + "token=" + token).json()
                tickets = response['tickets']
                response = requests.get(Methods.GET_RESPOND.value + "token=" + token).json()
                responds = response['responds']
                pretty_print_tickets_responds_admin(tickets, responds)
                input("Type anything to go back to your dashboard...")
                continue

            if cmd == 'change a ticket status':
                print("Please fill out this fields:")
                ticket_id = input("Ticket id:")
                new_status = input("tickets new status:")
                response = requests.get(Methods.EDIT_TICKET.value + "token=" + token + '&'
                                        + 'ticket_id=' + ticket_id +'&' + 'new_status=' + new_status).json()
                print(response['msg'])
                time.sleep(2)
                continue

            if cmd == 'Exit your dashboard':
                print("Going back to Menu...")
                time.sleep(1)
                break
    return


if __name__ == "__main__":
    while True:
        try:
            response = requests.get(SERVER_ADDRESS)
        except:
            print("could not make a successful connection to the server!\n"
                  " please check your internet connection or check that server is up and running on port {}".format(PORT))
            cmd = input("Press any key to try again...")
            continue
        break

    token = None
    while True:

        print("welcome to the ticketing service command prompt client app!")
        print("MENU")
        cmd = options(['Login', 'Dashboard', 'Sign up', 'Logout', 'Exit'])

        if cmd == 'Login':
            if token is not None:
                print("Please log out from your account before logging in with a new account.")
                time.sleep(1)
                continue
            while True:
                print("Please Enter your credentials:")
                username = input("Username :")
                password = input("Password :")
                response = requests.get(Methods.LOGIN.value + "username="+username+'&'+"password="+password).json()
                status = response['status']
                print(response['msg'])
                if status != 'OK':
                    cmd1 = options(['Retry', 'Go back to Menu'])
                    if cmd1 == 'Retry':
                        continue
                    else:
                        break
                else:
                    token = response['token']
                    show_dashboard(token)
                    break

        if cmd == 'Dashboard':
            if token is None:
                print("you need to login first...")
                time.sleep(1)
                continue
            else:
                show_dashboard(token)
                continue

        if cmd == 'Sign up':
            if token is not None:
                print("Please log out from your account before signing up a new account.")
                time.sleep(1)
                continue
            while True:
                print("Please Enter your info:")
                username = input("Username :")
                password = input("Password :")
                firstname = input("first name :")
                lastname = input("last name:")
                response = requests.get(
                    Methods.SIGNUP.value + "username=" + username + '&' + "password=" +
                    password + '&' + "firstname=" + firstname + '&' + "lastname=" + lastname).json()
                status = response['status']
                print(response['msg'])
                if status != 'OK':
                    cmd1 = options(['Retry', 'Go back to Menu'])
                    if cmd1 == 'Retry':
                        continue
                    else:
                        break
                else:
                    time.sleep(2)
                    break

        if cmd == 'Logout':
            if token is None:
                print("You have not logged in yet.")
                print("you will be redirecting to the menu in 2 seconds...")
            else:
                response = requests.get(Methods.LOGOUT.value + "token=" + token).json()
                print(response['msg'])
                token = None
            time.sleep(2)
            continue
        if cmd == 'Exit':
            if token is not None:
                response = requests.get(Methods.LOGOUT.value + "token=" + token).json()
                token = None
            print("Bye!")
            time.sleep(1)
            break