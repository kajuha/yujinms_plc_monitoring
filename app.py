from flask import Flask, render_template, request
import json
import os
import random
import struct
import inspect

from multiprocessing import Process, Queue
import time

STATE_LOOP_HZ = 10
# STATE_LOOP_HZ = 0
# WHISPER_LOOP_HZ = 400
WHISPER_LOOP_HZ = 0

queue_tx = Queue()
QUEUE_RX_STATE_CLEAR_NUM = 10
queue_rx_state = Queue()
QUEUE_RX_WHISPER_CLEAR_NUM = 10
queue_rx_whisper = Queue()

app = Flask(__name__)
# 하기가 없으면 csv를 계속 캐싱하여 출력하므로
# 데이터는 갱신되었음에도 동일한 데이터가 출력됨
# 캐싱을 해제하는 코드임
app.config['TEMPLATES_AUTO_RELOAD'] = True

# args=(host, port, debug)
web_server = Process(target=app.run, args=('0.0.0.0', 5000, False))
# True로 해두면 Pallete Control이 동작하지 않음(버튼 동작하지 않음)
# web_server = Process(target=app.run, args=('0.0.0.0', 5000, True))

@app.route('/')
@app.route('/index.html')
@app.route('/pages-dashboard.html')
@app.route('/dashboard')
def dashboard_page() -> 'html':
	return render_template('pages-dashboard.html')

@app.route('/pages-positiontable.html')
def positiontable_page() -> 'html':
	return render_template('pages-positiontable.html')

@app.errorhandler(404)
def page_not_found(e) -> 'html':
	return render_template('pages-404.html'), 404

@app.errorhandler(500)
def internal_server_error(e) -> 'html':
	return render_template('pages-500.html'), 500

@app.route('/post/simpleJogFrontButtonDown', methods=['POST'], endpoint="front_pushed")
@app.route('/post/simpleJogFrontButtonUp', methods=['POST'], endpoint="front_release")
@app.route('/post/simpleJogBackButtonDown', methods=['POST'], endpoint="back_pushed")
@app.route('/post/simpleJogBackButtonUp', methods=['POST'], endpoint="back_release")
@app.route('/post/simpleJogLeftButtonDown', methods=['POST'], endpoint="left_pushed")
@app.route('/post/simpleJogLeftButtonUp', methods=['POST'], endpoint="left_release")
@app.route('/post/simpleJogRightButtonDown', methods=['POST'], endpoint="right_pushed")
@app.route('/post/simpleJogRightButtonUp', methods=['POST'], endpoint="right_release")
@app.route('/post/simpleJogCwButtonDown', methods=['POST'], endpoint="cw_pushed")
@app.route('/post/simpleJogCwButtonUp', methods=['POST'], endpoint="cw_release")
@app.route('/post/simpleJogCcwButtonDown', methods=['POST'], endpoint="ccw_pushed")
@app.route('/post/simpleJogCcwButtonUp', methods=['POST'], endpoint="ccw_release")
@app.route('/post/simpleJogFLButtonDown', methods=['POST'], endpoint="fl_pushed")
@app.route('/post/simpleJogFLButtonUp', methods=['POST'], endpoint="fl_release")
@app.route('/post/simpleJogFRButtonDown', methods=['POST'], endpoint="fr_pushed")
@app.route('/post/simpleJogFRButtonUp', methods=['POST'], endpoint="fr_release")
@app.route('/post/simpleJogBLButtonDown', methods=['POST'], endpoint="bl_pushed")
@app.route('/post/simpleJogBLButtonUp', methods=['POST'], endpoint="bl_release")
@app.route('/post/simpleJogBRButtonDown', methods=['POST'], endpoint="br_pushed")
@app.route('/post/simpleJogBRButtonUp', methods=['POST'], endpoint="br_release")
def simpleJogButton() -> 'json':
	# print(request.endpoint)
	req_form = request.form.to_dict(flat=False)
	try:
		vel_x = float(req_form['simpleJogXVelInput'][0])
		vel_y = float(req_form['simpleJogYVelInput'][0])
		vel_z = float(req_form['simpleJogZVelInput'][0])
		acc_x = float(req_form['simpleJogXAccInput'][0])
		acc_y = float(req_form['simpleJogYAccInput'][0])
		acc_z = float(req_form['simpleJogZAccInput'][0])
		max_x = float(req_form['simpleJogXMaxInput'][0])
		max_y = float(req_form['simpleJogYMaxInput'][0])
		max_z = float(req_form['simpleJogZMaxInput'][0])
	except ValueError as e:
		return json.dumps({'error': True, 'message': 'Input value is Wrong'})
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	try:
		button = {
			'type' : Qtype.CmdJog,
			'button' : request.endpoint,
			'vel_x' : vel_x,
			'vel_y' : vel_y,
			'vel_z' : vel_z,
			'acc_x' : acc_x,
			'acc_y' : acc_y,
			'acc_z' : acc_z,
			'max_x' : max_x,
			'max_y' : max_y,
			'max_z' : max_z
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/simpleJogStopButton', methods=['POST'], endpoint="jog_stop")
def simpleJogStopButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		button = {
			'type' : Qtype.CmdStop,
			'button' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/simplePositionControlButton', methods=['POST'], endpoint="pos_ctrl")
def simplePositionControlButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		vel_x = float(req_form['simplePositionXVelInput'][0])
		vel_y = float(req_form['simplePositionYVelInput'][0])
		vel_z = float(req_form['simplePositionZVelInput'][0])
		acc_x = float(req_form['simplePositionXAccInput'][0])
		acc_y = float(req_form['simplePositionYAccInput'][0])
		acc_z = float(req_form['simplePositionZAccInput'][0])
		max_x = float(req_form['simplePositionXMaxInput'][0])
		max_y = float(req_form['simplePositionYMaxInput'][0])
		max_z = float(req_form['simplePositionZMaxInput'][0])
		xm = float(req_form['simplePositionLXInput'][0])
		ym = float(req_form['simplePositionLYInput'][0])
		zdeg = float(req_form['simplePositionTZInput'][0])
	except ValueError as e:
		return json.dumps({'error': True, 'message': 'Input value is Wrong'})
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	try:
		button = {
			'type' : Qtype.CmdPos,
			'button' : request.endpoint,
			'vel_x' : vel_x,
			'vel_y' : vel_y,
			'vel_z' : vel_z,
			'acc_x' : acc_x,
			'acc_y' : acc_y,
			'acc_z' : acc_z,
			'max_x' : max_x,
			'max_y' : max_y,
			'max_z' : max_z,
			'xm' : xm,
			'ym' : ym,
			'zdeg' : zdeg
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/simpleJoyControlButton', methods=['POST'], endpoint="joy_ctrl")
def simpleJoyControlButton() -> 'json':
	# print(request.endpoint)
	req_form = request.form.to_dict(flat=False)
	try:
		vel_x = float(req_form['joystickTwistX'][0])
		vel_y = float(req_form['joystickTwistY'][0])
		vel_z = float(req_form['joystickTwistZ'][0])
		acc_x = float(req_form['simpleJoyXAccInput'][0])
		acc_y = float(req_form['simpleJoyYAccInput'][0])
		acc_z = float(req_form['simpleJoyZAccInput'][0])
		max_x = float(req_form['simpleJoyXMaxInput'][0])
		max_y = float(req_form['simpleJoyYMaxInput'][0])
		max_z = float(req_form['simpleJoyZMaxInput'][0])
	except ValueError as e:
		return json.dumps({'error': True, 'message': 'Input value is Wrong'})
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	try:
		button = {
			'type' : Qtype.CmdJoy,
			'button' : request.endpoint,
			'vel_x' : vel_x,
			'vel_y' : vel_y,
			'vel_z' : vel_z,
			'acc_x' : acc_x,
			'acc_y' : acc_y,
			'acc_z' : acc_z,
			'max_x' : max_x,
			'max_y' : max_y,
			'max_z' : max_z
		}
		print(button)
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/simplePlatformInitButton', methods=['POST'], endpoint="platform_init")
def simplePlatformInitButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		button = {
			'type' : Qtype.CmdInit,
			'button' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})
	
@app.route('/post/simplePlatformClearErrorButton', methods=['POST'], endpoint="platform_clear_error")
def simplePlatformClearErrorButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		button = {
			'type' : Qtype.CmdClearError,
			'button' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})
	
@app.route('/post/ptStopButton', methods=['POST'], endpoint="pt_stop")
@app.route('/post/simplePositionStopButton', methods=['POST'], endpoint="pos_stop")
def simplePositionStopButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	try:
		button = {
			'type' : Qtype.CmdStop,
			'button' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/ptSendButton', methods=['POST'], endpoint="pt_ctrl")
def ptSendButton() -> 'json':
	req_form = request.form.to_dict(flat=False)
	# print('req_form: ', req_form)
	try:
		ptOrderString = req_form['ptOrder'][0]
		ptOrderList = ptOrderString.split(',')
		# # 숫자로 파싱되는지? 포지션테이블의 번호와 모두 일치하는지? 확인
		# print('ptOrderList: ', ptOrderList)

		orderList = []
		for ptOrder in ptOrderList:
			orderList.append(int(ptOrder))
		# print(orderList)

		posTables = []
		formLength = len(req_form['pt_num'])
		for i in range(formLength):
			postable = {
				'num' : int(req_form['pt_num'][i]),
				'type' : int(req_form['pt_type'][i]),
				'x' : float(req_form['pt_x'][i]),
				'y' : float(req_form['pt_y'][i]),
				'z' : float(req_form['pt_z'][i]),
				'xvel' : float(req_form['pt_xvel'][i]),
				'yvel' : float(req_form['pt_yvel'][i]),
				'zvel' : float(req_form['pt_zvel'][i]),
				'xacc' : float(req_form['pt_xacc'][i]),
				'yacc' : float(req_form['pt_yacc'][i]),
				'zacc' : float(req_form['pt_zacc'][i]),
				'xmax' : float(req_form['pt_xmax'][i]),
				'ymax' : float(req_form['pt_ymax'][i]),
				'zmax' : float(req_form['pt_zmax'][i]),
			}
			posTables.append(postable)
		# print(posTables)

	except ValueError as e:
		return json.dumps({'error': True, 'message': 'Input value is Wrong'})
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	try:
		button = {
			'type' : Qtype.CmdPT,
			'button' : request.endpoint,
			'orderList' : orderList,
			'posTables' : posTables
		}
		# print(button)
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/getPlatformStatus', methods=['POST'])
def getPlatformStatus() -> 'json':
	global queue_rx_state
	if not queue_rx_state.empty():
		# print(queue_rx_state.qsize())
		# tx_data = queue_rx_state.get()
		# print(tx_data)

		# 큐에 있는 데이터 중 최신 데이터만 가져옴
		rx_state = []
		for i in range(queue_rx_state.qsize()):
			rx_state = queue_rx_state.get()

		status = {}
		status['odom']  = {}
		status['odom']['linear'] = {}
		status['odom']['twist'] = {}
		status['platform'] = {}
		status['battery']  = {}
		status['battery']['voltage'] = {}
		status['battery']['current'] = {}
		status['battery']['percentage'] = {}
		try:
			# status['odom']['linear']['x'] = '{0:.2f}'.format(1+random.random())
			# status['odom']['linear']['y'] = '{0:.2f}'.format(2+random.random())
			# status['odom']['twist']['z'] = '{0:.2f}'.format(3+random.random())
			# status['platform']['mode'] = '{0:.2f}'.format(4+random.random())
			# status['platform']['state'] = '{0:.2f}'.format(5+random.random())
			# status['battery']['voltage'] = '{0:.2f}'.format(6+random.random())
			# status['battery']['current'] = '{0:.2f}'.format(7+random.random())
			# status['battery']['percentage'] = '{0:.2f}'.format(8+random.random())
			status['odom']['linear']['x'] = rx_state['odom']['linear']['x']
			status['odom']['linear']['y'] = rx_state['odom']['linear']['y']
			status['odom']['twist']['z'] = rx_state['odom']['twist']['z']
			status['platform']['mode'] = rx_state['platform']['mode']
			status['platform']['state'] = rx_state['platform']['state']
			status['battery']['voltage'] = rx_state['battery']['voltage']
			status['battery']['current'] = rx_state['battery']['current']
			status['battery']['percentage'] = rx_state['battery']['percentage']
			# print(status)
		except Exception as e:
			print(inspect.stack()[0][3], e)
			print(rx_state)
			return json.dumps({'error': True, 'message': str(e)})

		return json.dumps({'error': False, 'message': status})
	else:
		return json.dumps({'error': True, 'message': None})

@app.route('/post/getWhisperOut', methods=['POST'])
def getWhisperOut() -> 'json':
	global queue_rx_whisper
	if not queue_rx_whisper.empty():
		# print(queue_rx_whisper.qsize())
		# tx_data = queue_rx_whisper.get()
		# print(tx_data)

		# 큐에 있는 데이터 중 최신 데이터만 가져옴
		rx_whisper = []
		for i in range(queue_rx_whisper.qsize()):
			rx_whisper = queue_rx_whisper.get()

		whisper = {}
		whisper['val24'] = {}
		whisper['val25'] = {}
		whisper['val26'] = {}
		whisper['val27'] = {}
		whisper['val28'] = {}
		whisper['val29'] = {}
		try:
			whisper['val24']['subject'] = rx_whisper['val24']['subject']
			whisper['val24']['value'] = rx_whisper['val24']['value']
			whisper['val25']['subject'] = rx_whisper['val25']['subject']
			whisper['val25']['value'] = rx_whisper['val25']['value']
			whisper['val26']['subject'] = rx_whisper['val26']['subject']
			whisper['val26']['value'] = rx_whisper['val26']['value']
			whisper['val27']['subject'] = rx_whisper['val27']['subject']
			whisper['val27']['value'] = rx_whisper['val27']['value']
			whisper['val28']['subject'] = rx_whisper['val28']['subject']
			whisper['val28']['value'] = rx_whisper['val28']['value']
			whisper['val29']['subject'] = rx_whisper['val29']['subject']
			whisper['val29']['value'] = rx_whisper['val29']['value']
			# print(whisper)
		except Exception as e:
			print(inspect.stack()[0][3], e)
			print(rx_whisper)
			return json.dumps({'error': True, 'message': str(e)})

		return json.dumps({'error': False, 'message': whisper})
	else:
		return json.dumps({'error': True, 'message': None})

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

from enum import Enum

class Qtype(Enum):
	State = 0
	Graph = 1
	CmdJog = 2
	CmdPos = 3
	CmdStop = 4
	CmdJoy = 5
	CmdInit = 6
	CmdClearError = 7
	CmdPT = 9

class CmdType(Enum):
	Stop = 1
	SetMode = 5
	SetJogParam = 6
	SetPosParam = 7
	SetJogButton = 8
	SetPosition = 9
	StartPosControl = 10
	GetTotalInfo = 11
	InitPlatform = 15
	GetWhisper = 16
	SetJoyMode = 18
	SetTwist = 20
	SetPTParam = 21
	SetErrorMode = 22

class ModeType(Enum):
	Pos = 3
	Jog = 4
	Joy = 5

class StopType(Enum):
	Stop = 0
	Estop = 1

class ResType(Enum):
	Req = 0
	ACK = 1
	Res = 2
	Once = 4
	Period = 8

class PlatformMode(Enum):
	Jog = 0xA0
	Pos = 0xA1
	Stop = 0xA2
	Estop = 0xA3
	Joy = 0xA4
	Pose = 0xA5
	Ptable = 0xA6
	Error = 0xAA
	Init = 0xAF
	Ready = 0xAE

class PlatformState(Enum):
	Ready = 0xB0
	Run = 0xB1
	Running = 0xB2
	Stop = 0xB3
	Error = 0xB4

import socket
DUMMY_DELAY_SEC = 0.01
# DUMMY_DELAY_SEC = 0.0
RECONNECT_SEC = 3
RECONNECT_CHECK_SEC = 1
HOST = '127.0.0.1'
PORT = 10500

import time

def control_tcp(dummy):
	total_info = {
		'sensor' : {
			'front' : 0,
			'back' : 0,
			'right_front' : 0,
			'right_back' : 0
		}, 
		'pos' : {
			'x' : 0,
			'y' : 0,
			'rz' : 0,
			'ang' : 0
		},
		'platform' : {
			'mode' : 0,
			'state' : 0
		},
		'battery' : {
			'voltage' : 0,
			'current' : 0,
			'percentage' : 0
		}
	}

	whisper_info = {
		'val24' : {
			'subject' : '',
			'value' : 0
		},
		'val25' : {
			'subject' : '',
			'value' : 0
		}, 
		'val26' : {
			'subject' : '',
			'value' : 0
		}, 
		'val27' : {
			'subject' : '',
			'value' : 0
		}, 
		'val28' : {
			'subject' : '',
			'value' : 0
		}, 
		'val29' : {
			'subject' : '',
			'value' : 0
		}
	}

	retry = 0
	while True:
		try:
			# TCP 클라이언트 접속
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
				sock.connect((HOST, PORT))
				print('server connection success')

				ts_state_end = ts_state_start = time.time()
				ts_whisper_end = ts_whisper_start = time.time()

				while True:
					# 명령 수신
					data_length = 4
					# 버퍼개수 읽기(MSG_PEEK는 버퍼확인용, 버퍼 비우지 않음)
					sock.setblocking(False)
					# recv를 nonblocking할 경우 blockingioerror예외 처리해야함
					try:
						# 버퍼 비움없이 데이터 개수 받기
						# 수신 데이터 개수 확인하기(4byte)
						recv_data = sock.recv(data_length, socket.MSG_PEEK)
						if len(recv_data) >= data_length:
							# 정수형으로 데이터 변환
							packet = struct.unpack('I', recv_data)
							trail_length = packet[0]

							# 버퍼 비움없이 뒤따르는 데이터 받기
							# 실제 데이터 확인
							recv_data = sock.recv(data_length+trail_length, socket.MSG_PEEK)
							if len(recv_data) >= data_length+trail_length:
								# 버퍼 비우고 데이터 수신
								data = sock.recv(data_length+trail_length)
								# 파싱(데이터사이즈, 명령, 응답, 그외는 제외하므로 수신데이터를 슬라이싱)
								data_header = struct.unpack('IHH', data[0:8])
								data_size = data_header[0]
								data_cmd = data_header[1]
								data_res = data_header[2]
								# print('data_size: ', data_size, ' data_cmd: ', data_cmd, ' data_res: ', data_res)

								if data_cmd == CmdType.Stop.value:
									data_payload = struct.unpack('IHHI', data)
									data_value = data_payload[3]
									if data_value == StopType.Stop.value:
										print('[stop]')
									elif data_value == StopType.Estop.value:
										print('[e-stop]')
									else:
										pass
								elif data_cmd == CmdType.SetMode.value:
									data_payload = struct.unpack('IHHI', data)
									data_value = data_payload[3]
									if data_value == ModeType.Jog.value:
										print('[jog mode]')
									elif data_value == ModeType.Pos.value:
										print('[pos mode]')
									elif data_value == ModeType.Joy.value:
										print('[joy mode]')
									else:
										print('unknown data_value: ', data_value)
										while True:
											pass
								elif data_cmd == CmdType.SetJogParam.value:
									data_payload = struct.unpack('IHHddddddddd', data)
									# x, y : m/s, z : deg/s
									jog_param = {
										'x' : {
											'vel' : data_payload[3],
											'acc' : data_payload[4],
											'max' : data_payload[5]
										}, 
										'y' : {
											'vel' : data_payload[6],
											'acc' : data_payload[7],
											'max' : data_payload[8]
										},
										'z' : {
											'vel' : data_payload[9],
											'acc' : data_payload[10],
											'max' : data_payload[11]
										}
									}
									print('[jog param]', jog_param)
								elif data_cmd == CmdType.SetPosParam.value:
									data_payload = struct.unpack('IHHddddddddd', data)
									# x, y : m/s, z : deg/s
									pos_param = {
										'x' : {
											'vel' : data_payload[3],
											'acc' : data_payload[4],
											'max' : data_payload[5]
										}, 
										'y' : {
											'vel' : data_payload[6],
											'acc' : data_payload[7],
											'max' : data_payload[8]
										},
										'z' : {
											'vel' : data_payload[9],
											'acc' : data_payload[10],
											'max' : data_payload[11]
										}
									}
									print('[pos param]', pos_param)
								elif data_cmd == CmdType.SetJogButton.value:
									data_payload = struct.unpack('IHHIIIIII', data)
									jog_button = {
										'front' : data_payload[3],
										'back' : data_payload[4],
										'left' : data_payload[5],
										'right' : data_payload[6],
										'cw' : data_payload[7],
										'ccw' : data_payload[8]
									}
									print('[jog button]', jog_button)
								elif data_cmd == CmdType.SetPosition.value:
									data_payload = struct.unpack('IHHddd', data)
									# x, y : m/s, z : deg/s
									position = {
										'xm' : data_payload[3],
										'ym' : data_payload[4],
										'zdeg' : data_payload[5]
									}
									print('[position]', position)
								elif data_cmd == CmdType.StartPosControl.value:
									print('[start position control]')
								elif data_cmd == CmdType.GetTotalInfo.value:
									if data_res == ResType.ACK.value:
										# print('[get total info ACK]')
										pass
									else:
										data_payload = struct.unpack('IHHddddddddIIddd', data)
										total_info['sensor']['front'] = data_payload[3]
										total_info['sensor']['back'] = data_payload[4]
										total_info['sensor']['right_front'] = data_payload[5]
										total_info['sensor']['right_back'] = data_payload[6]
										total_info['pos']['x'] = data_payload[7]
										total_info['pos']['y'] = data_payload[8]
										total_info['pos']['rz'] = data_payload[9]
										total_info['pos']['ang'] = data_payload[10]
										total_info['platform']['mode'] = data_payload[11]
										total_info['platform']['state'] = data_payload[12]
										total_info['battery']['voltage'] = data_payload[13]
										total_info['battery']['current'] = data_payload[14]
										total_info['battery']['percentage'] = data_payload[15] * 100
								elif data_cmd == CmdType.GetWhisper.value:
									if data_res == ResType.ACK.value:
										# print('[get whisper info ACK]')
										pass
									else:
										# print('[get whisper info RES]')
										# print(type(data), data)
										# data_payload = struct.unpack('IHH', data)
										# print(data_payload)

										data_payload = struct.unpack('IHH\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd\
											QQdQQdQQd', data)
										whisperIndex = [75, 78, 81, 84, 87, 90]
										whispers = []
										for i in whisperIndex:
											whisper = {}
											whisper['subject'] = ''
											whisper['subject'] += int(data_payload[i]).to_bytes(8, 'little').decode('utf-8')
											whisper['subject'] += int(data_payload[i+1]).to_bytes(8, 'little').decode('utf-8')
											whisper['subject'] = whisper['subject'].strip()
											whisper['value'] = data_payload[i+2]
											whispers.append(whisper)

										whisper_info['val24']['subject'] = whispers[0]['subject']
										whisper_info['val24']['value'] = whispers[0]['value']
										whisper_info['val25']['subject'] = whispers[1]['subject']
										whisper_info['val25']['value'] = whispers[1]['value']
										whisper_info['val26']['subject'] = whispers[2]['subject']
										whisper_info['val26']['value'] = whispers[2]['value']
										whisper_info['val27']['subject'] = whispers[3]['subject']
										whisper_info['val27']['value'] = whispers[3]['value']
										whisper_info['val28']['subject'] = whispers[4]['subject']
										whisper_info['val28']['value'] = whispers[4]['value']
										whisper_info['val29']['subject'] = whispers[5]['subject']
										whisper_info['val29']['value'] = whispers[5]['value']
								elif data_cmd == CmdType.SetTwist.value:
									data_payload = struct.unpack('IHHdddddd', data)
									# x, y : m/s, z : deg/s
									position = {
										'x' : data_payload[3],
										'y' : data_payload[4],
										'z' : data_payload[8]
									}
									print('[twist]', position)
								elif data_cmd == CmdType.SetPTParam.value:
									data_payload = struct.unpack('IHH', data)
									print('[postable param]')
								elif data_cmd == CmdType.InitPlatform.value:
									if data_res == ResType.ACK.value:
										# print('[get InitPlatform ACK]')
										pass
									else:
										# print('[get InitPlatform RES]')
										pass
								elif data_cmd == CmdType.SetErrorMode.value:
									if data_res == ResType.ACK.value:
										# print('[get SetErrorMode ACK]')
										pass
									else:
										# print('[get SetErrorMode RES]')
										pass
								else:
									print('unknown data_cmd: ', data_cmd)
									while True:
										pass
					except BlockingIOError:
						pass
					except Exception as e:
						print(inspect.stack()[0][3], e)

					# 명령 전송
					if not queue_tx.empty():
						# print(queue_tx.qsize())
						tx_data = queue_tx.get()
						# print(tx_data)

						# tx_data['type']
						# tx_data['button']

						if tx_data['type'] == Qtype.CmdJog:
							if ('front_pushed' == tx_data['button']):
								jog_front = 1
							elif ('front_release' == tx_data['button']):
								jog_front = 0
							else:
								jog_front = 0
								
							if ('back_pushed' == tx_data['button']):
								jog_back = 1
							elif ('back_release' == tx_data['button']):
								jog_back = 0
							else:
								jog_back = 0
								
							if ('left_pushed' == tx_data['button']):
								jog_left = 1
							elif ('left_release' == tx_data['button']):
								jog_left = 0
							else:
								jog_left = 0
								
							if ('right_pushed' == tx_data['button']):
								jog_right = 1
							elif ('right_release' == tx_data['button']):
								jog_right = 0
							else:
								jog_right = 0
								
							if ('cw_pushed' == tx_data['button']):
								jog_cw = 1
							elif ('cw_release' == tx_data['button']):
								jog_cw = 0
							else:
								jog_cw = 0
								
							if ('ccw_pushed' == tx_data['button']):
								jog_ccw = 1
							elif ('ccw_release' == tx_data['button']):
								jog_ccw = 0
							else:
								jog_ccw = 0
								
							if ('fl_pushed' == tx_data['button']):
								jog_front = 1
								jog_left = 1
							elif ('fl_release' == tx_data['button']):
								jog_front = 0
								jog_left = 0
							else:
								pass
								
							if ('fr_pushed' == tx_data['button']):
								jog_front = 1
								jog_right = 1
							elif ('fr_release' == tx_data['button']):
								jog_front = 0
								jog_right = 0
							else:
								pass
								
							if ('bl_pushed' == tx_data['button']):
								jog_back = 1
								jog_left = 1
							elif ('bl_release' == tx_data['button']):
								jog_back = 0
								jog_left = 0
							else:
								pass
								
							if ('br_pushed' == tx_data['button']):
								jog_back = 1
								jog_right = 1
							elif ('br_release' == tx_data['button']):
								jog_back = 0
								jog_right = 0
							else:
								pass
							
							# set jog parameter
							command = 6
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 9
							byte_data = 8
							# set jog param : 6, set pos param : 7
							# x, y : m/s, z : deg/s
							packet = struct.pack('IHHddddddddd', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								tx_data['vel_x'], tx_data['acc_x'], tx_data['max_x'],
								tx_data['vel_y'], tx_data['acc_y'], tx_data['max_y'],
								tx_data['vel_z'], tx_data['acc_z'], tx_data['max_z'])
							# print(packet)
							sock.send(packet)
							
							# set mode
							command = 5
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							# jog mode : 4, pos mode : 3
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								4)
							# print(packet)
							sock.send(packet)
							
							# set jog button
							command = 8
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 6
							byte_data = 4
							packet = struct.pack('IHHIIIIII', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								jog_front, jog_back, jog_left, jog_right, jog_cw, jog_ccw)
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdPos:
							if ('pos_ctrl' != tx_data['button']):
								print('pos_ctrl not button')
								break
							
							# set pos parameter
							command = 7
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 9
							byte_data = 8
							# set jog param : 6, set pos param : 7
							# x, y : m/s, z : deg/s
							packet = struct.pack('IHHddddddddd', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								tx_data['vel_x'], tx_data['acc_x'], tx_data['max_x'],
								tx_data['vel_y'], tx_data['acc_y'], tx_data['max_y'],
								tx_data['vel_z'], tx_data['acc_z'], tx_data['max_z'])
							# print(packet)
							sock.send(packet)
							
							# set mode
							command = 5
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							# jog mode : 4, pos mode : 3
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								3)
							# print(packet)
							sock.send(packet)
							
							# set pos
							command = 9
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 3
							byte_data = 8
							# x, y : m/s, z : deg/s
							packet = struct.pack('IHHddd', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								tx_data['xm'], tx_data['ym'], tx_data['zdeg'])
							# print(packet)
							sock.send(packet)
							
							# start pos control
							command = 10
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 0
							byte_data = 0
							packet = struct.pack('IHH', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response)
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdStop:
							# stop(w/e-stop)
							command = 1
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							# stop : 0, e-stop : 1
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								0)
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdJoy:
							if ('joy_ctrl' != tx_data['button']):
								print('joy_ctrl not button')
								break
							
							# set joy parameter
							command = 6
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 9
							byte_data = 8
							# set jog param : 6, set pos param : 7
							# x, y : m/s, z : deg/s
							packet = struct.pack('IHHddddddddd', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								tx_data['vel_x'], tx_data['acc_x'], tx_data['max_x'],
								tx_data['vel_y'], tx_data['acc_y'], tx_data['max_y'],
								tx_data['vel_z'], tx_data['acc_z'], tx_data['max_z'])
							# print(packet)
							sock.send(packet)
							
							# set mode
							command = 5
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							# jog mode : 4, pos mode : 3, joy mode : 18
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								5)
							# print(packet)
							sock.send(packet)
							
							# set twist
							command = 20
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 6
							byte_data = 8
							# x, y : m/s, z : deg/s
							packet = struct.pack('IHHdddddd', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								tx_data['vel_x'], tx_data['vel_y'], 0.0,
								0.0, 0.0, tx_data['vel_z'])
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdInit:
							# init
							command = 15
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 0
							byte_data = 0
							# init
							packet = struct.pack('IHH', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response)
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdClearError:
							# clear error
							command = 22
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 0
							byte_data = 0
							# clear error
							packet = struct.pack('IHH', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response)
							# print(packet)
							sock.send(packet)
						elif tx_data['type'] == Qtype.CmdPT:
							if ('pt_ctrl' != tx_data['button']):
								print('pt_ctrl not button')
								break
							# print(tx_data)
							
							# set postable param
							command = 21
							response = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 0
							byte_data = 0

							packet = b''
							# order 리스트포맷 만들기
							packet += struct.pack('I', len(tx_data['orderList']))
							for order in tx_data['orderList']:
								packet += struct.pack('I', order)
							print(len(packet))
							# print(packet)
							# table 리스트포맷 만들기
							packet += struct.pack('I', len(tx_data['posTables']))
							for postable in tx_data['posTables']:
								packet += struct.pack('IIdddddddddddd',\
									postable['num'], postable['type'],\
									postable['x'], postable['y'], postable['z'],\
									postable['xvel'], postable['yvel'], postable['zvel'],\
									postable['xacc'], postable['yacc'], postable['zacc'],\
									postable['xmax'], postable['ymax'], postable['zmax'])
							print(len(packet))
							# print(packet)
							packet += struct.pack('I', 100)
							# 헤더포맷 만들기
							packet = struct.pack('IHH', size_cmd*byte_cmd+size_res*byte_res+len(packet), command, response) + packet
							print(len(packet))
							# print(packet)
							sock.send(packet)
						else:
							print('unknown qtype: ', tx_data['type'])
							while True:
								pass
					else:
						time.sleep(DUMMY_DELAY_SEC)

					ts_state_end = time.time()
					if STATE_LOOP_HZ != 0:
						if ts_state_end - ts_state_start > (1.0/STATE_LOOP_HZ):
							ts_state_start = ts_state_end
							# print(time.time())
							
							# request total info
							command = 11
							response = 0
							# data : 0 이면 1회 요청, 다른 숫자면 ms마다 자동 수신
							data = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								0)
							# print('start platform state : ', packet)
							sock.send(packet)
							
							# 플랫폼 상태 갱신
							if total_info['platform']['mode'] == PlatformMode.Jog.value:
								platform_mode = 'Jog'
							elif total_info['platform']['mode'] == PlatformMode.Pos.value:
								platform_mode = 'Pos'
							elif total_info['platform']['mode'] == PlatformMode.Stop.value:
								platform_mode = 'Stop'
							elif total_info['platform']['mode'] == PlatformMode.Estop.value:
								platform_mode = 'Estop'
							elif total_info['platform']['mode'] == PlatformMode.Joy.value:
								platform_mode = 'Joy'
							elif total_info['platform']['mode'] == PlatformMode.Pose.value:
								platform_mode = 'Pose'
							elif total_info['platform']['mode'] == PlatformMode.Ptable.value:
								platform_mode = 'Ptable'
							elif total_info['platform']['mode'] == PlatformMode.Error.value:
								platform_mode = 'Error'
							elif total_info['platform']['mode'] == PlatformMode.Init.value:
								platform_mode = 'Init'
							elif total_info['platform']['mode'] == PlatformMode.Ready.value:
								platform_mode = 'Ready'
							else:
								platform_mode = 'Unknown'

							if total_info['platform']['state'] == PlatformState.Ready.value:
								platform_state = 'Ready'
							elif total_info['platform']['state'] == PlatformState.Run.value:
								platform_state = 'Run'
							elif total_info['platform']['state'] == PlatformState.Running.value:
								platform_state = 'Running'
							elif total_info['platform']['state'] == PlatformState.Stop.value:
								platform_state = 'Stop'
							elif total_info['platform']['state'] == PlatformState.Error.value:
								platform_state = 'Error'
							else:
								platform_state = 'Unknown'

							status = {
								'type' : Qtype.State,
								'odom' : {
									'linear' : {
										'x' : '{0:.2f}'.format(total_info['pos']['x']),
										'y' : '{0:.2f}'.format(total_info['pos']['y'])
									},
									'twist' : {
										'z' : '{0:.2f}'.format(total_info['pos']['rz'])
									}
								},
								'platform' : {
									'mode' : platform_mode,
									'state' : platform_state
								},
								'battery' : {
									'voltage' : '{0:.2f}'.format(total_info['battery']['voltage']),
									'current' : '{0:.2f}'.format(total_info['battery']['current']),
									'percentage' : '{0:.2f}'.format(total_info['battery']['percentage'])
								}
							}
							# print(status)
							global queue_rx_state
							if queue_rx_state.qsize() > QUEUE_RX_STATE_CLEAR_NUM:
								get_num_rx_state = queue_rx_state.qsize() - QUEUE_RX_STATE_CLEAR_NUM
								# print("queue_rx_state.qsize(): ", queue_rx_state.qsize(), "get_num_rx_state: ", get_num_rx_state)
								for i in range(get_num_rx_state):
									queue_rx_state.get()
							queue_rx_state.put(status)

					ts_whisper_end = time.time()
					if WHISPER_LOOP_HZ != 0:
						if ts_whisper_end - ts_whisper_start > (1.0/WHISPER_LOOP_HZ):
							ts_whisper_start = ts_whisper_end
							# print(time.time())
							
							# request whisper
							command = 16
							response = 0
							# data : 0 이면 1회 요청, 다른 숫자면 ms마다 자동 수신
							data = 0
							size_cmd = 1
							byte_cmd = 2
							size_res = 1
							byte_res = 2
							size_data = 1
							byte_data = 4
							packet = struct.pack('IHHI', size_cmd*byte_cmd+size_res*byte_res+size_data*byte_data, command, response,
								0)
							# print('start whisper state : ', packet)
							sock.send(packet)

							whisper = {
								'val24' : {
									'subject' : whisper_info['val24']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val24']['value'])
									},
								'val25' : {
									'subject' : whisper_info['val25']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val25']['value'])
									},
								'val26' : {
									'subject' : whisper_info['val26']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val26']['value'])
									},
								'val27' : {
									'subject' : whisper_info['val27']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val27']['value'])
									},
								'val28' : {
									'subject' : whisper_info['val28']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val28']['value'])
									},
								'val29' : {
									'subject' : whisper_info['val29']['subject'],
									'value' : '{0:.2f}'.format(whisper_info['val29']['value'])
									}
							}
							# print(whisper)
							global queue_rx_whisper
							if queue_rx_whisper.qsize() > QUEUE_RX_WHISPER_CLEAR_NUM:
								get_num_rx_whisper = queue_rx_whisper.qsize() - QUEUE_RX_WHISPER_CLEAR_NUM
								# print("queue_rx_whisper.qsize(): ", queue_rx_whisper.qsize(), "get_num_rx_whisper: ", get_num_rx_whisper)
								for i in range(get_num_rx_whisper):
									queue_rx_whisper.get()
							queue_rx_whisper.put(whisper)
		except Exception as e:
			retry += 1
			# print(inspect.stack()[0][3], e)
			print('server connection failed')
			ts_end = ts_check = ts_start = time.time()
			while True:
				ts_end = time.time()
				if ts_end - ts_start > RECONNECT_SEC:
					ts_start = ts_end
					# print("end : ", time.time())
					break
				elif ts_end - ts_check > RECONNECT_CHECK_SEC:
					ts_check = ts_end
					# print("chk : ", time.time())
			print('server #', retry, 'reconnecting...')

if __name__ == '__main__':
	tcp_client = Process(target=control_tcp, args=(0, ))
	tcp_client.start()

	# Flask의 출력을 비활성화 할 경우
	import logging
	log = logging.getLogger('werkzeug')
	log.disabled = True

	# web_server = Process(target=app.run, args=('0.0.0.0', 8888, False))
	web_server.start()

	# tcp_client.join()
	# print("tcp client joined")
	# web_server.terminate()
	# web_server.join()
	# print("web server joined")
