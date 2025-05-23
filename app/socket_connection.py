import socketio

global socketClient
is_connected = False

def connectSocket(server_path):
    try:
        socketClient = socketio.Client()
        socketClient.connect(server_path)
    except socketio.exceptions.ConnectionError as err:
        is_connected = False
        print("Error on socket connection")
    else:
        print("Connected to Socket")
        is_connected = True

def sendData(segmentData):
    try:
        socketClient.emit('segmentData', segmentData)
    except socketio.exceptions.BadNamespaceError as err:
        print("error sending data", err)