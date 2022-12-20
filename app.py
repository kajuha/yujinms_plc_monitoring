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
QUEUE_RX_STATE_CLEAR_NUM = 10
queue_rx_state = Queue()
queue_tx = Queue()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

web_server = Process(target=app.run, args=('0.0.0.0', 5000, False))

@app.route('/')
@app.route('/index.html')
@app.route('/pages-main.html')
def dashboard_page() -> 'html':
	return render_template('pages-main.html')

@app.errorhandler(404)
def page_not_found(e) -> 'html':
	return render_template('pages-404.html'), 404

@app.errorhandler(500)
def internal_server_error(e) -> 'html':
	return render_template('pages-500.html'), 500

@app.route('/post/plc_x0_down', methods=['POST'], endpoint="plc_x0_down")
@app.route('/post/plc_x0_up', methods=['POST'], endpoint="plc_x0_up")
def plc_x0_button() -> 'json':
	# print(request.endpoint)

	try:
		button = {
			'address' : 'x0',
			'state' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/plc_x1_down', methods=['POST'], endpoint="plc_x1_down")
@app.route('/post/plc_x1_up', methods=['POST'], endpoint="plc_x1_up")
def plc_x1_button() -> 'json':
	# print(request.endpoint)

	try:
		button = {
			'address' : 'x1',
			'state' : request.endpoint
		}
		global queue_tx
		queue_tx.put(button)
	except Exception as e:
		print(inspect.stack()[0][3], e)
		return json.dumps({'error': True, 'message': str(e)})

	return json.dumps({'error': False})

@app.route('/post/getData', methods=['POST'])
def getData() -> 'json':
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
		try:
			status['plc_m0'] = '{0}'.format(rx_state['plc_m0'])
			status['plc_m1'] = '{0}'.format(rx_state['plc_m1'])
			status['plc_m2'] = '{0}'.format(rx_state['plc_m2'])
			status['plc_x0'] = '{0}'.format(rx_state['plc_x0'])
			status['plc_x1'] = '{0}'.format(rx_state['plc_x1'])
			# print(status)
		except Exception as e:
			print(inspect.stack()[0][3], e)
			return json.dumps({'error': True, 'message': str(e)})

		return json.dumps({'error': False, 'message': status})
	else:
		return json.dumps({'error': False, 'message': None})

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    
@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

PLC_HOST = '192.168.0.211'
PLC_PORT = 6000

IS_SIMULATION = True

import pymcprotocol
import time

def control_plc(dummy):
	if IS_SIMULATION:
		print("IS_SIMULATION:", IS_SIMULATION)

		PLC_SM412_SEC = 0.5
		ts_sm412_end = ts_sm412_start = time.time()

		plc_m0 = 0
		plc_m1 = 0
		plc_m2 = 0
		plc_x0 = 0
		plc_x1 = 0

		plc_m0s = [plc_m0]
		plc_m1s = [plc_m1]
		plc_m2s = [plc_m2]
		plc_x0s = [plc_x0]
		plc_x1s = [plc_x1]
	else:
		pymc3e = pymcprotocol.Type3E()

		pymc3e.setaccessopt(commtype="ascii")
		pymc3e.connect(PLC_HOST, PLC_PORT)

	ts_state_end = ts_state_start = time.time()

	while True:
		if not queue_tx.empty():
			# print(queue_tx.qsize())
			tx_data = queue_tx.get()
			print(tx_data)

			if IS_SIMULATION:
				if tx_data['address'] == 'x0':
					if tx_data['state'] == 'plc_x0_down':
						plc_x0 = 1
					elif tx_data['state'] == 'plc_x0_up':
						plc_x0 = 0
					else:
						pass

				if tx_data['address'] == 'x1':
					if tx_data['state'] == 'plc_x1_down':
						plc_x1 = 1
					elif tx_data['state'] == 'plc_x1_up':
						plc_x1 = 0
					else:
						pass
			else:
				if tx_data['address'] == 'x0':
					if tx_data['state'] == 'plc_x0_down':
						pymc3e.batchwrite_bitunits(headdevice="X0", values=[1])
					elif tx_data['state'] == 'plc_x0_up':
						pymc3e.batchwrite_bitunits(headdevice="X0", values=[0])
					else:
						pass

				if tx_data['address'] == 'x1':
					if tx_data['state'] == 'plc_x1_down':
						pymc3e.batchwrite_bitunits(headdevice="X1", values=[1])
					elif tx_data['state'] == 'plc_x1_up':
						pymc3e.batchwrite_bitunits(headdevice="X1", values=[0])
					else:
						pass

		ts_state_end = time.time()
		if ts_state_end - ts_state_start > (1.0/STATE_LOOP_HZ):
			if STATE_LOOP_HZ != 0:
				ts_state_start = ts_state_end
				# print(time.time())
				
				if IS_SIMULATION:
					ts_sm412_end = time.time()
					if (ts_sm412_end - ts_sm412_start) > PLC_SM412_SEC:
						ts_sm412_start = ts_sm412_end
						if plc_m0 == 0:
							# print('plc_m0 == 0')
							plc_m0 = 1
						elif plc_m0 == 1:
							# print('plc_m0 == 1')
							plc_m0 = 0
						else:
							pass

					plc_m0s = [plc_m0]
					if (plc_x0 or plc_m1) and (not plc_x1):
						plc_m1 = 1
					else:
						plc_m1 = 0
					plc_m1s = [plc_m1]
					plc_m2s = [plc_x1]
					plc_x0s = [plc_x0]
					plc_x1s = [plc_x1]
				else:
					plc_m0s = pymc3e.batchread_bitunits(headdevice="M0", readsize=1)
					plc_m1s = pymc3e.batchread_bitunits(headdevice="M1", readsize=1)
					plc_m2s = pymc3e.batchread_bitunits(headdevice="M2", readsize=1)
					# print(plc_m0s[0])
					# print(plc_m1s[0])
					# print(plc_m2s[0])
					plc_x0s = pymc3e.batchread_bitunits(headdevice="X0", readsize=1)
					plc_x1s = pymc3e.batchread_bitunits(headdevice="X1", readsize=1)
					# print(plc_x0s[0])
					# print(plc_x1s[0])

				status = {}
				status['plc_m0'] = plc_m0s[0]
				status['plc_m1'] = plc_m1s[0]
				status['plc_m2'] = plc_m2s[0]
				status['plc_x0'] = plc_x0s[0]
				status['plc_x1'] = plc_x1s[0]

				global queue_rx_state
				if queue_rx_state.qsize() > QUEUE_RX_STATE_CLEAR_NUM:
					get_num_rx_state = queue_rx_state.qsize() - QUEUE_RX_STATE_CLEAR_NUM
					# print("queue_rx_state.qsize(): ", queue_rx_state.qsize(), "get_num_rx_state: ", get_num_rx_state)
					for i in range(get_num_rx_state):
						queue_rx_state.get()
				queue_rx_state.put(status)

if __name__ == '__main__':
	plc_client = Process(target=control_plc, args=(0, ))
	plc_client.start()

	# Flask의 출력을 비활성화 할 경우
	import logging
	log = logging.getLogger('werkzeug')
	log.disabled = True
	# log.disabled = False

	web_server.start()

	plc_client.join()